import { RefreshCw, Save } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { getErrorMessage, showApiErrorToast } from '../../api/httpClient.js';
import { listNotificationLogs, getNotificationConfig, updateNotificationConfig } from '../../api/notificationApi.js';
import { listStores } from '../../api/checkout/storeApi.js';
import { Select } from './FormAndStatePrimitives.jsx';
import { SectionHeader } from './SectionHeader.jsx';

const defaultConfig = {
  is_enabled: false,
  notify_on_called: true,
  notify_on_next_soon: true,
  called_message_template: 'Your token {token_number} has been called. Please proceed to {service_point_name}.',
  next_soon_message_template: 'Your token {token_number} will be called soon. Please stay nearby.',
};

export function NotificationSettings({ moduleLabel = 'Queue' }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [stores, setStores] = useState([]);
  const [form, setForm] = useState(defaultConfig);
  const [logs, setLogs] = useState([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [storesLoaded, setStoresLoaded] = useState(false);
  const storeId = searchParams.get('store_id') || '';

  const selectedStore = useMemo(() => stores.find((store) => String(store.id) === String(storeId)), [storeId, stores]);
  const storeOptions = stores.length
    ? stores.map((store) => ({ label: `${store.name} (${store.store_number})`, value: String(store.id) }))
    : [{ label: 'No stores found', value: '' }];

  function setStoreId(value) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) next.set('store_id', value);
      else next.delete('store_id');
      return next;
    });
    setMessage('');
  }

  const loadStores = useCallback(async () => {
    try {
      setStores(await listStores({ include_inactive: true }));
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setStoresLoaded(true);
    }
  }, []);

  const loadNotificationData = useCallback(async () => {
    if (!storeId) {
      setForm(defaultConfig);
      setLogs([]);
      return;
    }

    setLoading(true);
    setMessage('');
    try {
      const [config, logRows] = await Promise.all([getNotificationConfig(storeId), listNotificationLogs(storeId, { limit: 50 })]);
      setForm({
        is_enabled: Boolean(config.is_enabled),
        notify_on_called: Boolean(config.notify_on_called),
        notify_on_next_soon: Boolean(config.notify_on_next_soon),
        called_message_template: config.called_message_template || defaultConfig.called_message_template,
        next_soon_message_template: config.next_soon_message_template || defaultConfig.next_soon_message_template,
      });
      setLogs(logRows);
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [storeId]);

  useEffect(() => {
    loadStores();
  }, [loadStores]);

  useEffect(() => {
    if (!stores.length) return;
    if (stores.some((store) => String(store.id) === String(storeId))) return;
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('store_id', String(stores[0].id));
      return next;
    });
  }, [setSearchParams, storeId, stores]);

  useEffect(() => {
    loadNotificationData();
  }, [loadNotificationData]);

  function setField(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function submitConfig(event) {
    event.preventDefault();
    if (!storeId) {
      setMessage('Select a store before saving notification settings.');
      return;
    }

    setLoading(true);
    setMessage('');
    try {
      const saved = await updateNotificationConfig(storeId, form);
      setForm({
        is_enabled: Boolean(saved.is_enabled),
        notify_on_called: Boolean(saved.notify_on_called),
        notify_on_next_soon: Boolean(saved.notify_on_next_soon),
        called_message_template: saved.called_message_template,
        next_soon_message_template: saved.next_soon_message_template,
      });
      setMessage('Notification settings saved');
      setLogs(await listNotificationLogs(storeId, { limit: 50 }));
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
        <SectionHeader eyebrow={`${moduleLabel} notifications`} title="Customer SMS settings" />
        <div className="mt-5 max-w-xl">
          <Select label="Store" value={storeId} options={storeOptions} onChange={setStoreId} disabled={!stores.length} />
        </div>
      </section>

      {storesLoaded && !stores.length ? (
        <section className="rounded-lg border border-dashed border-line bg-white p-5">
          <p className="text-sm font-medium text-charcoal">No stores available.</p>
          <p className="mt-1 text-sm text-muted">Create a store first, then notification settings will appear here.</p>
        </section>
      ) : null}

      {selectedStore ? (
      <>
      <section className="rounded-lg border border-line bg-white p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-red">Notification config</p>
            <h2 className="mt-1 text-xl font-semibold">{selectedStore ? selectedStore.name : 'Select a store'}</h2>
          </div>
          <button
            type="button"
            onClick={loadNotificationData}
            disabled={loading || !storeId}
            className="inline-flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-sm font-medium text-charcoal disabled:opacity-50"
          >
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>

        {!form.is_enabled ? <p className="mt-4 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900">Customer notifications are currently off for this store.</p> : null}

        <form className="mt-5 space-y-4" onSubmit={submitConfig}>
          <label className="flex items-center justify-between rounded-lg border border-line px-3 py-3">
            <span className="text-sm font-medium text-charcoal">Enable customer notifications</span>
            <input type="checkbox" checked={form.is_enabled} onChange={(event) => setField('is_enabled', event.target.checked)} className="size-5 accent-brand-red" />
          </label>
          <div className="grid gap-3 md:grid-cols-2">
            <label className="flex items-center justify-between rounded-lg border border-line px-3 py-3">
              <span className="text-sm font-medium text-charcoal">Notify when called</span>
              <input type="checkbox" checked={form.notify_on_called} onChange={(event) => setField('notify_on_called', event.target.checked)} className="size-5 accent-brand-red" />
            </label>
            <label className="flex items-center justify-between rounded-lg border border-line px-3 py-3">
              <span className="text-sm font-medium text-charcoal">Notify next soon</span>
              <input type="checkbox" checked={form.notify_on_next_soon} onChange={(event) => setField('notify_on_next_soon', event.target.checked)} className="size-5 accent-brand-red" />
            </label>
          </div>
          <TemplateField label="Called message" value={form.called_message_template} onChange={(value) => setField('called_message_template', value)} />
          <TemplateField label="Next-soon message" value={form.next_soon_message_template} onChange={(value) => setField('next_soon_message_template', value)} />
          <p className="text-xs text-muted">Variables: {'{token_number}'}, {'{store_name}'}, {'{service_point_name}'}, {'{module_name}'}</p>
          {message ? <p className="rounded-lg bg-brand-blush px-3 py-2 text-sm text-charcoal">{message}</p> : null}
          <button type="submit" disabled={loading || !storeId} className="inline-flex items-center gap-2 rounded-lg bg-brand-red px-4 py-3 text-sm font-semibold text-white disabled:opacity-60">
            <Save size={17} />
            Save notification settings
          </button>
        </form>
      </section>

      <section className="rounded-lg border border-line bg-white">
        <div className="border-b border-line p-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand-red">Recent logs</p>
          <h2 className="mt-1 text-xl font-semibold">Notification activity</h2>
        </div>
        <div className="divide-y divide-brand-soft">
          {logs.length ? (
            logs.map((log) => (
              <div key={log.id} className="grid gap-2 p-5 md:grid-cols-[1fr_auto]">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold">{log.notification_type}</span>
                    <span className="rounded-full bg-brand-blush px-2 py-1 text-xs text-charcoal">{log.module_type}</span>
                    <span className={`rounded-full px-2 py-1 text-xs ${log.status === 'SENT' ? 'bg-emerald-50 text-emerald-700' : log.status === 'FAILED' ? 'bg-rose-50 text-rose-700' : 'bg-amber-50 text-amber-800'}`}>{log.status}</span>
                  </div>
                  <p className="mt-1 text-sm text-charcoal">{log.message || log.error_message || 'No message body'}</p>
                  <p className="mt-1 text-xs text-muted">Phone: {log.phone_number} · Token #{log.token_id}</p>
                </div>
                <p className="text-sm text-muted">{new Date(log.created_at).toLocaleString()}</p>
              </div>
            ))
          ) : (
            <p className="p-5 text-sm text-muted">No notification logs for this store.</p>
          )}
        </div>
      </section>
      </>
      ) : null}
    </div>
  );
}

function TemplateField({ label, value, onChange }) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-charcoal">{label}</span>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        rows={3}
        maxLength={500}
        className="mt-1 w-full rounded-lg border border-line px-3 py-2.5 outline-none focus:border-brand-red focus:ring-2 focus:ring-brand-soft"
      />
    </label>
  );
}
