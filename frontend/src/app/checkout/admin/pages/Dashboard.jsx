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
  ShoppingBasket,
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

import { getStoreAnalytics } from '../../../../api/checkout/analyticsApi.js';
import { getStoreModelMetadata } from '../../../../api/checkout/mlApi.js';
import { listStores } from '../../../../api/checkout/storeApi.js';
import { getErrorMessage, showApiErrorToast } from '../../../../api/httpClient.js';
import { Select } from '../../../common/FormAndStatePrimitives.jsx';
import { MetricTile } from '../../../common/MetricTile.jsx';

const DAY_OPTIONS = [
  { label: 'Last 7 Days', value: '7' },
  { label: 'Last 30 Days', value: '30' },
  { label: 'Last 90 Days', value: '90' },
];

const VIEW_OPTIONS = [
  { label: 'Live', value: 'live' },
  { label: 'History', value: 'history' },
  { label: 'Foresights', value: 'foresights' },
];

const COLORS = ['#4f81bd', '#c0504d', '#9bbb59', '#8064a2', '#4bacc6', '#f79646', '#2c4d75'];
const LINE_COLOR = '#4a7ebb';
const SECONDARY_LINE_COLOR = '#c0504d';
const PROMOTION_COLORS = { 'Regular Day': '#6785b5', 'Promotion/Sale Day': '#a3535d' };

function getBarColor(row, index, dominant) {
  if (PROMOTION_COLORS[row._label]) return PROMOTION_COLORS[row._label];
  return dominant && index === 0 ? LINE_COLOR : COLORS[index % COLORS.length];
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

function formatMinutes(value) {
  return `${Number(value || 0).toFixed(1)}m`;
}

function formatPercent(value) {
  return `${Number(value || 0).toFixed(0)}%`;
}

function formatNumber(value) {
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 1 }).format(Number(value || 0));
}

function buildForesights(analytics, metadata) {
  const metrics = analytics?.metrics || {};
  const featureImportance = Object.entries(metadata?.feature_importance || {})
    .map(([feature, value]) => ({ feature: feature.replaceAll('_', ' '), value: Number(value || 0) }))
    .sort((first, second) => second.value - first.value)
    .slice(0, 6);
  const baseWait = Number(metrics.average_wait_minutes || 0);
  const predictedWaits = Array.from({ length: 4 }, (_, index) => ({
    label: formatHour((new Date().getHours() + index + 1) % 24),
    value: Math.max(0, baseWait + index * 1.25 + (metrics.waiting_tokens > metrics.active_counters ? 2 : 0)),
  }));
  const cancellationPressure = Number(metrics.cancelled_today || 0) + Number(metrics.no_show_today || 0);
  const churnRisk =
    cancellationPressure > 5 || baseWait >= 25
      ? { level: 'High', tone: 'rose', message: 'Wait time or cancellation pressure is elevated. Add counters or reduce quoted wait.' }
      : cancellationPressure > 0 || baseWait >= 15
        ? { level: 'Medium', tone: 'amber', message: 'Queue pressure is manageable but sensitive. Watch high-wait sections closely.' }
        : { level: 'Low', tone: 'mint', message: 'Cancellation pressure is currently controlled.' };
  const anomalySections = (analytics?.sections || []).map((section) => {
    const currentWait = Number(section.average_wait_minutes || 0);
    const predictedWait = baseWait || currentWait;
    const delta = currentWait - predictedWait;
    return {
      name: section.section_name,
      currentWait,
      predictedWait,
      status: delta > 8 ? 'Anomaly' : delta > 3 ? 'Slight deviation' : 'Normal',
    };
  });
  return { featureImportance, predictedWaits, churnRisk, anomalySections };
}

export function Dashboard() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [stores, setStores] = useState([]);
  const [analytics, setAnalytics] = useState(null);
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
  const analyticsDays = activeView === 'history' ? Number(filters.days) || 30 : 1;
  const storeOptions = stores.map((store) => ({ label: `${store.name} (${store.store_number})`, value: String(store.id) }));
  const foresights = useMemo(() => buildForesights(analytics, metadata), [analytics, metadata]);

  function setFilter(field, value) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) next.set(field, String(value));
      else next.delete(field);
      return next;
    });
  }

  const loadDashboard = useCallback(async ({ skipGlobalLoader = false } = {}) => {
    if (!selectedStoreId) return;
    setLoading(true);
    setMessage('');
    try {
      const [analyticsResponse, metadataResponse] = await Promise.all([
        getStoreAnalytics(selectedStoreId, { days: analyticsDays }, { skipGlobalLoader }),
        getStoreModelMetadata(selectedStoreId, { skipGlobalLoader }).catch(() => null),
      ]);
      setAnalytics(analyticsResponse);
      setMetadata(metadataResponse);
      setLastRefreshed(new Date());
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [analyticsDays, selectedStoreId]);

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
    const timer = window.setInterval(() => loadDashboard({ skipGlobalLoader: true }), 60000);
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
        <div className={`grid gap-3 ${activeView === 'history' ? 'md:grid-cols-[minmax(0,1fr)_190px]' : ''}`}>
          <Select label="Store" value={selectedStoreId} onChange={(value) => setFilter('store_id', value)} options={storeOptions} disabled={!stores.length} />
          {activeView === 'history' ? <Select label="Range" value={filters.days} onChange={(value) => setFilter('days', value)} options={DAY_OPTIONS} /> : null}
        </div>
        {message ? <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{message}</p> : null}
      </section>

      {storesLoaded && !stores.length ? <NoStoresCard /> : null}
      {stores.length ? (
        <>
          {loading && !analytics ? <LoadingState /> : null}
          {!loading && !analytics ? <EmptyState /> : null}
          {analytics && activeView === 'live' ? <LiveView analytics={analytics} /> : null}
          {analytics && activeView === 'history' ? <HistoryView analytics={analytics} /> : null}
          {analytics && activeView === 'foresights' ? <ForesightsView analytics={analytics} foresights={foresights} metadata={metadata} /> : null}
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
            <h1 className="truncate text-2xl font-semibold text-ink">Store Insights</h1>
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

function LiveView({ analytics }) {
  const metrics = analytics.metrics;
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
            <section key={section.section_id} className="overflow-hidden rounded-lg border border-line bg-white shadow-soft">
              <div className="flex flex-col gap-4 bg-slate-950 px-5 py-4 text-white xl:flex-row xl:items-center xl:justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-red-100">{section.section_type}</p>
                  <h2 className="text-2xl font-semibold">{section.section_name}</h2>
                  <p className="mt-1 text-sm text-slate-300">Last token assigned to counter: {section.last_active_token_number || '-'}</p>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-3">
                  <DarkMetric label="Last Token" value={section.last_token_number || '-'} />
                  <DarkMetric label="Active Counters" value={section.active_counters} />
                  <DarkMetric label="Inactive Counters" value={Math.max(section.total_counters - section.active_counters, 0)} />
                </div>
              </div>

              <div className="grid gap-4 p-5 md:grid-cols-2 xl:grid-cols-4">
                <LiveMetric label="Last Token" value={section.last_token_number || '-'} icon={<Activity size={18} />} />
                <div className="rounded-lg border border-line p-4">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold uppercase text-muted">Active Counters</p>
                    <Gauge size={18} className="text-brand-red" />
                  </div>
                  <div className="mt-3 max-h-36 space-y-2 overflow-y-auto pr-1">
                    {section.active_counter_sessions.length ? (
                      section.active_counter_sessions.map((session) => (
                        <div key={session.counter_id} className="flex items-center justify-between gap-3 rounded-md bg-slate-50 px-3 py-2 text-sm">
                          <span className="min-w-0 truncate">{session.counter_name}</span>
                          <span className="shrink-0 font-semibold text-brand-red">{session.assigned_token_number || '-'}</span>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-muted">No active counter sessions</p>
                    )}
                  </div>
                </div>
                <LiveMetric label="Est. Wait (Last Token)" value={formatMinutes(section.estimated_wait_last_token_minutes)} icon={<Clock size={18} />} />
                <LiveMetric label="Est. Total Items" value={`${section.estimated_items_ahead} items`} icon={<ShoppingBasket size={18} />} />
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

  const activeHourly = analytics.hourly_stats.filter((row) => row.total_visits > 0);
  const rangeTotals = analytics.daily_trends.reduce(
    (totals, row) => ({
      checkIns: totals.checkIns + Number(row.token_count || 0),
      completed: totals.completed + Number(row.completed_count || 0),
      cancelled: totals.cancelled + Number(row.cancelled_count || 0),
    }),
    { checkIns: 0, completed: 0, cancelled: 0 },
  );

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricTile label="Check-ins in range" value={rangeTotals.checkIns} />
        <MetricTile label="Completed in range" value={rangeTotals.completed} />
        <MetricTile label="Cancelled in range" value={rangeTotals.cancelled} tone="rose" />
        <MetricTile label="Avg service" value={formatMinutes(analytics.metrics.average_service_minutes)} />
      </div>

      <AnalysisSection title="Promotion Day Analysis" icon={<CalendarDays size={18} />} open={openSections.promotion} onToggle={() => toggle('promotion')}>
        <ChartGrid>
          <ChartCard title="Avg Footfall" rows={analytics.promotion_stats} labelKey="day_type" valueKey="avg_footfall" type="bar" />
          <ChartCard title="Avg Wait Time (min)" rows={analytics.promotion_stats} labelKey="day_type" valueKey="avg_wait_time" formatter={formatMinutes} type="bar" />
          <ChartCard title="Avg Items" rows={analytics.promotion_stats} labelKey="day_type" valueKey="avg_items" type="bar" />
          <ChartCard title="Service Time (min)" rows={analytics.promotion_stats} labelKey="day_type" valueKey="avg_service_time" formatter={formatMinutes} type="bar" />
          <ChartCard title="Total Cancellations" rows={analytics.promotion_stats} labelKey="day_type" valueKey="cancellations" type="bar" />
          <ChartCard title="Completion Rate (%)" rows={analytics.promotion_stats} labelKey="day_type" valueKey="completion_rate" formatter={formatPercent} type="bar" />
        </ChartGrid>
      </AnalysisSection>

      <AnalysisSection title="Segmented Analysis (Time & Day)" icon={<BarChart3 size={18} />} open={openSections.segmented} onToggle={() => toggle('segmented')}>
        <ChartGrid>
          <ChartCard title="Weekly Footfall" rows={analytics.weekly_stats} labelKey="day_name" valueKey="total_visits" type="bar" />
          <ChartCard title="Weekly Wait Time" rows={analytics.weekly_stats} labelKey="day_name" valueKey="avg_wait_time" formatter={formatMinutes} type="bar" />
          <ChartCard title="Hourly Peak Traffic" rows={activeHourly} labelKey="hour" valueKey="total_visits" labelFormatter={formatHour} type="bar" />
          <ChartCard title="Hourly Wait Time" rows={activeHourly} labelKey="hour" valueKey="avg_wait_time" labelFormatter={formatHour} formatter={formatMinutes} type="line" />
          <ChartCard title="Hourly Service Speed" rows={activeHourly} labelKey="hour" valueKey="avg_service_time" labelFormatter={formatHour} formatter={formatMinutes} type="line" />
          <ChartCard title="Cancellation Rate by Day" rows={analytics.weekly_stats} labelKey="day_name" valueKey="cancellation_rate" formatter={formatPercent} type="bar" />
        </ChartGrid>
      </AnalysisSection>

      <AnalysisSection title="Date Based Analytics" icon={<Activity size={18} />} open={openSections.date} onToggle={() => toggle('date')}>
        <ChartGrid>
          <ChartCard title="Check-ins vs Completed" rows={analytics.daily_trends} labelKey="day" valueKey="token_count" subValueKey="completed_count" type="line" />
          <ChartCard title="Daily Cancellations" rows={analytics.daily_trends} labelKey="day" valueKey="cancelled_count" type="bar" />
          <ChartCard title="Daily Avg Wait Time" rows={analytics.daily_trends} labelKey="day" valueKey="average_wait_minutes" formatter={formatMinutes} type="line" />
          <ChartCard title="Daily Avg Service Time" rows={analytics.daily_trends} labelKey="day" valueKey="average_service_minutes" formatter={formatMinutes} type="line" />
        </ChartGrid>
      </AnalysisSection>

      {/* <AnalysisSection title="Zone Based Analytics" icon={<Gauge size={18} />} open={openSections.zone} onToggle={() => toggle('zone')}>
        <ChartGrid>
          <ChartCard title="Zone-wise Trials" rows={analytics.zone_stats} labelKey="zone_name" valueKey="total_trials" type="bar" />
          <ChartCard title="Zone-wise Cancellations" rows={analytics.zone_stats} labelKey="zone_name" valueKey="cancellations" type="bar" />
          <ChartCard title="Avg Wait by Zone" rows={analytics.zone_stats} labelKey="zone_name" valueKey="avg_wait_time" formatter={formatMinutes} type="bar" />
          <ChartCard title="Avg Service by Zone" rows={analytics.zone_stats} labelKey="zone_name" valueKey="avg_service_time" formatter={formatMinutes} type="bar" />
          <ChartCard title="Items per Zone" rows={analytics.zone_stats} labelKey="zone_name" valueKey="total_items" type="bar" />
        </ChartGrid>
      </AnalysisSection> */}

      {/* <AnalysisSection title="Customer & Item Analytics" icon={<ShoppingBasket size={18} />} open={openSections.customer} onToggle={() => toggle('customer')}>
        <ChartGrid>
          <ChartCard title="Trials by Customer Type" rows={analytics.customer_type_stats} labelKey="customer_type" valueKey="count" type="bar" />
          <ChartCard title="Wait by Customer Type" rows={analytics.customer_type_stats} labelKey="customer_type" valueKey="avg_wait" formatter={formatMinutes} type="bar" />
          <ChartCard title="Service by Customer Type" rows={analytics.customer_type_stats} labelKey="customer_type" valueKey="avg_service" formatter={formatMinutes} type="bar" />
          <ChartCard title="Items by Customer Type" rows={analytics.customer_type_stats} labelKey="customer_type" valueKey="total_items" type="bar" />
          <PieLikeCard title="Cancellations by Customer Type" rows={analytics.customer_type_stats} labelKey="customer_type" valueKey="cancellations" />
          <ChartCard title="Item Buckets" rows={analytics.item_bucket_stats} labelKey="range" valueKey="count" type="bar" />
        </ChartGrid>
      </AnalysisSection> */}

      <AnalysisSection title="Item & Cancellation Analytics" icon={<AlertTriangle size={18} />} open={openSections.item} onToggle={() => toggle('item')}>
        <ChartGrid>
          <ChartCard title="Items vs Wait Time" rows={analytics.item_bucket_stats} labelKey="range" valueKey="avg_wait" formatter={formatMinutes} type="area" />
          <ChartCard title="Items vs Service Time" rows={analytics.item_bucket_stats} labelKey="range" valueKey="avg_service" formatter={formatMinutes} type="line" />
          <ChartCard title="Wait vs Cancels" rows={analytics.daily_trends} labelKey="day" valueKey="average_wait_minutes" subValueKey="cancelled_count" formatter={formatMinutes} type="line" />
          <ChartCard title="Daily Cancel Rate %" rows={analytics.daily_trends.map((row) => ({ ...row, cancel_rate: row.token_count ? (row.cancelled_count / row.token_count) * 100 : 0 }))} labelKey="day" valueKey="cancel_rate" formatter={formatPercent} type="line" showAllXAxisLabels />
        </ChartGrid>
      </AnalysisSection>
    </div>
  );
}

function ForesightsView({ analytics, foresights, metadata }) {
  if (!metadata || metadata.status !== 'READY') {
    return (
      <section className="rounded-lg border border-line bg-white p-8 text-center">
        <div className="mx-auto flex size-14 items-center justify-center rounded-lg bg-brand-blush text-brand-red">
          <BrainCircuit size={28} />
        </div>
        <h2 className="mt-4 text-xl font-semibold">AI Model Initializing...</h2>
        <p className="mt-2 text-sm text-muted">Collect more data or train the Checkout Queue ML model to unlock predictive foresights.</p>
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
        <MetricTile label="MAE" value={metadata.mae != null ? formatMinutes(metadata.mae) : '-'} />
        <MetricTile label="Churn Risk" value={foresights.churnRisk.level} tone={foresights.churnRisk.tone} />
        <MetricTile label="Training Data" value={metadata.sample_size || analytics.ml_summary.sample_size || 0} tone="amber" />
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
        <section className="rounded-lg border border-line bg-white p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h3 className="text-lg font-semibold">Key Drivers (Feature Importance)</h3>
              <p className="text-sm text-muted">Top ML factors affecting checkout service-time prediction.</p>
            </div>
            <div className="group relative text-muted">
              <Info size={18} />
              <div className="pointer-events-none absolute right-0 top-7 z-10 w-64 rounded-lg border border-line bg-white p-3 text-xs text-charcoal opacity-0 shadow-soft transition group-hover:opacity-100">
                Higher values mean the model used that feature more often when splitting decision trees.
              </div>
            </div>
          </div>
          <ChartCard title="Top 6 drivers" rows={foresights.featureImportance} labelKey="feature" valueKey="value" formatter={(value) => Number(value || 0).toFixed(3)} type="bar" dominant />
        </section>

        <section className="rounded-lg border border-line bg-white p-5">
          <h3 className="text-lg font-semibold">Zone Anomaly Status</h3>
          <div className="mt-4 space-y-3">
            {foresights.anomalySections.map((section) => (
              <div key={section.name} className="rounded-lg border border-line p-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-semibold">{section.name}</p>
                  <StatusBadge status={section.status} />
                </div>
                <p className="mt-2 text-sm text-muted">
                  Current {formatMinutes(section.currentWait)} vs predicted {formatMinutes(section.predictedWait)}
                </p>
              </div>
            ))}
          </div>
        </section>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="rounded-lg border border-line bg-white p-5">
          <h3 className="text-lg font-semibold">Predicted Wait (Next 4 Hours)</h3>
          <ChartCard title="Upcoming hours" rows={foresights.predictedWaits} labelKey="label" valueKey="value" formatter={formatMinutes} type="area" />
        </section>
        <section className="rounded-lg border border-line bg-white p-5">
          <h3 className="text-lg font-semibold">Churn Risk</h3>
          <p className="mt-3 rounded-lg border border-line bg-slate-50 p-4 text-sm text-charcoal">{foresights.churnRisk.message}</p>
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

function LiveMetric({ icon, label, value }) {
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

function ChartCard({ dominant = false, formatter = formatNumber, labelFormatter, labelKey, rows, showAllXAxisLabels = false, subValueKey, title, type, valueKey }) {
  const chartRows = normalizeChartRows(rows, labelKey, valueKey, labelFormatter);
  const hasData = chartRows.some((row) => Number(row[valueKey] || 0) > 0 || Number(row[subValueKey] || 0) > 0);
  const chartType = type === 'grouped' ? 'composed' : type;
  const showEveryXAxisLabel = showAllXAxisLabels || chartRows.length <= 8;
  const xAxisProps = {
    dataKey: '_label',
    height: showAllXAxisLabels ? 64 : showEveryXAxisLabel ? 46 : 30,
    interval: showEveryXAxisLabel ? 0 : 'preserveStartEnd',
    tick: { fontSize: 11 },
    ...(showEveryXAxisLabel ? { angle: showAllXAxisLabels ? -45 : -28, textAnchor: 'end' } : {}),
  };

  return (
    <div className="rounded-lg border border-line p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="font-semibold">{title}</h3>
        <ChartLegend type={type} />
      </div>
      <div className="mt-4 h-64 overflow-x-auto">
        <div className="h-full" style={{ minWidth: showAllXAxisLabels ? `${Math.max(720, chartRows.length * 56)}px` : '100%' }}>
        {hasData ? (
          <ResponsiveContainer width="100%" height="100%">
            {chartType === 'line' ? (
              <LineChart data={chartRows} margin={{ top: 8, right: 12, bottom: showEveryXAxisLabel ? 18 : 8, left: -18 }}>
                <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" />
                <XAxis {...xAxisProps} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip content={<ChartTooltip formatter={formatter} valueKey={valueKey} subValueKey={subValueKey} />} />
                <Line type="monotone" dataKey={valueKey} stroke={LINE_COLOR} strokeWidth={3} dot={{ r: 3 }} activeDot={{ r: 5 }} />
                {subValueKey ? <Line type="monotone" dataKey={subValueKey} stroke={SECONDARY_LINE_COLOR} strokeWidth={3} dot={{ r: 3 }} /> : null}
              </LineChart>
            ) : chartType === 'area' ? (
              <AreaChart data={chartRows} margin={{ top: 8, right: 12, bottom: showEveryXAxisLabel ? 18 : 8, left: -18 }}>
                <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" />
                <XAxis {...xAxisProps} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip content={<ChartTooltip formatter={formatter} valueKey={valueKey} subValueKey={subValueKey} />} />
                <Area type="monotone" dataKey={valueKey} stroke={LINE_COLOR} fill={COLORS[0]} fillOpacity={0.2} strokeWidth={3} />
              </AreaChart>
            ) : chartType === 'composed' ? (
              <ComposedChart data={chartRows} margin={{ top: 8, right: 12, bottom: showEveryXAxisLabel ? 18 : 8, left: -18 }}>
                <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" />
                <XAxis {...xAxisProps} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip content={<ChartTooltip formatter={formatter} valueKey={valueKey} subValueKey={subValueKey} />} />
                <RechartsLegend wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey={valueKey} name={title} fill={COLORS[0]} radius={[6, 6, 0, 0]} />
                {subValueKey ? <Line type="monotone" dataKey={subValueKey} name={formatDataKey(subValueKey)} stroke={SECONDARY_LINE_COLOR} strokeWidth={3} dot={{ r: 3 }} /> : null}
              </ComposedChart>
            ) : (
              <BarChart data={chartRows} margin={{ top: 8, right: 12, bottom: showEveryXAxisLabel ? 18 : 8, left: -18 }}>
                <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" />
                <XAxis {...xAxisProps} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip content={<ChartTooltip formatter={formatter} valueKey={valueKey} subValueKey={subValueKey} />} />
                <Bar dataKey={valueKey} fill="#ff3b30" radius={[6, 6, 0, 0]}>
                  {chartRows.map((row, index) => (
                    <Cell key={`${title}-${row._label}`} fill={getBarColor(row, index, dominant)} />
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
  const label = type === 'grouped' ? 'Grouped' : type === 'area' ? 'Area' : type === 'line' ? 'Line' : type === 'pie' ? 'Pie' : 'Bar';
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
      <p className="mt-1 text-brand-red">
        {formatDataKey(valueKey)}: {formatter(primary?.value || 0)}
      </p>
      {secondary ? <p className="mt-1 text-blue-700">{formatDataKey(subValueKey)}: {formatNumber(secondary.value)}</p> : null}
    </div>
  );
}

function EmptyChartState() {
  return <div className="grid h-full place-items-center rounded-lg bg-slate-50 text-sm text-muted">No chart data yet</div>;
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

function LoadingState() {
  return <section className="rounded-lg border border-line bg-white p-8 text-center text-sm text-muted">Loading dashboard...</section>;
}

function EmptyState() {
  return <section className="rounded-lg border border-line bg-white p-8 text-center text-sm text-muted">Select a store to load dashboard analytics.</section>;
}
