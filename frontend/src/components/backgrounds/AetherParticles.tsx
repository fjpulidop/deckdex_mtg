import { useRef, useEffect, useCallback } from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { MANA_COLORS } from './constants';
import { useReducedMotion } from './useReducedMotion';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  colorKey: string;
  opacity: number;
  opacityDir: number;
}

const PARTICLE_COUNT = 50;
const FPS = 30;
const FRAME_INTERVAL = 1000 / FPS;

function createParticle(width: number, height: number): Particle {
  const keys = Object.keys(MANA_COLORS);
  return {
    x: Math.random() * width,
    y: Math.random() * height,
    vx: (Math.random() - 0.5) * 0.4,
    vy: (Math.random() - 0.5) * 0.3,
    radius: 2 + Math.random() * 3,
    colorKey: keys[Math.floor(Math.random() * keys.length)],
    opacity: 0.05 + Math.random() * 0.2,
    opacityDir: (Math.random() > 0.5 ? 1 : -1) * (0.001 + Math.random() * 0.002),
  };
}

export function AetherParticles() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const animFrameRef = useRef<number>(0);
  const lastFrameRef = useRef<number>(0);
  const pausedRef = useRef<boolean>(false);
  const { theme } = useTheme();
  const reducedMotion = useReducedMotion();
  const isDark = theme === 'dark';

  const opacityMax = isDark ? 0.3 : 0.15;
  const opacityMin = 0.03;

  // Refs to hold current theme values so animation callbacks stay stable across theme changes
  const isDarkRef = useRef<boolean>(isDark);
  const opacityMaxRef = useRef<number>(opacityMax);

  // Sync theme values into refs without restarting the animation loop
  useEffect(() => {
    isDarkRef.current = isDark;
    opacityMaxRef.current = opacityMax;
  }, [isDark, opacityMax]);

  const initParticles = useCallback((width: number, height: number) => {
    particlesRef.current = Array.from({ length: PARTICLE_COUNT }, () =>
      createParticle(width, height)
    );
  }, []);

  const draw = useCallback(
    (ctx: CanvasRenderingContext2D, width: number, height: number) => {
      ctx.clearRect(0, 0, width, height);

      for (const p of particlesRef.current) {
        const color = MANA_COLORS[p.colorKey];
        const hex = isDarkRef.current ? color.dark : color.light;
        ctx.globalAlpha = Math.min(p.opacity, opacityMaxRef.current);
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = hex;
        ctx.fill();

        // Subtle glow in dark mode
        if (isDarkRef.current) {
          ctx.globalAlpha = Math.min(p.opacity * 0.3, opacityMaxRef.current * 0.3);
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.radius * 3, 0, Math.PI * 2);
          ctx.fillStyle = hex;
          ctx.fill();
        }
      }
      ctx.globalAlpha = 1;
    },
    [] // stable: reads theme state via refs
  );

  /* eslint-disable react-hooks/immutability -- mutating ref contents (particle positions) is intentional for canvas animation */
  const update = useCallback(
    (width: number, height: number) => {
      for (const p of particlesRef.current) {
        p.x += p.vx;
        p.y += p.vy;

        // Wrap around edges
        if (p.x < -10) p.x = width + 10;
        if (p.x > width + 10) p.x = -10;
        if (p.y < -10) p.y = height + 10;
        if (p.y > height + 10) p.y = -10;

        // Pulse opacity
        p.opacity += p.opacityDir;
        if (p.opacity >= opacityMaxRef.current || p.opacity <= opacityMin) {
          p.opacityDir *= -1;
        }
      }
    },
    [] // stable: reads opacityMax via ref
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

      if (particlesRef.current.length === 0) {
        initParticles(window.innerWidth, window.innerHeight);
      }
    };

    resize();

    // Draw static frame for reduced motion
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
  }, [reducedMotion, initParticles, draw, update]);

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none fixed inset-0 z-0"
      aria-hidden="true"
    />
  );
}
