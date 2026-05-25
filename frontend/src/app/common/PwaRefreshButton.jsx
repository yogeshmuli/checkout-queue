import { RefreshCw } from 'lucide-react';
import { useEffect, useState } from 'react';

function isStandalonePwa() {
  return window.matchMedia?.('(display-mode: standalone)').matches || window.navigator.standalone === true;
}

export function PwaRefreshButton() {
  const [isVisible, setIsVisible] = useState(() => isStandalonePwa());

  useEffect(() => {
    const mediaQuery = window.matchMedia?.('(display-mode: standalone)');
    if (!mediaQuery) return undefined;

    function syncVisibility() {
      setIsVisible(isStandalonePwa());
    }

    mediaQuery.addEventListener('change', syncVisibility);
    return () => mediaQuery.removeEventListener('change', syncVisibility);
  }, []);

  if (!isVisible) return null;

  return (
    <button
      type="button"
      onClick={() => window.location.reload()}
      className="fixed bottom-[max(1rem,env(safe-area-inset-bottom))] right-4 z-50 inline-flex size-12 items-center justify-center rounded-full border border-white/70 bg-brand-red text-white shadow-soft"
      aria-label="Refresh app"
      title="Refresh app"
    >
      <RefreshCw size={20} />
    </button>
  );
}
