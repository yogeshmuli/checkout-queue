import { useEffect, useMemo, useState } from 'react';

import { getTrialTokenStatus, joinTrialQueue, listTrialStoreZones } from '../../../api/trial/queueApi.js';
import { getErrorMessage, showApiErrorToast } from '../../../api/httpClient.js';
import { Field, Select } from '../../common/FormAndStatePrimitives.jsx';
import { SectionHeader } from '../../common/SectionHeader.jsx';

export function TrialCustomer() {
  const [stores, setStores] = useState([]);
  const [form, setForm] = useState({ store_id: '', trial_zone_id: '', phone_number: '', item_count: '', customer_type: 'regular' });
  const [token, setToken] = useState(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    listTrialStoreZones()
      .then(setStores)
      .catch((error) => {
        showApiErrorToast(error);
        setMessage(getErrorMessage(error));
      });
  }, []);

  const selectedStore = stores.find((store) => String(store.id) === String(form.store_id));
  const storeOptions = [{ label: 'Select store', value: '' }, ...stores.map((store) => ({ label: store.name, value: String(store.id) }))];
  const zoneOptions = [{ label: 'Select trial zone', value: '' }, ...((selectedStore?.zones || []).map((zone) => ({ label: zone.name, value: String(zone.id) })))];

  async function submit(event) {
    event.preventDefault();
    setMessage('');
    try {
      const created = await joinTrialQueue({
        store_id: Number(form.store_id),
        trial_zone_id: form.trial_zone_id ? Number(form.trial_zone_id) : null,
        phone_number: form.phone_number,
        item_count: form.item_count ? Number(form.item_count) : null,
        customer_type: form.customer_type || 'regular',
      });
      setToken(await getTrialTokenStatus({ token_id: created.token_id }));
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    }
  }

  const tokenDetails = useMemo(() => {
    if (!token) return [];
    return [
      ['Token', token.token_number],
      ['Status', token.status],
      ['Position', token.position],
      ['Estimated wait', `${token.estimated_wait_minutes} min`],
      ['Studio', token.assigned_studio_id ? `#${token.assigned_studio_id}` : 'Pending'],
    ];
  }, [token]);

  return (
    <main className="min-h-screen bg-brand-blush px-4 py-6 text-ink">
      <section className="mx-auto max-w-xl space-y-5">
        <SectionHeader eyebrow="Trial Queue" title="Create trial token" />
        {message ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{message}</p> : null}
        <form onSubmit={submit} className="space-y-3 rounded-lg bg-white p-4 shadow-soft">
          <Select label="Store" value={form.store_id} options={storeOptions} onChange={(value) => setForm({ ...form, store_id: value, trial_zone_id: '' })} />
          <Select label="Trial zone" value={form.trial_zone_id} options={zoneOptions} onChange={(value) => setForm({ ...form, trial_zone_id: value })} />
          <Field label="Phone number" value={form.phone_number} onChange={(value) => setForm({ ...form, phone_number: value })} />
          <Field label="Item count" value={form.item_count} onChange={(value) => setForm({ ...form, item_count: value })} />
          <button className="w-full rounded-lg bg-brand-red px-4 py-3 text-sm font-semibold text-white">Join trial queue</button>
        </form>
        {token ? (
          <div className="rounded-lg bg-white p-4 shadow-soft">
            {tokenDetails.map(([label, value]) => (
              <div key={label} className="flex justify-between border-b border-line py-2 text-sm last:border-b-0">
                <span className="text-muted">{label}</span>
                <span className="font-medium">{value}</span>
              </div>
            ))}
          </div>
        ) : null}
      </section>
    </main>
  );
}
