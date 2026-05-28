import {
  Activity,
  AlertTriangle,
  BarChart3,
  BrainCircuit,
  CalendarDays,
  ChevronDown,
  ChevronUp,
  Clock,
  Gauge,
  Info,
  LayoutDashboard,
  RefreshCw,
  Shirt,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend as RechartsLegend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { getErrorMessage, showApiErrorToast } from '../../../../api/httpClient.js';
import { getTrialCalendar } from '../../../../api/trial/calendarApi.js';
import { getTrialStoreModelMetadata } from '../../../../api/trial/mlApi.js';
import { listTrialQueueTokens } from '../../../../api/trial/queueApi.js';
import { listStores } from '../../../../api/trial/storeApi.js';
import { listTrialStudios } from '../../../../api/trial/studiosApi.js';
import { listTrialZones } from '../../../../api/trial/zonesApi.js';
import { Select } from '../../../common/FormAndStatePrimitives.jsx';
import { MetricTile } from '../../../common/MetricTile.jsx';

const VIEW_OPTIONS = [
  { label: 'Live', value: 'live' },
  { label: 'History', value: 'history' },
  { label: 'Foresights', value: 'foresights' },
];

const DAY_OPTIONS = [
  { label: 'Last 7 Days', value: '7' },
  { label: 'Last 30 Days', value: '30' },
  { label: 'Last 90 Days', value: '90' },
];

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const ITEM_BUCKETS = [
  { label: '0-5', test: (count) => count <= 5 },
  { label: '6-15', test: (count) => count >= 6 && count <= 15 },
  { label: '16-30', test: (count) => count >= 16 && count <= 30 },
  { label: '31+', test: (count) => count >= 31 },
];
const ACTIVE_STATUSES = new Set(['WAITING', 'CALLED', 'SERVING']);
const COLORS = ['#ff3b30', '#2563eb', '#16a34a', '#f59e0b', '#7c3aed', '#0891b2'];

function formatDate(value) {
  return new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(value));
}

function formatTime(value) {
  return new Intl.DateTimeFormat('en-IN', { hour: '2-digit', minute: '2-digit' }).format(new Date(value));
}

function formatHour(hour) {
  return `${String(hour).padStart(2, '0')}:00`;
}

function formatMinutes(value) {
  const minutes = Number(value || 0);
  if (minutes < 1) return `${Math.round(minutes * 60)}s`;
  const whole = Math.floor(minutes);
  const seconds = Math.round((minutes - whole) * 60);
  return seconds > 0 ? `${whole}m ${seconds}s` : `${whole}m`;
}

function formatShortMinutes(value) {
  return `${Number(value || 0).toFixed(1)}m`;
}

function formatPercent(value) {
  return `${Number(value || 0).toFixed(0)}%`;
}

function formatNumber(value) {
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 1 }).format(Number(value || 0));
}

function asDate(value) {
  return value ? new Date(value) : null;
}

function dateKey(value) {
  return new Date(value).toISOString().slice(0, 10);
}

function startOfDay(value) {
  const date = new Date(value);
  date.setHours(0, 0, 0, 0);
  return date;
}

function latestToken(tokens) {
  return [...tokens].sort((first, second) => {
    const firstDate = asDate(first.created_at)?.getTime() || 0;
    const secondDate = asDate(second.created_at)?.getTime() || 0;
    return secondDate - firstDate || Number(second.token_id || 0) - Number(first.token_id || 0);
  })[0];
}

function average(values) {
  const filtered = values.map(Number).filter((value) => Number.isFinite(value));
  if (!filtered.length) return 0;
  return filtered.reduce((sum, value) => sum + value, 0) / filtered.length;
}

function percent(numerator, denominator) {
  if (!denominator) return 0;
  return (Number(numerator || 0) / Number(denominator || 0)) * 100;
}

function waitMinutes(token) {
  const serviceStart = asDate(token.service_started_at);
  const created = asDate(token.created_at);
  if (serviceStart && created) return Math.max((serviceStart - created) / 60000, 0);
  return Number(token.estimated_wait_minutes || 0);
}

function serviceMinutes(token) {
  const serviceStart = asDate(token.service_started_at);
  const completed = asDate(token.completed_at);
  if (serviceStart && completed) return Math.max((completed - serviceStart) / 60000, 0);
  return Number(token.service_time_minutes || 0);
}

function isCompleted(token) {
  return token.status === 'COMPLETED';
}

function isCancelled(token) {
  return token.status === 'CANCELLED' || token.status === 'NO_SHOW';
}

function isActiveToken(token) {
  return ACTIVE_STATUSES.has(token.status);
}

function getPromotionDates(calendar) {
  return new Set(
    (calendar?.events || [])
      .filter((event) => event.is_active && ['PROMOTION', 'SALE'].includes(event.event_type))
      .map((event) => event.event_date),
  );
}

function buildRangeDays(days) {
  const today = startOfDay(new Date());
  return Array.from({ length: days }, (_, index) => {
    const date = new Date(today);
    date.setDate(today.getDate() - (days - index - 1));
    return date;
  });
}

function buildAnalytics({ zones, studios, tokens, calendar, metadata, days }) {
  const now = new Date();
  const todayStart = startOfDay(now);
  const rangeStart = buildRangeDays(days)[0];
  const promotionDates = getPromotionDates(calendar);
  const periodTokens = tokens.filter((token) => asDate(token.created_at) >= rangeStart);
  const activeTokens = tokens.filter(isActiveToken);
  const todayTokens = tokens.filter((token) => asDate(token.created_at) >= todayStart);
  const completedTokens = periodTokens.filter(isCompleted);
  const cancelledTokens = periodTokens.filter(isCancelled);

  const studiosByZoneId = new Map();
  for (const studio of studios) {
    const key = String(studio.trial_zone_id || '');
    studiosByZoneId.set(key, [...(studiosByZoneId.get(key) || []), studio]);
  }

  const activeStudioIds = new Set(studios.filter((studio) => studio.is_active).map((studio) => Number(studio.id)));
  const busyStudioIds = new Set(activeTokens.map((token) => Number(token.assigned_studio_id)).filter(Boolean));

  const zoneRows = zones.map((zone) => {
    const zoneStudios = studiosByZoneId.get(String(zone.id)) || [];
    const zoneActiveStudios = zoneStudios.filter((studio) => studio.is_active);
    const zoneTokens = periodTokens.filter((token) => Number(token.trial_zone_id) === Number(zone.id));
    const zoneActiveTokens = activeTokens.filter((token) => Number(token.trial_zone_id) === Number(zone.id));
    const zoneTodayTokens = todayTokens.filter((token) => Number(token.trial_zone_id) === Number(zone.id));
    const zoneCancelled = zoneTokens.filter(isCancelled);
    const zoneLastToken = latestToken([...zoneTokens, ...zoneActiveTokens]);
    const zoneLastCallingTime = asDate(zoneLastToken?.calling_time);
    const itemsAhead = zoneLastToken
      ? zoneActiveTokens
          .filter((token) => {
            if (token.token_id === zoneLastToken.token_id) return false;
            const tokenCallingTime = asDate(token.calling_time);
            if (tokenCallingTime && zoneLastCallingTime) return tokenCallingTime <= zoneLastCallingTime;
            return Number(token.token_id || 0) <= Number(zoneLastToken.token_id || 0);
          })
          .reduce((sum, token) => sum + Number(token.item_count || 0), 0)
      : 0;

    return {
      zone,
      studios: zoneStudios,
      activeStudios: zoneActiveStudios,
      inactiveStudios: zoneStudios.filter((studio) => !studio.is_active),
      activeSessions: zoneActiveStudios.map((studio) => {
        const assignedToken = latestToken(zoneActiveTokens.filter((token) => Number(token.assigned_studio_id) === Number(studio.id) && ['CALLED', 'SERVING'].includes(token.status)));
        return { studio, assignedToken };
      }),
      lastToken: zoneLastToken,
      lastActiveToken: latestToken(zoneActiveTokens.filter((token) => ['CALLED', 'SERVING'].includes(token.status))),
      estimatedWait: zoneLastToken?.estimated_wait_minutes || waitMinutes(zoneLastToken || {}),
      itemsAhead,
      averageWait: average(zoneActiveTokens.map(waitMinutes)),
      averageItems: average(zoneTodayTokens.map((token) => token.item_count || 0)),
      totalCancel: zoneCancelled.length,
      cancelLastHour: zoneCancelled.filter((token) => {
        const cancelledAt = asDate(token.cancelled_at || token.updated_at);
        return cancelledAt && now - cancelledAt <= 60 * 60 * 1000;
      }).length,
      completedToday: zoneTodayTokens.filter(isCompleted).length,
      waitingTokens: zoneActiveTokens.filter((token) => token.status === 'WAITING').length,
      servingTokens: zoneActiveTokens.filter((token) => ['CALLED', 'SERVING'].includes(token.status)).length,
    };
  });

  const dailyTrends = buildRangeDays(days).map((day) => {
    const key = dateKey(day);
    const dayTokens = periodTokens.filter((token) => dateKey(token.created_at) === key);
    const completed = dayTokens.filter(isCompleted);
    const cancelled = dayTokens.filter(isCancelled);
    return {
      day: key,
      token_count: dayTokens.length,
      completed_count: completed.length,
      cancelled_count: cancelled.length,
      cancel_rate: percent(cancelled.length, dayTokens.length),
      average_wait_minutes: average(dayTokens.map(waitMinutes)),
      average_service_minutes: average(completed.map(serviceMinutes)),
    };
  });

  const weeklyStats = WEEKDAYS.map((dayName, weekday) => {
    const dayTokens = periodTokens.filter((token) => {
      const day = asDate(token.created_at)?.getDay();
      return day === (weekday + 1) % 7;
    });
    const cancelled = dayTokens.filter(isCancelled);
    return {
      day_name: dayName,
      total_visits: dayTokens.length,
      avg_wait_time: average(dayTokens.map(waitMinutes)),
      avg_service_time: average(dayTokens.filter(isCompleted).map(serviceMinutes)),
      cancellations: cancelled.length,
      cancellation_rate: percent(cancelled.length, dayTokens.length),
    };
  });

  const hourlyStats = Array.from({ length: 24 }, (_, hour) => {
    const hourTokens = periodTokens.filter((token) => asDate(token.created_at)?.getHours() === hour);
    return {
      hour,
      total_visits: hourTokens.length,
      avg_wait_time: average(hourTokens.map(waitMinutes)),
      avg_service_time: average(hourTokens.filter(isCompleted).map(serviceMinutes)),
    };
  });

  const promotionStats = [
    { day_type: 'Promotion/Sale Day', tokens: periodTokens.filter((token) => promotionDates.has(dateKey(token.created_at))) },
    { day_type: 'Regular Day', tokens: periodTokens.filter((token) => !promotionDates.has(dateKey(token.created_at))) },
  ].map((row) => {
    const completed = row.tokens.filter(isCompleted);
    const cancelled = row.tokens.filter(isCancelled);
    return {
      day_type: row.day_type,
      avg_footfall: row.tokens.length,
      avg_wait_time: average(row.tokens.map(waitMinutes)),
      avg_items: average(row.tokens.map((token) => token.item_count || 0)),
      avg_service_time: average(completed.map(serviceMinutes)),
      cancellations: cancelled.length,
      completion_rate: percent(completed.length, row.tokens.length),
    };
  });

  const zoneStats = zoneRows.map((row) => {
    const zoneTokens = periodTokens.filter((token) => Number(token.trial_zone_id) === Number(row.zone.id));
    return {
      zone_name: row.zone.name,
      total_trials: zoneTokens.filter(isCompleted).length,
      cancellations: zoneTokens.filter(isCancelled).length,
      avg_wait_time: average(zoneTokens.map(waitMinutes)),
      avg_service_time: average(zoneTokens.filter(isCompleted).map(serviceMinutes)),
      total_items: zoneTokens.reduce((sum, token) => sum + Number(token.item_count || 0), 0),
    };
  });

  const customerTypes = [...new Set(periodTokens.map((token) => token.customer_type || 'regular'))];
  const customerStats = (customerTypes.length ? customerTypes : ['regular']).map((customerType) => {
    const customerTokens = periodTokens.filter((token) => (token.customer_type || 'regular') === customerType);
    return {
      customer_type: customerType,
      count: customerTokens.length,
      avg_wait: average(customerTokens.map(waitMinutes)),
      avg_service: average(customerTokens.filter(isCompleted).map(serviceMinutes)),
      total_items: customerTokens.reduce((sum, token) => sum + Number(token.item_count || 0), 0),
      cancellations: customerTokens.filter(isCancelled).length,
    };
  });

  const itemStats = ITEM_BUCKETS.map((bucket) => {
    const bucketTokens = periodTokens.filter((token) => bucket.test(Number(token.item_count || 0)));
    return {
      range: bucket.label,
      count: bucketTokens.length,
      avg_wait: average(bucketTokens.map(waitMinutes)),
      avg_service: average(bucketTokens.filter(isCompleted).map(serviceMinutes)),
    };
  });

  const totalActiveStudios = studios.filter((studio) => studio.is_active).length;
  const metrics = {
    waiting_tokens: activeTokens.filter((token) => token.status === 'WAITING').length,
    serving_tokens: activeTokens.filter((token) => ['CALLED', 'SERVING'].includes(token.status)).length,
    completed_today: todayTokens.filter(isCompleted).length,
    cancelled_today: todayTokens.filter(isCancelled).length,
    active_studios: totalActiveStudios,
    total_studios: studios.length,
    active_zones: zones.filter((zone) => zone.is_active).length,
    total_zones: zones.length,
    average_wait_minutes: average(activeTokens.map(waitMinutes)),
    average_service_minutes: average(completedTokens.map(serviceMinutes)),
    average_items_today: average(todayTokens.map((token) => token.item_count || 0)),
    cancellations_last_hour: cancelledTokens.filter((token) => {
      const cancelledAt = asDate(token.cancelled_at || token.updated_at);
      return cancelledAt && now - cancelledAt <= 60 * 60 * 1000;
    }).length,
    studio_utilization_percent: percent(busyStudioIds.size, activeStudioIds.size),
  };

  const busiestZone = [...zoneRows].sort((first, second) => second.waitingTokens + second.servingTokens - (first.waitingTokens + first.servingTokens))[0];
  const featureImportance = Object.entries(metadata?.feature_importance || {})
    .map(([feature, value]) => ({ feature: feature.replaceAll('_', ' '), value: Number(value || 0) }))
    .sort((first, second) => second.value - first.value)
    .slice(0, 6);
  const predictedWaits = Array.from({ length: 4 }, (_, index) => {
    const hour = (now.getHours() + index + 1) % 24;
    const base = metrics.average_wait_minutes || average(dailyTrends.slice(-7).map((row) => row.average_wait_minutes));
    return { label: formatHour(hour), value: Math.max(0, base + index * 1.5 + (metrics.waiting_tokens > metrics.active_studios ? 2 : 0)) };
  });

  return {
    metrics,
    zoneRows,
    dailyTrends,
    weeklyStats,
    hourlyStats,
    promotionStats,
    zoneStats,
    customerStats,
    itemStats,
    ml: {
      metadata,
      featureImportance,
      predictedWaits,
      churnRisk: buildChurnRisk(metrics, completedTokens.length, cancelledTokens.length),
      anomalyZones: zoneRows.map((row) => {
        const predicted = metrics.average_wait_minutes || row.averageWait;
        const delta = row.averageWait - predicted;
        return {
          zoneName: row.zone.name,
          currentWait: row.averageWait,
          predictedWait: predicted,
          status: delta > 8 ? 'Anomaly' : delta > 3 ? 'Slight deviation' : 'Normal',
        };
      }),
      busiestZone,
    },
  };
}

function buildChurnRisk(metrics, completedCount, cancelledCount) {
  const cancellationRate = percent(cancelledCount, completedCount + cancelledCount);
  if (cancellationRate >= 30 || metrics.average_wait_minutes >= 25) {
    return { level: 'High', tone: 'rose', message: 'Wait time or cancellation pressure is elevated. Add staff or reduce quoted wait.' };
  }
  if (cancellationRate >= 15 || metrics.average_wait_minutes >= 15) {
    return { level: 'Medium', tone: 'amber', message: 'Traffic is healthy but sensitive. Watch high-wait zones closely.' };
  }
  return { level: 'Low', tone: 'mint', message: 'Cancellation pressure is currently controlled.' };
}

export function Dashboard() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [stores, setStores] = useState([]);
  const [zones, setZones] = useState([]);
  const [studios, setStudios] = useState([]);
  const [tokens, setTokens] = useState([]);
  const [calendar, setCalendar] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(false);
  const [storesLoaded, setStoresLoaded] = useState(false);
  const [message, setMessage] = useState('');
  const [lastRefreshed, setLastRefreshed] = useState(null);

  const filters = {
    store_id: searchParams.get('store_id') || '',
    days: searchParams.get('days') || '30',
    view: searchParams.get('view') || 'live',
  };

  const selectedStoreId = filters.store_id || (stores[0] ? String(stores[0].id) : '');
  const selectedStore = stores.find((store) => String(store.id) === String(selectedStoreId));
  const activeView = VIEW_OPTIONS.some((option) => option.value === filters.view) ? filters.view : 'live';
  const days = Number(filters.days) || 30;
  const storeOptions = stores.map((store) => ({ label: `${store.name} (${store.store_number})`, value: String(store.id) }));

  const analytics = useMemo(() => buildAnalytics({ zones, studios, tokens, calendar, metadata, days }), [calendar, days, metadata, studios, tokens, zones]);

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
      const [zoneRows, studioRows, tokenRows, calendarData, modelMetadata] = await Promise.all([
        listTrialZones({ include_inactive: true, store_id: Number(selectedStoreId) }),
        listTrialStudios({ include_inactive: true, store_id: Number(selectedStoreId) }),
        listTrialQueueTokens({ include_terminal: true, store_id: Number(selectedStoreId) }),
        getTrialCalendar(Number(selectedStoreId)).catch(() => null),
        getTrialStoreModelMetadata(Number(selectedStoreId)).catch(() => null),
      ]);
      setZones(zoneRows);
      setStudios(studioRows);
      setTokens(tokenRows);
      setCalendar(calendarData);
      setMetadata(modelMetadata);
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
      })
      .finally(() => setStoresLoaded(true));
  }, []);

  useEffect(() => {
    if (!stores.length) return;
    if (stores.some((store) => String(store.id) === String(filters.store_id))) return;
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('store_id', String(stores[0].id));
      return next;
    });
  }, [filters.store_id, setSearchParams, stores]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  useEffect(() => {
    if (!selectedStoreId) return undefined;
    const timer = window.setInterval(loadDashboard, 60000);
    return () => window.clearInterval(timer);
  }, [loadDashboard, selectedStoreId]);

  return (
    <div className="space-y-6">
      <SmartHeader
        activeView={activeView}
        lastRefreshed={lastRefreshed}
        loading={loading}
        onRefresh={loadDashboard}
        selectedStore={selectedStore}
        selectedStoreId={selectedStoreId}
        setFilter={setFilter}
      />

      <section className="rounded-lg border border-line bg-white p-5">
        <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_190px]">
          <Select label="Store" value={selectedStoreId} onChange={(value) => setFilter('store_id', value)} options={storeOptions} disabled={!stores.length} />
          <Select label="Range" value={filters.days} onChange={(value) => setFilter('days', value)} options={DAY_OPTIONS} />
        </div>
        {message ? <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{message}</p> : null}
      </section>

      {storesLoaded && !stores.length ? <NoStoresCard /> : null}
      {stores.length ? (
        <>
          {activeView === 'live' ? <LiveView analytics={analytics} selectedStoreId={selectedStoreId} /> : null}
          {activeView === 'history' ? <HistoryView analytics={analytics} /> : null}
          {activeView === 'foresights' ? <ForesightsView analytics={analytics} /> : null}
        </>
      ) : null}
    </div>
  );
}

function NoStoresCard() {
  return (
    <section className="rounded-lg border border-dashed border-line bg-white p-5">
      <p className="text-sm font-medium text-charcoal">No stores available.</p>
      <p className="mt-1 text-sm text-muted">Create a store first, then dashboard details will appear here.</p>
    </section>
  );
}

function SmartHeader({ activeView, lastRefreshed, loading, onRefresh, selectedStore, selectedStoreId, setFilter }) {
  return (
    <header className="sticky top-16 z-20 -mx-4 border-b border-line bg-brand-blush/95 px-4 py-4 backdrop-blur">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex size-11 shrink-0 items-center justify-center rounded-lg bg-brand-red text-white">
            <LayoutDashboard size={22} />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-red">Smart View</p>
            <h1 className="truncate text-2xl font-semibold text-ink">Store Dashboard</h1>
          </div>
        </div>

        <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
          <div className="grid grid-cols-3 gap-1 rounded-lg border border-line bg-white p-1">
            {VIEW_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setFilter('view', option.value)}
                className={`relative rounded-md px-3 py-2 text-sm font-semibold transition-colors ${
                  activeView === option.value ? 'bg-brand-red text-white shadow-soft' : 'text-charcoal hover:bg-brand-blush hover:text-brand-red'
                }`}
              >
                {option.value === 'live' && activeView === 'live' ? <span className="absolute right-2 top-2 size-2 rounded-full bg-emerald-300" /> : null}
                {option.label}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={onRefresh}
            disabled={loading || !selectedStoreId}
            className="inline-flex items-center justify-center gap-2 rounded-lg border border-line bg-white px-3 py-2 text-sm font-medium text-charcoal disabled:opacity-60"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      <div className="mt-4 grid gap-3 text-sm text-charcoal md:grid-cols-3">
        <HeaderFact icon={<Gauge size={15} />} label="Store ID" value={selectedStore?.store_number || '-'} />
        <HeaderFact icon={<CalendarDays size={15} />} label="Current date" value={formatDate(new Date())} />
        <HeaderFact icon={<Clock size={15} />} label="Last refreshed" value={lastRefreshed ? formatTime(lastRefreshed) : '-'} live />
      </div>
    </header>
  );
}

function LiveView({ analytics, selectedStoreId }) {
  const metrics = analytics.metrics;
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricTile label="Waiting tokens" value={metrics.waiting_tokens} tone="amber" />
        <MetricTile label="In trial now" value={metrics.serving_tokens} tone="mint" />
        <MetricTile label="Active studios" value={`${metrics.active_studios}/${metrics.total_studios}`} />
        <MetricTile label="Avg wait" value={formatShortMinutes(metrics.average_wait_minutes)} tone="rose" />
      </div>

      <div className="space-y-5">
        {analytics.zoneRows.length ? (
          analytics.zoneRows.map((row) => <ZoneLiveCard key={row.zone.id} row={row} selectedStoreId={selectedStoreId} />)
        ) : (
          <section className="rounded-lg border border-line bg-white p-5 text-sm text-muted">No trial-zone activity available.</section>
        )}
      </div>
    </div>
  );
}

function ZoneLiveCard({ row, selectedStoreId }) {
  return (
    <section className="overflow-hidden rounded-lg border border-line bg-white shadow-soft">
      <div className="flex flex-col gap-4 bg-slate-950 px-5 py-4 text-white xl:flex-row xl:items-center xl:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-red-100">{row.zone.zone_type}</p>
          <h2 className="text-2xl font-semibold">{row.zone.name}</h2>
          <p className="mt-1 text-sm text-slate-300">Last token assigned to studio: {row.lastActiveToken?.token_number || '-'}</p>
        </div>
        <div className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-3">
          <DarkMetric label="Last Token" value={row.lastToken?.token_number || '-'} />
          <DarkMetric label="Active Studios" value={row.activeStudios.length} />
          <DarkMetric label="Inactive Studios" value={row.inactiveStudios.length} />
        </div>
      </div>

      <div className="grid gap-4 p-5 md:grid-cols-2 xl:grid-cols-4">
        <LiveMetric label="Last Token" value={row.lastToken?.token_number || '-'} icon={<Activity size={18} />} />
        <div className="rounded-lg border border-line p-4">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase text-muted">Active Studios</p>
            <Shirt size={18} className="text-brand-red" />
          </div>
          <div className="mt-3 max-h-36 space-y-2 overflow-y-auto pr-1">
            {row.activeSessions.length ? (
              row.activeSessions.map(({ studio, assignedToken }) => (
                <div key={studio.id} className="flex items-center justify-between gap-3 rounded-md bg-slate-50 px-3 py-2 text-sm">
                  <span className="min-w-0 truncate">{studio.name || `Studio #${studio.id}`}</span>
                  <span className="shrink-0 font-semibold text-brand-red">{assignedToken?.token_number || '-'}</span>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted">No active studio sessions</p>
            )}
          </div>
        </div>
        <LiveMetric label="Est. Wait (Last Token)" value={formatMinutes(row.estimatedWait)} icon={<Clock size={18} />} />
        <LiveMetric label="Est. Total Items" value={`${row.itemsAhead} items`} icon={<Shirt size={18} />} />
      </div>

      <div className="grid gap-3 border-t border-line bg-slate-50 p-5 sm:grid-cols-4">
        <SmallMetric label="Avg Wait" value={formatShortMinutes(row.averageWait)} />
        <SmallMetric label="Avg Items" value={formatNumber(row.averageItems)} />
        <SmallMetric label="Total Cancel" value={row.totalCancel} />
        <SmallMetric label="Cancel (1h)" value={row.cancelLastHour} />
      </div>

      <div className="flex flex-wrap gap-2 border-t border-line p-5">
        <ResourceLink to={`/app/trial/admin/zones?store_id=${selectedStoreId}`} label="Zones" />
        <ResourceLink to={`/app/trial/admin/studios?trial_zone_id=${row.zone.id}`} label="Studios" />
        <ResourceLink to={`/app/trial/admin/staff?store_id=${selectedStoreId}`} label="Staff" />
        <ResourceLink to={`/app/trial/admin/queue?trial_zone_id=${row.zone.id}`} label="Queue" />
      </div>
    </section>
  );
}

function HistoryView({ analytics }) {
  const [openSections, setOpenSections] = useState({
    promotion: true,
    segmented: true,
    date: true,
    zone: true,
    customer: true,
    item: true,
  });

  function toggle(section) {
    setOpenSections((current) => ({ ...current, [section]: !current[section] }));
  }

  const activeHourly = analytics.hourlyStats.filter((row) => row.total_visits > 0);

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricTile label="Completed today" value={analytics.metrics.completed_today} />
        <MetricTile label="Cancelled today" value={analytics.metrics.cancelled_today} tone="rose" />
        <MetricTile label="Avg service" value={formatShortMinutes(analytics.metrics.average_service_minutes)} />
        <MetricTile label="Avg items today" value={formatNumber(analytics.metrics.average_items_today)} tone="amber" />
      </div>

      <AnalysisSection title="Promotion Day Analysis" icon={<CalendarDays size={18} />} open={openSections.promotion} onToggle={() => toggle('promotion')}>
        <ChartGrid>
          <ChartCard title="Avg Footfall" rows={analytics.promotionStats} labelKey="day_type" valueKey="avg_footfall" type="bar" />
          <ChartCard title="Avg Wait Time (min)" rows={analytics.promotionStats} labelKey="day_type" valueKey="avg_wait_time" formatter={formatShortMinutes} type="bar" />
          <ChartCard title="Avg Items" rows={analytics.promotionStats} labelKey="day_type" valueKey="avg_items" type="bar" />
          <ChartCard title="Service Time (min)" rows={analytics.promotionStats} labelKey="day_type" valueKey="avg_service_time" formatter={formatShortMinutes} type="bar" />
          <ChartCard title="Total Cancellations" rows={analytics.promotionStats} labelKey="day_type" valueKey="cancellations" type="bar" />
          <ChartCard title="Completion Rate (%)" rows={analytics.promotionStats} labelKey="day_type" valueKey="completion_rate" formatter={formatPercent} type="bar" />
        </ChartGrid>
      </AnalysisSection>

      <AnalysisSection title="Segmented Analysis (Time & Day)" icon={<BarChart3 size={18} />} open={openSections.segmented} onToggle={() => toggle('segmented')}>
        <ChartGrid>
          <ChartCard title="Weekly Footfall" rows={analytics.weeklyStats} labelKey="day_name" valueKey="total_visits" type="bar" />
          <ChartCard title="Weekly Wait Time" rows={analytics.weeklyStats} labelKey="day_name" valueKey="avg_wait_time" formatter={formatShortMinutes} type="line" />
          <ChartCard title="Hourly Peak Traffic" rows={activeHourly} labelKey="hour" valueKey="total_visits" labelFormatter={formatHour} type="area" />
          <ChartCard title="Hourly Wait Time" rows={activeHourly} labelKey="hour" valueKey="avg_wait_time" labelFormatter={formatHour} formatter={formatShortMinutes} type="line" />
          <ChartCard title="Hourly Service Speed" rows={activeHourly} labelKey="hour" valueKey="avg_service_time" labelFormatter={formatHour} formatter={formatShortMinutes} type="line" />
          <ChartCard title="Cancellation Rate by Day" rows={analytics.weeklyStats} labelKey="day_name" valueKey="cancellation_rate" formatter={formatPercent} type="bar" />
        </ChartGrid>
      </AnalysisSection>

      <AnalysisSection title="Date Based Analytics" icon={<Activity size={18} />} open={openSections.date} onToggle={() => toggle('date')}>
        <ChartGrid>
          <ChartCard title="Check-ins vs Completed" rows={analytics.dailyTrends} labelKey="day" valueKey="token_count" subValueKey="completed_count" type="grouped" />
          <ChartCard title="Daily Cancellations" rows={analytics.dailyTrends} labelKey="day" valueKey="cancelled_count" type="bar" />
          <ChartCard title="Daily Avg Wait Time" rows={analytics.dailyTrends} labelKey="day" valueKey="average_wait_minutes" formatter={formatShortMinutes} type="line" />
          <ChartCard title="Daily Avg Service Time" rows={analytics.dailyTrends} labelKey="day" valueKey="average_service_minutes" formatter={formatShortMinutes} type="line" />
        </ChartGrid>
      </AnalysisSection>

      <AnalysisSection title="Zone Based Analytics" icon={<Gauge size={18} />} open={openSections.zone} onToggle={() => toggle('zone')}>
        <ChartGrid>
          <ChartCard title="Zone-wise Trials" rows={analytics.zoneStats} labelKey="zone_name" valueKey="total_trials" type="bar" />
          <ChartCard title="Zone-wise Cancellations" rows={analytics.zoneStats} labelKey="zone_name" valueKey="cancellations" type="bar" />
          <ChartCard title="Avg Wait by Zone" rows={analytics.zoneStats} labelKey="zone_name" valueKey="avg_wait_time" formatter={formatShortMinutes} type="line" />
          <ChartCard title="Avg Service by Zone" rows={analytics.zoneStats} labelKey="zone_name" valueKey="avg_service_time" formatter={formatShortMinutes} type="line" />
          <ChartCard title="Items per Zone" rows={analytics.zoneStats} labelKey="zone_name" valueKey="total_items" type="bar" />
        </ChartGrid>
      </AnalysisSection>

      <AnalysisSection title="Gender & Item Analytics" icon={<Shirt size={18} />} open={openSections.customer} onToggle={() => toggle('customer')}>
        <ChartGrid>
          <ChartCard title="Trials by Customer Type" rows={analytics.customerStats} labelKey="customer_type" valueKey="count" type="bar" />
          <ChartCard title="Wait by Customer Type" rows={analytics.customerStats} labelKey="customer_type" valueKey="avg_wait" formatter={formatShortMinutes} type="bar" />
          <ChartCard title="Service by Customer Type" rows={analytics.customerStats} labelKey="customer_type" valueKey="avg_service" formatter={formatShortMinutes} type="bar" />
          <ChartCard title="Items by Customer Type" rows={analytics.customerStats} labelKey="customer_type" valueKey="total_items" type="bar" />
          <PieLikeCard title="Cancellations by Customer Type" rows={analytics.customerStats} labelKey="customer_type" valueKey="cancellations" />
          <ChartCard title="Item Buckets" rows={analytics.itemStats} labelKey="range" valueKey="count" type="bar" />
        </ChartGrid>
      </AnalysisSection>

      <AnalysisSection title="Item & Cancellation Analytics" icon={<AlertTriangle size={18} />} open={openSections.item} onToggle={() => toggle('item')}>
        <ChartGrid>
          <ChartCard title="Items vs Wait Time" rows={analytics.itemStats} labelKey="range" valueKey="avg_wait" formatter={formatShortMinutes} type="area" />
          <ChartCard title="Items vs Service Time" rows={analytics.itemStats} labelKey="range" valueKey="avg_service" formatter={formatShortMinutes} type="line" />
          <ChartCard title="Wait vs Cancels" rows={analytics.dailyTrends} labelKey="day" valueKey="average_wait_minutes" subValueKey="cancelled_count" formatter={formatShortMinutes} type="grouped" />
          <ChartCard title="Daily Cancel Rate %" rows={analytics.dailyTrends} labelKey="day" valueKey="cancel_rate" formatter={formatPercent} type="line" />
        </ChartGrid>
      </AnalysisSection>
    </div>
  );
}

function ForesightsView({ analytics }) {
  const metadata = analytics.ml.metadata;
  if (!metadata || metadata.status !== 'READY') {
    return (
      <section className="rounded-lg border border-line bg-white p-8 text-center">
        <div className="mx-auto flex size-14 items-center justify-center rounded-lg bg-brand-blush text-brand-red">
          <BrainCircuit size={28} />
        </div>
        <h2 className="mt-4 text-xl font-semibold">AI Model Initializing...</h2>
        <p className="mt-2 text-sm text-muted">Collect more data or train the Trial Queue ML model to unlock predictive foresights.</p>
      </section>
    );
  }

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-line bg-white p-5">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-brand-blush p-3 text-brand-red">
            <BrainCircuit size={22} />
          </div>
          <div>
            <h2 className="text-xl font-semibold">AI Foresights & Predictions</h2>
            <p className="text-sm text-muted">Real-time analysis powered by Machine Learning</p>
          </div>
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricTile label="Model Accuracy" value={metadata.accuracy_score ? formatPercent(metadata.accuracy_score * 100) : 'Ready'} tone="mint" />
        <MetricTile label="MAE" value={metadata.mae != null ? formatShortMinutes(metadata.mae) : '-'} />
        <MetricTile label="Churn Risk" value={analytics.ml.churnRisk.level} tone={analytics.ml.churnRisk.tone} />
        <MetricTile label="Training Data" value={metadata.sample_size || 0} tone="amber" />
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
        <section className="rounded-lg border border-line bg-white p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h3 className="text-lg font-semibold">Key Drivers (Feature Importance)</h3>
              <p className="text-sm text-muted">Top ML factors affecting trial service-time prediction.</p>
            </div>
            <div className="group relative text-muted">
              <Info size={18} />
              <div className="pointer-events-none absolute right-0 top-7 z-10 w-64 rounded-lg border border-line bg-white p-3 text-xs text-charcoal opacity-0 shadow-soft transition group-hover:opacity-100">
                Higher values mean the model used that feature more often when splitting decision trees.
              </div>
            </div>
          </div>
          <ChartCard title="Top 6 drivers" rows={analytics.ml.featureImportance} labelKey="feature" valueKey="value" formatter={(value) => Number(value || 0).toFixed(3)} type="bar" dominant />
        </section>

        <section className="rounded-lg border border-line bg-white p-5">
          <h3 className="text-lg font-semibold">Zone Anomaly Status</h3>
          <div className="mt-4 space-y-3">
            {analytics.ml.anomalyZones.map((zone) => (
              <div key={zone.zoneName} className="rounded-lg border border-line p-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-semibold">{zone.zoneName}</p>
                  <StatusBadge status={zone.status} />
                </div>
                <p className="mt-2 text-sm text-muted">
                  Current {formatShortMinutes(zone.currentWait)} vs predicted {formatShortMinutes(zone.predictedWait)}
                </p>
              </div>
            ))}
          </div>
        </section>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="rounded-lg border border-line bg-white p-5">
          <h3 className="text-lg font-semibold">Predicted Wait (Next 4 Hours)</h3>
          <ChartCard title="Upcoming hours" rows={analytics.ml.predictedWaits} labelKey="label" valueKey="value" formatter={formatShortMinutes} type="area" />
        </section>
        <section className="rounded-lg border border-line bg-white p-5">
          <h3 className="text-lg font-semibold">Churn Risk</h3>
          <p className="mt-3 rounded-lg border border-line bg-slate-50 p-4 text-sm text-charcoal">{analytics.ml.churnRisk.message}</p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <SmallMetric label="Data quality" value={metadata.data_quality_score != null ? formatPercent(metadata.data_quality_score * 100) : '-'} />
            <SmallMetric label="Last trained" value={metadata.trained_at ? formatDate(metadata.trained_at) : '-'} />
          </div>
        </section>
      </div>
    </div>
  );
}

function HeaderFact({ icon, label, value, live = false }) {
  return (
    <div className="flex items-center gap-2 rounded-lg bg-white px-3 py-2 shadow-sm">
      <span className="text-brand-red">{icon}</span>
      <div className="min-w-0">
        <p className="text-[10px] font-semibold uppercase text-muted">{label}</p>
        <p className="flex items-center gap-2 font-medium">
          {live ? <span className="size-2 rounded-full bg-emerald-500" /> : null}
          <span className="truncate">{value}</span>
        </p>
      </div>
    </div>
  );
}

function DarkMetric({ label, value }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/5 px-3 py-2">
      <p className="text-[10px] font-semibold uppercase text-slate-400">{label}</p>
      <p className="mt-1 font-semibold text-white">{value}</p>
    </div>
  );
}

function LiveMetric({ label, value, icon }) {
  return (
    <div className="rounded-lg border border-line p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-semibold uppercase text-muted">{label}</p>
        <span className="text-brand-red">{icon}</span>
      </div>
      <p className="mt-4 text-2xl font-semibold text-ink">{value}</p>
    </div>
  );
}

function SmallMetric({ label, value }) {
  return (
    <div className="rounded-lg border border-line bg-white p-3">
      <p className="text-xs font-semibold uppercase text-muted">{label}</p>
      <p className="mt-1 font-semibold">{value}</p>
    </div>
  );
}

function AnalysisSection({ children, icon, onToggle, open, title }) {
  return (
    <section className="rounded-lg border border-line bg-white">
      <button type="button" onClick={onToggle} className="flex w-full items-center justify-between gap-3 border-b border-line p-5 text-left">
        <span className="flex items-center gap-2">
          <span className="text-brand-red">{icon}</span>
          <span className="text-lg font-semibold">{title}</span>
        </span>
        {open ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
      </button>
      {open ? <div className="p-5">{children}</div> : null}
    </section>
  );
}

function ChartGrid({ children }) {
  return <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{children}</div>;
}

function ChartCard({ dominant = false, formatter = formatNumber, labelFormatter, labelKey, rows, subValueKey, title, type, valueKey }) {
  const chartRows = normalizeChartRows(rows, labelKey, valueKey, labelFormatter).slice(-14);
  const hasData = chartRows.some((row) => Number(row[valueKey] || 0) > 0 || Number(row[subValueKey] || 0) > 0);
  const chartType = type === 'grouped' ? 'composed' : type;
  const showEveryXAxisLabel = chartRows.length <= 8;
  const xAxisProps = {
    dataKey: '_label',
    height: showEveryXAxisLabel ? 46 : 30,
    interval: showEveryXAxisLabel ? 0 : 'preserveStartEnd',
    tick: { fontSize: 11 },
    ...(showEveryXAxisLabel ? { angle: -28, textAnchor: 'end' } : {}),
  };

  return (
    <div className="rounded-lg border border-line p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="font-semibold">{title}</h3>
        <ChartLegend type={type} />
      </div>
      <div className="mt-4 h-64">
        {hasData ? (
          <ResponsiveContainer width="100%" height="100%">
            {chartType === 'line' ? (
              <LineChart data={chartRows} margin={{ top: 8, right: 12, bottom: showEveryXAxisLabel ? 18 : 8, left: -18 }}>
                <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" />
                <XAxis {...xAxisProps} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip content={<ChartTooltip formatter={formatter} valueKey={valueKey} subValueKey={subValueKey} />} />
                <Line type="monotone" dataKey={valueKey} stroke="#ff3b30" strokeWidth={3} dot={{ r: 3 }} activeDot={{ r: 5 }} />
              </LineChart>
            ) : chartType === 'area' ? (
              <AreaChart data={chartRows} margin={{ top: 8, right: 12, bottom: showEveryXAxisLabel ? 18 : 8, left: -18 }}>
                <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" />
                <XAxis {...xAxisProps} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip content={<ChartTooltip formatter={formatter} valueKey={valueKey} subValueKey={subValueKey} />} />
                <Area type="monotone" dataKey={valueKey} stroke="#ff3b30" fill="#ff3b30" fillOpacity={0.18} strokeWidth={3} />
              </AreaChart>
            ) : chartType === 'composed' ? (
              <ComposedChart data={chartRows} margin={{ top: 8, right: 12, bottom: showEveryXAxisLabel ? 18 : 8, left: -18 }}>
                <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" />
                <XAxis {...xAxisProps} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip content={<ChartTooltip formatter={formatter} valueKey={valueKey} subValueKey={subValueKey} />} />
                <RechartsLegend wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey={valueKey} name={title} fill="#ff3b30" radius={[6, 6, 0, 0]} />
                {subValueKey ? <Line type="monotone" dataKey={subValueKey} name={formatDataKey(subValueKey)} stroke="#2563eb" strokeWidth={3} dot={{ r: 3 }} /> : null}
              </ComposedChart>
            ) : (
              <BarChart data={chartRows} margin={{ top: 8, right: 12, bottom: showEveryXAxisLabel ? 18 : 8, left: -18 }}>
                <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" />
                <XAxis {...xAxisProps} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip content={<ChartTooltip formatter={formatter} valueKey={valueKey} subValueKey={subValueKey} />} />
                <Bar dataKey={valueKey} fill="#ff3b30" radius={[6, 6, 0, 0]}>
                  {chartRows.map((row, index) => (
                    <Cell key={`${title}-${row._label}`} fill={dominant && index === 0 ? '#ff3b30' : COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            )}
          </ResponsiveContainer>
        ) : (
          <EmptyChartState />
        )}
      </div>
    </div>
  );
}

function PieLikeCard({ formatter = formatNumber, labelKey, rows, title, valueKey }) {
  const chartRows = normalizeChartRows(rows, labelKey, valueKey);
  const total = chartRows.reduce((sum, row) => sum + Number(row[valueKey] || 0), 0);
  return (
    <div className="rounded-lg border border-line p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="font-semibold">{title}</h3>
        <ChartLegend type="pie" />
      </div>
      <div className="mt-4 h-64">
        {total > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Tooltip content={<ChartTooltip formatter={formatter} valueKey={valueKey} />} />
              <Pie data={chartRows} dataKey={valueKey} nameKey="_label" innerRadius={48} outerRadius={82} paddingAngle={2}>
                {chartRows.map((row, index) => (
                  <Cell key={`${title}-${row._label}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <RechartsLegend wrapperStyle={{ fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <EmptyChartState />
        )}
      </div>
    </div>
  );
}

function ChartLegend({ type }) {
  const label = type === 'grouped' ? 'Grouped' : type === 'area' ? 'Area' : type === 'line' ? 'Line' : 'Bar';
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-slate-50 px-2 py-1 text-[10px] font-semibold uppercase text-muted">
      <span className="size-2 rounded-full bg-brand-red" />
      {label}
    </span>
  );
}

function ChartTooltip({ active, formatter = formatNumber, label, payload, subValueKey, valueKey }) {
  if (!active || !payload?.length) return null;
  const primary = payload.find((item) => item.dataKey === valueKey) || payload[0];
  const secondary = subValueKey ? payload.find((item) => item.dataKey === subValueKey) : null;
  return (
    <div className="rounded-lg border border-line bg-white px-3 py-2 text-xs shadow-soft">
      <p className="font-semibold text-ink">{label}</p>
      <p className="mt-1 text-brand-red">{formatDataKey(valueKey)}: {formatter(primary?.value || 0)}</p>
      {secondary ? <p className="mt-1 text-blue-700">{formatDataKey(subValueKey)}: {formatNumber(secondary.value)}</p> : null}
    </div>
  );
}

function EmptyChartState() {
  return (
    <div className="grid h-full place-items-center rounded-lg bg-slate-50 text-sm text-muted">
      No chart data yet
    </div>
  );
}

function normalizeChartRows(rows, labelKey, valueKey, labelFormatter) {
  const sourceRows = rows.length ? rows : [{ [labelKey]: 'No data', [valueKey]: 0 }];
  return sourceRows.map((row) => ({
    ...row,
    [valueKey]: Number(row[valueKey] || 0),
    _label: String(labelFormatter ? labelFormatter(row[labelKey]) : row[labelKey]),
  }));
}

function formatDataKey(key) {
  return String(key || '').replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function StatusBadge({ status }) {
  const className =
    status === 'Anomaly'
      ? 'bg-rose-50 text-rose-700'
      : status === 'Slight deviation'
        ? 'bg-amber-50 text-amber-800'
        : 'bg-emerald-50 text-emerald-700';
  return <span className={`rounded-full px-2 py-1 text-xs font-semibold ${className}`}>{status}</span>;
}

function ResourceLink({ to, label }) {
  return (
    <Link to={to} className="rounded-lg border border-line px-3 py-1.5 text-xs font-medium text-charcoal hover:border-brand-red hover:text-brand-red">
      {label}
    </Link>
  );
}
