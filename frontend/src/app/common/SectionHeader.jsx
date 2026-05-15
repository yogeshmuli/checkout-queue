export function SectionHeader({ eyebrow, title, action }) {
  return (
    <div className="flex flex-col gap-3 border-b border-line pb-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {eyebrow ? <p className="text-xs font-semibold uppercase tracking-wide text-brand-red">{eyebrow}</p> : null}
        <h2 className="mt-1 text-xl font-semibold text-ink">{title}</h2>
      </div>
      {action}
    </div>
  );
}

