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
import { getCheckoutQueueKey, isCallable } from '../../common/queueCallUtils.js';
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
  const currentToken = tokens.find((token) => token.status === 'SERVING' || token.status === 'CALLED');
  const waitingTokens = useMemo(() => tokens.filter((token) => token.status === 'WAITING'), [tokens]);
  const callableWaitingTokenIds = useMemo(
    () => new Set(waitingTokens.filter((token) => isCallable(token, tokens, getCheckoutQueueKey)).map((token) => String(token.token_id))),
    [tokens, waitingTokens]
  );
  const counterActive = counterQueue?.is_active ?? true;
  const counterName = counterQueue?.counter_name || '';

  const loadCounterQueue = useCallback(async () => {
    if (!accessToken || !activeCounterId) return;
    setLoading(true);
    setMessage('');
    try {
      setCounterQueue(await getCounterQueue(activeCounterId));
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [accessToken, activeCounterId]);

  useEffect(() => {
    loadCounterQueue();
    const intervalId = window.setInterval(loadCounterQueue, COUNTER_QUEUE_REFRESH_MS);
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
    if (!token || !isCallable(token, tokens, getCheckoutQueueKey)) return;
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
