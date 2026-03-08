## Context

The landing page renders `CardMatrix` — a canvas element at `position: fixed; z-index: 0; inset: 0` — to display animated falling mana symbols. The canvas is mounted by `App.tsx` at the root level, outside the `Landing` component, which is correct.

The problem is layering. `Landing.tsx` wraps all content in a `<div className="relative z-10 min-h-screen bg-gradient-to-b from-slate-900/90 via-purple-900/20 to-slate-900/90">`. The `bg-gradient-to-b from-slate-900/90` creates a near-opaque background (90% opacity) that sits directly on top of the canvas. Inside that, `Hero.tsx` adds another `bg-gradient-to-br from-slate-900/80 via-purple-900/60 to-slate-900/80` on the `<section>` element, compounding the occlusion further.

The `relative z-10` on the Landing wrapper is correct — it lifts content above the canvas — but the background color on that same element is what occludes the canvas. The canvas must be visible through the wrapper's background.

The second issue: the Hero right column uses `<img src="/dashboard-preview.png">` with an `onError` handler that reveals a gradient fallback. In practice, `dashboard-preview.png` does not exist, so the `<img>` fires `onError` and the fallback div (which uses `display: hidden` by default) is revealed. This is a degenerate UX: the user sees a plain gradient box with no informational content.

## Goals / Non-Goals

**Goals:**
- Make the CardMatrix canvas visible through the Landing page content layers
- Replace the broken static image in Hero with a useful, bilingual inline description card
- Add i18n keys for the description card content in en.json and es.json
- Respect the existing `useTranslation()` pattern used throughout Hero.tsx

**Non-Goals:**
- Not changing CardMatrix rendering logic, opacity values, or animation behavior
- Not adding blur/frosted-glass effects to the content (a pure background removal is sufficient)
- Not introducing a new component file (the description card is an inline JSX block within Hero.tsx)
- Not changing any other landing section

## Decisions

### Decision 1: Remove background from Landing wrapper entirely vs. making it semi-transparent

**Options considered:**
- A) Remove `bg-gradient-to-b` entirely from `Landing.tsx` — the wrapper has no background, canvas is fully visible
- B) Replace with `bg-gradient-to-b from-slate-900/30 via-transparent to-slate-900/30` — keeps a subtle vignette at top/bottom
- C) Keep wrapper as-is, give the canvas a higher z-index — would require restructuring App.tsx and could cause interaction issues

**Decision: Option A** — remove the `bg-gradient-to-b` class from `Landing.tsx`. The wrapper's sole purpose is positioning (`relative z-10`). No background is needed at this level because each section (Hero, BentoGrid, FinalCTA, Footer) can carry its own subtle section-level tinting if desired. This is the simplest, most correct approach.

### Decision 2: Remove background from Hero section vs. making it transparent

**Options considered:**
- A) Remove `bg-gradient-to-br from-slate-900/80 via-purple-900/60 to-slate-900/80` entirely from the Hero `<section>` — canvas fully visible behind Hero text
- B) Replace with a very low-opacity tint (`from-slate-900/20 via-purple-900/10 to-slate-900/20`) — preserves a hint of depth layering beneath the hero text
- C) Keep the Hero gradient and only fix Landing — Hero would still occlude the canvas in the first viewport

**Decision: Option B** — keep a very subtle tint at the Hero section level (`from-slate-900/20 via-purple-900/10 to-slate-900/20`). The Hero text must remain readable against the dark canvas. A light tint (20-10% opacity) provides contrast without hiding the animation. This is the right balance: the animation is visible, the text is legible.

**Rationale for keeping some tint on Hero but not Landing:** The Hero section is the most text-dense area (H1, subtitle, CTAs). A slight darkening helps readability. The Landing wrapper, however, wraps all sections — a background there cascades over everything. The per-section approach gives fine-grained control.

### Decision 3: Inline description card vs. new component file

**Options considered:**
- A) New file `frontend/src/components/landing/AppDescriptionCard.tsx` — clean separation
- B) Inline JSX block inside `Hero.tsx`, replacing the `<div>` that held the `<img>` — simpler, smaller diff
- C) Reuse the BentoCard component — designed for the BentoGrid grid layout, wrong semantic context

**Decision: Option B** — inline in Hero.tsx. The description card is tightly coupled to the Hero layout (it's the right column of the two-column Hero grid). Extracting it to a separate file provides no reuse benefit since it will never appear elsewhere. This keeps the change contained to a single file.

### Decision 4: Bilingual card design — side-by-side panels vs. language-switcher tabs

**Options considered:**
- A) Two side-by-side mini panels (EN left, ES right) within the card — bilingual at a glance, no interaction required
- B) Use `useTranslation()` to render current language only — no second language shown, relies on user switching locale
- C) Language-switcher tabs within the card — interactive, adds complexity

**Decision: Option A** — two side-by-side panels. The intent is to visually signal that the app is bilingual without requiring any interaction. Each panel uses the same i18n key structure but one panel is always rendered in English and the other always in Spanish, using `i18next.getFixedT('en')` and `i18next.getFixedT('es')` respectively. This approach does not depend on the active locale for the card content — it always shows both languages.

**Rationale:** The bilingual card is a product signal ("this app speaks your language"), not a localized UI element. Rendering it in both languages simultaneously makes that signal immediate. It avoids adding tabs or state.

### Decision 5: i18n key location — `hero.descCard` namespace

New keys will be added under the existing `hero` namespace in both locale files:

```json
"hero": {
  ...existing keys...,
  "descCard": {
    "title": "What is DeckDex?",
    "feature1": "Track your MTG collection with real-time Scryfall prices",
    "feature2": "Build Commander decks with AI-powered insights",
    "feature3": "Import from MTGO, Moxfield, or paste a card list",
    "feature4": "Analytics: mana curve, color identity, set distribution",
    "tagline": "Free · Open Source · Community-Driven"
  }
}
```

Spanish equivalent keys added to `es.json` under `hero.descCard`. Using `hero.descCard` rather than a new top-level namespace is consistent with how existing hero content is organized.

## Impact Analysis

| File | Change |
|------|--------|
| `frontend/src/pages/Landing.tsx` | Remove `bg-gradient-to-b from-slate-900/90 via-purple-900/20 to-slate-900/90` from wrapper div |
| `frontend/src/components/landing/Hero.tsx` | (1) Replace `bg-gradient-to-br from-slate-900/80 via-purple-900/60 to-slate-900/80` with `bg-gradient-to-br from-slate-900/20 via-purple-900/10 to-slate-900/20`; (2) Replace `<img>` + fallback div with bilingual description card JSX |
| `frontend/src/locales/en.json` | Add `hero.descCard` keys (5 strings) |
| `frontend/src/locales/es.json` | Add `hero.descCard` keys (5 strings, Spanish) |

No backend changes. No new routes. No new component files.

## Risks / Trade-offs

- **Text readability risk** → Mitigation: The Hero section retains a 10-20% opacity tint, and the existing H1 uses `bg-clip-text` gradient (inherently high contrast). The subtitle uses `text-slate-300` which is light enough to read against the dark canvas symbols. If readability testing reveals issues, the Hero tint can be increased to 30-40% without breaking the canvas visibility.

- **CardMatrix symbol density** → The canvas drops `opacity: 0.03–0.12` per symbol (from `createDrop`). With the gradients removed, symbols may appear more prominently than intended. The existing max opacity of 0.12 is quite subtle, so this is not expected to overwhelm the text. No changes to the canvas code are needed.

- **i18next fixed-language rendering** → Using `i18next.getFixedT('en')` and `i18next.getFixedT('es')` to render fixed-language panels requires importing `i18next` directly (not just `useTranslation`). This is a valid pattern in i18next and does not conflict with existing usage. Both locale files must have the `hero.descCard` keys or the fixed-language panel will fall back to the key name.

## Migration Plan

This is a pure frontend styling and content change. No migration is required.

1. Write i18n keys to both locale files first (unblocks the Hero component)
2. Update Landing.tsx (one-line class removal)
3. Update Hero.tsx (two changes: section class + right-column JSX replacement)
4. Verify visually in dev server (`npm run dev`) — inspect that the CardMatrix canvas is visible through the Hero viewport
5. No rollback concern; reverting is a trivial git revert

## Open Questions

None. All decisions are made above.
