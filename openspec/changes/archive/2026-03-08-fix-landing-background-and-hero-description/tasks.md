## 1. i18n — Add hero.descCard keys to locale files [frontend]

- [ ] 1.1 In `frontend/src/locales/en.json`, add the `hero.descCard` key group under the existing `hero` object with the following six keys: `title`, `feature1`, `feature2`, `feature3`, `feature4`, `tagline`. Done when `en.json` is valid JSON and `hero.descCard.title` resolves to an English string describing DeckDex.
- [ ] 1.2 In `frontend/src/locales/es.json`, add the same six `hero.descCard.*` keys with Spanish translations matching the meaning of the English strings. Done when `es.json` is valid JSON and `hero.descCard.title` resolves to the Spanish equivalent.

## 2. Fix CardMatrix background visibility in Landing wrapper [frontend]

- [ ] 2.1 In `frontend/src/pages/Landing.tsx`, remove the Tailwind classes `bg-gradient-to-b from-slate-900/90 via-purple-900/20 to-slate-900/90` from the wrapper `<div>`. The div should retain only `relative z-10 min-h-screen`. Done when the Landing wrapper has no background-color or background-gradient class, and the CardMatrix canvas is visible in a browser at `http://localhost:5173/`.

## 3. Fix Hero section gradient opacity [frontend]

- [ ] 3.1 In `frontend/src/components/landing/Hero.tsx`, replace the `<section>` className's gradient from `bg-gradient-to-br from-slate-900/80 via-purple-900/60 to-slate-900/80` to `bg-gradient-to-br from-slate-900/20 via-purple-900/10 to-slate-900/20`. Done when the Hero section has a visibly translucent background and the CardMatrix mana symbols are perceptible behind the hero content area.

## 4. Replace static image with bilingual description card in Hero [frontend]

- [ ] 4.1 In `frontend/src/components/landing/Hero.tsx`, add `import i18next from 'i18next'` at the top of the file (alongside the existing `useTranslation` import). Done when the import is present and TypeScript reports no errors.
- [ ] 4.2 In `frontend/src/components/landing/Hero.tsx`, remove the entire `<div>` block that wraps the `<img src="/dashboard-preview.png">` and its gradient fallback sibling (lines 88-104 in the original file). Replace it with an inline bilingual card JSX block. The card structure must be: a styled container div, inside it two side-by-side `<div>` panels (`flex flex-row gap-4`). The left panel renders English strings via `i18next.getFixedT('en')('hero.descCard.title')` etc. The right panel renders Spanish strings via `i18next.getFixedT('es')('hero.descCard.title')` etc. Each panel shows: a language label ("EN" / "ES"), the title, four feature bullets (each prefixed with a checkmark character or bullet), and the tagline. Done when: (a) no `<img>` or `dashboard-preview.png` reference remains in Hero.tsx; (b) the bilingual card renders two columns of text in the browser; (c) TypeScript strict mode (`npm run build`) passes with no errors.
- [ ] 4.3 Style the bilingual card container to match the existing Hero panel visual language: use `rounded-2xl`, `border border-slate-700/50`, `bg-slate-900/60 backdrop-blur-sm`, and `shadow-2xl shadow-purple-500/20`. The EN panel and ES panel should each have a subtle `border-r border-slate-700/30` divider (the EN panel only). Feature bullets should use `text-slate-300 text-sm`. The title should use `text-purple-300 font-semibold`. The language label ("EN" / "ES") should use `text-xs font-bold text-purple-400/70 uppercase tracking-widest`. The tagline at the bottom of each panel should be `text-slate-400 text-xs italic`. Done when the card visually integrates with the hero dark-purple color palette without looking disconnected.

## 5. Verification [frontend]

- [ ] 5.1 Run `npm run build` from `frontend/` and confirm zero TypeScript errors and zero Vite build errors. Done when the command exits with code 0.
- [ ] 5.2 Run `npm run lint` from `frontend/` and confirm no new lint errors introduced by changes in Hero.tsx, Landing.tsx, or either locale file. Done when lint exits with code 0 or only pre-existing warnings remain.
- [ ] 5.3 In a browser at `http://localhost:5173/`, verify: (a) the CardMatrix falling mana symbols are visible in the background on the landing page; (b) the Hero right column shows two panels labeled "EN" and "ES" with description content; (c) Hero text (headline, subtitle, CTA buttons) remains readable; (d) switching the app locale (via the LandingNavbar language switcher) does not change the bilingual card content (both panels always show their fixed language).
