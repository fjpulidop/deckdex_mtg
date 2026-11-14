# Intent: Fix systematic 400s on grouped Scryfall price lookups and surface the cause

## Problem

During a bulk price refresh, every grouped POST to Scryfall /cards/collection returns 400 Bad Request. The code logs a generic warning and silently falls back to one request per card, so a ~4,400-card refresh makes thousands of calls and loses the speed-up spec #2 was meant to deliver. Scryfall's error body is discarded, so the cause is invisible.

## Outcome

A bulk price refresh resolves cards through grouped lookups, with the per-card fallback used only for names Scryfall can't resolve in bulk. When a grouped request fails, the logs show Scryfall's status and error detail.

## Hypothesis

We believe diagnosing and fixing the cause of the 400, and surfacing the response body when it recurs, will restore the batching. We will know when a full-collection refresh makes roughly one request per 75 cards.

## How we will know

- A refresh of ~4,400 cards issues about 60 grouped requests plus a small number of fallback lookups, not thousands of per-card requests
- No 'Grouped price lookup failed' warnings appear in the backend logs for a normal refresh
- When a grouped request does fail, the log line includes Scryfall's response status and error detail
- A 4xx response other than 429 is not retried

## Who and what it affects

- Bulk price refresh (POST /api/prices/update)
- deckdex/card_fetcher.py (get_cards_collection, _post_request)
- deckdex/magic_card_processor.py (_fetch_card_prices_grouped)
- Scryfall API usage and rate-limit exposure

## Constraints

- Keep the per-card fallback so a failed chunk never loses prices
- Keep chunks within Scryfall's 75-identifier limit
- Spec #2 is still on_review, so this must not break its freshness and skip-if-fresh behaviour

## Open questions

- What does Scryfall's 400 response body say? Nobody has seen it yet
- Is the cause the data (empty or malformed names), the request shape (missing User-Agent or Accept headers), or something else? The run must find out, not guess
- Should this land as a follow-up linked to #2, or wait until #2 is merged?
