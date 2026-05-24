import { useEffect, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';

import { getErrorMessage, showApiErrorToast } from '../../../api/httpClient.js';
import { listTrialQueueTokens } from '../../../api/trial/queueApi.js';
import { listTrialStudios } from '../../../api/trial/studiosApi.js';
import { listStores } from '../../../api/trial/storeApi.js';
import { listTrialZones } from '../../../api/trial/zonesApi.js';
import { StatCard } from '../../common/FormAndStatePrimitives.jsx';
import { SectionHeader } from '../../common/SectionHeader.jsx';
import { Calendar } from './pages/Calendar.jsx';
import { Config } from './pages/Config.jsx';
import { Dashboard } from './pages/Dashboard.jsx';
import { MachineLearning } from './pages/MachineLearning.jsx';
import { Queue } from './pages/Queue.jsx';
import { Staff } from './pages/Staff.jsx';
import { Stores } from './pages/Stores.jsx';
import { Studios } from './pages/Studios.jsx';
import { Zones } from './pages/Zones.jsx';

function useTrialAdminData() {
  const [stores, setStores] = useState([]);
  const [zones, setZones] = useState([]);
  const [studios, setStudios] = useState([]);
  const [tokens, setTokens] = useState([]);
  const [message, setMessage] = useState('');

  async function loadAll() {
    try {
      const [storeRows, zoneRows, studioRows, tokenRows] = await Promise.all([
        listStores({ include_inactive: true }),
        listTrialZones({ include_inactive: true }),
        listTrialStudios({ include_inactive: true }),
        listTrialQueueTokens({ include_terminal: true }),
      ]);
      setStores(storeRows);
      setZones(zoneRows);
      setStudios(studioRows);
      setTokens(tokenRows);
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  return { stores, zones, studios, tokens, message };
}

export function TrialAdmin() {
  const data = useTrialAdminData();
  return (
    <Routes>
      <Route index element={<Dashboard />} />
      <Route path="overview" element={<TrialOverview {...data} />} />
      <Route path="stores" element={<Stores />} />
      <Route path="zones" element={<Zones />} />
      <Route path="studios" element={<Studios />} />
      <Route path="staff" element={<Staff />} />
      <Route path="config" element={<Config />} />
      <Route path="calendar" element={<Calendar />} />
      <Route path="ml" element={<MachineLearning />} />
      <Route path="queue" element={<Queue />} />
      <Route path="*" element={<Navigate to="/app/trial/admin" replace />} />
    </Routes>
  );
}

function TrialOverview({ zones, studios, tokens, message }) {
  return (
    <div className="space-y-5">
      <SectionHeader eyebrow="Trial Queue" title="Overview" />
      {message ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{message}</p> : null}
      <div className="grid gap-3 md:grid-cols-3">
        <StatCard label="Trial zones" value={zones.length} />
        <StatCard label="Studios" value={studios.length} />
        <StatCard label="Trial tokens" value={tokens.length} />
      </div>
    </div>
  );
}
