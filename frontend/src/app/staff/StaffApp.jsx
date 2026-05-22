import { useCallback, useEffect, useMemo, useState } from 'react';

import { getErrorMessage, showApiErrorToast } from '../../api/httpClient.js';
import {
  cancelToken,
  completeToken,
  getCounterQueue,
  startToken,
  updateCounterStatus,
} from '../../api/queueApi.js';
import { useAuthStore } from '../../store/authStore.js';
import { useQueueStore } from '../../store/queueStore.js';
import { Counter } from './pages/Counter.jsx';

const COUNTER_QUEUE_REFRESH_MS = 30000;

export function StaffApp() {
  const { activeCounterId, setActiveCounterId } = useQueueStore();
  const { accessToken, clearSession } = useAuthStore();
  const [counterQueue, setCounterQueue] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const tokens = useMemo(() => counterQueue?.tokens || [], [counterQueue]);
  const currentToken = tokens.find((token) => token.status === 'SERVING' || token.status === 'CALLED');
  const waitingTokens = useMemo(() => tokens.filter((token) => token.status === 'WAITING'), [tokens]);
  const counterActive = counterQueue?.is_active ?? true;

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

  function startNextToken() {
    const next = waitingTokens[0];
    if (!next) return;
    runAction(() => startToken(next.token_id));
  }

  return (
    <Counter
      activeCounterId={activeCounterId}
      setActiveCounterId={setActiveCounterId}
      clearSession={clearSession}
      counterActive={counterActive}
      loading={loading}
      runAction={runAction}
      updateCounterStatus={updateCounterStatus}
      accessToken={accessToken}
      message={message}
      currentToken={currentToken}
      completeToken={completeToken}
      cancelToken={cancelToken}
      waitingTokens={waitingTokens}
      startNextToken={startNextToken}
      loadCounterQueue={loadCounterQueue}
    />
  );
}
