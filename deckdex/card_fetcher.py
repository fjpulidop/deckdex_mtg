import os
import re
import time
import random
import json
import requests
from typing import Dict, Any, Optional, List, Tuple
from loguru import logger
from rapidfuzz import fuzz
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError, RateLimitError, APIConnectionError, AuthenticationError, BadRequestError, APIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class CardFetcher:
    """Fetches card data from Scryfall API."""
    
    BASE_URL = "https://api.scryfall.com"
    MAX_RETRIES = 3
    RETRY_DELAY = 0.5
    
    def __init__(self):
        """Initialize the CardFetcher."""
        load_dotenv()
        # Initialize OpenAI client if API key is present
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
            self.openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        else:
            self.openai_client = None
            self.openai_model = None
            logger.info("OpenAI API key not found, card analysis will be disabled")
        
    def _make_request(self, url: str) -> Dict[str, Any]:
        """
        Make a request to the Scryfall API with retry logic.
        
        Args:
            url: The URL to request.
            
        Returns:
            The JSON response from the API.
            
        Raises:
            Exception: If the request fails after retries.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.get(url)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt == self.MAX_RETRIES - 1:
                    # No registramos el error en el log, solo lo propagamos
                    raise
                time.sleep(self.RETRY_DELAY * (2 ** attempt))
    
    def _exact_match_search(self, card_name: str) -> Optional[Dict[str, Any]]:
        """
        Search for a card by exact name.
        
        Args:
            card_name: The exact name of the card.
            
        Returns:
            The card data if found, None otherwise.
        """
        url = f"{self.BASE_URL}/cards/named?exact={card_name}"
        try:
            return self._make_request(url)
        except Exception:
            return None
    
    def _fuzzy_match_search(self, card_name: str) -> Optional[Dict[str, Any]]:
        """
        Search for a card by fuzzy name matching.
        
        Args:
            card_name: The approximate name of the card.
            
        Returns:
            The card data if found, None otherwise.
        """
        url = f"{self.BASE_URL}/cards/named?fuzzy={card_name}"
        try:
            return self._make_request(url)
        except Exception:
            return None
    
    def _search_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Search for a card using a full-text search query.
        
        Args:
            query: The search query.
            
        Returns:
            The first card data if found, None otherwise.
        """
        url = f"{self.BASE_URL}/cards/search?q={query}"
        try:
            response = self._make_request(url)
            if response.get("data") and len(response["data"]) > 0:
                return response["data"][0]
            return None
        except Exception:
            return None
    
    def search_card(self, card_name: str) -> Dict[str, Any]:
        """
        Search for a card using multiple strategies.
        
        Args:
            card_name: The name of the card to search for.
            
        Returns:
            The card data if found.
            
        Raises:
            Exception: If the card cannot be found using any strategy.
        """
        # Estrategia 1: Búsqueda exacta
        result = self._exact_match_search(card_name)
        if result:
            return result
        
        # Estrategia 2: Búsqueda difusa
        result = self._fuzzy_match_search(card_name)
        if result:
            return result
        
        # Estrategia 3: Búsqueda de frase exacta
        result = self._search_query(f'!"{card_name}"')
        if result:
            return result
        
        # Estrategia 4: Búsqueda con expresión regular
        # Eliminar caracteres especiales y construir una consulta más flexible
        simplified_name = re.sub(r'[^\w\s]', '', card_name).strip()
        words = simplified_name.split()
        if len(words) > 1:
            regex_query = " ".join([f"/{word}/i" for word in words])
            result = self._search_query(regex_query)
            if result:
                return result
        
        # Si llegamos aquí, no pudimos encontrar la carta
        # No registramos el error en el log, solo lo propagamos
        raise Exception(f"Card not found: {card_name}")
    
    def _validate_analysis(self, result: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """
        Validate and sanitize OpenAI analysis response.
        
        Args:
            result: Dictionary containing strategy and tier from OpenAI.
            
        Returns:
            Tuple of (strategy, tier) with validated values.
        """
        # Extract and validate strategy
        strategy = result.get("strategy")
        if strategy and not isinstance(strategy, str):
            strategy = str(strategy)
        if strategy and len(strategy) > 500:
            strategy = strategy[:500]
        
        # Extract and validate tier
        tier = result.get("tier", "").upper()
        if tier not in ["S", "A", "B", "C", "D"]:
            if tier:  # Only log if tier was present but invalid
                logger.warning(f"Invalid tier '{tier}', defaulting to None")
            tier = None
        
        return strategy, tier
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type(RateLimitError)
    )
    def _call_openai(self, messages: List[Dict[str, str]]) -> Any:
        """
        Call OpenAI Chat Completions API with retry logic for rate limits.
        
        Args:
            messages: List of message dicts with role and content.
            
        Returns:
            OpenAI response object.
        """
        return self.openai_client.chat.completions.create(
            model=self.openai_model,
            messages=messages,
            response_format={"type": "json_object"},
            max_tokens=150,
            temperature=0.7
        )
    
    def get_card_info(self, card_name: str) -> Tuple[Dict[str, Any], Optional[str], Optional[str]]:
        """
        Get card data and generate game strategy and tier using OpenAI Chat Completions API.
        
        Uses JSON mode for structured output and includes granular error handling
        with automatic retry logic for rate limits.
        
        Args:
            card_name: The name of the card.
            
        Returns:
            A tuple of (card_data, game_strategy, tier).
            Returns (card_data, None, None) if OpenAI is disabled or on error.
        """
        card_data = self.search_card(card_name)
        
        # Early return if OpenAI client is not initialized
        if not self.openai_client:
            return card_data, None, None
        
        try:
            # Build card text for analysis
            card_text = f"Name: {card_data.get('name')}\n"
            card_text += f"Type: {card_data.get('type_line')}\n"
            card_text += f"Text: {card_data.get('oracle_text')}\n"
            
            if 'power' in card_data and 'toughness' in card_data:
                card_text += f"Power/Toughness: {card_data.get('power')}/{card_data.get('toughness')}\n"
            
            if 'loyalty' in card_data:
                card_text += f"Loyalty: {card_data.get('loyalty')}\n"
            
            # Create messages for Chat Completions API
            system_message = {
                "role": "system",
                "content": (
                    "You are an expert Magic: The Gathering analyst. "
                    "Analyze cards and provide strategic insights. "
                    "Always respond with valid JSON containing 'strategy' and 'tier' fields."
                )
            }
            
            user_message = {
                "role": "user",
                "content": (
                    f"Analyze this MTG card:\n\n{card_text}\n\n"
                    f"Provide:\n"
                    f"1. strategy: Brief game strategy (2-3 sentences max)\n"
                    f"2. tier: Power level (S/A/B/C/D only)\n\n"
                    f"Return as JSON with keys 'strategy' and 'tier'."
                )
            }
            
            # Call OpenAI with retry logic (via decorator)
            response = self._call_openai([system_message, user_message])
            
            # Parse JSON response
            result = json.loads(response.choices[0].message.content)
            
            # Validate and extract strategy and tier
            strategy, tier = self._validate_analysis(result)
            
            return card_data, strategy, tier
            
        except AuthenticationError as e:
            logger.critical(f"OpenAI authentication failed: {e}")
            return card_data, None, None
        except RateLimitError as e:
            # This is caught after retries are exhausted
            logger.error(f"OpenAI rate limit exceeded after retries: {e}")
            return card_data, None, None
        except BadRequestError as e:
            logger.error(f"OpenAI invalid request: {e}")
            return card_data, None, None
        except APIConnectionError as e:
            logger.error(f"OpenAI connection error: {e}")
            return card_data, None, None
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return card_data, None, None
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse OpenAI JSON response: {e}")
            return card_data, None, None
        except Exception as e:
            logger.error(f"Unexpected error during OpenAI analysis: {e}")
            return card_data, None, None

