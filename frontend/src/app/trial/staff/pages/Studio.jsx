import { CheckCircle2, CirclePause, CirclePlay, LogOut, RefreshCcw, XCircle } from 'lucide-react';

import brandLogo from '../../../../assets/images/equilateral_logo.png';
import { formatTime } from '../utils/staffUtils.js';

export function Studio({
  studioId,
  setStudioId,
  clearSession,
  studioActive,
  loading,
  runAction,
  updateTrialStudioStatus,
  accessToken,
  message,
  currentToken,
  completeTrialToken,
  cancelTrialToken,
  waitingTokens,
  startNextToken,
  loadStudioQueue,
  startTrialToken,
}) {
  return (
    <main className="min-h-screen  text-white animate-fadeIn">
      <section className="mx-auto flex min-h-screen max-w-md flex-col px-4 py-5 animate-slideUp">
        <header className="flex items-center justify-between rounded-lg bg-brand-red px-4 py-3 shadow-brand">
          <div className="flex items-center gap-3">
            <img src={brandLogo} alt="Trial Queue logo" className="h-10 w-24 rounded-lg bg-white p-1 object-cover" />
            <div>
              <p className="text-sm text-red-100">Studio console</p>
              <h1 className="text-2xl font-semibold text-white">Studio {studioId || '--'}</h1>
            </div>
          </div>
          <button type="button" onClick={clearSession} className="rounded-lg bg-white/15 p-2 text-white" title="Logout">
            <LogOut size={20} />
          </button>
        </header>

        <div className="mt-5 rounded-lg bg-white p-4 text-ink glass-panel">
          <label className="text-sm font-medium text-charcoal">Studio ID</label>
          <input
            value={studioId}
            onChange={(event) => setStudioId(event.target.value)}
            className="mt-1 w-full rounded-lg border border-line px-3 py-2 outline-none focus:border-brand-red"
          />
          <button
            type="button"
            onClick={() => runAction(() => updateTrialStudioStatus(Number(studioId), { is_active: !studioActive }))}
            disabled={!accessToken || !studioId || loading}
            className={`mt-3 inline-flex w-full items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-semibold disabled:opacity-60 ${
              studioActive ? 'bg-success text-white' : 'bg-brand-soft text-charcoal'
            }`}
          >
            {studioActive ? <CirclePlay size={18} /> : <CirclePause size={18} />}
            {studioActive ? 'Studio active' : 'Studio inactive'}
          </button>
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
                <button
                  type="button"
                  onClick={() => runAction(() => completeTrialToken(currentToken.token_id))}
                  className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-red px-4 py-3 text-sm font-semibold text-white"
                >
                  <CheckCircle2 size={18} />
                  Complete
                </button>
                <button
                  type="button"
                  onClick={() => runAction(() => cancelTrialToken(currentToken.token_id, 'Cancelled from studio console'))}
                  className="inline-flex items-center justify-center gap-2 rounded-lg bg-rose-600 px-4 py-3 text-sm font-semibold text-white"
                >
                  <XCircle size={18} />
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <button
              type="button"
              disabled={!accessToken || waitingTokens.length === 0 || loading}
              onClick={startNextToken}
              className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-brand-red px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
            >
              <RefreshCcw size={18} />
              Start next token
            </button>
          )}
        </section>

        <section className="mt-5 flex-1 rounded-lg bg-white p-4 text-ink glass-panel">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Waiting queue</h2>
            <button
              type="button"
              onClick={loadStudioQueue}
              disabled={!accessToken || loading}
              className="rounded-lg border border-line px-3 py-2 text-sm font-medium text-charcoal disabled:opacity-60"
            >
              Refresh
            </button>
          </div>
          <div className="mt-3 space-y-3">
            {waitingTokens.length === 0 ? <p className="text-sm text-muted">No waiting tokens for this studio.</p> : null}
            {waitingTokens.map((token) => (
              <div key={token.token_id} className="flex items-center justify-between rounded-lg border border-line p-3">
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
                    onClick={() => runAction(() => startTrialToken(token.token_id))}
                    className="rounded-lg bg-brand-red px-3 py-2 text-xs font-semibold text-white"
                  >
                    Start
                  </button>
                  <button
                    type="button"
                    onClick={() => runAction(() => cancelTrialToken(token.token_id, 'Cancelled from waiting queue'))}
                    className="rounded-lg border border-rose-200 p-2 text-rose-700"
                    title="Cancel token"
                  >
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
