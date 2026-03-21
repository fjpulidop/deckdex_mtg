import { useTranslation } from 'react-i18next';
import type { DeckSnapshot } from '../api/client';
import { RevertButton } from './RevertButton';

interface DeckHistoryTimelineProps {
  deckId: number;
  snapshots: DeckSnapshot[];
  onReverted: () => void;
}

function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60_000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  const rtf = new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' });
  if (diffDays > 0) return rtf.format(-diffDays, 'day');
  if (diffHours > 0) return rtf.format(-diffHours, 'hour');
  if (diffMins > 0) return rtf.format(-diffMins, 'minute');
  return rtf.format(0, 'second');
}

function DiffSummary({ snapshot }: { snapshot: DeckSnapshot }) {
  const { t } = useTranslation();
  const { diff } = snapshot;
  const addedCount = diff.added.reduce((s, c) => s + c.quantity, 0);
  const removedCount = diff.removed.reduce((s, c) => s + c.quantity, 0);

  const parts: string[] = [];
  if (addedCount > 0) parts.push(t('deckHistory.diffAdded', { count: addedCount }));
  if (removedCount > 0) parts.push(t('deckHistory.diffRemoved', { count: removedCount }));
  if (parts.length === 0 && diff.quantity_changed.length === 0 && diff.commander_changed == null) {
    return <span className="text-xs text-gray-400 dark:text-gray-500">{t('deckHistory.noChanges')}</span>;
  }
  return <span className="text-xs text-gray-500 dark:text-gray-400">{parts.join(', ')}</span>;
}

export function DeckHistoryTimeline({ deckId, snapshots, onReverted }: DeckHistoryTimelineProps) {
  const { t } = useTranslation();

  if (snapshots.length === 0) {
    return (
      <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
        {t('deckHistory.empty')}
      </p>
    );
  }

  return (
    <ol className="space-y-1">
      {snapshots.map((snap, idx) => {
        const isCurrentVersion = idx === 0;
        return (
          <li
            key={snap.id}
            className="flex items-start justify-between gap-3 py-2 px-3 rounded hover:bg-gray-50 dark:hover:bg-gray-700/50"
          >
            <div className="flex flex-col gap-0.5 min-w-0">
              <span className="text-sm text-gray-900 dark:text-white truncate">
                {snap.change_summary}
                {isCurrentVersion && (
                  <span className="ml-2 text-xs text-indigo-600 dark:text-indigo-400">
                    ({t('deckHistory.currentVersion')})
                  </span>
                )}
              </span>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400 dark:text-gray-500">
                  {formatRelativeTime(snap.created_at)}
                </span>
                <DiffSummary snapshot={snap} />
              </div>
            </div>
            <RevertButton
              deckId={deckId}
              snapshotId={snap.id}
              onReverted={onReverted}
              disabled={isCurrentVersion}
            />
          </li>
        );
      })}
    </ol>
  );
}
