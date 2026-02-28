## Tarea 1 — CSS custom properties en index.css

- [ ] 1.1 En `frontend/src/index.css`, sustituir el bloque `.dark body { background-color: #111827; }` por `background-color: #282a36` (Drácula Background).

- [ ] 1.2 Añadir a continuación un bloque `.dark { ... }` con todos los overrides de custom properties de Tailwind v4:
  ```css
  .dark {
    /* Gray scale → Dracula */
    --color-gray-950: #21222c;
    --color-gray-900: #282a36;
    --color-gray-800: #282a36;
    --color-gray-700: #44475a;
    --color-gray-600: #6272a4;
    --color-gray-500: #6272a4;
    --color-gray-400: #6272a4;
    --color-gray-300: #f8f8f2;
    --color-gray-200: #f8f8f2;
    --color-gray-100: #f8f8f2;

    /* Indigo → Dracula Purple */
    --color-indigo-400: #bd93f9;
    --color-indigo-500: #bd93f9;
    --color-indigo-600: #bd93f9;
    --color-indigo-700: #a87de8;
    --color-indigo-900: #383a59;

    /* Green → Dracula Green */
    --color-green-400: #50fa7b;
    --color-green-500: #50fa7b;
    --color-green-600: #50fa7b;
    --color-green-900: #1a2b1f;

    /* Red → Dracula Red */
    --color-red-200: #ffb3b3;
    --color-red-300: #ff7070;
    --color-red-400: #ff5555;
    --color-red-500: #ff5555;
    --color-red-800: #3d1f1f;
    --color-red-900: #3d1f1f;

    /* Blue → Dracula Cyan */
    --color-blue-400: #8be9fd;
    --color-blue-500: #8be9fd;
    --color-blue-900: #1a2d3d;

    /* Amber/Yellow → Dracula Yellow */
    --color-amber-200: #f1fa8c;
    --color-amber-300: #f1fa8c;
    --color-amber-900: #3d3d1f;
    --color-yellow-200: #f1fa8c;
    --color-yellow-300: #f1fa8c;
    --color-yellow-400: #f1fa8c;

    /* Orange */
    --color-orange-900: #3d2a1f;
  }
  ```

- [ ] 1.3 En el bloque existente `.dark .deck-detail-mana-curve .recharts-cartesian-axis-tick text`, cambiar `fill: #e5e7eb` por `fill: #f8f8f2` (Drácula Foreground).

## Tarea 2 — tailwind.config.ts: colores primary y accent

- [ ] 2.1 En `frontend/tailwind.config.ts`, actualizar el objeto `primary` a:
  ```ts
  primary: {
    400: '#d6b4fc',
    500: '#bd93f9',  // Dracula Purple
    600: '#a87de8',
    700: '#9a6dd6',
  },
  ```

- [ ] 2.2 Actualizar el objeto `accent` a:
  ```ts
  accent: {
    400: '#ff92d0',
    500: '#ff79c6',  // Dracula Pink
    600: '#e866b3',
  },
  ```

## Tarea 3 — Analytics.tsx: colores Recharts hardcodeados

- [ ] 3.1 En `frontend/src/pages/Analytics.tsx`, localizar las líneas ~175–179 donde se definen `axisColor`, `gridColor`, `tooltipBg`, `tooltipBorder`, `tooltipTextColor`. Sustituir los valores dark por sus equivalentes Drácula:
  ```ts
  const axisColor      = isDark ? '#6272a4' : '#6b7280';
  const gridColor      = isDark ? '#44475a' : '#e5e7eb';
  const tooltipBg      = isDark ? '#282a36' : '#ffffff';
  const tooltipBorder  = isDark ? '#44475a' : '#e5e7eb';
  const tooltipTextColor = isDark ? '#f8f8f2' : '#111827';
  ```

- [ ] 3.2 Sustituir el array `CHART_COLORS` (~línea 44) por la paleta Drácula:
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

- [ ] 3.3 Localizar el stroke del pie chart (búsqueda: `stroke={isDark ? '#1f2937'`). Sustituir `'#1f2937'` por `'#282a36'` (Drácula Background).

## Tarea 4 — DeckDetailModal.tsx: mini bar chart curva de maná

- [ ] 4.1 En `frontend/src/components/DeckDetailModal.tsx`, añadir el import de `useTheme`:
  ```ts
  import { useTheme } from '../contexts/ThemeContext';
  ```

- [ ] 4.2 Dentro del componente, añadir (junto al resto de hooks):
  ```ts
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  ```

- [ ] 4.3 Localizar el `fill` del `<Bar>` del mini chart (~línea 299):
  ```tsx
  fill={filterByCmc == null || filterByCmc === entry.cmcKey ? '#6366f1' : '#94a3b8'}
  ```
  Sustituir por:
  ```tsx
  fill={filterByCmc == null || filterByCmc === entry.cmcKey
    ? (isDark ? '#bd93f9' : '#6366f1')
    : (isDark ? '#6272a4' : '#94a3b8')}
  ```

## Tarea 5 — Verificación visual

- [ ] 5.1 Arrancar el frontend (`cd frontend && npm run dev`) y abrir `http://localhost:5173`.
- [ ] 5.2 Activar dark mode con el toggle. Comprobar que el fondo general es `#282a36`, las tarjetas/paneles son `#44475a`, el texto es `#f8f8f2` y los acentos tienen color Drácula Purple.
- [ ] 5.3 Navegar a `/analytics` y comprobar que los charts usan la paleta Drácula en dark mode.
- [ ] 5.4 Abrir un deck y comprobar que el mini bar chart de la curva de maná usa Drácula Purple en dark mode.
- [ ] 5.5 Cambiar de vuelta a light mode y confirmar que los colores del modo claro no han cambiado.
