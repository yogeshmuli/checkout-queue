import { useCallback, useEffect, useMemo, useState } from 'react';

import { cancelTrialToken, completeTrialToken, getTrialZoneStudios, startTrialToken, updateTrialStudioStatus } from '../../../api/trial/queueApi.js';
import { listTrialZones } from '../../../api/trial/zonesApi.js';
import { getErrorMessage, showApiErrorToast } from '../../../api/httpClient.js';
import { useAuthStore } from '../../../store/authStore.js';
import { Studio } from './pages/Studio.jsx';
import { STUDIO_QUEUE_REFRESH_MS } from './utils/staffUtils.js';

export function TrialStaff() {
  
  const { clearSession, user, accessToken } = useAuthStore();
  const assignedZoneId = user?.assigned_zone_id ? String(user.assigned_zone_id) : '';
  const isManager = user?.default_role === 'MANAGER';
  const [zones, setZones] = useState([]);
  const [zoneId, setZoneId] = useState(assignedZoneId || localStorage.getItem('trial_zone_id') || '');
  const [zoneQueue, setZoneQueue] = useState(null);
  const [selectedStudioId, setSelectedStudioId] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const studios = useMemo(() => zoneQueue?.studios || [], [zoneQueue]);
  const selectedStudio = useMemo(
    () => studios.find((studio) => String(studio.studio_id) === String(selectedStudioId)) || null,
    [selectedStudioId, studios]
  );
  const tokens = useMemo(() => selectedStudio?.tokens || [], [selectedStudio]);
  const waitingTokens = useMemo(() => tokens.filter((token) => token.status === 'WAITING'), [tokens]);
  const currentToken = useMemo(() => tokens.find((token) => token.status === 'SERVING' || token.status === 'CALLED'), [tokens]);

  const loadZones = useCallback(async () => {
    if (!accessToken || !isManager) return;
    try {
      setZones(await listTrialZones(user?.store_id ? { store_id: user.store_id } : {}));
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    }
  }, [accessToken, isManager, user?.store_id]);

  const loadZoneQueue = useCallback(async () => {
    if (!accessToken || !zoneId) return;
    setLoading(true);
    setMessage('');
    try {
      localStorage.setItem('trial_zone_id', zoneId);
      setZoneQueue(await getTrialZoneStudios(Number(zoneId)));
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
      setSelectedStudioId('');
      localStorage.setItem('trial_zone_id', assignedZoneId);
    }
  }, [assignedZoneId]);

  useEffect(() => {
    if (!isManager || !zones.length) return;
    if (zones.some((zone) => String(zone.id) === zoneId)) return;

    const nextZoneId = String(zones[0].id);
    setZoneId(nextZoneId);
    setZoneQueue(null);
    setSelectedStudioId('');
    localStorage.setItem('trial_zone_id', nextZoneId);
  }, [isManager, zoneId, zones]);

  useEffect(() => {
    loadZoneQueue();
    const intervalId = window.setInterval(loadZoneQueue, STUDIO_QUEUE_REFRESH_MS);
    return () => window.clearInterval(intervalId);
  }, [loadZoneQueue]);

  useEffect(() => {
    if (!studios.length || !zoneId) {
      setSelectedStudioId('');
      return;
    }
    if (studios.some((studio) => String(studio.studio_id) === String(selectedStudioId))) return;
    const rememberedStudioId = localStorage.getItem(`trial_zone_${zoneId}_studio_id`);
    const rememberedStudio = studios.find((studio) => String(studio.studio_id) === String(rememberedStudioId));
    const nextStudio = rememberedStudio || studios.find((studio) => studio.is_active) || studios[0];
    setSelectedStudioId(String(nextStudio.studio_id));
  }, [selectedStudioId, studios, zoneId]);

  function selectStudio(studioId) {
    const nextStudioId = String(studioId);
    setSelectedStudioId(nextStudioId);
    if (zoneId) localStorage.setItem(`trial_zone_${zoneId}_studio_id`, nextStudioId);
  }

  function selectZone(nextZoneId) {
    setZoneId(nextZoneId);
    setZoneQueue(null);
    setSelectedStudioId('');
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

  function startNextToken() {
    const next = waitingTokens[0];
    if (!next) return;
    runAction(() => startTrialToken(next.token_id));
  }

  return (
    <Studio
      zoneId={zoneId}
      zoneName={zoneQueue?.zone_name || ''}
      zones={zones}
      setZoneId={selectZone}
      canSelectZone={isManager && !assignedZoneId}
      studios={studios}
      selectedStudio={selectedStudio}
      selectStudio={selectStudio}
      clearSession={clearSession}
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
      loadZoneQueue={loadZoneQueue}
      startTrialToken={startTrialToken}
    />
  );
}
