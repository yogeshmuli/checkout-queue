import { Activity, BarChart3, BrainCircuit, CalendarDays, Clock, RefreshCw } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

import { getErrorMessage, showApiErrorToast } from '../../../../api/httpClient.js';
import { listTrialQueueTokens } from '../../../../api/trial/queueApi.js';
import { listStores } from '../../../../api/trial/storeApi.js';
import { listTrialStudios } from '../../../../api/trial/studiosApi.js';
import { listTrialZones } from '../../../../api/trial/zonesApi.js';
import { Select } from '../../../common/FormAndStatePrimitives.jsx';
import { MetricTile } from '../../../common/MetricTile.jsx';
import { SectionHeader } from '../../../common/SectionHeader.jsx';

const VIEW_OPTIONS = [
  { label: 'Live', value: 'live' },
  { label: 'History', value: 'history' },
  { label: 'Foresights', value: 'foresights' },
];

function formatTime(value) {
  return new Intl.DateTimeFormat('en-IN', { hour: '2-digit', minute: '2-digit' }).format(value);
}

function getStatusCount(tokens, status) {
  return tokens.filter((token) => token.status === status).length;
}

export function Dashboard() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [stores, setStores] = useState([]);
  const [zones, setZones] = useState([]);
  const [studios, setStudios] = useState([]);
  const [tokens, setTokens] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [lastRefreshed, setLastRefreshed] = useState(null);

  const filters = {
    store_id: searchParams.get('store_id') || '',
    view: searchParams.get('view') || 'live',
  };

  const selectedStoreId = filters.store_id || (stores[0] ? String(stores[0].id) : '');
  const selectedStore = stores.find((store) => String(store.id) === String(selectedStoreId));
  const activeView = VIEW_OPTIONS.some((option) => option.value === filters.view) ? filters.view : 'live';

  const storeOptions = stores.map((store) => ({
    label: `${store.name} (${store.store_number})`,
    value: String(store.id),
  }));

  const zoneById = useMemo(() => {
    const map = new Map();
    for (const zone of zones) {
      map.set(String(zone.id), zone);
    }
    return map;
  }, [zones]);

  const studioById = useMemo(() => {
    const map = new Map();
    for (const studio of studios) {
      map.set(String(studio.id), studio);
    }
    return map;
  }, [studios]);

  const zoneRows = useMemo(() => {
    const counts = new Map();

    for (const token of tokens) {
      if (!token.trial_zone_id) continue;
      const key = String(token.trial_zone_id);
      const current = counts.get(key) || { waiting: 0, serving: 0, completed: 0, total: 0 };
      current.total += 1;
      if (token.status === 'WAITING' || token.status === 'CALLED') current.waiting += 1;
      if (token.status === 'SERVING') current.serving += 1;
      if (token.status === 'COMPLETED') current.completed += 1;
      counts.set(key, current);
    }

    return [...counts.entries()]
      .map(([zoneId, stats]) => ({
        zone: zoneById.get(zoneId),
        zoneId,
        ...stats,
      }))
      .sort((a, b) => b.waiting + b.serving - (a.waiting + a.serving))
      .slice(0, 6);
  }, [tokens, zoneById]);

  const recentTerminalTokens = useMemo(() => {
    return [...tokens]
      .filter((token) => ['COMPLETED', 'CANCELLED', 'NO_SHOW'].includes(token.status))
      .sort((first, second) => second.token_id - first.token_id)
      .slice(0, 8);
  }, [tokens]);

  function setFilter(field, value) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) next.set(field, String(value));
      else next.delete(field);
      return next;
    });
  }

  const loadDashboard = useCallback(async () => {
    if (!selectedStoreId) return;

    setLoading(true);
    setMessage('');
    try {
      const [zoneRows, studioRows, tokenRows] = await Promise.all([
        listTrialZones({ include_inactive: true, store_id: Number(selectedStoreId) }),
        listTrialStudios({ include_inactive: true, store_id: Number(selectedStoreId) }),
        listTrialQueueTokens({ include_terminal: true, store_id: Number(selectedStoreId) }),
      ]);
      setZones(zoneRows);
      setStudios(studioRows);
      setTokens(tokenRows);
      setLastRefreshed(new Date());
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [selectedStoreId]);

  useEffect(() => {
    listStores({ include_inactive: true })
      .then(setStores)
      .catch((error) => {
        showApiErrorToast(error);
        setMessage(getErrorMessage(error));
      });
  }, []);

  useEffect(() => {
    if (!filters.store_id && stores[0]) {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.set('store_id', String(stores[0].id));
        return next;
      });
    }
  }, [filters.store_id, setSearchParams, stores]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  useEffect(() => {
    if (!selectedStoreId) return undefined;
    const timer = window.setInterval(loadDashboard, 60000);
    return () => window.clearInterval(timer);
  }, [loadDashboard, selectedStoreId]);

  const activeZones = zones.filter((zone) => zone.is_active).length;
  const activeStudios = studios.filter((studio) => studio.is_active).length;
  const waitingCount = getStatusCount(tokens, 'WAITING') + getStatusCount(tokens, 'CALLED');
  const servingCount = getStatusCount(tokens, 'SERVING');
  const completedCount = getStatusCount(tokens, 'COMPLETED');
  const cancelledCount = getStatusCount(tokens, 'CANCELLED') + getStatusCount(tokens, 'NO_SHOW');

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Trial Dashboard"
        title={selectedStore ? `${selectedStore.name} smart view` : 'Smart view'}
        action={
          <button
            type="button"
            onClick={loadDashboard}
            disabled={loading || !selectedStoreId}
            className="inline-flex items-center gap-2 rounded-lg border border-line bg-white px-3 py-2 text-sm font-medium text-charcoal disabled:opacity-60"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        }
      />

      <section className="rounded-lg border border-line bg-white p-5">
        <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)]">
          <Select label="Store" value={selectedStoreId} onChange={(value) => setFilter('store_id', value)} options={storeOptions} />
        </div>
        <div className="mt-4 grid gap-3 text-sm text-charcoal sm:grid-cols-3">
          <HeaderFact icon={<Activity size={15} />} label="Store ID" value={selectedStore?.store_number || '-'} />
          <HeaderFact icon={<CalendarDays size={15} />} label="Date" value={new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date())} />
          <HeaderFact icon={<Clock size={15} />} label="Last refreshed" value={lastRefreshed ? formatTime(lastRefreshed) : '-'} />
        </div>
        {message ? <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{message}</p> : null}
      </section>

      <div className="grid grid-cols-3 gap-2 rounded-lg border border-line bg-white p-1">
        {VIEW_OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => setFilter('view', option.value)}
            className={`rounded-md px-3 py-2 text-sm font-semibold transition-colors ${
              activeView === option.value ? 'bg-brand-red text-white' : 'text-charcoal hover:bg-brand-blush hover:text-brand-red'
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>

      {activeView === 'live' ? (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricTile label="Active zones" value={`${activeZones}/${zones.length || 0}`} tone="mint" />
            <MetricTile label="Active studios" value={`${activeStudios}/${studios.length || 0}`} />
            <MetricTile label="Waiting tokens" value={waitingCount} tone="amber" />
            <MetricTile label="Serving now" value={servingCount} tone="rose" />
          </div>

          <section className="rounded-lg border border-line bg-white p-5">
            <h2 className="text-lg font-semibold">Top active zones</h2>
            <div className="mt-4 space-y-3">
              {zoneRows.length === 0 ? <p className="text-sm text-muted">No zone activity available.</p> : null}
              {zoneRows.map((row) => (
                <div key={row.zoneId} className="rounded-lg border border-line p-3">
                  <div className="flex items-center justify-between">
                    <p className="font-semibold">{row.zone?.name || `Zone #${row.zoneId}`}</p>
                    <p className="text-xs text-muted">{row.zone?.zone_type || '-'}</p>
                  </div>
                  <p className="mt-1 text-sm text-charcoal">
                    Waiting: {row.waiting} | Serving: {row.serving} | Completed: {row.completed}
                  </p>
                </div>
              ))}
            </div>
          </section>
        </div>
      ) : null}

      {activeView === 'history' ? (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricTile label="Completed" value={completedCount} tone="mint" />
            <MetricTile label="Cancelled / no-show" value={cancelledCount} tone="rose" />
            <MetricTile label="Total tokens" value={tokens.length} />
            <MetricTile label="Store zones" value={zones.length} tone="amber" />
          </div>

          <section className="rounded-lg border border-line bg-white p-5">
            <div className="flex items-center gap-2">
              <BarChart3 size={18} className="text-brand-red" />
              <h2 className="text-lg font-semibold">Recent terminal tokens</h2>
            </div>
            <div className="mt-4 space-y-2">
              {recentTerminalTokens.length === 0 ? <p className="text-sm text-muted">No completed/cancelled tokens found.</p> : null}
              {recentTerminalTokens.map((token) => {
                const studio = token.assigned_studio_id ? studioById.get(String(token.assigned_studio_id)) : null;
                return (
                  <div key={token.token_id} className="flex items-center justify-between rounded-lg border border-line px-3 py-2 text-sm">
                    <span>{token.token_number}</span>
                    <span className="text-charcoal">{token.status}</span>
                    <span className="text-muted">{studio?.name || `Studio #${token.assigned_studio_id || '-'}`}</span>
                  </div>
                );
              })}
            </div>
          </section>
        </div>
      ) : null}

      {activeView === 'foresights' ? (
        <section className="rounded-lg border border-line bg-white p-5">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-brand-blush p-3 text-brand-red">
              <BrainCircuit size={22} />
            </div>
            <div>
              <h2 className="text-xl font-semibold">Operational foresights</h2>
              <p className="text-sm text-muted">Rule-based recommendations from current queue pressure.</p>
            </div>
          </div>

          <div className="mt-4 space-y-3 text-sm">
            <InsightCard
              title="Zone balancing"
              body={waitingCount > servingCount * 2 ? 'Queue pressure is elevated. Consider activating more studios in peak zones.' : 'Zone load looks balanced for current demand.'}
            />
            <InsightCard
              title="Cancellation risk"
              body={cancelledCount > Math.max(1, Math.floor(completedCount * 0.25)) ? 'Cancellation ratio is high. Check wait-time communication and staffing.' : 'Cancellation ratio is in acceptable range.'}
            />
            <InsightCard
              title="Action shortcuts"
              body="Use the links below to tune trial setup and staffing quickly."
            />
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <ResourceLink to={`/app/trial/admin/zones?store_id=${selectedStoreId}`} label="Zones" />
            <ResourceLink to={`/app/trial/admin/studios?store_id=${selectedStoreId}`} label="Studios" />
            <ResourceLink to={`/app/trial/admin/staff?store_id=${selectedStoreId}`} label="Staff" />
            <ResourceLink to={`/app/trial/admin/queue?store_id=${selectedStoreId}`} label="Queue" />
            <ResourceLink to={`/app/trial/admin/config?store_id=${selectedStoreId}`} label="Config" />
            <ResourceLink to={`/app/trial/admin/calendar?store_id=${selectedStoreId}`} label="Calendar" />
          </div>
        </section>
      ) : null}
    </div>
  );
}

function HeaderFact({ icon, label, value }) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-line px-3 py-2.5">
      <div className="text-brand-red">{icon}</div>
      <div>
        <p className="text-xs uppercase tracking-wide text-muted">{label}</p>
        <p className="font-semibold">{value}</p>
      </div>
    </div>
  );
}

function InsightCard({ title, body }) {
  return (
    <div className="rounded-lg border border-line bg-slate-50 px-3 py-2.5">
      <p className="font-semibold text-charcoal">{title}</p>
      <p className="mt-1 text-charcoal">{body}</p>
    </div>
  );
}

function ResourceLink({ to, label }) {
  return (
    <Link to={to} className="rounded-lg border border-line px-3 py-1.5 text-xs font-medium text-charcoal hover:border-brand-red hover:text-brand-red">
      {label}
    </Link>
  );
}
