import { ArrowLeft, Clock3, RefreshCw, TicketCheck } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import brandLogo from '../../../../assets/images/equilateral_logo.png';
import { getErrorMessage, showApiErrorToast } from '../../../../api/httpClient.js';
import { cancelCustomerToken, getTokenStatus, moveCustomerTokenLast } from '../../../../api/checkout/queueApi.js';
import { ConfirmationModal } from '../../../common/ConfirmationModal.jsx';
import { EmptyStateCard, StatCard } from '../../../common/FormAndStatePrimitives.jsx';
import { useQueueStore } from '../../../../store/queueStore.js';
import { formatTime, getWaitMinutes, TOKEN_STATUS_REFRESH_MS } from '../utils/customerUtils.js';
import { InvalidToken } from './InvalidToken.jsx';

export function TokenStatus() {
  const { tokenId } = useParams();
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);
  const [movingLast, setMovingLast] = useState(false);
  const [statusLoading, setStatusLoading] = useState(false);
  const [pendingAction, setPendingAction] = useState(null);
  const [message, setMessage] = useState('');
  const { lastToken, setLastToken } = useQueueStore();
  const navigate = useNavigate();
  const liveWaitMinutes = useMemo(() => getWaitMinutes(lastToken?.calling_time), [lastToken]);
  const parsedTokenId = Number(tokenId);
  const canChangeQueue = lastToken?.status === 'WAITING' || lastToken?.status === 'CALLED';
  const isCancelled = lastToken?.status === 'CANCELLED';
  const actionLoading = cancelling || movingLast;
  const pendingActionConfig =
    pendingAction === 'cancel'
      ? {
          title: 'Cancel token?',
          message: 'Your token will be removed from the active queue. You can create a new token later if needed.',
          confirmLabel: 'Cancel token',
          variant: 'danger',
        }
      : {
          title: 'Move last to queue?',
          message: 'Your current token will be cancelled and a new token will be created at the end of the same queue.',
          confirmLabel: 'Move last',
          variant: 'primary',
        };

  async function handleCancelToken() {
    if (!canChangeQueue || cancelling || movingLast) return;

    setCancelling(true);
    setMessage('');

    try {
      await cancelCustomerToken(parsedTokenId);
      const token = await getTokenStatus({ token_id: parsedTokenId });
      setLastToken(token);
      setMessage('Token cancelled successfully.');
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setCancelling(false);
      setPendingAction(null);
    }
  }

  async function handleMoveLast() {
    if (!canChangeQueue || movingLast || cancelling) return;

    setMovingLast(true);
    setMessage('');

    try {
      const token = await moveCustomerTokenLast(parsedTokenId);
      setLastToken(token);
      navigate(`/app/checkout/customer/status/${token.token_id}`, { replace: true });
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setMovingLast(false);
      setPendingAction(null);
    }
  }

  function handleConfirmAction() {
    if (pendingAction === 'cancel') {
      handleCancelToken();
      return;
    }
    if (pendingAction === 'move-last') {
      handleMoveLast();
    }
  }

  async function refreshTokenStatus() {
    if (statusLoading) return;

    setStatusLoading(true);
    setMessage('');
    try {
      const token = await getTokenStatus({ token_id: parsedTokenId });
      setLastToken(token);
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setStatusLoading(false);
      setLoading(false);
    }
  }

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
        showApiErrorToast(error);
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
      <section className="mx-auto max-w-md">
        <header className="customer-sticky-header glass-panel rounded-xl border border-white/30 bg-brand-red p-4 text-white shadow-soft">
          <div className="flex items-start gap-3">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="flex size-10 shrink-0 items-center justify-center rounded-lg border border-white/30 text-white"
              aria-label="Go back"
              title="Go back"
            >
              <ArrowLeft size={18} />
            </button>
            <Link to="/" className="flex h-12 w-28 shrink-0 items-center justify-center rounded-md border border-white/40 bg-white/95 p-1 shadow-sm" aria-label="Go to landing page">
              <img src={brandLogo} alt="Checkout Queue logo" className="h-full w-full object-cover" />
            </Link>
            <div className="min-w-0">
              <p className="text-xs font-medium uppercase tracking-wide text-white/90 sm:text-sm">QR checkout queue</p>
              <h1 className="text-xl font-semibold leading-tight sm:text-2xl">Token status</h1>
            </div>
          </div>
          <p className="mt-3 text-sm text-white/95">Token ID: {parsedTokenId}</p>
        </header>

        {loading ? (
          <section className="mt-5 rounded-lg bg-white p-5 text-ink shadow-soft">
            <p className="text-sm text-charcoal">Loading token status...</p>
          </section>
        ) : null}

        {!loading && lastToken ? (
          <section className="mt-5 rounded-lg bg-white p-5 text-ink shadow-soft">
            <div className="flex items-start justify-between gap-3">
              <div className="flex min-w-0 items-center gap-3">
                <div className="flex size-12 shrink-0 items-center justify-center rounded-lg bg-brand-blush text-brand-red">
                  <TicketCheck size={26} />
                </div>
                <div className="min-w-0">
                  <p className="text-sm text-muted">Your token</p>
                  <h2 className="truncate text-3xl font-bold">{lastToken.token_number}</h2>
                </div>
              </div>
              <button
                type="button"
                onClick={refreshTokenStatus}
                disabled={statusLoading}
                className="flex size-10 shrink-0 items-center justify-center rounded-lg border border-line text-charcoal disabled:opacity-60"
                aria-label="Refresh token status"
                title="Refresh token status"
              >
                <RefreshCw size={18} className={statusLoading ? 'animate-spin' : ''} />
              </button>
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
            {message ? <p className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{message}</p> : null}
            <button
              type="button"
              onClick={() => setPendingAction('cancel')}
              disabled={!canChangeQueue || cancelling || movingLast}
              className="mt-4 w-full rounded-lg bg-rose-600 px-4 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {cancelling ? 'Cancelling token...' : 'Cancel token'}
            </button>
            <button
              type="button"
              onClick={() => setPendingAction('move-last')}
              disabled={!canChangeQueue || movingLast || cancelling}
              className="mt-3 w-full rounded-lg bg-brand-red px-4 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {movingLast ? 'Moving token...' : 'Move last to queue'}
            </button>
            {isCancelled ? (
              <Link
                to="/app/checkout/customer"
                className="mt-3 block w-full rounded-lg bg-brand-red px-4 py-3 text-center text-sm font-semibold text-white"
              >
                Create new token
              </Link>
            ) : null}
            <Link
              to="/app/checkout/customer/status/lookup"
              className="mt-3 block w-full rounded-lg bg-brand-blush px-4 py-3 text-center text-sm font-semibold text-brand-red"
            >
              Check another token by mobile
            </Link>
          </section>
        ) : null}

        {!loading && !lastToken ? (
          <EmptyStateCard
            message={message || 'Invalid or no token present.'}
            ctaTo="/app/checkout/customer/create"
            ctaLabel="Go to create token"
          />
        ) : null}
      </section>
      <ConfirmationModal
        isOpen={Boolean(pendingAction)}
        title={pendingActionConfig.title}
        message={pendingActionConfig.message}
        confirmLabel={pendingActionConfig.confirmLabel}
        variant={pendingActionConfig.variant}
        loading={actionLoading}
        onConfirm={handleConfirmAction}
        onCancel={() => setPendingAction(null)}
      />
    </main>
  );
}
