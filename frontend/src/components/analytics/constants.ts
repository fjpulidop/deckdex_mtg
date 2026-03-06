// Shared palettes and theme helpers for analytics components

export const RARITY_COLORS: Record<string, string> = {
  common: '#9ca3af',
  uncommon: '#6ee7b7',
  rare: '#facc15',
  mythic: '#f97316',
  'mythic rare': '#f97316',
  special: '#a78bfa',
  bonus: '#f472b6',
};

export const TYPE_COLORS: Record<string, string> = {
  Creature:     '#6366f1',
  Land:         '#22c55e',
  Artifact:     '#9ca3af',
  Enchantment:  '#a855f7',
  Planeswalker: '#f59e0b',
  Instant:      '#06b6d4',
  Sorcery:      '#ef4444',
  Battle:       '#f97316',
  Other:        '#6b7280',
};

export const MTG_COLOR_MAP: Record<string, { label: string; hex: string }> = {
  W: { label: 'White', hex: '#f5f0e1' },
  U: { label: 'Blue', hex: '#0e68ab' },
  B: { label: 'Black', hex: '#4b4b4b' },
  R: { label: 'Red', hex: '#d32029' },
  G: { label: 'Green', hex: '#00733e' },
  C: { label: 'Colorless', hex: '#9ca3af' },
};

export const WUBRG_ORDER = ['W', 'U', 'B', 'R', 'G'] as const;

export const CHART_COLORS = [
  '#6366f1', '#06b6d4', '#f59e0b', '#ef4444', '#22c55e',
  '#a855f7', '#ec4899', '#14b8a6', '#f97316', '#8b5cf6',
];

export interface ChartTheme {
  axisColor: string;
  gridColor: string;
  tooltipBg: string;
  tooltipBorder: string;
  tooltipText: string;
}

export function buildChartTheme(isDark: boolean): ChartTheme {
  return {
    axisColor: isDark ? '#9ca3af' : '#6b7280',
    gridColor: isDark ? '#374151' : '#e5e7eb',
    tooltipBg: isDark ? '#1f2937' : '#ffffff',
    tooltipBorder: isDark ? '#374151' : '#e5e7eb',
    tooltipText: isDark ? '#ffffff' : '#111827',
  };
}

export function tooltipContentStyle(theme: ChartTheme) {
  return {
    backgroundColor: theme.tooltipBg,
    border: `1px solid ${theme.tooltipBorder}`,
    borderRadius: 8,
    color: theme.tooltipText,
  };
}

export function tooltipItemStyle(theme: ChartTheme) {
  return { color: theme.tooltipText };
}

export function tooltipLabelStyle(theme: ChartTheme) {
  return { color: theme.tooltipText };
}

// Color identity helpers
export function colorIdentityLabel(ci: string): string {
  if (!ci || ci === 'C') return 'Colorless';
  const letters = ci.split('').filter(c => c in MTG_COLOR_MAP);
  if (letters.length === 0) return ci;
  if (letters.length === 1) return MTG_COLOR_MAP[letters[0]].label;
  return letters.map(c => MTG_COLOR_MAP[c]?.label ?? c).join('/');
}

export function colorIdentityHex(ci: string): string {
  if (!ci || ci === 'C') return MTG_COLOR_MAP['C'].hex;
  const letters = ci.split('').filter(c => c in MTG_COLOR_MAP);
  if (letters.length === 0) return '#6366f1';
  return MTG_COLOR_MAP[letters[0]]?.hex ?? '#6366f1';
}

export function colorIdentityShort(ci: string): string {
  if (!ci || ci === 'C') return 'C';
  const letters = ci.split('').filter(c => c in MTG_COLOR_MAP);
  if (letters.length === 0) return ci;
  if (letters.length === 1) return MTG_COLOR_MAP[letters[0]].label;
  if (letters.length >= 4) return `${letters.length}C`;
  return letters.join('/');
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' }).format(value);
}
