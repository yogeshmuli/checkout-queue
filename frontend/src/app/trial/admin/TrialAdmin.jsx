import { useEffect, useMemo, useState } from 'react';
import { Route, Routes, useSearchParams } from 'react-router-dom';

import { getTrialConfig, updateTrialConfig } from '../../../api/trial/configApi.js';
import { listTrialQueueTokens } from '../../../api/trial/queueApi.js';
import { createTrialStudio, listTrialStudios } from '../../../api/trial/studiosApi.js';
import { createTrialZone, listTrialZones } from '../../../api/trial/zonesApi.js';
import { listStores } from '../../../api/checkout/storeApi.js';
import { getErrorMessage, showApiErrorToast } from '../../../api/httpClient.js';
import { Field, Select, StatCard } from '../../common/FormAndStatePrimitives.jsx';
import { SectionHeader } from '../../common/SectionHeader.jsx';

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

  return { stores, zones, studios, tokens, message, setMessage, loadAll };
}

export function TrialAdmin() {
  const data = useTrialAdminData();
  return (
    <Routes>
      <Route index element={<TrialOverview {...data} />} />
      <Route path="zones" element={<TrialZones {...data} />} />
      <Route path="studios" element={<TrialStudios {...data} />} />
      <Route path="config" element={<TrialConfig stores={data.stores} setMessage={data.setMessage} />} />
      <Route path="queue" element={<TrialQueue {...data} />} />
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

function TrialZones({ stores, zones, loadAll, setMessage }) {
  const [form, setForm] = useState({ store_id: '', name: '' });
  const storeOptions = [{ label: 'Select store', value: '' }, ...stores.map((store) => ({ label: store.name, value: String(store.id) }))];
  async function submit(event) {
    event.preventDefault();
    try {
      await createTrialZone({ store_id: Number(form.store_id), name: form.name });
      setForm({ store_id: '', name: '' });
      setMessage('Trial zone saved.');
      await loadAll();
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    }
  }
  return (
    <div className="space-y-5">
      <SectionHeader eyebrow="Trial setup" title="Trial zones" />
      <form onSubmit={submit} className="grid gap-3 rounded-lg border border-line bg-white p-4 md:grid-cols-3">
        <Select label="Store" value={form.store_id} options={storeOptions} onChange={(value) => setForm({ ...form, store_id: value })} />
        <Field label="Zone name" value={form.name} onChange={(value) => setForm({ ...form, name: value })} />
        <button className="self-end rounded-lg bg-brand-red px-4 py-3 text-sm font-semibold text-white">Save zone</button>
      </form>
      <List rows={zones.map((zone) => `${zone.name} | Store #${zone.store_id} | ${zone.is_active ? 'Active' : 'Inactive'}`)} empty="No trial zones yet." />
    </div>
  );
}

function TrialStudios({ zones, studios, loadAll, setMessage }) {
  const [form, setForm] = useState({ trial_zone_id: '', name: '' });
  const zoneOptions = [{ label: 'Select trial zone', value: '' }, ...zones.map((zone) => ({ label: zone.name, value: String(zone.id) }))];
  async function submit(event) {
    event.preventDefault();
    try {
      await createTrialStudio({ trial_zone_id: Number(form.trial_zone_id), name: form.name });
      setForm({ trial_zone_id: '', name: '' });
      setMessage('Studio saved.');
      await loadAll();
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    }
  }
  return (
    <div className="space-y-5">
      <SectionHeader eyebrow="Trial setup" title="Studios" />
      <form onSubmit={submit} className="grid gap-3 rounded-lg border border-line bg-white p-4 md:grid-cols-3">
        <Select label="Trial zone" value={form.trial_zone_id} options={zoneOptions} onChange={(value) => setForm({ ...form, trial_zone_id: value })} />
        <Field label="Studio name" value={form.name} onChange={(value) => setForm({ ...form, name: value })} />
        <button className="self-end rounded-lg bg-brand-red px-4 py-3 text-sm font-semibold text-white">Save studio</button>
      </form>
      <List rows={studios.map((studio) => `${studio.name || `Studio #${studio.id}`} | Zone #${studio.trial_zone_id} | ${studio.is_active ? 'Active' : 'Inactive'}`)} empty="No studios yet." />
    </div>
  );
}

function TrialConfig({ stores, setMessage }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const storeId = searchParams.get('store_id') || '';
  const [form, setForm] = useState({ token_id_prefix: '', base_service_minutes: 8, per_unit_service_minutes: 1, min_service_minutes: 10 });
  const storeOptions = [{ label: 'Select store', value: '' }, ...stores.map((store) => ({ label: store.name, value: String(store.id) }))];

  useEffect(() => {
    if (!storeId) return;
    getTrialConfig(storeId)
      .then((config) => setForm({
        token_id_prefix: config.token_id_prefix || '',
        base_service_minutes: config.base_service_minutes,
        per_unit_service_minutes: config.per_unit_service_minutes,
        min_service_minutes: config.min_service_minutes,
      }))
      .catch((error) => setMessage(getErrorMessage(error)));
  }, [storeId, setMessage]);

  async function submit(event) {
    event.preventDefault();
    try {
      await updateTrialConfig(storeId, {
        token_id_prefix: form.token_id_prefix || null,
        base_service_minutes: Number(form.base_service_minutes),
        per_unit_service_minutes: Number(form.per_unit_service_minutes),
        min_service_minutes: Number(form.min_service_minutes),
      });
      setMessage('Trial config saved.');
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    }
  }

  return (
    <div className="space-y-5">
      <SectionHeader eyebrow="Trial rules" title="Trial config" />
      <form onSubmit={submit} className="grid gap-3 rounded-lg border border-line bg-white p-4 md:grid-cols-2">
        <Select label="Store" value={storeId} options={storeOptions} onChange={(value) => setSearchParams(value ? { store_id: value } : {})} />
        <Field label="Token prefix" value={form.token_id_prefix} onChange={(value) => setForm({ ...form, token_id_prefix: value })} />
        <Field label="Base minutes" value={String(form.base_service_minutes)} onChange={(value) => setForm({ ...form, base_service_minutes: value })} />
        <Field label="Per unit minutes" value={String(form.per_unit_service_minutes)} onChange={(value) => setForm({ ...form, per_unit_service_minutes: value })} />
        <Field label="Minimum minutes" value={String(form.min_service_minutes)} onChange={(value) => setForm({ ...form, min_service_minutes: value })} />
        <button disabled={!storeId} className="self-end rounded-lg bg-brand-red px-4 py-3 text-sm font-semibold text-white disabled:opacity-50">Save config</button>
      </form>
    </div>
  );
}

function TrialQueue({ tokens }) {
  const rows = useMemo(() => tokens.map((token) => `${token.token_number} | ${token.phone_number} | ${token.status} | Wait ${token.estimated_wait_minutes}m`), [tokens]);
  return (
    <div className="space-y-5">
      <SectionHeader eyebrow="Trial operations" title="Live trial queue" />
      <List rows={rows} empty="No trial tokens found." />
    </div>
  );
}

function List({ rows, empty }) {
  return (
    <div className="rounded-lg border border-line bg-white">
      {rows.length ? rows.map((row) => <p key={row} className="border-b border-line px-4 py-3 text-sm last:border-b-0">{row}</p>) : <p className="p-4 text-sm text-muted">{empty}</p>}
    </div>
  );
}
