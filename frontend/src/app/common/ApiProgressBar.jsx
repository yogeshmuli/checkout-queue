import { useEffect, useState } from 'react';
import { LoaderCircle } from 'lucide-react';

import { subscribeToApiActivity } from '../../api/httpClient.js';

const SHOW_DELAY_MS = 120;

export function ApiProgressBar() {
  const [activeRequests, setActiveRequests] = useState(0);
  const [visible, setVisible] = useState(false);

  useEffect(() => subscribeToApiActivity(setActiveRequests), []);

  useEffect(() => {
    if (!activeRequests) {
      setVisible(false);
      return undefined;
    }

    const timer = window.setTimeout(() => setVisible(true), SHOW_DELAY_MS);
    return () => window.clearTimeout(timer);
  }, [activeRequests]);

  if (!visible) return null;

  return (
    <div
      className="pointer-events-none fixed inset-0 z-[100] flex items-center justify-center"
      role="status"
      aria-label="Loading application data"
    >
      <div className="flex items-center gap-3 rounded-xl border border-line bg-white/95 px-5 py-4 text-brand-red shadow-xl backdrop-blur-sm">
        <LoaderCircle size={28} className="animate-spin" aria-hidden="true" />
        <span className="text-sm font-semibold text-charcoal">Loading...</span>
      </div>
    </div>
  );
}
