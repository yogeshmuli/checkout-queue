import { AlertTriangle, X } from 'lucide-react';
import { useEffect } from 'react';

export function ConfirmationModal({
  isOpen,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'danger',
  loading = false,
  onConfirm,
  onCancel,
}) {
  useEffect(() => {
    if (!isOpen) return undefined;

    function handleKeyDown(event) {
      if (event.key === 'Escape' && !loading) {
        onCancel?.();
      }
    }

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, loading, onCancel]);

  if (!isOpen) return null;

  const confirmClass =
    variant === 'danger'
      ? 'bg-rose-600 text-white hover:bg-rose-700'
      : 'bg-brand-red text-white hover:bg-red-700';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 px-4" role="dialog" aria-modal="true" aria-labelledby="confirmation-modal-title">
      <div className="w-full max-w-md animate-slideUp rounded-xl bg-white p-5 text-ink shadow-soft">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-brand-blush text-brand-red">
              <AlertTriangle size={20} />
            </div>
            <div>
              <h2 id="confirmation-modal-title" className="text-lg font-semibold">
                {title}
              </h2>
              <p className="mt-2 text-sm text-charcoal">{message}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="rounded-lg p-1 text-muted hover:bg-slate-100 disabled:opacity-50"
            aria-label="Close confirmation"
          >
            <X size={18} />
          </button>
        </div>

        <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="rounded-lg border border-line px-4 py-2.5 text-sm font-medium text-charcoal disabled:opacity-50"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={loading}
            className={`rounded-lg px-4 py-2.5 text-sm font-semibold disabled:opacity-60 ${confirmClass}`}
          >
            {loading ? 'Working...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
