import { useCallback, useEffect, useMemo, useState } from 'react';

import { cancelTrialToken, completeTrialToken, getTrialStudioQueue, startTrialToken, updateTrialStudioStatus } from '../../../api/trial/queueApi.js';
import { getErrorMessage, showApiErrorToast } from '../../../api/httpClient.js';
import { useAuthStore } from '../../../store/authStore.js';
import { Studio } from './pages/Studio.jsx';
import { STUDIO_QUEUE_REFRESH_MS } from './utils/staffUtils.js';

export function TrialStaff() {
  const { clearSession, user, accessToken } = useAuthStore();
  const assignedStudioId = user?.assigned_studio_id ? String(user.assigned_studio_id) : '';
  const [studioId, setStudioId] = useState(assignedStudioId || localStorage.getItem('trial_studio_id') || '');
  const [studioQueue, setStudioQueue] = useState(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const tokens = useMemo(() => studioQueue?.tokens || [], [studioQueue]);
  const waitingTokens = useMemo(() => tokens.filter((token) => token.status === 'WAITING'), [tokens]);
  const currentToken = useMemo(() => tokens.find((token) => token.status === 'SERVING' || token.status === 'CALLED'), [tokens]);
  const studioActive = studioQueue?.is_active ?? true;

  const loadStudioQueue = useCallback(async () => {
    if (!accessToken || !studioId) return;
    setLoading(true);
    setMessage('');
    try {
      localStorage.setItem('trial_studio_id', studioId);
      const response = await getTrialStudioQueue(Number(studioId));
      setStudioQueue(response);
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [accessToken, studioId]);

  useEffect(() => {
    loadStudioQueue();
    const intervalId = window.setInterval(loadStudioQueue, STUDIO_QUEUE_REFRESH_MS);
    return () => window.clearInterval(intervalId);
  }, [loadStudioQueue]);

  useEffect(() => {
    if (assignedStudioId) {
      setStudioId(assignedStudioId);
      localStorage.setItem('trial_studio_id', assignedStudioId);
    }
  }, [assignedStudioId]);

  async function runAction(action) {
    setLoading(true);
    setMessage('');
    try {
      await action();
      await loadStudioQueue();
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
    runAction(() => startTrialToken(next.token_id));
  }

  return (
    <Studio
      studioId={studioId}
      setStudioId={setStudioId}
      clearSession={clearSession}
      studioActive={studioActive}
      loading={loading}
      runAction={runAction}
      updateTrialStudioStatus={updateTrialStudioStatus}
      accessToken={accessToken}
      message={message}
      currentToken={currentToken}
      completeTrialToken={completeTrialToken}
      cancelTrialToken={cancelTrialToken}
      waitingTokens={waitingTokens}
      startNextToken={startNextToken}
      loadStudioQueue={loadStudioQueue}
      startTrialToken={startTrialToken}
    />
  );
}
