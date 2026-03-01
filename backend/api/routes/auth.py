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

from ..dependencies import (
    get_collection_repo, is_admin_user, _promote_bootstrap_admin,
    blacklist_token, decode_jwt_token,
)
from ..main import limiter

router = APIRouter(prefix="/api/auth", tags=["auth"])

GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 1

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


def _is_dev_mode() -> bool:
    """Check if running in development mode."""
    return os.getenv("DECKDEX_PROFILE", "default") in ("default", "development")


def _backend_origin(request: Request) -> str:
    """Derive the public backend origin from the incoming request."""
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    return f"{proto}://{host}"


def _frontend_origin(request: Request) -> str:
    """Derive the public frontend origin."""
    origin = request.headers.get("origin")
    if origin:
        return origin.rstrip("/")

    referer = request.headers.get("referer")
    if referer:
        from urllib.parse import urlparse
        parsed = urlparse(referer)
        return f"{parsed.scheme}://{parsed.netloc}"

    backend = _backend_origin(request)
    if "-8000." in backend:
        return backend.replace("-8000.", "-5173.")
    return backend.replace(":8000", ":5173")

# Temporary in-memory store for one-time auth codes: code -> {jwt, expires}
_auth_codes: Dict[str, Dict[str, Any]] = {}


def _cleanup_expired_auth_codes():
    """Remove expired one-time auth codes to prevent memory leak."""
    now = datetime.utcnow()
    expired = [k for k, v in _auth_codes.items() if v["expires"] < now]
    for k in expired:
        del _auth_codes[k]
    if expired:
        logger.debug(f"Cleaned up {len(expired)} expired auth codes")


def _set_jwt_cookie(response: Response, token: str):
    """Set JWT as HTTP-only cookie on the response."""
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        path="/",
        max_age=3600,
        secure=not _is_dev_mode(),
    )


# Models
class UserPayload(BaseModel):
    id: int
    email: str
    display_name: Optional[str] = None
    picture: Optional[str] = None
    is_admin: bool = False


def create_jwt(user: Dict[str, Any]) -> str:
    """Create JWT token with user payload including JTI for revocation."""
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY environment variable not set")

    payload = {
        "sub": str(user.get("id")),
        "email": user.get("email"),
        "display_name": user.get("display_name"),
        "picture": user.get("picture"),
        "jti": str(uuid.uuid4()),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> Dict[str, Any]:
    """Validate and decode JWT token."""
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY environment variable not set")
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])


def get_current_user_from_request(request: Request) -> Dict[str, Any]:
    """
    Extract and validate JWT from cookie (primary) or Authorization header (fallback).
    Returns decoded user payload or raises 401.
    """
    token: Optional[str] = None

    # 1. Cookie (primary — HTTP-only cookie set by backend)
    token = request.cookies.get("access_token")

    # 2. Fallback: Authorization header (for API/non-browser clients)
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        payload = decode_jwt_token(token)
        return payload
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


@router.get("/google")
@limiter.limit("10/minute")
async def google_login(request: Request):
    """Redirect to Google OAuth consent screen."""
    if not GOOGLE_OAUTH_CLIENT_ID:
        logger.error("GOOGLE_OAUTH_CLIENT_ID not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth not configured"
        )

    callback_url = f"{_backend_origin(request)}/api/auth/callback"

    query_params = {
        "client_id": GOOGLE_OAUTH_CLIENT_ID,
        "redirect_uri": callback_url,
        "response_type": "code",
        "scope": "openid email profile",
    }

    redirect_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(query_params)}"

    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=redirect_url)


@router.get("/callback")
@limiter.limit("10/minute")
async def oauth_callback(request: Request, code: str = None, error: str = None):
    """Google OAuth callback — exchange code, create/update user, issue one-time auth code."""
    frontend = _frontend_origin(request)
    login_error_url = f"{frontend}/login?error=auth_failed"

    if error:
        logger.error(f"OAuth callback error: {error}")
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=login_error_url)

    if not code:
        logger.error("No authorization code in callback")
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=login_error_url)

    if not GOOGLE_OAUTH_CLIENT_ID or not GOOGLE_OAUTH_CLIENT_SECRET:
        logger.error("Google OAuth credentials not configured")
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=login_error_url)

    try:
        callback_url = f"{_backend_origin(request)}/api/auth/callback"

        token_data = {
            "client_id": GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": callback_url,
        }

        async with httpx.AsyncClient() as client:
            token_response = await client.post(GOOGLE_TOKEN_URL, data=token_data)
            token_response.raise_for_status()
            tokens = token_response.json()

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
            return RedirectResponse(url=login_error_url)

        repo = get_collection_repo()
        if not repo:
            logger.error("Database not configured")
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=login_error_url)

        user = None
        try:
            user = repo.get_user_by_google_id(google_id)
        except Exception as e:
            logger.debug(f"User lookup by google_id failed: {e}")

        if not user:
            try:
                user = repo.get_user_by_email(email)
                if user and user.get("google_id") == "__seed_pending__":
                    repo.update_user_google_id(user["id"], google_id)
                    user["google_id"] = google_id
            except Exception as e:
                logger.debug(f"User lookup by email failed: {e}")

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
                return RedirectResponse(url=login_error_url)

        try:
            repo.update_user_last_login(user["id"])
        except Exception as e:
            logger.debug(f"Failed to update last_login: {e}")

        jwt_token = create_jwt({
            "id": user["id"],
            "email": user["email"],
            "display_name": user.get("display_name"),
            "picture": user.get("avatar_url")
        })

        # Clean up expired codes before adding new one
        _cleanup_expired_auth_codes()

        auth_code = str(uuid.uuid4())
        _auth_codes[auth_code] = {
            "jwt": jwt_token,
            "expires": datetime.utcnow() + timedelta(minutes=5),
        }

        logger.info(f"User id={user['id']} logged in successfully")
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"{frontend}/auth/callback?code={auth_code}")

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=login_error_url)


@router.get("/exchange")
@limiter.limit("10/minute")
async def exchange_auth_code(request: Request, response: Response, code: str = ""):
    """Exchange a one-time auth code for a JWT set as HTTP-only cookie."""
    entry = _auth_codes.pop(code, None)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")
    if datetime.utcnow() > entry["expires"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")

    jwt_token = entry["jwt"]
    try:
        decode_jwt(jwt_token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

    # Set JWT as HTTP-only cookie
    _set_jwt_cookie(response, jwt_token)

    return {"ok": True}


@router.get("/me", response_model=Optional[UserPayload])
async def get_current_user(request: Request):
    """Get current authenticated user from database (always fresh)."""
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
                text("SELECT id, email, display_name, avatar_url, is_admin FROM users WHERE id = :id"),
                {"id": user_id}
            ).mappings().fetchone()
        if row is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        admin = bool(row.get("is_admin")) or is_admin_user(row["email"])
        if admin:
            _promote_bootstrap_admin(row["email"])
        return UserPayload(
            id=row["id"],
            email=row["email"],
            display_name=row.get("display_name"),
            picture=row.get("avatar_url"),
            is_admin=admin,
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


# Domains allowed for avatar URLs (Google profile pics, Gravatar, etc.)
_SAFE_AVATAR_DOMAINS = {
    "lh3.googleusercontent.com",
    "lh4.googleusercontent.com",
    "lh5.googleusercontent.com",
    "lh6.googleusercontent.com",
    "googleusercontent.com",
    "gravatar.com",
    "www.gravatar.com",
    "avatars.githubusercontent.com",
}


def _validate_avatar_url(url: Optional[str]) -> Optional[str]:
    """Validate that avatar_url is a safe HTTPS URL or None."""
    if not url:
        return None
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="avatar_url must use HTTPS",
        )
    host = (parsed.hostname or "").lower()
    if not any(host == d or host.endswith("." + d) for d in _SAFE_AVATAR_DOMAINS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="avatar_url domain not allowed",
        )
    return url


@router.patch("/profile", response_model=UserPayload)
async def update_profile(request: Request, body: ProfileUpdateRequest):
    """Update authenticated user's display_name and/or avatar_url."""
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 500 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Request body too large (max 500KB)")

    # Validate avatar_url if provided
    if body.avatar_url is not None:
        body.avatar_url = _validate_avatar_url(body.avatar_url)

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


@router.post("/refresh")
async def refresh_token(request: Request, response: Response):
    """
    Silent token refresh: issue a new JWT if the current one is still valid.
    The old token's JTI is blacklisted so it cannot be reused.
    Sets the new JWT as an HTTP-only cookie.
    """
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_jwt_token(token)
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    # Blacklist old token
    old_jti = payload.get("jti")
    old_exp = payload.get("exp")
    if old_jti and old_exp:
        blacklist_token(old_jti, datetime.utcfromtimestamp(old_exp))

    # Issue new token with same user info
    new_token = create_jwt({
        "id": payload.get("sub"),
        "email": payload.get("email"),
        "display_name": payload.get("display_name"),
        "picture": payload.get("picture"),
    })
    _set_jwt_cookie(response, new_token)
    return {"ok": True}


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout: blacklist current token and clear cookie."""
    # Try to blacklist the current token
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if token:
        try:
            payload = decode_jwt(token)
            jti = payload.get("jti")
            exp_ts = payload.get("exp")
            if jti and exp_ts:
                blacklist_token(jti, datetime.utcfromtimestamp(exp_ts))
        except (JWTError, Exception):
            pass  # Token already expired or invalid — fine

    response.delete_cookie(key="access_token", httponly=True, samesite="lax", path="/")
    logger.info("User logged out")
    return {"message": "Logged out successfully"}


@router.get("/health")
async def health():
    """Health check endpoint (no auth required)"""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Avatar proxy — serves cached user avatars instead of leaking external URLs
# ---------------------------------------------------------------------------
import hashlib
from pathlib import Path
from fastapi.responses import FileResponse

_AVATAR_CACHE_DIR = Path(
    os.getenv("DECKDEX_AVATAR_DIR", os.path.join(os.path.dirname(__file__), "../../../data/avatars"))
).resolve()
_AVATAR_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Max avatar download size (2 MB)
_MAX_AVATAR_BYTES = 2 * 1024 * 1024


@router.get("/avatar/{user_id}")
async def get_avatar(user_id: int, request: Request):
    """Proxy endpoint that serves a locally cached copy of the user's avatar.

    On first request (cache miss), downloads the avatar from the stored
    ``avatar_url``, saves it to disk, and serves it.  Subsequent requests
    serve from cache.  Returns 404 if the user has no avatar.
    """
    # Authenticate
    get_current_user_from_request(request)

    repo = get_collection_repo()
    if repo is None:
        raise HTTPException(status_code=503, detail="Database not configured")

    from sqlalchemy import text
    with repo._get_engine().connect() as conn:
        row = conn.execute(
            text("SELECT avatar_url FROM users WHERE id = :id"),
            {"id": user_id},
        ).fetchone()

    if row is None or not row[0]:
        raise HTTPException(status_code=404, detail="No avatar")

    avatar_url: str = row[0]

    # Deterministic cache key from URL
    url_hash = hashlib.sha256(avatar_url.encode()).hexdigest()[:16]
    cache_path = _AVATAR_CACHE_DIR / f"{user_id}_{url_hash}.img"

    if cache_path.exists():
        # Guess content type from magic bytes
        ct = _guess_content_type(cache_path)
        return FileResponse(cache_path, media_type=ct)

    # Download avatar (validate domain first)
    from urllib.parse import urlparse
    parsed = urlparse(avatar_url)
    if parsed.scheme != "https":
        raise HTTPException(status_code=400, detail="Avatar URL must be HTTPS")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(avatar_url)
            resp.raise_for_status()
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to fetch avatar")

    if len(resp.content) > _MAX_AVATAR_BYTES:
        raise HTTPException(status_code=502, detail="Avatar too large")

    # Write to cache atomically
    import tempfile
    fd, tmp = tempfile.mkstemp(dir=_AVATAR_CACHE_DIR)
    try:
        os.write(fd, resp.content)
        os.close(fd)
        os.replace(tmp, cache_path)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise

    ct = resp.headers.get("content-type", "image/jpeg")
    return FileResponse(cache_path, media_type=ct)


def _guess_content_type(path: Path) -> str:
    """Guess image content type from file magic bytes."""
    try:
        header = path.read_bytes()[:8]
        if header[:3] == b"\xff\xd8\xff":
            return "image/jpeg"
        if header[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        if header[:4] == b"RIFF" and header[8:12] == b"WEBP" if len(header) >= 12 else False:
            return "image/webp"
    except Exception:
        pass
    return "image/jpeg"
