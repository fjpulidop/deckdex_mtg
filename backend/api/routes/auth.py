"""
Authentication routes for Google OAuth 2.0
Handles OAuth callback, JWT issuance, user lookup, and logout
"""
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode

from fastapi import APIRouter, Request, Response, HTTPException, status
from pydantic import BaseModel
import httpx
from jose import jwt, JWTError
from loguru import logger

from ..dependencies import get_collection_repo

router = APIRouter(prefix="/api/auth", tags=["auth"])

GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 1

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

# Temporary in-memory store for one-time auth codes: code -> {jwt, expires}
# Codes are single-use and expire after 5 minutes.
_auth_codes: Dict[str, Dict[str, Any]] = {}

# Models
class UserPayload(BaseModel):
    id: int
    email: str
    display_name: Optional[str] = None
    picture: Optional[str] = None


def create_jwt(user: Dict[str, Any]) -> str:
    """
    Create JWT token with user payload.
    Uses HS256 algorithm and includes 1h expiry.
    
    Args:
        user: Dictionary with 'id', 'email', 'display_name', 'picture' keys
        
    Returns:
        Signed JWT token
    """
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY environment variable not set")
    
    payload = {
        "sub": str(user.get("id")),
        "email": user.get("email"),
        "display_name": user.get("display_name"),
        "picture": user.get("picture"),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> Dict[str, Any]:
    """
    Validate and decode JWT token.
    Raises JWTError if token is invalid or expired.
    
    Args:
        token: JWT token to decode
        
    Returns:
        Decoded token payload
    """
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY environment variable not set")
    
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])


def get_current_user_from_request(request: Request) -> Dict[str, Any]:
    """
    Extract and validate JWT from Authorization header (preferred) or cookie.
    Returns decoded user payload or raises 401.

    The frontend stores the JWT in sessionStorage and sends it via
    ``Authorization: Bearer <token>``.  Cookie-based auth is kept as a
    fallback for non-browser clients or future use.
    """
    token: Optional[str] = None

    # 1. Authorization header (preferred — works through Vite proxy in Docker)
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]

    # 2. Fallback: cookie
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        payload = decode_jwt(token)
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


@router.get("/google")
async def google_login():
    """
    Redirect to Google OAuth consent screen.
    The user logs in with their Google account, consents to share openid/email/profile,
    and is redirected to /api/auth/callback with an authorization code.
    """
    if not GOOGLE_OAUTH_CLIENT_ID:
        logger.error("GOOGLE_OAUTH_CLIENT_ID not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth not configured"
        )
    
    # Redirect to Google OAuth consent screen
    query_params = {
        "client_id": GOOGLE_OAUTH_CLIENT_ID,
        "redirect_uri": "http://localhost:8000/api/auth/callback",  # Will be updated for production
        "response_type": "code",
        "scope": "openid email profile",
    }
    
    redirect_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(query_params)}"
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=redirect_url)


@router.get("/callback")
async def oauth_callback(code: str = None, error: str = None):
    """
    Google OAuth callback endpoint.
    Exchange authorization code for ID token, extract user info, create/update user, and set JWT cookie.
    """
    if error:
        logger.error(f"OAuth callback error: {error}")
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="http://localhost:5173/login?error=auth_failed")
    
    if not code:
        logger.error("No authorization code in callback")
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="http://localhost:5173/login?error=auth_failed")
    
    if not GOOGLE_OAUTH_CLIENT_ID or not GOOGLE_OAUTH_CLIENT_SECRET:
        logger.error("Google OAuth credentials not configured")
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="http://localhost:5173/login?error=auth_failed")
    
    try:
        # Exchange code for tokens
        token_data = {
            "client_id": GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": "http://localhost:8000/api/auth/callback",
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(GOOGLE_TOKEN_URL, data=token_data)
            token_response.raise_for_status()
            tokens = token_response.json()
        
        # Get user info from ID token or userinfo endpoint
        # For simplicity, we'll use the userinfo endpoint which doesn't require parsing the ID token
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {tokens.get('access_token')}"}
            userinfo_response = await client.get(GOOGLE_USERINFO_URL, headers=headers)
            userinfo_response.raise_for_status()
            userinfo = userinfo_response.json()
        
        google_id = userinfo.get("sub")
        email = userinfo.get("email")
        name = userinfo.get("name")
        picture = userinfo.get("picture")
        
        if not google_id or not email:
            logger.error("Missing required fields in Google userinfo")
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="http://localhost:5173/login?error=auth_failed")
        
        # Get or create user in database
        repo = get_collection_repo()
        if not repo:
            logger.error("Database not configured")
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="http://localhost:5173/login?error=auth_failed")
        
        # Check if user exists by google_id
        user = None
        try:
            # Try to get the user from the repository (will need to implement this method)
            user = repo.get_user_by_google_id(google_id)
        except Exception as e:
            logger.debug(f"User lookup by google_id failed: {e}")
        
        # If not found by google_id, check if this is the seed user (email match + __seed_pending__)
        if not user:
            try:
                user = repo.get_user_by_email(email)
                if user and user.get("google_id") == "__seed_pending__":
                    # This is the seed user, update the google_id
                    repo.update_user_google_id(user["id"], google_id)
                    user["google_id"] = google_id
            except Exception as e:
                logger.debug(f"User lookup by email failed: {e}")
        
        # Create new user if not found
        if not user:
            try:
                user = repo.create_user(
                    google_id=google_id,
                    email=email,
                    display_name=name,
                    avatar_url=picture
                )
            except Exception as e:
                logger.error(f"Failed to create user: {e}")
                from fastapi.responses import RedirectResponse
                return RedirectResponse(url="http://localhost:5173/login?error=auth_failed")
        
        # Update last_login
        try:
            repo.update_user_last_login(user["id"])
        except Exception as e:
            logger.debug(f"Failed to update last_login: {e}")
        
        # Create JWT
        jwt_token = create_jwt({
            "id": user["id"],
            "email": user["email"],
            "display_name": user.get("display_name"),
            "picture": user.get("avatar_url")
        })

        # Store JWT under a one-time code so the frontend can exchange it
        # via the Vite proxy (same origin), which allows the cookie to be
        # set correctly in the browser.
        code = str(uuid.uuid4())
        _auth_codes[code] = {
            "jwt": jwt_token,
            "expires": datetime.utcnow() + timedelta(minutes=5),
        }

        logger.info(f"User {email} logged in successfully")
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"http://localhost:5173/auth/callback?code={code}")
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="http://localhost:5173/login?error=auth_failed")


@router.get("/exchange")
async def exchange_auth_code(code: str):
    """
    Exchange a one-time auth code (issued by /callback) for a JWT token.
    The frontend stores the token in sessionStorage and sends it via
    Authorization header on subsequent requests.
    """
    entry = _auth_codes.pop(code, None)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")
    if datetime.utcnow() > entry["expires"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")

    jwt_token = entry["jwt"]
    try:
        payload = decode_jwt(jwt_token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

    # Return token in body so the frontend can set the cookie itself via JS.
    # (Vite's dev proxy does not reliably forward Set-Cookie headers from the
    # backend to the browser, so we let the frontend set the cookie directly.)
    return {"ok": True, "token": jwt_token}


@router.get("/me", response_model=Optional[UserPayload])
async def get_current_user(request: Request):
    """
    Get current authenticated user from database (always fresh).
    Returns 401 if not authenticated.
    """
    try:
        payload = get_current_user_from_request(request)
        user_id = int(payload.get("sub", 0))
        repo = get_collection_repo()
        if repo is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database not configured"
            )
        from sqlalchemy import text
        with repo._get_engine().connect() as conn:
            row = conn.execute(
                text("SELECT id, email, display_name, avatar_url FROM users WHERE id = :id"),
                {"id": user_id}
            ).mappings().fetchone()
        if row is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return UserPayload(
            id=row["id"],
            email=row["email"],
            display_name=row.get("display_name"),
            picture=row.get("avatar_url")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )


class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


@router.patch("/profile", response_model=UserPayload)
async def update_profile(request: Request, body: ProfileUpdateRequest):
    """
    Update authenticated user's display_name and/or avatar_url.
    Returns 413 if request body exceeds 500KB.
    """
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 500 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Request body too large (max 500KB)")

    payload = get_current_user_from_request(request)
    user_id = int(payload.get("sub", 0))
    repo = get_collection_repo()
    if repo is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database not configured")

    updated = repo.update_user_profile(
        user_id=user_id,
        display_name=body.display_name,
        avatar_url=body.avatar_url,
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserPayload(
        id=updated["id"],
        email=updated["email"],
        display_name=updated.get("display_name"),
        picture=updated.get("avatar_url"),
    )


@router.post("/logout")
async def logout(response: Response):
    """
    Logout current user.
    Clears the JWT cookie.
    """
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    logger.info("User logged out")
    return {"message": "Logged out successfully"}


@router.get("/health")
async def health():
    """Health check endpoint (no auth required)"""
    return {"status": "ok"}
