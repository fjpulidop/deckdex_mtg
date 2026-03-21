# Proposal: Bracket / Power Level Auto-Estimation

**Issue**: #133
**Status**: Proposed
**Capability**: Decks / Deck Builder UI

---

## Problem Statement

Commander players need to communicate their deck's power level to their playgroup before sitting down. Today, DeckDex stores the full card composition of a deck but produces no analysis of how powerful that composition is. Players must self-assess — a notoriously unreliable and socially fraught process.

The Commander community uses the Commander Brackets framework (1–4 scale) and informal 1–10 numeric ratings as common vocabulary. DeckDex is well-positioned to automate a first-cut estimate: every card's `oracle_text`, `keywords`, `type_line`, `cmc`, and `mana_cost` are already stored in the `cards` table from Scryfall ingestion.

---

## Proposed Solution

Add a heuristic power-level analysis service that operates entirely on data already in the database. The service evaluates a deck's card list against a curated set of weighted signals — fast mana, tutors, combo density, average CMC, land quality — to produce:

- A numeric score on a 1–10 scale
- A Commander Bracket classification (1–4) derived from the score
- A one-sentence natural-language summary (e.g. "7 — strong tempo deck with premium mana base but few tutors")
- A per-factor breakdown so the user can understand the score

The score is surfaced in two places:
1. A compact badge on each deck tile in the DeckBuilder grid
2. A "Power Level" section in the DeckDetailModal header row

---

## User Story

As an MTG Player, I want DeckDex to estimate my deck's power level on the Commander Brackets scale automatically so that I can match my deck to the right playgroup and communicate power level clearly.

---

## Goals

- Estimate power level without any external API calls (fully offline from Scryfall's perspective)
- Return results in < 200 ms for a typical 100-card Commander deck (all data is local)
- Display score in both the deck grid tile and the deck detail modal
- Be explainable: show per-factor breakdown so players can understand and challenge the estimate

## Non-Goals

- Replacing human judgment — this is an aid, not an authority
- Detecting every combo in existence (the heuristic focuses on well-known signals)
- Providing different algorithms for different formats (this is Commander/EDH only for now)
- Persisting the score to the database (computed on demand, see caching strategy in design doc)

---

## Alternatives Considered

1. **OpenAI enrichment**: Rich but slow, costs money, and requires the optional OpenAI integration. Ruled out — this feature should work in the base configuration.
2. **EDHREC rank thresholds**: EDHREC rank is already stored in `cards.edhrec_rank`. Appealing but unreliable alone: a card with rank 500 could be a staple in the 99 or a commander answer. Kept as a supplemental signal rather than primary.
3. **Persistent cached score column in `decks` table**: Clean, but requires a migration and invalidation logic. Since computation is fast (< 200 ms), we cache in-process with a short TTL instead. Revisit if profiling shows a bottleneck.
