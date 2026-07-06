import { CheckCircle2, LogOut, Megaphone, Play, XCircle } from 'lucide-react';

import brandLogo from '../../../../assets/images/equilateral_logo.png';
import { formatTime } from '../utils/staffUtils.js';

export function Counter({
  activeCounterId,
  counterName,
  clearSession,
  counterActive,
  loading,
  runAction,
  updateCounterStatus,
  accessToken,
  message,
  currentToken,
  startToken,
  completeToken,
  requestCancelToken,
  waitingTokens,
  callableWaitingTokenIds,
  callNextToken,
  startNextToken,
  callWaitingToken,
  loadCounterQueue,
}) {
  const counterLabel = counterName || (activeCounterId ? `Counter #${activeCounterId}` : 'Counter');
  const currentTokenCalled = currentToken?.status === 'CALLED';
  const currentTokenServing = currentToken?.status === 'SERVING';
  const canCallWaitingToken = Boolean(accessToken && activeCounterId && counterActive && !currentToken && !loading);

  return (
    <main className="min-h-screen text-white animate-fadeIn">
      <section className="mx-auto flex min-h-screen max-w-md flex-col px-4 py-5 animate-slideUp">
        <header className="customer-sticky-header flex items-center justify-between rounded-lg bg-brand-red px-4 py-3 shadow-brand">
          <div className="flex items-center gap-3">
            <img src={brandLogo} alt="Checkout Queue logo" className="h-10 w-24 rounded-lg bg-white p-1 object-cover" />
            <div>
            <p className="text-sm text-red-100">Counter console</p>
            <h1 className="text-2xl font-semibold text-white">{counterLabel}</h1>
            </div>
          </div>
          <button type="button" onClick={clearSession} className="rounded-lg bg-white/15 p-2 text-white" title="Logout">
            <LogOut size={20} />
          </button>
        </header>

        <div className="mt-5 rounded-lg bg-white p-4 text-ink glass-panel">
          {/* <label className="text-sm font-medium text-charcoal">Assigned counter</label>
          {counterName ? (
            <div className="mt-1 rounded-lg border border-line bg-slate-50 px-3 py-2 text-sm font-semibold text-ink">{counterName}</div>
          ) : (
            <input
              value={activeCounterId}
              onChange={(event) => setActiveCounterId(event.target.value)}
              className="mt-1 w-full rounded-lg border border-line px-3 py-2 outline-none focus:border-brand-red"
              aria-label="Counter ID"
            />
          )} */}
          <div className="mt-3 rounded-lg border border-line bg-slate-50 p-3">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-charcoal">Counter status</p>
                <p className={`mt-1 text-xs font-semibold ${counterActive ? 'text-success' : 'text-muted'}`}>
                  {counterActive ? 'Active and accepting tokens' : 'Inactive'}
                </p>
              </div>
              <label className="relative inline-flex cursor-pointer items-center">
                <input
                  type="checkbox"
                  checked={counterActive}
                  onChange={() => runAction(() => updateCounterStatus(activeCounterId, { is_active: !counterActive }))}
                  disabled={!accessToken || loading || !activeCounterId}
                  className="peer sr-only"
                  aria-label="Toggle counter active status"
                />
                <span className="h-7 w-12 rounded-full bg-slate-300 transition-colors peer-checked:bg-success peer-disabled:opacity-60" />
                <span className="absolute left-1 top-1 size-5 rounded-full bg-white shadow transition-transform peer-checked:translate-x-5" />
              </label>
            </div>
          </div>
        </div>

        {message ? <p className="mt-4 rounded-lg bg-rose-100 px-3 py-2 text-sm text-rose-800">{message}</p> : null}

        <section className="mt-5 rounded-lg bg-white p-4 text-ink glass-panel">
          <p className="text-sm font-semibold text-muted">Now serving</p>
          {currentToken ? (
            <div className="mt-3">
              <div className="text-4xl font-bold">{currentToken.token_number}</div>
              <p className="mt-1 text-sm text-charcoal">
                {currentToken.item_count || 0} items · {currentToken.phone_number}
              </p>
              <p className="mt-1 text-sm text-charcoal">Status: {currentToken.status}</p>
              <div className="mt-4 grid grid-cols-2 gap-3">
                {currentTokenCalled ? (
                  <button
                    type="button"
                    onClick={() => runAction(() => startToken(currentToken.token_id))}
                    disabled={loading}
                    className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-red px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
                  >
                    <Play size={18} />
                    Start service
                  </button>
                ) : null}
                {currentTokenServing ? (
                  <button
                    type="button"
                    onClick={() => runAction(() => completeToken(currentToken.token_id))}
                    disabled={loading}
                    className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-red px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
                  >
                    <CheckCircle2 size={18} />
                    Complete
                  </button>
                ) : null}
                <button
                  type="button"
                  onClick={() => requestCancelToken(currentToken)}
                  disabled={loading}
                  className="inline-flex items-center justify-center gap-2 rounded-lg bg-rose-600 px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
                >
                  <XCircle size={18} />
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="mt-3 grid grid-cols-2 gap-3">
              <button
                type="button"
                disabled={!accessToken || !activeCounterId || !counterActive || waitingTokens.length === 0 || loading}
                onClick={callNextToken}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-red px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
              >
                <Megaphone size={18} />
                Call next
              </button>
              <button
                type="button"
                disabled={!accessToken || !activeCounterId || !counterActive || waitingTokens.length === 0 || loading}
                onClick={startNextToken}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
              >
                <Play size={18} />
                Start next
              </button>
            </div>
          )}
        </section>

        <section className="mt-5 flex-1 rounded-lg bg-white p-4 text-ink glass-panel">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Waiting queue</h2>
            <button type="button" onClick={loadCounterQueue} className="rounded-lg border border-line px-3 py-2 text-sm font-medium text-charcoal">
              Refresh
            </button>
          </div>
          <div className="mt-3 space-y-3">
            {waitingTokens.length === 0 ? <p className="text-sm text-muted">No waiting tokens for this counter.</p> : null}
            {waitingTokens.map((token) => (
              <div key={token.token_id} className="flex items-center justify-between gap-3 rounded-lg border border-line p-3">
                <div>
                  <p className="font-semibold">{token.token_number}</p>
                  <p className="text-sm text-charcoal">
                    {token.item_count || 0} items · {token.estimated_wait_minutes}m wait
                  </p>
                  <p className="text-xs text-muted">Call {formatTime(token.calling_time)}</p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => callWaitingToken(token)}
                    disabled={!canCallWaitingToken || !callableWaitingTokenIds.has(String(token.token_id))}
                    className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-red px-3 py-2 text-sm font-semibold text-white disabled:opacity-60"
                    title="Call token"
                  >
                    <Megaphone size={18} />
                    Call
                  </button>
                  <button type="button" onClick={() => requestCancelToken(token)} className="rounded-lg border border-rose-200 p-2 text-rose-700" title="Cancel token">
                    <XCircle size={18} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}
