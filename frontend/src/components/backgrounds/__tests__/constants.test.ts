import { describe, it, expect } from 'vitest';
import { MANA_SVGS, MANA_SYMBOLS, MANA_COLORS, symbolToColorKey } from '../constants';

describe('MANA_SVGS', () => {
  it('is exported', () => {
    expect(MANA_SVGS).toBeDefined();
  });

  it('has exactly 5 keys: W, U, B, R, G', () => {
    const keys = Object.keys(MANA_SVGS);
    expect(keys).toHaveLength(5);
    expect(keys).toContain('W');
    expect(keys).toContain('U');
    expect(keys).toContain('B');
    expect(keys).toContain('R');
    expect(keys).toContain('G');
  });

  it('each value starts with "data:image/svg+xml;base64,"', () => {
    for (const key of ['W', 'U', 'B', 'R', 'G']) {
      expect(MANA_SVGS[key]).toMatch(/^data:image\/svg\+xml;base64,/);
    }
  });
});

describe('MANA_SYMBOLS', () => {
  it('has exactly 5 entries', () => {
    expect(MANA_SYMBOLS).toHaveLength(5);
  });

  it('contains exactly {W}, {U}, {B}, {R}, {G}', () => {
    expect(MANA_SYMBOLS).toContain('{W}');
    expect(MANA_SYMBOLS).toContain('{U}');
    expect(MANA_SYMBOLS).toContain('{B}');
    expect(MANA_SYMBOLS).toContain('{R}');
    expect(MANA_SYMBOLS).toContain('{G}');
  });

  it('does NOT contain colorless or numeric symbols', () => {
    expect(MANA_SYMBOLS).not.toContain('{T}');
    expect(MANA_SYMBOLS).not.toContain('{X}');
    expect(MANA_SYMBOLS).not.toContain('{1}');
    expect(MANA_SYMBOLS).not.toContain('{2}');
    expect(MANA_SYMBOLS).not.toContain('{3}');
  });
});

describe('MANA_COLORS', () => {
  it('has all 5 WUBRG keys', () => {
    expect(MANA_COLORS).toHaveProperty('W');
    expect(MANA_COLORS).toHaveProperty('U');
    expect(MANA_COLORS).toHaveProperty('B');
    expect(MANA_COLORS).toHaveProperty('R');
    expect(MANA_COLORS).toHaveProperty('G');
  });

  it('each entry has dark and light color strings', () => {
    for (const key of ['W', 'U', 'B', 'R', 'G']) {
      expect(MANA_COLORS[key]).toHaveProperty('dark');
      expect(MANA_COLORS[key]).toHaveProperty('light');
      expect(typeof MANA_COLORS[key].dark).toBe('string');
      expect(typeof MANA_COLORS[key].light).toBe('string');
    }
  });
});

describe('symbolToColorKey', () => {
  it('returns the key directly for known WUBRG symbols', () => {
    expect(symbolToColorKey('{W}')).toBe('W');
    expect(symbolToColorKey('{U}')).toBe('U');
    expect(symbolToColorKey('{B}')).toBe('B');
    expect(symbolToColorKey('{R}')).toBe('R');
    expect(symbolToColorKey('{G}')).toBe('G');
  });

  it('returns a valid WUBRG key for unknown symbols', () => {
    const validKeys = ['W', 'U', 'B', 'R', 'G'];
    const result = symbolToColorKey('{X}');
    expect(validKeys).toContain(result);
  });
});
