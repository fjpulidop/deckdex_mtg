import type { Card } from '../api/client';

export interface CardCollectionViewProps {
  cards: Card[];
  isLoading?: boolean;
  onAdd?: () => void;
  onImport?: () => void;
  onUpdatePrices?: () => void;
  updatingPrices?: boolean;
  onRowClick?: (card: Card) => void;
  onQuantityChange?: (id: number, qty: number) => void;
  /** Server-side total count (before pagination). Displayed in the pagination footer. */
  serverTotal?: number;
  /** Current sort column key (controlled by parent for server-side sorting). */
  sortBy?: string;
  /** Current sort direction (controlled by parent for server-side sorting). */
  sortDir?: 'asc' | 'desc';
  /** Called when user clicks a sortable column header. Parent updates query and re-fetches. */
  onSortChange?: (key: string, dir: 'asc' | 'desc') => void;
  /** Current page number (1-based, controlled by parent). */
  page?: number;
  /** Total number of pages derived from serverTotal. */
  totalPages?: number;
  /** Called when user navigates to a different page. */
  onPageChange?: (page: number) => void;
}
