import { Clock3, TicketCheck } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';

import brandLogo from '../../../assets/images/equilateral_logo.png';
import { getErrorMessage } from '../../../api/httpClient.js';
import { getTokenStatus } from '../../../api/queueApi.js';
import { EmptyStateCard, StatCard } from '../../../app/common/FormAndStatePrimitives.jsx';
import { useQueueStore } from '../../../store/queueStore.js';
import { formatTime, getWaitMinutes, TOKEN_STATUS_REFRESH_MS } from '../utils/customerUtils.js';
import { InvalidToken } from './InvalidToken.jsx';

export function TokenStatus() {
  const { tokenId } = useParams();
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const { lastToken, setLastToken } = useQueueStore();
  const liveWaitMinutes = useMemo(() => getWaitMinutes(lastToken?.calling_time), [lastToken]);
  const parsedTokenId = Number(tokenId);

  useEffect(() => {
    if (!tokenId || Number.isNaN(parsedTokenId)) {
      setLoading(false);
      setMessage('Invalid or missing token ID in URL.');
      return;
    }

    let cancelled = false;

    const fetchToken = async () => {
      try {
        const token = await getTokenStatus({ token_id: parsedTokenId });
        if (cancelled) return;
        setLastToken(token);
        setMessage('');
      } catch (error) {
        if (cancelled) return;
        setMessage(getErrorMessage(error));
        setLastToken(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchToken();

    const intervalId = window.setInterval(fetchToken, TOKEN_STATUS_REFRESH_MS);
    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [tokenId, parsedTokenId, setLastToken]);

  if (!tokenId || Number.isNaN(parsedTokenId)) {
    return <InvalidToken />;
  }

  return (
    <main className="min-h-screen px-4 py-5  animate-fadeIn">
      <section className="mx-auto max-w-md animate-slideUp">
        <header className="rounded-lg bg-brand-red  text-white p-4 text-ink glass-panel border-l-4 border-brand-red">
          <div className="flex items-center gap-3">
            <img src={brandLogo} alt="Checkout Queue logo" className="h-10 w-24 rounded-lg bg-white p-1 object-contain" />
            <div>
              <p className="text-sm text-white">QR checkout queue</p>
              <h1 className="text-2xl font-semibold">Token status</h1>
            </div>
          </div>
          <p className="mt-3 text-sm text-white">Token ID: {parsedTokenId}</p>
        </header>

        {loading ? (
          <section className="mt-5 rounded-lg bg-white p-5 text-ink shadow-soft">
            <p className="text-sm text-charcoal">Loading token status...</p>
          </section>
        ) : null}

        {!loading && lastToken ? (
          <section className="mt-5 rounded-lg bg-white p-5 text-ink shadow-soft">
            <div className="flex items-center gap-3">
              <div className="flex size-12 items-center justify-center rounded-lg bg-brand-blush text-brand-red">
                <TicketCheck size={26} />
              </div>
              <div>
                <p className="text-sm text-muted">Your token</p>
                <h2 className="text-3xl font-bold">{lastToken.token_number}</h2>
              </div>
            </div>
            <div className="mt-5 grid grid-cols-2 gap-3">
              <StatCard icon={<Clock3 size={18} />} label="Wait" value={`${liveWaitMinutes}m`} />
              <StatCard label="Position" value={`#${lastToken.position}`} />
            </div>
            <div className="mt-3 rounded-lg border border-line p-3">
              <p className="text-sm text-muted">Status</p>
              <p className="mt-1 font-semibold">{lastToken.status}</p>
              <p className="mt-2 text-sm text-charcoal">Calling time: {formatTime(lastToken.calling_time)}</p>
            </div>
            <p className="mt-4 rounded-lg bg-brand-blush px-3 py-2 text-sm text-charcoal">
              Estimate method: {lastToken.calculation_method}
            </p>
          </section>
        ) : null}

        {!loading && !lastToken ? (
          <EmptyStateCard
            message={message || 'Invalid or no token present.'}
            ctaTo="/app/customer/create"
            ctaLabel="Go to create token"
          />
        ) : null}
      </section>
    </main>
  );
}
