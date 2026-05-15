export function MetricTile({ label, value, tone = 'slate' }) {
  const tones = {
    slate: 'border-line bg-white text-ink',
    mint: 'border-brand-soft bg-brand-blush text-ink',
    amber: 'border-amber-200 bg-amber-50 text-amber-900',
    rose: 'border-rose-200 bg-rose-50 text-rose-900',
  };

  return (
    <div className={`rounded-lg border p-4 ${tones[tone]}`}>
      <div className="text-sm font-medium text-charcoal">{label}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
    </div>
  );
}

