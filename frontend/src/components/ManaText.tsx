import React from 'react';

const MANA_SYMBOL_REGEX = /\{([^}]+)\}/g;

type ManaPart = { type: 'text'; value: string } | { type: 'symbol'; key: string; label: string };

function parseManaParts(text: string): ManaPart[] {
  if (!text || typeof text !== 'string') return [];
  const parts: ManaPart[] = [];
  let lastIndex = 0;
  let m: RegExpExecArray | null;
  const re = new RegExp(MANA_SYMBOL_REGEX.source, 'g');
  while ((m = re.exec(text)) !== null) {
    if (m.index > lastIndex) {
      parts.push({ type: 'text', value: text.slice(lastIndex, m.index) });
    }
    const inner = m[1].toUpperCase();
    /* Scryfall class suffix: remove / for hybrid (e.g. W/U -> WU, 2/W -> 2W) */
    let key = inner.replace(/\//g, '');
    if (key.length <= 2 && /^\d+$/.test(key)) {
      const n = parseInt(key, 10);
      key = String(Math.min(20, Math.max(0, n)));
    }
    parts.push({ type: 'symbol', key, label: m[0] });
    lastIndex = re.lastIndex;
  }
  if (lastIndex < text.length) {
    parts.push({ type: 'text', value: text.slice(lastIndex) });
  }
  return parts;
}

export interface ManaTextProps {
  /** Text that may contain mana symbols like {U}, {R}, {1} */
  text: string;
  /** Optional class name for the wrapper (e.g. for line height / spacing) */
  className?: string;
}

/**
 * Renders text with MTG mana symbols using Scryfall SVG assets.
 * Uses .card-symbol and .card-symbol-{key}; key is normalized (e.g. W/U → WU, 2/W → 2W).
 * Recognizes WUBRG, 0–20, C, X, hybrid (WU, 2W, …), phyrexian (UP, …), etc.
 */
export function ManaText({ text, className }: ManaTextProps) {
  const parts = parseManaParts(text);
  return (
    <span className={className}>
      {parts.map((part, i) => {
        if (part.type === 'text') {
          return <React.Fragment key={i}>{part.value}</React.Fragment>;
        }
        return (
          <span
            key={i}
            className={`card-symbol card-symbol-${part.key}`}
            title={part.label}
            aria-label={part.label}
          >
            {part.label}
          </span>
        );
      })}
    </span>
  );
}
