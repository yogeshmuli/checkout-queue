import { ChevronDown } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

export function Field({ label, value, onChange,disabled = false, ...rest }) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-charcoal">{label}</span>
      <input
     { ...rest}
      disabled={disabled}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1 w-full rounded-lg border border-line px-3 py-2.5 outline-none focus:border-brand-red focus:ring-2 focus:ring-brand-soft"
      />
    </label>
  );
}

export function Select({ label, value, onChange, options, disabled = false }) {
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef(null);
  const labelId = `${String(label).toLowerCase().replace(/[^a-z0-9]+/g, '-') || 'select'}-label`;

  const normalizedOptions = useMemo(
    () =>
      options.map((option) => {
        if (typeof option === 'string') {
          return { label: option, value: option };
        }
        return option;
      }),
    [options]
  );

  const selectedOption =
    normalizedOptions.find((option) => String(option.value) === String(value)) ?? normalizedOptions[0] ?? null;

  useEffect(() => {
    if (!isOpen) return undefined;

    function handlePointerDown(event) {
      if (!wrapperRef.current?.contains(event.target)) {
        setIsOpen(false);
      }
    }

    function handleKeyDown(event) {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  function handleSelect(nextValue) {
    if (disabled) {
      return;
    }
    onChange(nextValue);
    setIsOpen(false);
  }

  return (
    <div className="block">
      <span id={labelId} className="text-sm font-medium text-charcoal">
        {label}
      </span>
      <div ref={wrapperRef} className="relative mt-1">
        <button
          type="button"
          onClick={() => {
            if (!disabled) {
              setIsOpen((prev) => !prev);
            }
          }}
          disabled={disabled}
          className={`flex w-full items-center justify-between rounded-lg border border-line bg-white px-3 py-2.5 text-left outline-none focus:border-brand-red focus:ring-2 focus:ring-brand-soft ${
            disabled ? 'cursor-not-allowed opacity-60' : ''
          }`}
          aria-haspopup="listbox"
          aria-expanded={isOpen}
          aria-labelledby={labelId}
        >
          <span className="truncate text-sm text-charcoal">{selectedOption?.label ?? 'Select option'}</span>
          <ChevronDown size={16} className={`text-muted transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        {isOpen && !disabled ? (
          <div className="absolute z-20 mt-1 w-full rounded-lg border border-line bg-white p-1 shadow-soft" role="listbox" aria-labelledby={labelId}>
            {normalizedOptions.map((option) => {
              const isSelected = String(option.value) === String(value);
              return (
                <button
                  key={String(option.value)}
                  type="button"
                  onClick={() => handleSelect(option.value)}
                  className={`w-full rounded-md px-3 py-2 text-left text-sm ${
                    isSelected ? 'bg-brand-blush font-medium text-brand-red' : 'text-charcoal hover:bg-slate-50'
                  }`}
                  role="option"
                  aria-selected={isSelected}
                >
                  {option.label}
                </button>
              );
            })}
          </div>
        ) : null}
      </div>
    </div>
  );
}

export function StatCard({ icon, label, value }) {
  return (
    <div className="rounded-lg border border-line p-3">
      <div className="flex items-center gap-2 text-sm text-muted">
        {icon}
        {label}
      </div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
    </div>
  );
}

export function EmptyStateCard({ message, ctaTo, ctaLabel }) {
  return (
    <section className="mt-5 rounded-lg bg-white p-5 text-ink shadow-soft">
      <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{message}</p>
      <Link to={ctaTo} className="mt-4 block rounded-lg bg-brand-red px-4 py-3 text-center text-sm font-semibold text-white">
        {ctaLabel}
      </Link>
    </section>
  );
}
