import { useEffect, useRef, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { X } from 'lucide-react';

interface AccessibleModalProps {
  isOpen: boolean;
  onClose: () => void;
  /** id of the heading element inside the modal panel, used for aria-labelledby */
  titleId: string;
  children: ReactNode;
  className?: string;
  /**
   * When true, renders a consistent X close button in the top-right corner of
   * the modal panel with aria-label={t('common.close')}.
   */
  showCloseButton?: boolean;
}

const FOCUSABLE_SELECTORS = [
  'button:not([disabled])',
  '[href]',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(', ');

/**
 * Reusable accessible modal wrapper.
 *
 * Provides:
 * - role="dialog", aria-modal="true", aria-labelledby
 * - Focus trap (Tab cycles within modal)
 * - Escape key to close
 * - Auto-focus first focusable element on open
 * - Focus restoration to trigger element on close
 * - Body scroll-lock while open
 * - Overlay click to close
 */
export function AccessibleModal({
  isOpen,
  onClose,
  titleId,
  children,
  className,
  showCloseButton = false,
}: AccessibleModalProps) {
  const { t } = useTranslation();
  const panelRef = useRef<HTMLDivElement>(null);
  // Capture the element that had focus before the modal opened
  const previousFocusRef = useRef<Element | null>(null);

  // On open: capture previous focus, lock scroll, auto-focus first element
  useEffect(() => {
    if (!isOpen) return;

    previousFocusRef.current = document.activeElement;
    document.body.style.overflow = 'hidden';

    // Auto-focus first focusable element after render
    const timer = setTimeout(() => {
      const panel = panelRef.current;
      if (!panel) return;
      const first = panel.querySelector<HTMLElement>(FOCUSABLE_SELECTORS);
      first?.focus();
    }, 0);

    return () => {
      clearTimeout(timer);
    };
  }, [isOpen]);

  // On close: restore scroll and return focus to previous element
  useEffect(() => {
    if (isOpen) return;
    document.body.style.overflow = '';
    if (previousFocusRef.current instanceof HTMLElement) {
      previousFocusRef.current.focus();
    }
  }, [isOpen]);

  // Cleanup scroll-lock if component unmounts while open
  useEffect(() => {
    return () => {
      document.body.style.overflow = '';
    };
  }, []);

  // Escape-to-close and focus trap via document keydown
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
        return;
      }

      if (e.key !== 'Tab') return;

      const panel = panelRef.current;
      if (!panel) return;

      // Collect focusable elements on each keypress to handle dynamic content
      const focusable = Array.from(
        panel.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTORS)
      ).filter(el => !el.closest('[aria-hidden="true"]'));

      if (focusable.length === 0) {
        e.preventDefault();
        return;
      }

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey) {
        // Shift+Tab: if on first element, wrap to last
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        // Tab: if on last element, wrap to first
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className={`fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 ${className ?? ''}`}
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      onClick={onClose}
    >
      <div
        ref={panelRef}
        className="relative"
        onClick={e => e.stopPropagation()}
      >
        {showCloseButton && (
          <button
            type="button"
            onClick={onClose}
            aria-label={t('common.close')}
            className="absolute top-3 right-3 z-10 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        )}
        {children}
      </div>
    </div>
  );
}
