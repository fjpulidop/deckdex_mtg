import os
import requests
from typing import Any
import openai


class CardFetcher:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.scryfall.com"
        openai.api_key = self.api_key

    def search_card(self, card_name: str) -> Any:
        try:
            response = requests.get(
                f"{self.base_url}/cards/named", params={"fuzzy": card_name}
            )
            return response.json() if response.status_code == 200 else None
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while fetching card: {e}")
            return None

    def get_game_strategy(self, text: str) -> str:
        if text is None:
            text = ""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "user",
                        "content": "get game strategy in one word that follows this text from the Magic card (avoid phrases as output) (use common terms in magic like aggro, control, etc): "
                        + text,
                    }
                ],
                temperature=0.5,
                max_tokens=256,
            )
            return response.choices[0]["message"]["content"]
        except openai.api.OpenAIAPIError as e:
            print(f"Error occurred while getting game strategy: {e}")
            return None

    def get_tier(self, text: str, cmc: str, power: str, toughness: str) -> str:
        if text is None:
            text = ""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "user",
                        "content": "classify this Magic card (tier class: top, high, mid, low, bottom): description: "
                        + text
                        + " converted mana cost:"
                        + str(cmc)
                        + " strength:"
                        + str(power)
                        + " resilience:"
                        + str(toughness)
                        + " return me only the classification in one word.",
                    }
                ],
                temperature=0.5,
                max_tokens=256,
            )
            return response.choices[0]["message"]["content"]
        except openai.api.OpenAIAPIError as e:
            print(f"Error occurred while getting card tier: {e}")
            return None

    def get_card_info(self, card_name: str):
        data = self.search_card(card_name)
        if data is not None:
            game_strategy = self.get_game_strategy(data.get("oracle_text"))
            tier = self.get_tier(
                data.get("oracle_text"),
                data.get("cmc"),
                data.get("power"),
                data.get("toughness"),
            )
            return data, game_strategy, tier
        return None, None, None
