import { useEffect, useRef, useState } from 'react';

function easeOut(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

/**
 * Animates a number from its previous value to the target over ~duration ms.
 * Returns the current display value.
 */
export function useCountUp(target: number, duration = 800): number {
  const [display, setDisplay] = useState(0);
  const prevTarget = useRef(0);
  const rafId = useRef(0);

  useEffect(() => {
    const from = prevTarget.current;
    const diff = target - from;
    if (diff === 0) return;

    const start = performance.now();

    function tick(now: number) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const value = from + diff * easeOut(progress);
      setDisplay(value);

      if (progress < 1) {
        rafId.current = requestAnimationFrame(tick);
      } else {
        prevTarget.current = target;
      }
    }

    rafId.current = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(rafId.current);
    };
  }, [target, duration]);

  // Snap on first render if target is already set
  useEffect(() => {
    if (prevTarget.current === 0 && target === 0) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- intentional: snap display to 0 on init
      setDisplay(0);
    }
  }, [target]);

  return display;
}
