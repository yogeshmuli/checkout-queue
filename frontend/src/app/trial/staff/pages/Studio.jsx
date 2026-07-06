import { CheckCircle2, CirclePause, CirclePlay, LogOut, Megaphone, RefreshCcw, XCircle } from 'lucide-react';

import brandLogo from '../../../../assets/images/equilateral_logo.png';
import { Select } from '../../../common/FormAndStatePrimitives.jsx';
import { formatTime } from '../utils/staffUtils.js';

export function Studio({
  zoneId,
  zoneName,
  zones,
  setZoneId,
  canSelectZone,
  studios,
  clearSession,
  loading,
  runAction,
  updateTrialStudioStatus,
  accessToken,
  message,
  calledToken,
  servingTokens,
  activeStudios,
  vacantActiveStudios,
  completeTrialToken,
  cancelTrialToken,
  waitingTokens,
  nextWaitingToken,
  loadZoneQueue,
  startCalledToken,
  startNextWaitingToken,
  callNextToken,
}) {
  const zoneLabel = zoneName || (zoneId ? `Zone #${zoneId}` : 'Zone console');
  const calledCount = calledToken ? 1 : 0;
  const canCallNext = Boolean(accessToken && zoneId && !calledToken && nextWaitingToken && vacantActiveStudios.length > 0 && !loading);
  const servingTokenByStudioId = new Map(servingTokens.map((token) => [String(token.assigned_studio_id), token]));

  return (
    <main className="min-h-screen animate-fadeIn text-white">
      <section className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-4 py-5 animate-slideUp">
        <header className="customer-sticky-header flex items-center justify-between rounded-lg bg-brand-red px-4 py-3 shadow-brand">
          <div className="flex items-center gap-3">
            <img src={brandLogo} alt="Quick Trial logo" className="h-10 w-24 rounded-lg bg-white p-1 object-cover" />
            <div>
              <p className="text-sm text-red-100">Zone console</p>
              <h1 className="text-2xl font-semibold text-white">{zoneLabel}</h1>
            </div>
          </div>
          <button type="button" onClick={clearSession} className="rounded-lg bg-white/15 p-2 text-white" title="Logout">
            <LogOut size={20} />
          </button>
        </header>

        {canSelectZone ? (
          <div className="mt-5 rounded-lg bg-white p-4 text-ink glass-panel">
            <Select
              label="Trial zone"
              value={zoneId}
              onChange={setZoneId}
              options={[
                { label: 'Select trial zone', value: '' },
                ...zones.map((zone) => ({ label: zone.name, value: String(zone.id) })),
              ]}
            />
          </div>
        ) : null}

        {message ? <p className="mt-4 rounded-lg bg-rose-100 px-3 py-2 text-sm text-rose-800">{message}</p> : null}

        {zoneId ? (
          <>
            <section className="mt-5 rounded-lg bg-white p-4 text-ink glass-panel">
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <h2 className="font-semibold">Zone queue</h2>
                  <p className="text-sm text-muted">Shared queue, per-studio service assignment</p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={loadZoneQueue}
                    disabled={!accessToken || !zoneId || loading}
                    className="rounded-lg border border-line px-3 py-3 text-sm font-medium text-charcoal disabled:opacity-60"
                    title="Refresh"
                  >
                    <RefreshCcw size={18} />
                  </button>
                </div>
              </div>

              <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <MetricCard label="Waiting" value={waitingTokens.length} />
                <MetricCard label="Called" value={calledCount} />
                <MetricCard label="Serving" value={servingTokens.length} />
                <MetricCard label="Vacant active" value={vacantActiveStudios.length} />
              </div>

              {calledToken ? (
                <div className="mt-4 rounded-lg border border-brand-red/20 bg-brand-blush p-3">
                  <p className="text-sm font-semibold text-brand-red">Called customer</p>
                  <div className="mt-1 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                      <p className="text-3xl font-bold text-ink">{calledToken.token_number}</p>
                      <p className="text-sm text-charcoal">{calledToken.item_count || 0} items · {calledToken.phone_number}</p>
                    </div>
                    <p className="text-sm text-muted">Start this token from any vacant active studio.</p>
                  </div>
                </div>
              ) : null}
              {!calledToken && nextWaitingToken ? (
                <div className="mt-4 rounded-lg border border-line bg-slate-50 p-3">
                  <p className="text-sm font-semibold text-charcoal">Next waiting customer</p>
                  <div className="mt-1 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                      <p className="text-3xl font-bold text-ink">{nextWaitingToken.token_number}</p>
                      <p className="text-sm text-charcoal">{nextWaitingToken.item_count || 0} items · {nextWaitingToken.phone_number}</p>
                    </div>
                    <div className="flex flex-col gap-2 sm:items-end">
                      <p className="text-sm text-muted">Start directly from any vacant active studio.</p>
                      <button
                        type="button"
                        onClick={callNextToken}
                        disabled={!canCallNext}
                        className="inline-flex items-center justify-center gap-2 rounded-lg border border-brand-red px-3 py-2 text-sm font-semibold text-brand-red disabled:opacity-60"
                      >
                        <RefreshCcw size={16} />
                        Call customer
                      </button>
                    </div>
                  </div>
                </div>
              ) : null}
            </section>

            <section className="mt-5 rounded-lg bg-white p-4 text-ink glass-panel">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold">Studios</h2>
                <span className="text-sm text-muted">{activeStudios.length} active</span>
              </div>

              <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {studios.length === 0 ? <p className="text-sm text-muted">No studios configured for this zone.</p> : null}
                {studios.map((studio) => {
                  const servingToken = servingTokenByStudioId.get(String(studio.studio_id)) || null;
                  const isVacantActive = studio.is_active && !servingToken;
                  const assignableToken = calledToken || nextWaitingToken;
                  const canStartHere = Boolean(assignableToken && isVacantActive && accessToken && !loading);

                  return (
                    <article key={studio.studio_id} className="rounded-lg border border-line bg-white p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <h3 className="font-semibold">{studio.studio_name || `Studio #${studio.studio_id}`}</h3>
                          <p className="mt-1 text-xs text-muted">
                            {servingToken ? `Projected clear ${formatTime(studio.next_available_time)}` : isVacantActive ? 'Available now' : 'Inactive'}
                          </p>
                        </div>
                        <span className={`shrink-0 rounded-full px-2 py-1 text-xs ${studio.is_active ? 'bg-emerald-50 text-success' : 'bg-rose-50 text-rose-700'}`}>
                          {studio.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>

                      <div className="mt-4 min-h-28 rounded-lg border border-line bg-slate-50 p-3">
                        {servingToken ? (
                          <>
                            <p className="text-xs font-semibold uppercase tracking-wide text-muted">Serving</p>
                            <p className="mt-1 text-3xl font-bold text-ink">{servingToken.token_number}</p>
                            <p className="mt-1 text-sm text-charcoal">{servingToken.item_count || 0} items · {servingToken.phone_number}</p>
                          </>
                        ) : (
                          <>
                            {isVacantActive && assignableToken ? (
                              <>
                                <p className="text-xs font-semibold uppercase tracking-wide text-muted">{calledToken ? 'Called customer' : 'Next waiting customer'}</p>
                                <p className="mt-1 text-3xl font-bold text-ink">{assignableToken.token_number}</p>
                                <p className="mt-1 text-sm text-charcoal">{assignableToken.item_count || 0} items · {assignableToken.phone_number}</p>
                              </>
                            ) : (
                              <>
                                <p className="text-xs font-semibold uppercase tracking-wide text-muted">Vacant</p>
                                <p className="mt-2 text-sm text-charcoal">{studio.is_active ? 'Ready for the next customer.' : 'Studio is not accepting customers.'}</p>
                              </>
                            )}
                          </>
                        )}
                      </div>

                      <div className="mt-4 grid grid-cols-2 gap-2">
                        {servingToken ? (
                          <>
                            <button
                              type="button"
                              onClick={() => runAction(() => completeTrialToken(servingToken.token_id))}
                              disabled={loading}
                              className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-red px-3 py-2 text-sm font-semibold text-white disabled:opacity-60"
                            >
                              <CheckCircle2 size={18} />
                              Complete
                            </button>
                            <button
                              type="button"
                              onClick={() => runAction(() => cancelTrialToken(servingToken.token_id, 'Cancelled from zone studio board'))}
                              disabled={loading}
                              className="inline-flex items-center justify-center gap-2 rounded-lg bg-rose-600 px-3 py-2 text-sm font-semibold text-white disabled:opacity-60"
                            >
                              <XCircle size={18} />
                              Cancel
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              type="button"
                              onClick={() => (calledToken ? startCalledToken(studio.studio_id) : startNextWaitingToken(studio.studio_id))}
                              disabled={!canStartHere}
                              className="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-3 py-2 text-sm font-semibold text-white disabled:opacity-60"
                            >
                              <CirclePlay size={18} />
                              {calledToken ? 'Start here' : 'Assign next'}
                            </button>
                            <button
                              type="button"
                              onClick={() => runAction(() => updateTrialStudioStatus(Number(studio.studio_id), { is_active: !studio.is_active }))}
                              disabled={!accessToken || loading}
                              className="inline-flex items-center justify-center gap-2 rounded-lg border border-line px-3 py-2 text-sm font-semibold text-charcoal disabled:opacity-60"
                            >
                              {studio.is_active ? <CirclePause size={18} /> : <CirclePlay size={18} />}
                              {studio.is_active ? 'Deactivate' : 'Activate'}
                            </button>
                          </>
                        )}
                      </div>
                    </article>
                  );
                })}
              </div>
            </section>

            <section className="mt-5 flex-1 rounded-lg bg-white p-4 text-ink glass-panel">
              <h2 className="font-semibold">Waiting queue</h2>
              <div className="mt-3 space-y-3">
                {waitingTokens.length === 0 ? <p className="text-sm text-muted">No waiting tokens for this zone.</p> : null}
                {waitingTokens.map((token) => {
                  const isNextCallableToken = String(token.token_id) === String(nextWaitingToken?.token_id);

                  return (
                    <div key={token.token_id} className="flex items-center justify-between gap-3 rounded-lg border border-line p-3">
                      <div>
                        <p className="font-semibold">{token.token_number}</p>
                        <p className="text-sm text-charcoal">{token.item_count || 0} items · {token.estimated_wait_minutes}m wait</p>
                        <p className="text-xs text-muted">Call {formatTime(token.calling_time)}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={callNextToken}
                          disabled={!canCallNext || !isNextCallableToken}
                          className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-red px-3 py-2 text-sm font-semibold text-white disabled:opacity-60"
                          title="Call token"
                        >
                          <Megaphone size={18} />
                          Call
                        </button>
                        <button
                          type="button"
                          onClick={() => runAction(() => cancelTrialToken(token.token_id, 'Cancelled from waiting queue'))}
                          disabled={loading}
                          className="rounded-lg border border-rose-200 p-2 text-rose-700 disabled:opacity-60"
                          title="Cancel token"
                        >
                          <XCircle size={18} />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          </>
        ) : null}
      </section>
    </main>
  );
}

function MetricCard({ label, value }) {
  return (
    <div className="rounded-lg border border-line bg-slate-50 p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted">{label}</p>
      <p className="mt-1 text-2xl font-bold text-ink">{value}</p>
    </div>
  );
}
