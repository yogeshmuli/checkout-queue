import { RefreshCw, Save, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';

import { createStore, deleteStore, listStores } from '../../api/storeApi.js';
import { getErrorMessage } from '../../api/httpClient.js';
import { SectionHeader } from '../common/SectionHeader.jsx';

const emptyStore = {
  store_number: '',
  name: '',
  address: '',
  manager_name: '',
  manager_phone: '',
  spoc_name: '',
  spoc_phone: '',
  is_active: true,
};

export function AdminStores() {
  const [stores, setStores] = useState([]);
  const [form, setForm] = useState(emptyStore);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  async function loadStores() {
    setLoading(true);
    setMessage('');
    try {
      setStores(await listStores({ include_inactive: true }));
    } catch (error) {
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadStores();
  }, []);

  async function submitStore(event) {
    event.preventDefault();
    setLoading(true);
    setMessage('');
    try {
      await createStore({
        ...form,
        manager_phone: form.manager_phone || null,
        spoc_phone: form.spoc_phone || null,
      });
      setForm(emptyStore);
      setMessage('Store created');
      await loadStores();
    } catch (error) {
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function deactivateStore(storeId) {
    setLoading(true);
    setMessage('');
    try {
      await deleteStore(storeId);
      setMessage('Store deactivated');
      await loadStores();
    } catch (error) {
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[420px_1fr]">
      <section className="rounded-lg border border-line bg-white p-5">
        <SectionHeader eyebrow="Store setup" title="Create store" />
        <form className="mt-5 space-y-4" onSubmit={submitStore}>
          <Field label="Store number" value={form.store_number} onChange={(store_number) => setForm({ ...form, store_number })} />
          <Field label="Store name" value={form.name} onChange={(name) => setForm({ ...form, name })} />
          <Field label="Address" value={form.address} onChange={(address) => setForm({ ...form, address })} />
          <Field label="Manager name" value={form.manager_name} onChange={(manager_name) => setForm({ ...form, manager_name })} />
          <Field label="Manager phone" value={form.manager_phone} onChange={(manager_phone) => setForm({ ...form, manager_phone })} />
          <Field label="SPOC name" value={form.spoc_name} onChange={(spoc_name) => setForm({ ...form, spoc_name })} />
          <Field label="SPOC phone" value={form.spoc_phone} onChange={(spoc_phone) => setForm({ ...form, spoc_phone })} />
          {message ? <p className="rounded-lg bg-brand-blush px-3 py-2 text-sm text-charcoal">{message}</p> : null}
          <button
            type="submit"
            disabled={loading}
            className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-brand-red px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
          >
            <Save size={17} />
            Save store
          </button>
        </form>
      </section>

      <section className="rounded-lg border border-line bg-white">
        <div className="flex items-center justify-between border-b border-line p-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-red">Store directory</p>
            <h2 className="mt-1 text-xl font-semibold">Configured stores</h2>
          </div>
          <button type="button" onClick={loadStores} className="rounded-lg border border-line p-2 text-charcoal hover:border-brand-red" title="Refresh stores">
            <RefreshCw size={18} />
          </button>
        </div>
        <div className="divide-y divide-brand-soft">
          {stores.length === 0 ? (
            <p className="p-5 text-sm text-muted">No stores loaded.</p>
          ) : (
            stores.map((store) => (
              <div key={store.id} className="grid gap-3 p-5 lg:grid-cols-[1fr_auto]">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-semibold">{store.name}</h3>
                    <span className="rounded-full bg-brand-blush px-2 py-1 text-xs text-charcoal">{store.store_number}</span>
                    <span className={`rounded-full px-2 py-1 text-xs ${store.is_active ? 'bg-brand-blush text-success' : 'bg-rose-50 text-rose-700'}`}>
                      {store.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-charcoal">{store.address || 'No address'}</p>
                </div>
                <button
                  type="button"
                  onClick={() => deactivateStore(store.id)}
                  className="inline-flex items-center justify-center gap-2 rounded-lg border border-rose-200 px-3 py-2 text-sm font-medium text-rose-700 disabled:opacity-50"
                  disabled={!store.is_active || loading}
                >
                  <Trash2 size={16} />
                  Deactivate
                </button>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}

function Field({ label, value, onChange }) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-charcoal">{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1 w-full rounded-lg border border-line px-3 py-2.5 outline-none focus:border-brand-red focus:ring-2 focus:ring-brand-soft"
      />
    </label>
  );
}

