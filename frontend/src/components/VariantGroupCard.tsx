import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ChevronDown } from 'lucide-react';
import { CardVariantGroup } from '../api/client';
import { VariantCopyRow } from './VariantCopyRow';

interface VariantGroupCardProps {
  group: CardVariantGroup;
  defaultExpanded?: boolean;
}

export function VariantGroupCard({ group, defaultExpanded = false }: VariantGroupCardProps) {
  const { t } = useTranslation();
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const owned = group.owned_variant_count;
  const total = group.total_known_variants;
  const progressPercent = total > 0 ? (owned / total) * 100 : 0;
  const headerId = `variant-group-${group.card_name.replace(/\s+/g, '-').toLowerCase()}`;

  return (
    <article className="border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 rounded-xl overflow-hidden">
      {/* Collapsible header */}
      <button
        id={headerId}
        type="button"
        onClick={() => setIsExpanded((prev) => !prev)}
        aria-expanded={isExpanded}
        aria-controls={`${headerId}-body`}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 dark:focus-visible:ring-indigo-400"
      >
        <div className="flex-1 min-w-0 mr-4">
          {/* Card name */}
          <p className="font-semibold text-gray-900 dark:text-white truncate">
            {group.card_name}
          </p>

          {/* Variants count */}
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
            {t('variants.variantsOwned', { owned, total })}
          </p>

          {/* Progress bar */}
          <div
            role="progressbar"
            aria-valuenow={owned}
            aria-valuemin={0}
            aria-valuemax={total}
            aria-label={t('variants.variantsOwned', { owned, total })}
            className="mt-2 h-1.5 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden"
          >
            <div
              className="h-full rounded-full bg-indigo-500 dark:bg-indigo-400 transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* Chevron icon */}
        <ChevronDown
          className={`w-5 h-5 flex-shrink-0 text-gray-400 transition-transform duration-200 ${
            isExpanded ? 'rotate-180' : ''
          }`}
          aria-hidden="true"
        />
      </button>

      {/* Expandable body */}
      <div
        id={`${headerId}-body`}
        className={`transition-all duration-200 overflow-hidden ${
          isExpanded ? 'max-h-[2000px]' : 'max-h-0'
        }`}
      >
        <ul
          role="list"
          className="divide-y divide-gray-100 dark:divide-gray-700"
        >
          {group.slots.map((slot) => {
            const firstCopyId = slot.copies[0]?.id;
            return (
              <li key={slot.variant_label}>
                <VariantCopyRow slot={slot} firstCopyId={firstCopyId} />
              </li>
            );
          })}
        </ul>
      </div>
    </article>
  );
}
