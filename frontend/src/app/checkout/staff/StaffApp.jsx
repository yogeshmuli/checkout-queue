import { useCallback, useEffect, useMemo, useState } from 'react';

import { getErrorMessage, showApiErrorToast } from '../../../api/httpClient.js';
import {
  callNextTokenForCounter,
  callToken,
  cancelToken,
  completeToken,
  getCounterQueue,
  startNextTokenForCounter,
  startToken,
  updateCounterStatus,
} from '../../../api/checkout/queueApi.js';
import { useAuthStore } from '../../../store/authStore.js';
import { useQueueStore } from '../../../store/queueStore.js';
import { ConfirmationModal } from '../../common/ConfirmationModal.jsx';
import { Counter } from './pages/Counter.jsx';

const COUNTER_QUEUE_REFRESH_MS = 30000;

export function StaffApp() {
  const { activeCounterId, setActiveCounterId } = useQueueStore();
  const { accessToken, clearSession, user } = useAuthStore();
  const [counterQueue, setCounterQueue] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [tokenToCancel, setTokenToCancel] = useState(null);
  const assignedCounterId = user?.assigned_counter_id ? String(user.assigned_counter_id) : '';

  const tokens = useMemo(() => counterQueue?.tokens || [], [counterQueue]);
  const waitingTokens = useMemo(() => tokens.filter((token) => token.status === 'WAITING'), [tokens]);
  const calledTokens = useMemo(
    () => tokens.filter((token) => token.status === 'CALLED').sort((first, second) => {
      const timeDelta = new Date(first.called_at || first.calling_time || 0).getTime() - new Date(second.called_at || second.calling_time || 0).getTime();
      return timeDelta || Number(first.token_id) - Number(second.token_id);
    }),
    [tokens]
  );
  const servingToken = tokens.find((token) => token.status === 'SERVING') || null;
  const currentToken = servingToken || calledTokens[0] || null;
  const queuedTokens = useMemo(() => [...calledTokens, ...waitingTokens], [calledTokens, waitingTokens]);
  const counterActive = counterQueue?.is_active ?? true;
  const availableCallSlots = Math.max(0, (counterActive ? 1 : 0) - calledTokens.length);
  const callableWaitingTokenIds = useMemo(
    () => new Set(waitingTokens.slice(0, availableCallSlots).map((token) => String(token.token_id))),
    [availableCallSlots, waitingTokens]
  );
  const counterName = counterQueue?.counter_name || '';

  const loadCounterQueue = useCallback(async ({ skipGlobalLoader = false } = {}) => {
    if (!accessToken || !activeCounterId) return;
    setLoading(true);
    setMessage('');
    try {
      setCounterQueue(await getCounterQueue(activeCounterId, { skipGlobalLoader }));
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [accessToken, activeCounterId]);

  useEffect(() => {
    loadCounterQueue();
    const intervalId = window.setInterval(() => loadCounterQueue({ skipGlobalLoader: true }), COUNTER_QUEUE_REFRESH_MS);
    return () => window.clearInterval(intervalId);
  }, [loadCounterQueue]);

  useEffect(() => {
    if (assignedCounterId) {
      setActiveCounterId(assignedCounterId);
    }
  }, [assignedCounterId, setActiveCounterId]);

  async function runAction(action) {
    setLoading(true);
    setMessage('');
    try {
      await action();
      await loadCounterQueue();
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  function callNextToken() {
    if (!activeCounterId) return;
    runAction(() => callNextTokenForCounter(activeCounterId));
  }

  function startNextToken() {
    if (!activeCounterId) return;
    runAction(() => startNextTokenForCounter(activeCounterId));
  }

  function callWaitingToken(token) {
    if (!token || !callableWaitingTokenIds.has(String(token.token_id))) return;
    runAction(() => callToken(token.token_id));
  }

  function requestCancelToken(token) {
    setTokenToCancel(token);
  }

  function closeCancelModal() {
    if (loading) return;
    setTokenToCancel(null);
  }

  async function confirmCancelToken() {
    if (!tokenToCancel) return;
    const tokenId = tokenToCancel.token_id;
    setTokenToCancel(null);
    await runAction(() => cancelToken(tokenId));
  }

  return (
    <>
    <Counter
      activeCounterId={activeCounterId}
      counterName={counterName}
      clearSession={clearSession}
      counterActive={counterActive}
      loading={loading}
      runAction={runAction}
      updateCounterStatus={updateCounterStatus}
      accessToken={accessToken}
      message={message}
      currentToken={currentToken}
      startToken={startToken}
      completeToken={completeToken}
      requestCancelToken={requestCancelToken}
      waitingTokens={waitingTokens}
      queuedTokens={queuedTokens}
      callableWaitingTokenIds={callableWaitingTokenIds}
      callNextToken={callNextToken}
      startNextToken={startNextToken}
      callWaitingToken={callWaitingToken}
      loadCounterQueue={loadCounterQueue}
    />
    <ConfirmationModal
      isOpen={Boolean(tokenToCancel)}
      title="Cancel token?"
      message={`This will cancel token ${tokenToCancel?.token_number || ''}. The customer will no longer keep this queue position.`}
      confirmLabel="Cancel token"
      cancelLabel="Keep token"
      variant="danger"
      loading={loading}
      onConfirm={confirmCancelToken}
      onCancel={closeCancelModal}
    />
    </>
  );
}
