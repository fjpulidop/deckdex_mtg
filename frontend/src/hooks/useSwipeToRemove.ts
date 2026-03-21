import { useState, useRef, useCallback } from 'react';

const SWIPE_THRESHOLD = 72;
const AXIS_LOCK_RATIO = 1.5;
const CAPTURE_START_PX = 8;

export function useSwipeToRemove(onRemove: () => void): {
  containerProps: React.HTMLAttributes<HTMLElement>;
  translateX: number;
  animatingBack: boolean;
  isRevealed: boolean;
} {
  const [translateX, setTranslateX] = useState(0);
  const [animatingBack, setAnimatingBack] = useState(false);
  const startX = useRef(0);
  const startY = useRef(0);
  const tracking = useRef(false);
  const axisLocked = useRef<'horizontal' | 'vertical' | null>(null);

  const onPointerDown = useCallback((e: React.PointerEvent) => {
    if (e.pointerType === 'mouse') return;
    startX.current = e.clientX;
    startY.current = e.clientY;
    tracking.current = true;
    axisLocked.current = null;
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  }, []);

  const onPointerMove = useCallback((e: React.PointerEvent) => {
    if (!tracking.current) return;
    const dx = e.clientX - startX.current;
    const dy = e.clientY - startY.current;
    const dist = Math.sqrt(dx * dx + dy * dy);

    if (axisLocked.current === null && dist > CAPTURE_START_PX) {
      axisLocked.current =
        Math.abs(dx) > Math.abs(dy) * AXIS_LOCK_RATIO ? 'horizontal' : 'vertical';
    }

    if (axisLocked.current !== 'horizontal') return;

    if (dx < 0) {
      setAnimatingBack(false);
      setTranslateX(Math.max(dx, -SWIPE_THRESHOLD));
    }
  }, []);

  const onPointerUp = useCallback(() => {
    if (!tracking.current) return;
    tracking.current = false;

    setTranslateX((prev) => {
      if (prev <= -SWIPE_THRESHOLD) {
        onRemove();
        return 0;
      }
      setAnimatingBack(true);
      setTimeout(() => setAnimatingBack(false), 200);
      return 0;
    });
  }, [onRemove]);

  const onPointerCancel = useCallback(() => {
    tracking.current = false;
    setAnimatingBack(true);
    setTranslateX(0);
    setTimeout(() => setAnimatingBack(false), 200);
  }, []);

  return {
    containerProps: { onPointerDown, onPointerMove, onPointerUp, onPointerCancel },
    translateX,
    animatingBack,
    isRevealed: translateX <= -36,
  };
}
