/** MTG WUBRG mana colors for animated backgrounds */

export interface ManaColor {
  dark: string;
  light: string;
}

export const MANA_COLORS: Record<string, ManaColor> = {
  W: { dark: '#FFFBD5', light: '#B8860B' },
  U: { dark: '#0E68AB', light: '#0A4F8A' },
  B: { dark: '#A070B0', light: '#5C3D6E' },
  R: { dark: '#D3202A', light: '#A01820' },
  G: { dark: '#00733E', light: '#005A2E' },
};

export const MANA_SYMBOLS = ['{W}', '{U}', '{B}', '{R}', '{G}', '{T}', '{X}', '{1}', '{2}', '{3}'];

/** Map symbol to its mana color key (colorless symbols get a random WUBRG) */
export function symbolToColorKey(symbol: string): string {
  const key = symbol.replace(/[{}]/g, '');
  if (key in MANA_COLORS) return key;
  const keys = Object.keys(MANA_COLORS);
  return keys[Math.floor(Math.random() * keys.length)];
}
