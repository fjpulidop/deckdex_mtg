import { useTranslation } from 'react-i18next';
import { VariantSlot } from '../api/client';

interface VariantCopyRowProps {
  slot: VariantSlot;
  /** ID of the first owned copy (used to build /api/cards/{id}/image URL). */
  firstCopyId?: number;
}

function FinishBadge({ finish }: { finish: string }) {
  const { t } = useTranslation();
  const lower = finish.toLowerCase();

  if (lower === 'foil') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-400 text-yellow-900">
        {t('variants.finishFoil')}
      </span>
    );
  }
  if (lower === 'etched') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-400 text-slate-900">
        {t('variants.finishEtched')}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
      {t('variants.finishRegular')}
    </span>
  );
}

export function VariantCopyRow({ slot, firstCopyId }: VariantCopyRowProps) {
  const { t } = useTranslation();

  const imageSrc: string | undefined =
    firstCopyId != null
      ? `/api/cards/${firstCopyId}/image`
      : slot.scryfall_image_uri;

  const firstCopy = slot.copies[0];
  const condition = firstCopy?.condition;
  const quantity = firstCopy?.quantity ?? 0;
  const price = firstCopy?.price;

  return (
    <div
      role="listitem"
      className={`flex items-start gap-4 p-3 rounded-lg transition-opacity ${
        slot.owned ? '' : 'opacity-40'
      }`}
      aria-label={
        !slot.owned
          ? `${t('variants.notOwned')} — ${slot.variant_label}`
          : undefined
      }
    >
      {/* Image area */}
      <div className="w-20 flex-shrink-0">
        {imageSrc ? (
          <img
            src={imageSrc}
            alt={slot.variant_label}
            className="w-full rounded shadow-sm object-cover"
          />
        ) : (
          <div className="w-full aspect-[2/3] rounded shadow-sm bg-gray-200 dark:bg-gray-700" />
        )}
      </div>

      {/* Detail area */}
      <div className="flex-1 min-w-0 flex flex-col gap-1.5 pt-1">
        {/* Variant label pill */}
        <span className="inline-flex items-center self-start px-2 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300">
          {slot.variant_label}
        </span>

        {/* Finish badge */}
        <FinishBadge finish={slot.finish} />

        {slot.owned ? (
          <div className="flex flex-wrap items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
            {condition && (
              <span className="px-1.5 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-700">
                {condition}
              </span>
            )}
            {quantity > 0 && (
              <span>x{quantity}</span>
            )}
            {price && (
              <span className="font-medium text-green-600 dark:text-green-400">
                {price}
              </span>
            )}
          </div>
        ) : (
          <span className="text-xs text-gray-400 dark:text-gray-500">
            {t('variants.notOwned')}
          </span>
        )}
      </div>
    </div>
  );
}
