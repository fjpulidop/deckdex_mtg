## Context

Frontend React 19 + Vite 7 + **Tailwind v4** (`^4.1.18`). Dark mode activado via clase `.dark` en `<html>`. Todos los componentes usan clases `dark:bg-gray-*`, `dark:text-gray-*`, `dark:border-gray-*`, etc.

En Tailwind v4, los colores de utilidad se generan como CSS custom properties:
```css
bg-gray-800 → background-color: var(--color-gray-800)
text-gray-400 → color: var(--color-gray-400)
```
Esto permite redefinir `--color-gray-800` dentro de `.dark {}` y todos los `dark:bg-gray-800` del codebase heredan el nuevo valor automáticamente, sin tocar ningún componente.

## Goals / Non-Goals

**Goals:**
- Aplicar la paleta Drácula completa al modo oscuro.
- Hacer el cambio con superficie mínima: solo CSS/config + 2 archivos con colores hardcodeados.
- No modificar el modo claro.
- No modificar colores canónicos de MTG (rareza e identidad de color).

**Non-Goals:**
- Crear un sistema de temas multi-paleta (solo Drácula en dark, existente en light).
- Tocar lógica de componentes, hooks, backend o tests.
- Animar la transición de colores (out of scope).

## Decisions

### 1. Estrategia: Override de CSS custom properties de Tailwind v4

En lugar de modificar las clases `dark:` en cada componente, se redefinen las variables CSS de Tailwind v4 dentro del selector `.dark` en `index.css`:

```css
.dark {
  --color-gray-950: #21222c;
  --color-gray-900: #282a36;   /* Dracula Background */
  --color-gray-800: #282a36;   /* Dracula Background */
  --color-gray-700: #44475a;   /* Dracula Current Line */
  --color-gray-600: #6272a4;   /* Dracula Comment */
  /* ... etc */
}
```

Ventaja: cero cambios en los 20+ componentes. La propagación es total y automática.

### 2. Mapping completo gray palette → Drácula

| Variable Tailwind       | Valor actual  | Valor Drácula | Rol semántico              |
|-------------------------|---------------|---------------|----------------------------|
| `--color-gray-950`      | `#030712`     | `#21222c`     | fondo más profundo         |
| `--color-gray-900`      | `#111827`     | `#282a36`     | fondo principal            |
| `--color-gray-800`      | `#1f2937`     | `#282a36`     | fondo principal (igual)    |
| `--color-gray-700`      | `#374151`     | `#44475a`     | tarjetas, inputs, paneles  |
| `--color-gray-600`      | `#4b5563`     | `#6272a4`     | hover, elementos muted     |
| `--color-gray-500`      | `#6b7280`     | `#6272a4`     | texto secundario muted     |
| `--color-gray-400`      | `#9ca3af`     | `#6272a4`     | texto secundario           |
| `--color-gray-300`      | `#d1d5db`     | `#f8f8f2`     | texto primario             |
| `--color-gray-200`      | `#e5e7eb`     | `#f8f8f2`     | texto primario             |
| `--color-gray-100`      | `#f3f4f6`     | `#f8f8f2`     | texto primario alternativo |

### 3. Mapping colores de acento → Drácula

| Variable Tailwind         | Valor Drácula | Nota                        |
|---------------------------|---------------|-----------------------------|
| `--color-indigo-400`      | `#bd93f9`     | Drácula Purple — nav, logo  |
| `--color-indigo-500`      | `#bd93f9`     | Drácula Purple              |
| `--color-indigo-600`      | `#bd93f9`     | Drácula Purple              |
| `--color-indigo-700`      | `#a87de8`     | Purple más oscuro           |
| `--color-indigo-900`      | `#383a59`     | Purple tinted bg (avatar)   |
| `--color-green-400`       | `#50fa7b`     | Drácula Green — precios     |
| `--color-green-500`       | `#50fa7b`     | Drácula Green               |
| `--color-green-600`       | `#50fa7b`     | Drácula Green               |
| `--color-green-900`       | `#1a2b1f`     | Dark green bg               |
| `--color-red-200`         | `#ffb3b3`     | Light red text              |
| `--color-red-300`         | `#ff7070`     | Red text                    |
| `--color-red-400`         | `#ff5555`     | Drácula Red — errores       |
| `--color-red-500`         | `#ff5555`     | Drácula Red                 |
| `--color-red-800`         | `#3d1f1f`     | Dark red bg                 |
| `--color-red-900`         | `#3d1f1f`     | Dark red bg                 |
| `--color-blue-400`        | `#8be9fd`     | Drácula Cyan — analytics    |
| `--color-blue-500`        | `#8be9fd`     | Drácula Cyan                |
| `--color-blue-900`        | `#1a2d3d`     | Dark cyan bg                |
| `--color-amber-200`       | `#f1fa8c`     | Drácula Yellow — badges     |
| `--color-amber-300`       | `#f1fa8c`     | Drácula Yellow              |
| `--color-amber-900`       | `#3d3d1f`     | Dark yellow bg              |
| `--color-yellow-200`      | `#f1fa8c`     | Drácula Yellow              |
| `--color-yellow-400`      | `#f1fa8c`     | Drácula Yellow              |
| `--color-orange-900`      | `#3d2a1f`     | Dark orange bg              |

### 4. tailwind.config.ts: primary y accent

Los custom colors `primary` (indigo, 400–700) y `accent` (pink, 400–600) se usan en componentes con clases como `bg-primary-500`, `text-accent-400`. En dark mode, deben apuntar a Drácula:

```ts
primary: {
  400: '#d6b4fc',  // lighter purple
  500: '#bd93f9',  // Dracula Purple
  600: '#a87de8',
  700: '#9a6dd6',
},
accent: {
  400: '#ff92d0',  // lighter pink
  500: '#ff79c6',  // Dracula Pink
  600: '#e866b3',
},
```

Nota: estos colores también afectan al modo claro (son los mismos tokens). Se pueden actualizar a Drácula directamente ya que el purple/pink ya era la paleta del proyecto, solo se ajustan los valores hex para que coincidan con Drácula exacto.

### 5. Colores hardcodeados en Recharts (Analytics.tsx)

`Analytics.tsx` usa `isDark` para seleccionar colores que se pasan a Recharts como props (no Tailwind). Se actualizan directamente las ramas `isDark`:

```ts
const axisColor    = isDark ? '#6272a4' : '#6b7280';  // Dracula Comment
const gridColor    = isDark ? '#44475a' : '#e5e7eb';  // Dracula Current Line
const tooltipBg    = isDark ? '#282a36' : '#ffffff';  // Dracula Background
const tooltipBorder= isDark ? '#44475a' : '#e5e7eb';  // Dracula Current Line
const tooltipText  = isDark ? '#f8f8f2' : '#111827';  // Dracula Foreground
```

`CHART_COLORS` (colores de series genéricas en gráficas) se actualiza a la paleta Drácula:
```ts
const CHART_COLORS = [
  '#bd93f9', // Purple
  '#8be9fd', // Cyan
  '#50fa7b', // Green
  '#ff5555', // Red
  '#ffb86c', // Orange
  '#ff79c6', // Pink
  '#f1fa8c', // Yellow
  '#6272a4', // Comment
];
```

El stroke del pie chart (`#1f2937` → `#282a36`).

### 6. DeckDetailModal.tsx: mini bar chart de curva de maná

El componente no importa `useTheme`. Añadir el import y derivar `isDark`. El fill activo (`#6366f1`) → `isDark ? '#bd93f9' : '#6366f1'` (Drácula Purple en dark, indigo existente en light). El fill inactivo (`#94a3b8`) → `isDark ? '#6272a4' : '#94a3b8'` (Drácula Comment en dark).

### 7. Qué NO cambia

- Colores de rareza (`common: #9ca3af`, `uncommon: #6ee7b7`, `rare: #facc15`, `mythic: #f97316`) — canónicos MTG.
- Colores de identidad de color (`W/U/B/R/G/C`) — canónicos MTG.
- Modo claro: toda la paleta light-mode permanece intacta.
- Lógica de componentes, hooks, backend, tests.

## Risks / Trade-offs

- **Tailwind v4 assumption**: La estrategia de override de CSS custom properties depende de que Tailwind v4 genere los colores como variables. Esto es confirmado (versión `^4.1.18`). Si se hace downgrade a v3, este approach no funcionaría.
- **Custom properties no cobertas**: Si algún componente usa un shade de gris no mapeado (e.g. `gray-950`), podría quedar sin override. Mitigado añadiendo la variable `--color-gray-950`.
- **`primary`/`accent` en light mode**: Actualizar estos tokens cambia ligeramente el light mode. Los valores Drácula Purple/Pink son muy similares a los actuales (ya eran purple/pink) — el cambio es mínimo y bienvenido.
