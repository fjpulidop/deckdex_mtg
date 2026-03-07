import { useRef, useEffect, useCallback } from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { MANA_COLORS, MANA_SYMBOLS, symbolToColorKey } from './constants';
import { useReducedMotion } from './useReducedMotion';

interface SymbolDrop {
  symbol: string;
  colorKey: string;
  x: number;
  y: number;
  speed: number;
  opacity: number;
  fontSize: number;
}

const COLUMN_COUNT = 10;
const FPS = 30;
const FRAME_INTERVAL = 1000 / FPS;

function createDrop(x: number, height: number, randomY?: boolean): SymbolDrop {
  const symbol = MANA_SYMBOLS[Math.floor(Math.random() * MANA_SYMBOLS.length)];
  return {
    symbol,
    colorKey: symbolToColorKey(symbol),
    x,
    y: randomY ? Math.random() * height : -(Math.random() * height * 0.5),
    speed: 0.3 + Math.random() * 0.5,
    opacity: 0.03 + Math.random() * 0.12,
    fontSize: 14 + Math.random() * 4,
  };
}

/**
 * Returns a cached off-screen canvas with the given symbol pre-rendered with a glow effect.
 * Cache key is "hex:fontSize" — avoids shadowBlur on the main canvas context every frame.
 */
function getGlowCanvas(
  cache: Map<string, HTMLCanvasElement>,
  hex: string,
  fontSize: number,
  symbol: string
): HTMLCanvasElement {
  const key = `${hex}:${fontSize}`;
  const cached = cache.get(key);
  if (cached) return cached;

  const size = fontSize * 4;
  const offscreen = document.createElement('canvas');
  offscreen.width = size;
  offscreen.height = size;
  const offCtx = offscreen.getContext('2d');
  if (offCtx) {
    offCtx.globalAlpha = 1;
    offCtx.font = `${fontSize}px monospace`;
    offCtx.textAlign = 'center';
    offCtx.textBaseline = 'middle';
    offCtx.fillStyle = hex;
    offCtx.shadowColor = hex;
    offCtx.shadowBlur = 8;
    offCtx.fillText(symbol, size / 2, size / 2);
  }
  cache.set(key, offscreen);
  return offscreen;
}

export function CardMatrix() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const dropsRef = useRef<SymbolDrop[]>([]);
  const animFrameRef = useRef<number>(0);
  const lastFrameRef = useRef<number>(0);
  const pausedRef = useRef<boolean>(false);
  const glowCacheRef = useRef<Map<string, HTMLCanvasElement>>(new Map());
  const { theme } = useTheme();
  const reducedMotion = useReducedMotion();
  const isDark = theme === 'dark';

  const opacityMax = isDark ? 0.2 : 0.1;

  // Refs to hold current theme values so animation callbacks stay stable across theme changes
  const isDarkRef = useRef<boolean>(isDark);
  const opacityMaxRef = useRef<number>(opacityMax);

  // Sync theme values into refs and clear the glow cache when theme changes
  useEffect(() => {
    isDarkRef.current = isDark;
    opacityMaxRef.current = opacityMax;
    glowCacheRef.current.clear(); // invalidate stale glow canvases keyed by old hex values
  }, [isDark, opacityMax]);

  const initDrops = useCallback((width: number, height: number) => {
    const drops: SymbolDrop[] = [];
    const colWidth = width / COLUMN_COUNT;

    for (let col = 0; col < COLUMN_COUNT; col++) {
      const x = col * colWidth + colWidth * 0.3 + Math.random() * colWidth * 0.4;
      // 3-5 symbols per column at staggered heights
      const count = 3 + Math.floor(Math.random() * 3);
      for (let i = 0; i < count; i++) {
        drops.push(createDrop(x, height, true));
      }
    }

    dropsRef.current = drops;
  }, []);

  const draw = useCallback(
    (ctx: CanvasRenderingContext2D, width: number, height: number) => {
      ctx.clearRect(0, 0, width, height);
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';

      for (const d of dropsRef.current) {
        const color = MANA_COLORS[d.colorKey];
        const hex = isDarkRef.current ? color.dark : color.light;
        const alpha = Math.min(d.opacity, opacityMaxRef.current);

        ctx.globalAlpha = alpha;
        ctx.font = `${d.fontSize}px monospace`;
        ctx.fillStyle = hex;
        ctx.fillText(d.symbol, d.x, d.y);

        // Glow via pre-rendered off-screen canvas — avoids shadowBlur on every frame
        if (isDarkRef.current) {
          const glowCanvas = getGlowCanvas(glowCacheRef.current, hex, d.fontSize, d.symbol);
          ctx.globalAlpha = alpha * 0.4;
          ctx.drawImage(
            glowCanvas,
            d.x - glowCanvas.width / 2,
            d.y - glowCanvas.height / 2
          );
        }
      }
      ctx.globalAlpha = 1;
    },
    [] // stable: reads theme state and glow cache via refs
  );

  /* eslint-disable react-hooks/immutability -- mutating ref contents (drop positions) is intentional for canvas animation */
  const update = useCallback(
    (width: number, height: number) => {
      for (const d of dropsRef.current) {
        d.y += d.speed;

        // Reset when off screen
        if (d.y > height + 30) {
          const colWidth = width / COLUMN_COUNT;
          const col = Math.floor(d.x / colWidth);
          d.x = col * colWidth + colWidth * 0.3 + Math.random() * colWidth * 0.4;
          d.y = -(Math.random() * 100);
          d.speed = 0.3 + Math.random() * 0.5;
          d.opacity = 0.03 + Math.random() * 0.12;
          const symbol = MANA_SYMBOLS[Math.floor(Math.random() * MANA_SYMBOLS.length)];
          d.symbol = symbol;
          d.colorKey = symbolToColorKey(symbol);
        }
      }
    },
    []
  );
  /* eslint-enable react-hooks/immutability */

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resize = () => {
      const dpr = window.devicePixelRatio || 1;
      canvas.width = window.innerWidth * dpr;
      canvas.height = window.innerHeight * dpr;
      canvas.style.width = `${window.innerWidth}px`;
      canvas.style.height = `${window.innerHeight}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      if (dropsRef.current.length === 0) {
        initDrops(window.innerWidth, window.innerHeight);
      }
    };

    resize();

    if (reducedMotion) {
      draw(ctx, window.innerWidth, window.innerHeight);
      return;
    }

    let resizeTimer: ReturnType<typeof setTimeout>;
    const onResize = () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(resize, 200);
    };
    window.addEventListener('resize', onResize);

    const animate = (timestamp: number) => {
      if (timestamp - lastFrameRef.current >= FRAME_INTERVAL) {
        lastFrameRef.current = timestamp;
        update(window.innerWidth, window.innerHeight);
        draw(ctx, window.innerWidth, window.innerHeight);
      }
      animFrameRef.current = requestAnimationFrame(animate);
    };

    // Pause immediately if document is already hidden at mount time
    if (document.hidden) {
      pausedRef.current = true;
    } else {
      animFrameRef.current = requestAnimationFrame(animate);
    }

    const handleVisibility = () => {
      if (document.hidden) {
        pausedRef.current = true;
        cancelAnimationFrame(animFrameRef.current);
      } else {
        pausedRef.current = false;
        animFrameRef.current = requestAnimationFrame(animate);
      }
    };
    document.addEventListener('visibilitychange', handleVisibility);

    return () => {
      cancelAnimationFrame(animFrameRef.current);
      window.removeEventListener('resize', onResize);
      document.removeEventListener('visibilitychange', handleVisibility);
      clearTimeout(resizeTimer);
    };
  }, [reducedMotion, initDrops, draw, update]);

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none fixed inset-0 z-0"
      aria-hidden="true"
    />
  );
}
