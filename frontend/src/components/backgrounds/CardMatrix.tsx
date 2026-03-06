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

export function CardMatrix() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const dropsRef = useRef<SymbolDrop[]>([]);
  const animFrameRef = useRef<number>(0);
  const lastFrameRef = useRef<number>(0);
  const { theme } = useTheme();
  const reducedMotion = useReducedMotion();
  const isDark = theme === 'dark';

  const opacityMax = isDark ? 0.2 : 0.1;

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
        const hex = isDark ? color.dark : color.light;
        const alpha = Math.min(d.opacity, opacityMax);

        ctx.globalAlpha = alpha;
        ctx.font = `${d.fontSize}px monospace`;
        ctx.fillStyle = hex;
        ctx.fillText(d.symbol, d.x, d.y);

        // Subtle glow
        if (isDark) {
          ctx.globalAlpha = alpha * 0.4;
          ctx.shadowColor = hex;
          ctx.shadowBlur = 8;
          ctx.fillText(d.symbol, d.x, d.y);
          ctx.shadowBlur = 0;
        }
      }
      ctx.globalAlpha = 1;
    },
    [isDark, opacityMax]
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
    animFrameRef.current = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animFrameRef.current);
      window.removeEventListener('resize', onResize);
      clearTimeout(resizeTimer);
    };
  }, [draw, update, initDrops, reducedMotion]);

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none fixed inset-0 z-0"
      aria-hidden="true"
    />
  );
}
