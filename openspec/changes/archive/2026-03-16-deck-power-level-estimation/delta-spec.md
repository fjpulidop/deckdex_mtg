# Delta Spec: Deck Power Level Auto-Estimation

This document records the additive changes to existing specs. No existing requirements are removed or modified.

---

## Changes to `openspec/specs/decks/spec.md`

### ADD: Requirement — Power level estimation endpoint

> The system SHALL expose `GET /api/decks/{deck_id}/power-level` (auth required, 501 if Postgres unavailable). The endpoint SHALL compute a heuristic power level score for the deck using only data already stored in the `cards` table (card names, oracle text, CMC, EDHREC rank). The response SHALL include:
>
> - `score` (float, 1.0–10.0): composite power rating
> - `bracket` (int, 1–4): Commander Bracket mapping derived from score
> - `summary` (string): one-sentence human-readable explanation (e.g. "7 — strong tempo deck with premium mana base but few tutors")
> - `breakdown` (object): per-factor normalized scores for fast_mana, tutors, combo_pieces, avg_cmc, land_quality, staple_density
>
> The endpoint SHALL NOT require any external API calls. The endpoint SHALL return 404 if the deck does not exist or does not belong to the authenticated user.

#### Scenario: Fetch power level for a valid deck

- **WHEN** the authenticated user calls `GET /api/decks/{deck_id}/power-level` for a deck they own
- **THEN** the API returns HTTP 200 with a JSON body containing `score`, `bracket`, `summary`, and `breakdown`

#### Scenario: Deck not found

- **WHEN** the authenticated user calls `GET /api/decks/{deck_id}/power-level` with a deck_id that does not exist or belongs to another user
- **THEN** the API returns HTTP 404

#### Scenario: Postgres not configured

- **WHEN** no `DATABASE_URL` is set and the endpoint is called
- **THEN** the API returns HTTP 501 with the standard Postgres-required message

---

## Changes to `openspec/specs/deck-builder-ui/spec.md`

### ADD: Requirement — Power level badge on deck tile

> Each deck tile in the deck grid SHALL display a power level badge showing the numeric score and bracket (e.g. "B3 · 7.2"). The badge SHALL use a colour indicating the bracket: green for bracket 1, blue for bracket 2, orange for bracket 3, red for bracket 4. The badge SHALL be fetched asynchronously; it SHALL be absent (not an error state) while loading or on fetch failure.

#### Scenario: Badge appears on loaded deck tile

- **WHEN** the user views the deck grid and the power level has loaded for a deck
- **THEN** the deck tile shows a small coloured badge with the bracket and score (e.g. "B3 · 7.2")

#### Scenario: Badge absent while loading

- **WHEN** the power level request is in-flight or has failed
- **THEN** the tile renders normally without a badge (no spinner, no error state visible)

---

### ADD: Requirement — Power level section in deck detail modal

> The DeckDetailModal SHALL include a "Power Level" display in the header area. It SHALL show: the numeric score styled with the bracket colour, the bracket label (e.g. "High Power · B3"), and on hover a tooltip containing the full summary string and a mini-table of per-factor breakdown scores. The section SHALL render as an invisible placeholder while loading and be omitted gracefully on fetch error.

#### Scenario: Power level displayed in detail modal

- **WHEN** the user opens a deck detail modal and the power level has loaded
- **THEN** the header area shows the score and bracket label with appropriate colour coding

#### Scenario: Hovering power level shows breakdown

- **WHEN** the user hovers over the power level display in the deck detail modal
- **THEN** a tooltip appears showing the full summary sentence and per-factor scores (fast_mana, tutors, combo_pieces, avg_cmc, land_quality, staple_density)

#### Scenario: Power level gracefully absent on error

- **WHEN** the power level fetch fails (network error or backend unavailable)
- **THEN** the deck detail modal renders fully without the power level section; no error message is shown to the user for this non-critical feature
