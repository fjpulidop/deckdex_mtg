import { useState, useEffect } from 'react';
import { Card } from '../api/client';

interface CardFormModalProps {
  title: string;
  initial?: Partial<Card>;
  onSubmit: (payload: Partial<Card>) => Promise<void>;
  onClose: () => void;
}

export function CardFormModal({ title, initial, onSubmit, onClose }: CardFormModalProps) {
  const [name, setName] = useState(initial?.name ?? '');
  const [type, setType] = useState(initial?.type ?? '');
  const [rarity, setRarity] = useState(initial?.rarity ?? '');
  const [price, setPrice] = useState(initial?.price ?? '');
  const [setNameVal, setSetNameVal] = useState(initial?.set_name ?? '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setName(initial?.name ?? '');
    setType(initial?.type ?? '');
    setRarity(initial?.rarity ?? '');
    setPrice(initial?.price ?? '');
    setSetNameVal(initial?.set_name ?? '');
  }, [initial]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      await onSubmit({
        name: name.trim() || undefined,
        type: type.trim() || undefined,
        rarity: rarity.trim() || undefined,
        price: price.trim() || undefined,
        set_name: setNameVal.trim() || undefined,
      });
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6" onClick={e => e.stopPropagation()}>
        <h2 className="text-lg font-semibold mb-4">{title}</h2>
        {error && <div className="mb-4 text-red-600 text-sm">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              className="w-full border rounded px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
            <input
              type="text"
              value={type}
              onChange={e => setType(e.target.value)}
              className="w-full border rounded px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Rarity</label>
            <input
              type="text"
              value={rarity}
              onChange={e => setRarity(e.target.value)}
              className="w-full border rounded px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Price</label>
            <input
              type="text"
              value={price}
              onChange={e => setPrice(e.target.value)}
              className="w-full border rounded px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Set</label>
            <input
              type="text"
              value={setNameVal}
              onChange={e => setSetNameVal(e.target.value)}
              className="w-full border rounded px-3 py-2"
            />
          </div>
          <div className="flex gap-2 justify-end pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 border rounded hover:bg-gray-50">
              Cancel
            </button>
            <button type="submit" disabled={saving} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50">
              {saving ? 'Saving…' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
