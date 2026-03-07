# Proposal: Card Image Lightbox and Price History Chart in CardDetailModal

## Problem

When a user opens the card detail modal, they see a thumbnail-sized card image (max 280×390 px). There is no way to examine the card art or text at full resolution without leaving the app. Additionally, while the backend records price history over time, there is no UI surface that exposes this data — users cannot see whether a card's value is trending up or down.

## Solution

Two focused UI enhancements to `CardDetailModal`:

### 1. Image Lightbox

Clicking the card image opens a full-screen overlay that displays the card at a larger size (up to 488×680 px). The overlay is dismissible via ESC key or clicking anywhere outside the image. The cursor changes to `zoom-in` when hovering the thumbnail and `zoom-out` when the lightbox is open, communicating the interaction affordance clearly. The lightbox is implemented as a nested `AccessibleModal` with a proper `aria-modal` focus trap.

### 2. Price History Chart

Below the card metadata in the right panel, a line chart displays the card's recorded price over the last 90 days. The chart uses Recharts (already installed) with date labels on the X-axis and EUR price on the Y-axis. When no history exists yet, a friendly prompt encourages the user to run a price update. Loading state shows an animated skeleton placeholder.

## Scope

- Frontend only: `CardDetailModal.tsx`, new `PriceChart.tsx` component
- No backend changes: `GET /api/cards/{id}/price-history` endpoint already exists
- No new API client methods: `api.getPriceHistory` already exists in `client.ts`
- No new hooks: `usePriceHistory` already exists in `useApi.ts`
- i18n additions: new keys under `priceChart.*` and additions to `cardDetail.*` in both locale files

## Motivation

Both features address the same underlying gap: users want richer card context in the detail view. The lightbox addresses the immediate visual inspection use case (checking art details, card text readability). The price chart addresses the investment tracking use case — users who are using DeckDex to monitor collection value want to see price trends per card without leaving the modal.

## Out of Scope

- Backend changes to price history endpoint
- Price history for date ranges other than 90 days (no UI control for this initially)
- Download or export of price history data
- Gallery view lightbox (separate feature)
