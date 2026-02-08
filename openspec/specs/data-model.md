# Data Model

Storage-agnostic: in-memory JSON-like objects and Google Sheets rows.

**Card:** id (Scryfall), name, english_name, type_line, description, keywords, mana_cost, cmc, colors, color_identity, power, toughness, rarity, set_id, set_name, set_number, release_date, edhrec_rank, scryfall_uri, prices{usd,eur,usd_foil}, last_price_update, game_strategy, tier.

**PriceHistory:** card_id, timestamp, source, currency, price. **SheetRow:** row_index, values (column→string), processed_at. Card 1:N PriceHistory; SheetRow 1:1 Card when matched.

**Sheets columns:** Name, English name, Type, Description, Keywords, Mana Cost, Cmc, Color, Identity, Strength, Resistance, Rarity, Price (eur), Release, Date, Set ID, Set Name, Number in Set, Edhrec, Rank, Game Strategy, Tier. Version layout (DATA_MODEL_VERSION); migrations for new columns.
