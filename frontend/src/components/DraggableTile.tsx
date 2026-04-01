import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import type { CardAllocation } from '../api/client';
import { AllocationTile } from './AllocationTile';

interface DraggableTileProps {
  allocation: CardAllocation;
  onTileClick: (allocation: CardAllocation) => void;
}

export function DraggableTile({ allocation, onTileClick }: DraggableTileProps) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: allocation.card_id,
    data: { type: 'card', allocation },
  });

  const style = transform
    ? { transform: CSS.Translate.toString(transform) }
    : undefined;

  return (
    <div ref={setNodeRef} style={style} {...listeners} {...attributes}>
      <AllocationTile
        allocation={allocation}
        onTileClick={onTileClick}
        isDragging={isDragging}
      />
    </div>
  );
}
