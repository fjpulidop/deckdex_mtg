import { renderHook, act } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';
import { useSwipeToRemove } from '../useSwipeToRemove';

// ---------------------------------------------------------------------------
// Helpers to build synthetic PointerEvents for the hook handlers
// ---------------------------------------------------------------------------

function makePointerEvent(
  type: string,
  overrides: Partial<React.PointerEvent> = {},
): React.PointerEvent {
  return {
    pointerType: 'touch',
    clientX: 0,
    clientY: 0,
    pointerId: 1,
    currentTarget: {
      setPointerCapture: vi.fn(),
    },
    stopPropagation: vi.fn(),
    preventDefault: vi.fn(),
    ...overrides,
  } as unknown as React.PointerEvent;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('useSwipeToRemove', () => {
  it('mouse pointerdown — onRemove never called, translateX stays 0', () => {
    const onRemove = vi.fn();
    const { result } = renderHook(() => useSwipeToRemove(onRemove));

    act(() => {
      result.current.containerProps.onPointerDown?.(
        makePointerEvent('pointerdown', { pointerType: 'mouse', clientX: 0, clientY: 0 }),
      );
    });
    act(() => {
      result.current.containerProps.onPointerMove?.(
        makePointerEvent('pointermove', { pointerType: 'mouse', clientX: -80, clientY: 0 }),
      );
    });
    act(() => {
      result.current.containerProps.onPointerUp?.(
        makePointerEvent('pointerup', { pointerType: 'mouse' }),
      );
    });

    expect(onRemove).not.toHaveBeenCalled();
    expect(result.current.translateX).toBe(0);
  });

  it('touch swipe >= 72 px left then pointerup — onRemove called once', () => {
    const onRemove = vi.fn();
    const { result } = renderHook(() => useSwipeToRemove(onRemove));

    act(() => {
      result.current.containerProps.onPointerDown?.(
        makePointerEvent('pointerdown', { clientX: 100, clientY: 0 }),
      );
    });
    // Move enough horizontally to pass axis-lock (|dx| > |dy| * 1.5)
    act(() => {
      result.current.containerProps.onPointerMove?.(
        makePointerEvent('pointermove', { clientX: 88, clientY: 0 }), // dx = -12 > 8 px threshold
      );
    });
    // Move past the 72 px threshold
    act(() => {
      result.current.containerProps.onPointerMove?.(
        makePointerEvent('pointermove', { clientX: 20, clientY: 0 }), // dx = -80
      );
    });
    act(() => {
      result.current.containerProps.onPointerUp?.(
        makePointerEvent('pointerup'),
      );
    });

    expect(onRemove).toHaveBeenCalledOnce();
  });

  it('touch swipe < 72 px then pointerup — onRemove not called, translateX returns to 0', () => {
    const onRemove = vi.fn();
    const { result } = renderHook(() => useSwipeToRemove(onRemove));

    act(() => {
      result.current.containerProps.onPointerDown?.(
        makePointerEvent('pointerdown', { clientX: 100, clientY: 0 }),
      );
    });
    act(() => {
      result.current.containerProps.onPointerMove?.(
        makePointerEvent('pointermove', { clientX: 88, clientY: 0 }), // dx = -12 (axis lock)
      );
    });
    act(() => {
      result.current.containerProps.onPointerMove?.(
        makePointerEvent('pointermove', { clientX: 60, clientY: 0 }), // dx = -40 < threshold
      );
    });
    act(() => {
      result.current.containerProps.onPointerUp?.(
        makePointerEvent('pointerup'),
      );
    });

    expect(onRemove).not.toHaveBeenCalled();
    // After pointerup, translateX resets to 0
    expect(result.current.translateX).toBe(0);
  });

  it('more horizontal than vertical — swipe is captured (axis-lock passes)', () => {
    const onRemove = vi.fn();
    const { result } = renderHook(() => useSwipeToRemove(onRemove));

    act(() => {
      result.current.containerProps.onPointerDown?.(
        makePointerEvent('pointerdown', { clientX: 100, clientY: 0 }),
      );
    });
    // dx = -20, dy = -5 → |dx| > |dy| * 1.5 → horizontal lock
    act(() => {
      result.current.containerProps.onPointerMove?.(
        makePointerEvent('pointermove', { clientX: 80, clientY: 5 }),
      );
    });
    // translateX should be negative (row is sliding)
    expect(result.current.translateX).toBeLessThan(0);
  });

  it('more vertical than horizontal — swipe is NOT captured (axis-lock fails)', () => {
    const onRemove = vi.fn();
    const { result } = renderHook(() => useSwipeToRemove(onRemove));

    act(() => {
      result.current.containerProps.onPointerDown?.(
        makePointerEvent('pointerdown', { clientX: 100, clientY: 0 }),
      );
    });
    // dx = -5, dy = -20 → |dx| < |dy| * 1.5 → vertical lock → no translation
    act(() => {
      result.current.containerProps.onPointerMove?.(
        makePointerEvent('pointermove', { clientX: 95, clientY: 20 }),
      );
    });
    // translateX should remain 0 because axis-locked to vertical
    expect(result.current.translateX).toBe(0);
    expect(onRemove).not.toHaveBeenCalled();
  });
});
