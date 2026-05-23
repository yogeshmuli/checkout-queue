import { Activity, AlertTriangle, BarChart3, BrainCircuit, CalendarDays, Clock, Gauge, RefreshCw, SlidersHorizontal } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

import { getStoreAnalytics } from '../../../../api/checkout/analyticsApi.js';
import { getErrorMessage, showApiErrorToast } from '../../../../api/httpClient.js';
import { listStores } from '../../../../api/checkout/storeApi.js';
import { Select } from '../../../common/FormAndStatePrimitives.jsx';
import { MetricTile } from '../../../common/MetricTile.jsx';
import { SectionHeader } from '../../../common/SectionHeader.jsx';

const DAY_OPTIONS = [
  { label: 'Last 7 days', value: '7' },
  { label: 'Last 30 days', value: '30' },
  { label: 'Last 90 days', value: '90' },
];

const VIEW_OPTIONS = [
  { label: 'Live', value: 'live' },
  { label: 'History', value: 'history' },
  { label: 'Foresights', value: 'foresights' },
];

const INSIGHT_STYLES = {
  warning: 'border-amber-200 bg-amber-50 text-amber-900',
  info: 'border-sky-200 bg-sky-50 text-sky-900',
  success: 'border-emerald-200 bg-emerald-50 text-emerald-900',
};

function formatMinutes(value) {
  return `${Number(value || 0).toFixed(1)}m`;
}

function formatPercent(value) {
  return `${Number(value || 0).toFixed(0)}%`;
}

function formatNumber(value) {
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 1 }).format(Number(value || 0));
}

function formatDate(value) {
  return new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(value));
}

function formatTime(value) {
  return new Intl.DateTimeFormat('en-IN', { hour: '2-digit', minute: '2-digit' }).format(new Date(value));
}

function formatHour(hour) {
  return `${String(hour).padStart(2, '0')}:00`;
}

function getMax(rows, key) {
  return Math.max(...rows.map((row) => Number(row[key] || 0)), 1);
}

export function Dashboard() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [stores, setStores] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [lastRefreshed, setLastRefreshed] = useState(null);

  const filters = {
    store_id: searchParams.get('store_id') || '',
    days: searchParams.get('days') || '7',
    view: searchParams.get('view') || 'live',
  };

  const selectedStoreId = filters.store_id || (stores[0] ? String(stores[0].id) : '');
  const selectedStore = stores.find((store) => String(store.id) === String(selectedStoreId));
  const activeView = VIEW_OPTIONS.some((option) => option.value === filters.view) ? filters.view : 'live';

  const storeOptions = stores.map((store) => ({
    label: `${store.name} (${store.store_number})`,
    value: String(store.id),
  }));

  const topCounters = useMemo(() => {
    return [...(analytics?.counters || [])]
      .sort((first, second) => second.serving_tokens + second.waiting_tokens - (first.serving_tokens + first.waiting_tokens))
      .slice(0, 8);
  }, [analytics]);

  function setFilter(field, value) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) next.set(field, String(value));
      else next.delete(field);
      return next;
    });
  }

  async function loadStores() {
    try {
      setStores(await listStores({ include_inactive: true }));
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    }
  }

  const loadAnalytics = useCallback(async () => {
    if (!selectedStoreId) return;
    setLoading(true);
    setMessage('');
    try {
      const response = await getStoreAnalytics(selectedStoreId, { days: Number(filters.days) || 7 });
      setAnalytics(response);
      setLastRefreshed(new Date());
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [filters.days, selectedStoreId]);

  useEffect(() => {
    loadStores();
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
    loadAnalytics();
  }, [loadAnalytics]);

  useEffect(() => {
    if (!selectedStoreId) return undefined;
    const timer = window.setInterval(loadAnalytics, 60000);
    return () => window.clearInterval(timer);
  }, [loadAnalytics, selectedStoreId]);

  const metrics = analytics?.metrics;

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Store Dashboard"
        title={selectedStore ? `${selectedStore.name} smart view` : 'Smart view'}
        action={
          <button
            type="button"
            onClick={loadAnalytics}
            disabled={loading || !selectedStoreId}
            className="inline-flex items-center gap-2 rounded-lg border border-line bg-white px-3 py-2 text-sm font-medium text-charcoal disabled:opacity-60"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        }
      />

      <section className="rounded-lg border border-line bg-white p-5">
        <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_190px]">
          <Select label="Store" value={selectedStoreId} onChange={(value) => setFilter('store_id', value)} options={storeOptions} />
          <Select label="Range" value={filters.days} onChange={(value) => setFilter('days', value)} options={DAY_OPTIONS} />
        </div>
        <div className="mt-4 grid gap-3 text-sm text-charcoal sm:grid-cols-3">
          <HeaderFact icon={<Gauge size={15} />} label="Store ID" value={analytics?.store?.store_number || selectedStore?.store_number || '-'} />
          <HeaderFact icon={<CalendarDays size={15} />} label="Date" value={formatDate(new Date())} />
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

      {loading && !analytics ? <LoadingState /> : null}
      {!loading && !analytics ? <EmptyState /> : null}

      {analytics && metrics && activeView === 'live' ? <LiveView analytics={analytics} metrics={metrics} /> : null}
      {analytics && metrics && activeView === 'history' ? <HistoryView analytics={analytics} metrics={metrics} /> : null}
      {analytics && metrics && activeView === 'foresights' ? <ForesightsView analytics={analytics} metrics={metrics} topCounters={topCounters} /> : null}
    </div>
  );
}

function LiveView({ analytics, metrics }) {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricTile label="Waiting tokens" value={metrics.waiting_tokens} tone="amber" />
        <MetricTile label="Serving now" value={metrics.called_tokens + metrics.serving_tokens} tone="mint" />
        <MetricTile label="Active counters" value={`${metrics.active_counters}/${metrics.total_counters}`} />
        <MetricTile label="Avg wait" value={formatMinutes(metrics.average_wait_minutes)} tone="rose" />
      </div>

      <div className="space-y-5">
        {analytics.sections.length ? (
          analytics.sections.map((section) => (
            <section key={section.section_id} className="overflow-hidden rounded-lg border border-line bg-white">
              <div className="flex flex-col gap-3 bg-slate-900 px-5 py-4 text-white md:flex-row md:items-center md:justify-between">
                <div>
                  <h2 className="text-xl font-semibold">{section.section_name}</h2>
                  <p className="text-sm text-slate-300">{section.section_type}</p>
                </div>
                <div className="grid grid-cols-3 gap-2 text-sm">
                  <DarkMetric label="Last token assigned to counter" value={section.last_active_token_number || '-'} />
                  <DarkMetric label="Active" value={section.active_counters} />
                  <DarkMetric label="Inactive" value={Math.max(section.total_counters - section.active_counters, 0)} />
                </div>
              </div>

              <div className="grid gap-4 p-5 sm:grid-cols-2 xl:grid-cols-4">
                <LiveMetric label="Last Token" value={section.last_token_number || '-'} />
                <div className="rounded-lg border border-line p-4 sm:col-span-2 xl:col-span-1">
                  <p className="text-xs font-semibold uppercase text-muted">Active Counters</p>
                  <div className="mt-3 max-h-32 space-y-2 overflow-y-auto">
                    {section.active_counter_sessions.length ? (
                      section.active_counter_sessions.map((session) => (
                        <div key={session.counter_id} className="flex items-center justify-between rounded-md bg-slate-50 px-3 py-2 text-sm">
                          <span className="truncate">{session.counter_name}</span>
                          <span className="font-semibold text-brand-red">{session.assigned_token_number || '-'}</span>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-muted">No active sessions</p>
                    )}
                  </div>
                </div>
                <LiveMetric label="Est. Wait (Last Token)" value={formatMinutes(section.estimated_wait_last_token_minutes)} />
                <LiveMetric label="Est. Total Items" value={`${section.estimated_items_ahead} items`} />
              </div>

              <div className="grid gap-3 border-t border-line bg-slate-50 p-5 sm:grid-cols-4">
                <SmallMetric label="Avg Wait" value={formatMinutes(section.average_wait_minutes)} />
                <SmallMetric label="Avg Items" value={formatNumber(section.average_items_today)} />
                <SmallMetric label="Total Cancel" value={section.total_cancellations} />
                <SmallMetric label="Cancel (1h)" value={section.cancellations_last_hour} />
              </div>

              <div className="flex flex-wrap gap-2 border-t border-line p-5">
                <ResourceLink to={`/app/checkout/admin/sections?store_id=${analytics.store.id}`} label="Sections" />
                <ResourceLink to={`/app/checkout/admin/counters?section_id=${section.section_id}`} label="Counters" />
                <ResourceLink to={`/app/checkout/admin/staff?section_id=${section.section_id}`} label="Staff" />
                <ResourceLink to={`/app/checkout/admin/queue?section_id=${section.section_id}`} label="Queue" />
              </div>
            </section>
          ))
        ) : (
          <section className="rounded-lg border border-line bg-white p-5 text-sm text-muted">No live section data available.</section>
        )}
      </div>
    </div>
  );
}

function HistoryView({ analytics, metrics }) {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricTile label="Completed today" value={metrics.completed_today} />
        <MetricTile label="Cancelled / no-show" value={metrics.cancelled_today + metrics.no_show_today} tone="rose" />
        <MetricTile label="Avg service" value={formatMinutes(metrics.average_service_minutes)} />
        <MetricTile label="Avg items today" value={formatNumber(metrics.average_items_today)} tone="amber" />
      </div>

      <AnalyticsPanel title="Promotion Day Analysis" icon={<CalendarDays size={18} />}>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <ComparisonCard title="Avg Footfall" rows={analytics.promotion_stats} labelKey="day_type" valueKey="avg_footfall" />
          <ComparisonCard title="Avg Wait Time" rows={analytics.promotion_stats} labelKey="day_type" valueKey="avg_wait_time" formatter={formatMinutes} />
          <ComparisonCard title="Avg Items" rows={analytics.promotion_stats} labelKey="day_type" valueKey="avg_items" />
          <ComparisonCard title="Service Time" rows={analytics.promotion_stats} labelKey="day_type" valueKey="avg_service_time" formatter={formatMinutes} />
          <ComparisonCard title="Total Cancellations" rows={analytics.promotion_stats} labelKey="day_type" valueKey="cancellations" />
          <ComparisonCard title="Completion Rate" rows={analytics.promotion_stats} labelKey="day_type" valueKey="completion_rate" formatter={formatPercent} />
        </div>
      </AnalyticsPanel>

      <AnalyticsPanel title="Segmented Analysis (Time & Day)" icon={<BarChart3 size={18} />}>
        <div className="grid gap-4 xl:grid-cols-2">
          <BarList title="Weekly Footfall" rows={analytics.weekly_stats} labelKey="day_name" valueKey="total_visits" />
          <BarList title="Weekly Wait Time" rows={analytics.weekly_stats} labelKey="day_name" valueKey="avg_wait_time" formatter={formatMinutes} />
          <BarList title="Hourly Peak Traffic" rows={analytics.hourly_stats.filter((row) => row.total_visits > 0)} labelKey="hour" valueKey="total_visits" labelFormatter={formatHour} />
          <BarList title="Hourly Wait Time" rows={analytics.hourly_stats.filter((row) => row.total_visits > 0)} labelKey="hour" valueKey="avg_wait_time" labelFormatter={formatHour} formatter={formatMinutes} />
          <BarList title="Hourly Service Speed" rows={analytics.hourly_stats.filter((row) => row.total_visits > 0)} labelKey="hour" valueKey="avg_service_time" labelFormatter={formatHour} formatter={formatMinutes} />
          <BarList title="Cancellation Rate by Day" rows={analytics.weekly_stats} labelKey="day_name" valueKey="cancellation_rate" formatter={formatPercent} />
        </div>
      </AnalyticsPanel>

      <AnalyticsPanel title="Date Based Analytics" icon={<Activity size={18} />}>
        <div className="grid gap-4 xl:grid-cols-2">
          <BarList title="Check-ins vs Completed" rows={analytics.daily_trends} labelKey="day" valueKey="token_count" subValueKey="completed_count" />
          <BarList title="Daily Cancellations" rows={analytics.daily_trends} labelKey="day" valueKey="cancelled_count" />
          <BarList title="Daily Avg Wait Time" rows={analytics.daily_trends} labelKey="day" valueKey="average_wait_minutes" formatter={formatMinutes} />
          <BarList title="Daily Avg Service Time" rows={analytics.daily_trends} labelKey="day" valueKey="average_service_minutes" formatter={formatMinutes} />
        </div>
      </AnalyticsPanel>

      <AnalyticsPanel title="Zone Based Analytics" icon={<Gauge size={18} />}>
        <div className="grid gap-4 xl:grid-cols-2">
          <BarList title="Zone-wise Trials" rows={analytics.zone_stats} labelKey="zone_name" valueKey="total_trials" />
          <BarList title="Zone-wise Cancellations" rows={analytics.zone_stats} labelKey="zone_name" valueKey="cancellations" />
          <BarList title="Avg Wait by Zone" rows={analytics.zone_stats} labelKey="zone_name" valueKey="avg_wait_time" formatter={formatMinutes} />
          <BarList title="Items per Zone" rows={analytics.zone_stats} labelKey="zone_name" valueKey="total_items" />
        </div>
      </AnalyticsPanel>

      <AnalyticsPanel title="Customer & Item Analytics" icon={<SlidersHorizontal size={18} />}>
        <div className="grid gap-4 xl:grid-cols-2">
          <BarList title="Trials by Customer Type" rows={analytics.customer_type_stats} labelKey="customer_type" valueKey="count" />
          <BarList title="Cancellations by Customer Type" rows={analytics.customer_type_stats} labelKey="customer_type" valueKey="cancellations" />
          <BarList title="Items vs Wait Time" rows={analytics.item_bucket_stats} labelKey="range" valueKey="avg_wait" formatter={formatMinutes} />
          <BarList title="Items vs Service Time" rows={analytics.item_bucket_stats} labelKey="range" valueKey="avg_service" formatter={formatMinutes} />
        </div>
      </AnalyticsPanel>
    </div>
  );
}

function ForesightsView({ analytics, metrics, topCounters }) {
  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-line bg-white p-5">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-brand-blush p-3 text-brand-red">
            <BrainCircuit size={22} />
          </div>
          <div>
            <h2 className="text-xl font-semibold">AI Foresights & Predictions</h2>
            <p className="text-sm text-muted">Real-time analysis powered by queue analytics and ML metadata.</p>
          </div>
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricTile label="ML status" value={analytics.ml_summary.status} tone="mint" />
        <MetricTile label="Model samples" value={analytics.ml_summary.sample_size} />
        <MetricTile label="Churn risk" value={metrics.cancellations_last_hour > 0 ? 'Elevated' : 'Normal'} tone={metrics.cancellations_last_hour > 0 ? 'rose' : 'slate'} />
        <MetricTile label="Utilization" value={formatPercent(metrics.counter_utilization_percent)} tone="amber" />
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
        <section className="rounded-lg border border-line bg-white">
          <div className="flex items-center gap-2 border-b border-line p-5">
            <AlertTriangle size={18} className="text-brand-red" />
            <h2 className="text-lg font-semibold">Operational insights</h2>
          </div>
          <div className="space-y-3 p-5">
            {analytics.insights.length ? (
              analytics.insights.map((insight) => (
                <div key={`${insight.title}-${insight.detail}`} className={`rounded-lg border p-3 ${INSIGHT_STYLES[insight.level] || INSIGHT_STYLES.info}`}>
                  <p className="font-medium">{insight.title}</p>
                  <p className="mt-1 text-sm">{insight.detail}</p>
                </div>
              ))
            ) : (
              <p className="rounded-lg border border-line p-3 text-sm text-muted">No smart signals need attention right now.</p>
            )}
          </div>
        </section>

        <section className="rounded-lg border border-line bg-white">
          <div className="border-b border-line p-5">
            <h2 className="text-lg font-semibold">Active counter pressure</h2>
          </div>
          <div className="space-y-2 p-5">
            {topCounters.map((counter) => (
              <Link
                key={counter.counter_id}
                to={`/app/checkout/admin/queue?counter_id=${counter.counter_id}`}
                className="flex items-center justify-between rounded-lg border border-line px-3 py-2 hover:border-brand-red/40 hover:bg-brand-blush"
              >
                <span className="min-w-0 truncate text-sm font-medium">{counter.counter_name}</span>
                <span className="ml-3 shrink-0 text-sm text-muted">{counter.current_token_number || `${counter.waiting_tokens} waiting`}</span>
              </Link>
            ))}
            {!topCounters.length ? <p className="text-sm text-muted">No counter data available.</p> : null}
          </div>
        </section>
      </div>
    </div>
  );
}

function HeaderFact({ icon, label, value }) {
  return (
    <div className="flex items-center gap-2 rounded-lg bg-slate-50 px-3 py-2">
      <span className="text-brand-red">{icon}</span>
      <div>
        <p className="text-[10px] font-semibold uppercase text-muted">{label}</p>
        <p className="font-medium">{value}</p>
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

function LiveMetric({ label, value }) {
  return (
    <div className="rounded-lg border border-line p-4">
      <p className="text-xs font-semibold uppercase text-muted">{label}</p>
      <p className="mt-3 text-2xl font-semibold text-ink">{value}</p>
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

function AnalyticsPanel({ title, icon, children }) {
  return (
    <section className="rounded-lg border border-line bg-white">
      <div className="flex items-center gap-2 border-b border-line p-5">
        <span className="text-brand-red">{icon}</span>
        <h2 className="text-lg font-semibold">{title}</h2>
      </div>
      <div className="p-5">{children}</div>
    </section>
  );
}

function ComparisonCard({ title, rows, labelKey, valueKey, formatter = formatNumber }) {
  return (
    <div className="rounded-lg border border-line p-4">
      <h3 className="font-semibold">{title}</h3>
      <div className="mt-4 space-y-3">
        {rows.map((row) => (
          <div key={`${title}-${row[labelKey]}`} className="flex items-center justify-between gap-3">
            <span className="text-sm text-muted">{row[labelKey]}</span>
            <span className="font-semibold">{formatter(row[valueKey])}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function BarList({ title, rows, labelKey, valueKey, subValueKey, formatter = formatNumber, labelFormatter }) {
  const maxValue = getMax(rows, valueKey);
  return (
    <div className="rounded-lg border border-line p-4">
      <h3 className="font-semibold">{title}</h3>
      <div className="mt-4 space-y-3">
        {rows.length ? (
          rows.map((row) => {
            const rawValue = Number(row[valueKey] || 0);
            const width = Math.max((rawValue / maxValue) * 100, rawValue ? 8 : 0);
            const label = labelFormatter ? labelFormatter(row[labelKey]) : String(row[labelKey]);
            return (
              <div key={`${title}-${label}`} className="grid grid-cols-[92px_minmax(0,1fr)_86px] items-center gap-3">
                <span className="truncate text-sm text-muted">{label}</span>
                <div className="h-3 overflow-hidden rounded-full bg-brand-soft">
                  <div className="h-full rounded-full bg-brand-red" style={{ width: `${width}%` }} />
                </div>
                <span className="text-right text-sm font-medium">
                  {formatter(row[valueKey])}
                  {subValueKey ? <span className="text-muted"> / {formatNumber(row[subValueKey])}</span> : null}
                </span>
              </div>
            );
          })
        ) : (
          <p className="text-sm text-muted">No data available.</p>
        )}
      </div>
    </div>
  );
}

function ResourceLink({ to, label }) {
  return (
    <Link to={to} className="rounded-full border border-line px-3 py-1 text-xs font-medium text-charcoal hover:border-brand-red/40 hover:bg-brand-blush hover:text-brand-red">
      {label}
    </Link>
  );
}

function LoadingState() {
  return <section className="rounded-lg border border-line bg-white p-8 text-center text-sm text-muted">Loading dashboard...</section>;
}

function EmptyState() {
  return <section className="rounded-lg border border-line bg-white p-8 text-center text-sm text-muted">Select a store to load dashboard analytics.</section>;
}
