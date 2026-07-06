import { CheckCircle2, Megaphone, Play, RefreshCw, Search, SlidersHorizontal, XCircle } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { getErrorMessage, showApiErrorToast } from '../../../../api/httpClient.js';
import { callTrialToken, cancelTrialToken, completeTrialToken, listTrialQueueTokens, startTrialToken } from '../../../../api/trial/queueApi.js';
import { listStores } from '../../../../api/trial/storeApi.js';
import { listTrialStudios } from '../../../../api/trial/studiosApi.js';
import { listTrialZones } from '../../../../api/trial/zonesApi.js';
import { Select } from '../../../common/FormAndStatePrimitives.jsx';
import { SectionHeader } from '../../../common/SectionHeader.jsx';

const STATUS_OPTIONS = [
  { label: 'Active tokens', value: '' },
  { label: 'Waiting', value: 'WAITING' },
  { label: 'Called', value: 'CALLED' },
  { label: 'Serving', value: 'SERVING' },
  { label: 'Completed', value: 'COMPLETED' },
  { label: 'Cancelled', value: 'CANCELLED' },
  { label: 'No show', value: 'NO_SHOW' },
];

const STATUS_STYLES = {
  WAITING: 'bg-amber-50 text-amber-700',
  CALLED: 'bg-sky-50 text-sky-700',
  SERVING: 'bg-brand-blush text-success',
  COMPLETED: 'bg-emerald-50 text-emerald-700',
  CANCELLED: 'bg-rose-50 text-rose-700',
  NO_SHOW: 'bg-slate-100 text-slate-700',
};

function formatTime(value) {
  if (!value) return 'Not scheduled';
  return new Intl.DateTimeFormat('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    day: '2-digit',
    month: 'short',
  }).format(new Date(value));
}

function formatEnumLabel(value) {
  return String(value || '').replaceAll('_', ' ').toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function Queue() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [tokens, setTokens] = useState([]);
  const [stores, setStores] = useState([]);
  const [zones, setZones] = useState([]);
  const [studios, setStudios] = useState([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const filters = {
    store_id: searchParams.get('store_id') || '',
    trial_zone_id: searchParams.get('trial_zone_id') || '',
    studio_id: searchParams.get('studio_id') || '',
    status: searchParams.get('status') || '',
    include_terminal: searchParams.get('include_terminal') === 'true',
  };

  const storeNameById = useMemo(() => {
    const map = new Map();
    for (const store of stores) {
      map.set(String(store.id), store.name);
    }
    return map;
  }, [stores]);

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

  const storeOptions = [
    { label: 'All stores', value: '' },
    ...stores.map((store) => ({
      label: `${store.name} (${store.store_number})`,
      value: String(store.id),
    })),
  ];

  const zoneOptions = [
    { label: 'All zones', value: '' },
    ...zones
      .filter((zone) => !filters.store_id || String(zone.store_id) === filters.store_id)
      .map((zone) => ({
        label: `${zone.name} (${formatEnumLabel(zone.gender)})`,
        value: String(zone.id),
      })),
  ];

  const studioOptions = [
    { label: 'All studios', value: '' },
    ...studios
      .filter((studio) => {
        if (filters.trial_zone_id) {
          return String(studio.trial_zone_id) === filters.trial_zone_id;
        }
        if (filters.store_id) {
          const zone = zoneById.get(String(studio.trial_zone_id));
          return zone && String(zone.store_id) === filters.store_id;
        }
        return true;
      })
      .map((studio) => {
        const zone = zoneById.get(String(studio.trial_zone_id));
        return {
          label: `${studio.name} (${zone?.name || `Zone #${studio.trial_zone_id}`})`,
          value: String(studio.id),
        };
      }),
  ];

  const normalizedQuery = query.trim().toLowerCase();
  const filteredTokens = tokens.filter((token) => {
    if (!normalizedQuery) return true;
    const zone = zoneById.get(String(token.trial_zone_id));
    const studio = studioById.get(String(token.assigned_studio_id));
    const haystack = `${token.token_number || ''} ${token.phone_number || ''} ${token.status || ''} ${
      storeNameById.get(String(token.store_id)) || ''
    } ${zone?.name || ''} ${studio?.name || ''} ${studio?.studio_type || ''}`.toLowerCase();
    return haystack.includes(normalizedQuery);
  });

  const statusCounts = tokens.reduce(
    (acc, token) => {
      acc.total += 1;
      acc[token.status] = (acc[token.status] || 0) + 1;
      return acc;
    },
    { total: 0 }
  );

  function setFilter(field, value) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) {
        next.set(field, String(value));
      } else {
        next.delete(field);
      }
      if (field === 'store_id') {
        next.delete('trial_zone_id');
        next.delete('studio_id');
      }
      if (field === 'trial_zone_id') {
        next.delete('studio_id');
      }
      return next;
    });
  }

  async function loadLookups() {
    try {
      const [storeRows, zoneRows, studioRows] = await Promise.all([
        listStores({ include_inactive: true }),
        listTrialZones({ include_inactive: true }),
        listTrialStudios({ include_inactive: true }),
      ]);
      setStores(storeRows);
      setZones(zoneRows);
      setStudios(studioRows);
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    }
  }

  const loadTokens = useCallback(async () => {
    const params = {};
    if (filters.store_id) params.store_id = Number(filters.store_id);
    if (filters.trial_zone_id) params.trial_zone_id = Number(filters.trial_zone_id);
    if (filters.studio_id) params.studio_id = Number(filters.studio_id);
    if (filters.status) params.status = filters.status;
    if (filters.include_terminal || filters.status) params.include_terminal = true;

    setLoading(true);
    setMessage('');
    try {
      setTokens(await listTrialQueueTokens(params));
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [filters.include_terminal, filters.status, filters.store_id, filters.studio_id, filters.trial_zone_id]);

  useEffect(() => {
    loadLookups();
  }, []);

  useEffect(() => {
    loadTokens();
  }, [loadTokens]);

  async function runTokenAction(action, successMessage) {
    setLoading(true);
    setMessage('');
    try {
      await action();
      setMessage(successMessage);
      await loadTokens();
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-line bg-white p-5">
        <SectionHeader eyebrow="Queue operations" title="Live trial queue control" />

        <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
          <Metric label="Total" value={statusCounts.total || 0} />
          <Metric label="Waiting" value={statusCounts.WAITING || 0} />
          <Metric label="Called" value={statusCounts.CALLED || 0} />
          <Metric label="Serving" value={statusCounts.SERVING || 0} />
          <Metric label="Closed" value={(statusCounts.COMPLETED || 0) + (statusCounts.CANCELLED || 0) + (statusCounts.NO_SHOW || 0)} />
        </div>
      </section>

      <section className="rounded-lg border border-line bg-white">
        <div className="border-b border-line p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <SlidersHorizontal size={18} className="text-brand-red" />
              <h2 className="text-xl font-semibold">Queue filters</h2>
            </div>
            <button
              type="button"
              onClick={loadTokens}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-sm font-medium text-charcoal disabled:opacity-60"
            >
              <RefreshCw size={16} />
              Refresh
            </button>
          </div>

          <div className="mt-4 grid gap-3 lg:grid-cols-5">
            <Select label="Store" value={filters.store_id} options={storeOptions} onChange={(value) => setFilter('store_id', value)} />
            <Select label="Zone" value={filters.trial_zone_id} options={zoneOptions} onChange={(value) => setFilter('trial_zone_id', value)} />
            <Select label="Studio" value={filters.studio_id} options={studioOptions} onChange={(value) => setFilter('studio_id', value)} />
            <Select label="Status" value={filters.status} options={STATUS_OPTIONS} onChange={(value) => setFilter('status', value)} />
            <label className="flex items-end">
              <span className="flex h-[42px] w-full items-center justify-between rounded-lg border border-line px-3 text-sm font-medium text-charcoal">
                Include closed
                <input
                  type="checkbox"
                  checked={filters.include_terminal}
                  onChange={(event) => setFilter('include_terminal', event.target.checked)}
                  className="size-5 accent-brand-red"
                />
              </span>
            </label>
          </div>

          <label className="mt-4 block">
            <span className="flex items-center gap-2 text-sm font-medium text-charcoal">
              <Search size={16} />
              Search queue
            </span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search by token, phone, store, zone, studio, or status"
              className="mt-1 w-full rounded-lg border border-line px-3 py-2.5 outline-none focus:border-brand-red focus:ring-2 focus:ring-brand-soft"
            />
          </label>

          {message ? <p className="mt-4 rounded-lg bg-brand-blush px-3 py-2 text-sm text-charcoal">{message}</p> : null}
        </div>

        <div className="divide-y divide-brand-soft">
          {filteredTokens.length === 0 ? (
            <p className="p-5 text-sm text-muted">No queue tokens found.</p>
          ) : (
            filteredTokens.map((token) => (
              <TokenRow
                key={token.token_id}
                token={token}
                storeName={storeNameById.get(String(token.store_id))}
                zone={zoneById.get(String(token.trial_zone_id))}
                studio={studioById.get(String(token.assigned_studio_id))}
                loading={loading}
                onCall={() => runTokenAction(() => callTrialToken(token.token_id), 'Token called')}
                onStart={() => runTokenAction(() => startTrialToken(token.token_id, token.assigned_studio_id), 'Token moved to serving')}
                onComplete={() => runTokenAction(() => completeTrialToken(token.token_id), 'Token completed')}
                onCancel={() => runTokenAction(() => cancelTrialToken(token.token_id, 'Cancelled from admin queue'), 'Token cancelled')}
              />
            ))
          )}
        </div>
      </section>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-lg border border-line p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-ink">{value}</p>
    </div>
  );
}

function TokenRow({ token, storeName, zone, studio, loading, onCall, onStart, onComplete, onCancel }) {
  const canCall = token.status === 'WAITING';
  const canStart = (token.status === 'WAITING' || token.status === 'CALLED') && Boolean(token.assigned_studio_id);
  const canComplete = token.status === 'SERVING';
  const canCancel = token.status === 'WAITING' || token.status === 'CALLED';

  return (
    <div className="grid gap-4 p-5 xl:grid-cols-[1fr_auto]">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="font-semibold">{token.token_number}</h3>
          <span className={`rounded-full px-2 py-1 text-xs ${STATUS_STYLES[token.status] || 'bg-slate-100 text-slate-700'}`}>{token.status}</span>
          <span className="rounded-full bg-brand-blush px-2 py-1 text-xs text-charcoal">Position {token.position}</span>
          <span className="rounded-full bg-brand-blush px-2 py-1 text-xs text-charcoal">{token.estimated_wait_minutes} min wait</span>
        </div>

        <div className="mt-2 grid gap-1 text-sm text-charcoal md:grid-cols-2 xl:grid-cols-3">
          <p>Phone: {token.phone_number}</p>
          <p>Store: {storeName || `#${token.store_id}`}</p>
          <p>Zone: {zone?.name || 'None'}</p>
          <p>Studio: {studio?.name || (token.assigned_studio_id ? `#${token.assigned_studio_id}` : 'Pending assignment')}</p>
          <p>Calling: {formatTime(token.calling_time)}</p>
          <p>Items: {token.item_count ?? 'Not set'}</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 xl:justify-end">
        <button
          type="button"
          onClick={onCall}
          disabled={loading || !canCall}
          className="inline-flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-sm font-medium text-charcoal disabled:opacity-40"
        >
          <Megaphone size={16} />
          Call
        </button>
        <button
          type="button"
          onClick={onStart}
          disabled={loading || !canStart}
          className="inline-flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-sm font-medium text-charcoal disabled:opacity-40"
        >
          <Play size={16} />
          Start
        </button>
        <button
          type="button"
          onClick={onComplete}
          disabled={loading || !canComplete}
          className="inline-flex items-center gap-2 rounded-lg border border-emerald-200 px-3 py-2 text-sm font-medium text-emerald-700 disabled:opacity-40"
        >
          <CheckCircle2 size={16} />
          Complete
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={loading || !canCancel}
          className="inline-flex items-center gap-2 rounded-lg border border-rose-200 px-3 py-2 text-sm font-medium text-rose-700 disabled:opacity-40"
        >
          <XCircle size={16} />
          Cancel
        </button>
      </div>
    </div>
  );
}
