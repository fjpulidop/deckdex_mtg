# Card Detail Modal

Read-only modal: card image (GET /api/cards/{id}/image) + structured data (name, type, mana cost, oracle, P/T, set, rarity, price) in Scryfall-style layout. Opened on table row click (not on Edit/Delete).

### Requirements (compact)

- **Image + data:** Image from backend; loading placeholder; 404/error → fallback message, text still shown. Text layout: name, type line, mana cost, description, P/T, set, number, rarity, price.
- **Mana symbols:** {W}, {U}, etc. rendered as Scryfall-style SVGs (cost + oracle); hybrid/generic/special supported; aria-label/title for a11y. Close → dismiss, no persist.
- **Update price:** Button when card has id; POST /api/prices/update/{card_id} → job in global bar; no button when no id.
- **Refresh on job complete:** When single-card Update price job completes: refresh dashboard stats, modal price (if same card open), and table row.
- **Lightbox:** Click image → larger overlay; click overlay or Escape → close, modal stays. Cursor: zoom-in on modal image, zoom-out on lightbox.
