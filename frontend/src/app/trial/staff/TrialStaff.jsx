import { useCallback, useEffect, useMemo, useState } from 'react';

import { callNextTrialTokenForZone, cancelTrialToken, completeTrialToken, getTrialZoneStudios, startTrialToken, updateTrialStudioStatus } from '../../../api/trial/queueApi.js';
import { listTrialZones } from '../../../api/trial/zonesApi.js';
import { getErrorMessage, showApiErrorToast } from '../../../api/httpClient.js';
import { useAuthStore } from '../../../store/authStore.js';
import { getTrialQueueKey, isCallable } from '../../common/queueCallUtils.js';
import { Studio } from './pages/Studio.jsx';
import { STUDIO_QUEUE_REFRESH_MS } from './utils/staffUtils.js';

export function TrialStaff() {
  const { clearSession, user, accessToken } = useAuthStore();
  const assignedZoneId = user?.assigned_zone_id ? String(user.assigned_zone_id) : '';
  const isManager = user?.default_role === 'MANAGER';
  const [zones, setZones] = useState([]);
  const [zoneId, setZoneId] = useState(assignedZoneId || localStorage.getItem('trial_zone_id') || '');
  const [zoneQueue, setZoneQueue] = useState(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const studios = useMemo(() => zoneQueue?.studios || [], [zoneQueue]);
  const tokens = useMemo(() => zoneQueue?.tokens || [], [zoneQueue]);
  const waitingTokens = useMemo(() => tokens.filter((token) => token.status === 'WAITING'), [tokens]);
  const nextWaitingToken = useMemo(() => waitingTokens.find((token) => isCallable(token, tokens, getTrialQueueKey)) || null, [tokens, waitingTokens]);
  const calledToken = useMemo(() => tokens.find((token) => token.status === 'CALLED') || null, [tokens]);
  const servingTokens = useMemo(() => tokens.filter((token) => token.status === 'SERVING'), [tokens]);
  const activeStudios = useMemo(() => studios.filter((studio) => studio.is_active), [studios]);
  const vacantActiveStudios = useMemo(
    () => activeStudios.filter((studio) => !servingTokens.some((token) => String(token.assigned_studio_id) === String(studio.studio_id))),
    [activeStudios, servingTokens]
  );

  const loadZones = useCallback(async () => {
    if (!accessToken || !isManager) return;
    try {
      setZones(await listTrialZones(user?.store_id ? { store_id: user.store_id } : {}));
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    }
  }, [accessToken, isManager, user?.store_id]);

  const loadZoneQueue = useCallback(async ({ skipGlobalLoader = false } = {}) => {
    if (!accessToken || !zoneId) return;
    setLoading(true);
    setMessage('');
    try {
      localStorage.setItem('trial_zone_id', zoneId);
      setZoneQueue(await getTrialZoneStudios(Number(zoneId), { skipGlobalLoader }));
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [accessToken, zoneId]);

  useEffect(() => {
    loadZones();
  }, [loadZones]);

  useEffect(() => {
    if (assignedZoneId) {
      setZoneId(assignedZoneId);
      setZoneQueue(null);
      localStorage.setItem('trial_zone_id', assignedZoneId);
    }
  }, [assignedZoneId]);

  useEffect(() => {
    if (!isManager || !zones.length) return;
    if (zones.some((zone) => String(zone.id) === zoneId)) return;

    const nextZoneId = String(zones[0].id);
    setZoneId(nextZoneId);
    setZoneQueue(null);
    localStorage.setItem('trial_zone_id', nextZoneId);
  }, [isManager, zoneId, zones]);

  useEffect(() => {
    loadZoneQueue();
    const intervalId = window.setInterval(() => loadZoneQueue({ skipGlobalLoader: true }), STUDIO_QUEUE_REFRESH_MS);
    return () => window.clearInterval(intervalId);
  }, [loadZoneQueue]);

  function selectZone(nextZoneId) {
    setZoneId(nextZoneId);
    setZoneQueue(null);
    localStorage.setItem('trial_zone_id', nextZoneId);
  }

  async function runAction(action) {
    setLoading(true);
    setMessage('');
    try {
      await action();
      await loadZoneQueue();
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  function startCalledToken(studioId) {
    if (!calledToken || !studioId) return;
    runAction(() => startTrialToken(calledToken.token_id, studioId));
  }

  function startNextWaitingToken(studioId) {
    if (!nextWaitingToken || !studioId) return;
    runAction(() => startTrialToken(nextWaitingToken.token_id, studioId));
  }

  function callNextToken() {
    if (!zoneId || calledToken || !nextWaitingToken || vacantActiveStudios.length === 0) return;
    runAction(() => callNextTrialTokenForZone(Number(zoneId)));
  }

  return (
    <Studio
      zoneId={zoneId}
      zoneName={zoneQueue?.zone_name || ''}
      zones={zones}
      setZoneId={selectZone}
      canSelectZone={isManager && !assignedZoneId}
      studios={studios}
      clearSession={clearSession}
      loading={loading}
      runAction={runAction}
      updateTrialStudioStatus={updateTrialStudioStatus}
      accessToken={accessToken}
      message={message}
      calledToken={calledToken}
      servingTokens={servingTokens}
      activeStudios={activeStudios}
      vacantActiveStudios={vacantActiveStudios}
      completeTrialToken={completeTrialToken}
      cancelTrialToken={cancelTrialToken}
      waitingTokens={waitingTokens}
      nextWaitingToken={nextWaitingToken}
      loadZoneQueue={loadZoneQueue}
      startCalledToken={startCalledToken}
      startNextWaitingToken={startNextWaitingToken}
      callNextToken={callNextToken}
    />
  );
}
