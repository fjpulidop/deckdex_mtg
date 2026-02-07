import os
import re
import time
import random
import requests
from typing import Dict, Any, Optional, List, Tuple
from loguru import logger
from rapidfuzz import fuzz
from dotenv import load_dotenv


class CardFetcher:
    """Fetches card data from Scryfall API."""
    
    BASE_URL = "https://api.scryfall.com"
    MAX_RETRIES = 3
    RETRY_DELAY = 0.5
    
    def __init__(self):
        """Initialize the CardFetcher."""
        load_dotenv()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
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
    
    def get_card_info(self, card_name: str) -> Tuple[Dict[str, Any], Optional[str], Optional[str]]:
        """
        Get card data and generate game strategy and tier using OpenAI.
        
        Args:
            card_name: The name of the card.
            
        Returns:
            A tuple of (card_data, game_strategy, tier).
        """
        card_data = self.search_card(card_name)
        
        if not self.openai_api_key:
            return card_data, None, None
        
        try:
            import openai
            openai.api_key = self.openai_api_key
            
            card_text = f"Name: {card_data.get('name')}\n"
            card_text += f"Type: {card_data.get('type_line')}\n"
            card_text += f"Text: {card_data.get('oracle_text')}\n"
            
            if 'power' in card_data and 'toughness' in card_data:
                card_text += f"Power/Toughness: {card_data.get('power')}/{card_data.get('toughness')}\n"
            
            if 'loyalty' in card_data:
                card_text += f"Loyalty: {card_data.get('loyalty')}\n"
            
            prompt = (
                f"Analyze the following Magic: The Gathering card and provide:\n"
                f"1. A brief game strategy for using this card effectively (2-3 sentences)\n"
                f"2. A power tier rating (S, A, B, C, or D tier)\n\n"
                f"{card_text}\n\n"
                f"Format your response exactly as:\n"
                f"Strategy: [your strategy here]\n"
                f"Tier: [tier letter]"
            )
            
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=150,
                temperature=0.7
            )
            
            result = response.choices[0].text.strip()
            strategy_match = re.search(r"Strategy: (.*?)(?:\n|$)", result)
            tier_match = re.search(r"Tier: ([SABCD])", result)
            
            strategy = strategy_match.group(1) if strategy_match else None
            tier = tier_match.group(1) if tier_match else None
            
            return card_data, strategy, tier
        except Exception as e:
            # No registramos el error en el log
            return card_data, None, None
