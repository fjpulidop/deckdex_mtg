# Context Bundle

Compact developer reference for implementing `fix-landing-background-and-hero-description`.
All file paths are relative to repo root.

---

## frontend/src/pages/Landing.tsx

**Role:** Page wrapper for the landing route (`/`). Renders Hero, BentoGrid, FinalCTA, Footer in order.

**Current line to change (line 8):**
```tsx
<div className="relative z-10 min-h-screen bg-gradient-to-b from-slate-900/90 via-purple-900/20 to-slate-900/90">
```
**Target state:** Remove the three background gradient classes. Keep only:
```tsx
<div className="relative z-10 min-h-screen">
```

**Why z-10 is correct:** CardMatrix canvas is `position: fixed; z-index: 0`. The Landing wrapper at `z-10` lifts content above the canvas. The background-color on the wrapper is what occludes the canvas — not the z-index.

---

## frontend/src/components/landing/Hero.tsx

**Role:** Full-viewport hero section. Two-column grid: left = text/CTA, right = visual panel.

**Existing imports (top of file):**
```tsx
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { ArrowRight } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { redirectToGoogleLogin } from '@/utils/auth';
```
**Add this import:**
```tsx
import i18next from 'i18next';
```

**Change 1 — section background (line 15):**
```tsx
// FROM:
<section className="min-h-screen pt-20 pb-16 bg-gradient-to-br from-slate-900/80 via-purple-900/60 to-slate-900/80 flex items-center">
// TO:
<section className="min-h-screen pt-20 pb-16 bg-gradient-to-br from-slate-900/20 via-purple-900/10 to-slate-900/20 flex items-center">
```

**Change 2 — right column (lines 82-105), remove entirely and replace:**
```tsx
{/* Right Column - App Description Card */}
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.8, delay: 0.2, ease: 'easeOut' }}
  className="flex justify-center"
>
  <div className="relative w-full max-w-xl rounded-2xl overflow-hidden shadow-2xl shadow-purple-500/20 border border-slate-700/50 bg-slate-900/60 backdrop-blur-sm p-6">
    <div className="flex gap-4">
      {/* English panel */}
      <div className="flex-1 border-r border-slate-700/30 pr-4">
        <p className="text-xs font-bold text-purple-400/70 uppercase tracking-widest mb-3">EN</p>
        <p className="text-purple-300 font-semibold text-sm mb-3">
          {i18next.getFixedT('en')('hero.descCard.title')}
        </p>
        <ul className="space-y-2 mb-4">
          {(['feature1', 'feature2', 'feature3', 'feature4'] as const).map((key) => (
            <li key={key} className="text-slate-300 text-sm flex gap-2">
              <span className="text-purple-400 shrink-0">✦</span>
              {i18next.getFixedT('en')(`hero.descCard.${key}`)}
            </li>
          ))}
        </ul>
        <p className="text-slate-400 text-xs italic">{i18next.getFixedT('en')('hero.descCard.tagline')}</p>
      </div>
      {/* Spanish panel */}
      <div className="flex-1 pl-0">
        <p className="text-xs font-bold text-purple-400/70 uppercase tracking-widest mb-3">ES</p>
        <p className="text-purple-300 font-semibold text-sm mb-3">
          {i18next.getFixedT('es')('hero.descCard.title')}
        </p>
        <ul className="space-y-2 mb-4">
          {(['feature1', 'feature2', 'feature3', 'feature4'] as const).map((key) => (
            <li key={key} className="text-slate-300 text-sm flex gap-2">
              <span className="text-purple-400 shrink-0">✦</span>
              {i18next.getFixedT('es')(`hero.descCard.${key}`)}
            </li>
          ))}
        </ul>
        <p className="text-slate-400 text-xs italic">{i18next.getFixedT('es')('hero.descCard.tagline')}</p>
      </div>
    </div>
  </div>
</motion.div>
```

---

## frontend/src/locales/en.json

**Where to add:** Inside the existing `"hero"` object, after `"tryLiveDemo"`.

```json
"descCard": {
  "title": "What is DeckDex?",
  "feature1": "Track your MTG collection with real-time Scryfall prices",
  "feature2": "Build Commander decks with AI-powered insights",
  "feature3": "Import from MTGO, Moxfield, or paste a card list",
  "feature4": "Analytics: mana curve, color identity, set distribution",
  "tagline": "Free · Open Source · Community-Driven"
}
```

---

## frontend/src/locales/es.json

**Where to add:** Inside the existing `"hero"` object, after `"tryLiveDemo"`.

```json
"descCard": {
  "title": "¿Qué es DeckDex?",
  "feature1": "Gestiona tu colección de MTG con precios Scryfall en tiempo real",
  "feature2": "Construye mazos Commander con análisis potenciados por IA",
  "feature3": "Importa desde MTGO, Moxfield o pega una lista de cartas",
  "feature4": "Estadísticas: curva de maná, identidad de color, distribución por edición",
  "tagline": "Gratis · Código abierto · Impulsado por la comunidad"
}
```

---

## frontend/src/components/backgrounds/CardMatrix.tsx

**No changes needed.** Reference only.

- Canvas renders at `position: fixed; z-index: 0; inset: 0` (via Tailwind `fixed inset-0 z-0`)
- Symbols have opacity `0.03–0.12` per drop (`createDrop` function), max capped at `0.2` in dark mode
- Animation runs at 30 FPS, pauses on `document.hidden`
- Respects `prefers-reduced-motion` via `useReducedMotion` hook

---

## frontend/src/App.tsx

**No changes needed.** Reference only.

- CardMatrix is mounted conditionally: `{isLandingPage && <CardMatrix />}` (line 35)
- The canvas is a sibling of the Landing page in the DOM, not a child — which is why removing the background from the Landing wrapper (not from App.tsx) is the correct fix
