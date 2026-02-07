# Data Model Specification

## Purpose

Define core entities, their fields, and relationships used by DeckDex MTG. This spec is storage-agnostic: the canonical representation is JSON-like objects used in application memory and persisted rows in Google Sheets.

## Entities

1. Card
   - id: string (Scryfall ID)
   - name: string
   - english_name: string | null
   - type_line: string
   - description: string | null
   - keywords: string[] (oracle text keywords)
   - mana_cost: string | null
   - cmc: number
   - colors: string[] (e.g., ["W","U"])
   - color_identity: string[]
   - power: string | null
   - toughness: string | null
   - rarity: enum ["common","uncommon","rare","mythic"]
   - set_id: string
   - set_name: string
   - set_number: string
   - release_date: string (ISO date)
   - edhrec_rank: integer | null
   - scryfall_uri: string
   - prices:
     - usd: string | null
     - eur: string | null
     - usd_foil: string | null
   - last_price_update: string (ISO datetime)
   - game_strategy: string | null (OpenAI)
   - tier: string | null (OpenAI)

2. PriceHistory
   - card_id: string (foreign -> Card.id)
   - timestamp: string (ISO datetime)
   - source: string (e.g., "scryfall")
   - currency: string (e.g., "EUR")
   - price: number

3. Deck (optional)
   - id: string
   - name: string
   - owner_id: string (User.id)
   - cards: [{ card_id, count }]
   - created_at, updated_at

4. User (optional)
   - id: string
   - name: string
   - email: string
   - google_service_account_shared: boolean

5. SheetRow (mapping to Google Sheets)
   - row_index: integer
   - values: mapping of column name -> string
   - processed_at: string | null

## Relationships

- Card 1:N PriceHistory
- Deck N:M Card (via cards list)
- SheetRow 1:1 Card (when matched)

## Example JSON (Card)

```json
{
  "id": "a1b2c3",
  "name": "Lightning Bolt",
  "cmc": 1,
  "colors": ["R"],
  "prices": { "usd": "2.50", "eur": "2.30" },
  "last_price_update": "2026-02-01T12:00:00Z",
  "game_strategy": "Aggro",
  "tier": "High"
}
```

## Google Sheets Column Mapping

- Name -> Card.name
- English name -> Card.english_name
- Type -> Card.type_line
- Description -> Card.description
- Keywords -> join(Card.keywords, ", ")
- Mana Cost -> Card.mana_cost
- Cmc -> Card.cmc
- Color -> join(Card.colors, ",")
- Identity -> join(Card.color_identity, ",")
- Strength -> Card.power
- Resistance -> Card.toughness
- Rarity -> Card.rarity
- Price -> Card.prices.eur (or chosen currency)
- Release -> Card.release_date
- Date -> last_price_update
- Set ID -> Card.set_id
- Set Name -> Card.set_name
- Number in Set -> Card.set_number
- Edhrec -> Card.edhrec_rank
- Rank -> derived ranking
- Game Strategy -> Card.game_strategy
- Tier -> Card.tier

## Versioning and Migration

- Keep the data model versioned (e.g., DATA_MODEL_VERSION = "1.0"). When changing sheet layout, provide a migration tool that can convert older sheets to the new columns.

