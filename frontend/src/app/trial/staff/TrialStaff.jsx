import { useCallback, useEffect, useMemo, useState } from 'react';

import { cancelTrialToken, completeTrialToken, listTrialQueueTokens, startTrialToken } from '../../../api/trial/queueApi.js';
import { getErrorMessage, showApiErrorToast } from '../../../api/httpClient.js';
import { Field } from '../../common/FormAndStatePrimitives.jsx';
import { SectionHeader } from '../../common/SectionHeader.jsx';
import { useAuthStore } from '../../../store/authStore.js';

export function TrialStaff() {
  const { clearSession } = useAuthStore();
  const [studioId, setStudioId] = useState(localStorage.getItem('trial_studio_id') || '');
  const [tokens, setTokens] = useState([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const waitingTokens = useMemo(() => tokens.filter((token) => token.status === 'WAITING'), [tokens]);
  const currentToken = useMemo(() => tokens.find((token) => token.status === 'SERVING' || token.status === 'CALLED'), [tokens]);

  const loadTokens = useCallback(async () => {
    if (!studioId) return;
    setLoading(true);
    try {
      localStorage.setItem('trial_studio_id', studioId);
      setTokens(await listTrialQueueTokens({ studio_id: Number(studioId) }));
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [studioId]);

  useEffect(() => {
    loadTokens();
  }, [loadTokens]);

  async function run(action) {
    setLoading(true);
    setMessage('');
    try {
      await action();
      await loadTokens();
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-brand-blush px-4 py-6 text-ink">
      <section className="mx-auto max-w-3xl space-y-5">
        <div className="flex items-center justify-between gap-3">
          <SectionHeader eyebrow="Trial Queue" title="Studio console" />
          <button type="button" onClick={clearSession} className="rounded-lg border border-line bg-white px-3 py-2 text-sm">Logout</button>
        </div>
        <div className="rounded-lg bg-white p-4 shadow-soft">
          <Field label="Studio ID" value={studioId} onChange={setStudioId} />
          <button type="button" onClick={loadTokens} disabled={!studioId || loading} className="mt-3 rounded-lg bg-brand-red px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">
            Load queue
          </button>
        </div>
        {message ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{message}</p> : null}
        <div className="rounded-lg bg-white p-4 shadow-soft">
          <h2 className="font-semibold">Current trial token</h2>
          {currentToken ? (
            <div className="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-line p-3">
              <span>{currentToken.token_number} | {currentToken.status}</span>
              <div className="flex gap-2">
                <button onClick={() => run(() => completeTrialToken(currentToken.token_id))} className="rounded-lg bg-success px-3 py-2 text-sm font-semibold text-white">Complete</button>
                <button onClick={() => run(() => cancelTrialToken(currentToken.token_id, 'Cancelled from studio'))} className="rounded-lg border border-line px-3 py-2 text-sm">Cancel</button>
              </div>
            </div>
          ) : <p className="mt-2 text-sm text-muted">No active token.</p>}
        </div>
        <div className="rounded-lg bg-white p-4 shadow-soft">
          <h2 className="font-semibold">Waiting tokens</h2>
          {waitingTokens.length ? waitingTokens.map((token) => (
            <div key={token.token_id} className="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-line p-3">
              <span>{token.token_number} | Wait {token.estimated_wait_minutes}m</span>
              <button onClick={() => run(() => startTrialToken(token.token_id))} className="rounded-lg bg-brand-red px-3 py-2 text-sm font-semibold text-white">Start</button>
            </div>
          )) : <p className="mt-2 text-sm text-muted">No waiting tokens.</p>}
        </div>
      </section>
    </main>
  );
}
