## Why

El modo oscuro actual usa la paleta de grises genérica de Tailwind (`gray-700`, `gray-800`, `gray-900`), lo que resulta en una experiencia visual anodina. El tema Drácula es una paleta bien establecida en el ecosistema de editores de código — colores saturados y con alta legibilidad sobre fondos oscuros — que encaja perfectamente con la audiencia de DeckDex (jugadores y coleccionistas técnicos de MTG).

Este cambio sustituye la paleta dark-mode por Drácula sin alterar el modo claro ni la lógica de ningún componente.

## What Changes

- **`frontend/src/index.css`**: Añadir un bloque `.dark { --color-* }` que redefine las CSS custom properties de Tailwind v4 para grises, indigo, green, red, amber, blue y orange en modo oscuro. Actualizar el background de `body` a `#282a36`. Actualizar el color del eje de la curva de maná en `.dark .deck-detail-mana-curve`.
- **`frontend/tailwind.config.ts`**: Actualizar los colores `primary` (purple → `#bd93f9` Drácula Purple) y `accent` (pink → `#ff79c6` Drácula Pink).
- **`frontend/src/pages/Analytics.tsx`**: Actualizar los colores hardcodeados de Recharts (`axisColor`, `gridColor`, `tooltipBg`, `tooltipBorder`, `tooltipTextColor`, `CHART_COLORS`, stroke del pie chart) a sus equivalentes Drácula en modo oscuro.
- **`frontend/src/components/DeckDetailModal.tsx`**: Actualizar los colores de relleno del mini bar chart de la curva de maná a Drácula Purple/Comment.

Los 20+ archivos de componentes con clases `dark:` de Tailwind **no se tocan**: en Tailwind v4 los colores son CSS custom properties, por lo que el override en `index.css` propaga automáticamente.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- **dark-mode-theme**: El modo oscuro SHALL usar la paleta Drácula (`#282a36` background, `#44475a` surfaces, `#f8f8f2` foreground, `#6272a4` muted, con acentos en purple, green, red, cyan y yellow de Drácula). El modo claro no se ve afectado.

## Impact

- **Frontend styling**: Solo `index.css`, `tailwind.config.ts`, `Analytics.tsx` y `DeckDetailModal.tsx`.
- **Sin cambios en lógica**: Cero modificaciones a componentes, hooks, rutas o backend.
- **Sin cambios en modo claro**: Toda la paleta light-mode permanece intacta.
- **MTG canonical colors**: Los colores de rareza (common/uncommon/rare/mythic) y de identidad de color (W/U/B/R/G) no se modifican — son colores canónicos del juego.
