import { RefreshCw, Save } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { getErrorMessage, showApiErrorToast } from '../../../../api/httpClient.js';
import { getTrialConfig, updateTrialConfig } from '../../../../api/trial/configApi.js';
import { listStores } from '../../../../api/trial/storeApi.js';
import { Select } from '../../../common/FormAndStatePrimitives.jsx';
import { SectionHeader } from '../../../common/SectionHeader.jsx';

const emptyConfig = {
  token_id_prefix: '',
  base_service_minutes: '8',
  per_unit_service_minutes: '1',
  min_service_minutes: '10',
};

export function Config() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [stores, setStores] = useState([]);
  const [form, setForm] = useState(emptyConfig);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [storesLoaded, setStoresLoaded] = useState(false);
  const [formErrors, setFormErrors] = useState({});
  const storeId = searchParams.get('store_id') || '';

  const storeOptions = stores.length
    ? stores.map((store) => ({
      label: `${store.name} (${store.store_number})`,
      value: String(store.id),
    }))
    : [{ label: 'No stores found', value: '' }];

  const selectedStore = useMemo(() => stores.find((store) => String(store.id) === storeId), [storeId, stores]);

  function setStoreId(value) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) {
        next.set('store_id', value);
      } else {
        next.delete('store_id');
      }
      return next;
    });
    setMessage('');
    setFormErrors({});
  }

  function toForm(config) {
    return {
      token_id_prefix: config.token_id_prefix || '',
      base_service_minutes: String(config.base_service_minutes ?? 8),
      per_unit_service_minutes: String(config.per_unit_service_minutes ?? 1),
      min_service_minutes: String(config.min_service_minutes ?? 10),
    };
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

  const loadConfig = useCallback(async () => {
    if (!storeId) {
      setForm(emptyConfig);
      return;
    }

    setLoading(true);
    setMessage('');
    try {
      setForm(toForm(await getTrialConfig(storeId)));
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
    loadConfig();
  }, [loadConfig]);

  function setFormField(field, value) {
    const nextValue = field === 'token_id_prefix' ? value.toUpperCase().replace(/[^A-Z0-9_-]/g, '').slice(0, 20) : value;
    setForm((prev) => ({ ...prev, [field]: nextValue }));
    setFormErrors((prev) => {
      const nextErrors = { ...prev };
      delete nextErrors[field];
      return nextErrors;
    });
  }

  function validateForm() {
    const errors = {};
    const base = Number(form.base_service_minutes);
    const perUnit = Number(form.per_unit_service_minutes);
    const min = Number(form.min_service_minutes);

    if (!Number.isFinite(base) || base < 0 || base > 240) {
      errors.base_service_minutes = 'Base service minutes must be between 0 and 240.';
    }
    if (!Number.isFinite(perUnit) || perUnit < 0 || perUnit > 60) {
      errors.per_unit_service_minutes = 'Per unit service minutes must be between 0 and 60.';
    }
    if (!Number.isFinite(min) || min < 1 || min > 240) {
      errors.min_service_minutes = 'Minimum service minutes must be between 1 and 240.';
    }

    return errors;
  }

  async function submitConfig(event) {
    event.preventDefault();
    if (!storeId) {
      setMessage('Select a store before saving config.');
      return;
    }

    const errors = validateForm();
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      setMessage('Please fix validation errors before saving.');
      return;
    }

    setLoading(true);
    setMessage('');
    try {
      const payload = {
        token_id_prefix: form.token_id_prefix.trim() || null,
        base_service_minutes: Number(form.base_service_minutes),
        per_unit_service_minutes: Number(form.per_unit_service_minutes),
        min_service_minutes: Number(form.min_service_minutes),
      };
      setForm(toForm(await updateTrialConfig(storeId, payload)));
      setMessage('Trial queue config saved');
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
        <SectionHeader eyebrow="Trial queue config" title="Token and service-time rules" />
        <div className="mt-5 max-w-xl">
          <Select label="Store" value={storeId} options={storeOptions} onChange={setStoreId} disabled={!stores.length} />
        </div>
      </section>

      {storesLoaded && !stores.length ? <NoStoresCard /> : null}

      {selectedStore ? (
      <section className="rounded-lg border border-line bg-white p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-red">Trial behavior</p>
            <h2 className="mt-1 text-xl font-semibold">{selectedStore ? selectedStore.name : 'Select a store'}</h2>
          </div>
          <button
            type="button"
            onClick={loadConfig}
            disabled={loading || !storeId}
            className="inline-flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-sm font-medium text-charcoal disabled:opacity-50"
          >
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>

        <form className="mt-5 grid gap-4 lg:grid-cols-2" onSubmit={submitConfig}>
          <Field
            label="Token ID prefix"
            value={form.token_id_prefix}
            onChange={(value) => setFormField('token_id_prefix', value)}
            placeholder="Example: TRIAL"
          />
          <Field
            label="Base service minutes"
            value={form.base_service_minutes}
            onChange={(value) => setFormField('base_service_minutes', value)}
            error={formErrors.base_service_minutes}
            type="number"
            min="0"
            step="1"
          />
          <Field
            label="Per unit service minutes"
            value={form.per_unit_service_minutes}
            onChange={(value) => setFormField('per_unit_service_minutes', value)}
            error={formErrors.per_unit_service_minutes}
            type="number"
            min="0"
            step="0.01"
          />
          <Field
            label="Minimum service minutes"
            value={form.min_service_minutes}
            onChange={(value) => setFormField('min_service_minutes', value)}
            error={formErrors.min_service_minutes}
            type="number"
            min="1"
            step="1"
          />

          {message ? <p className="rounded-lg bg-brand-blush px-3 py-2 text-sm text-charcoal lg:col-span-2">{message}</p> : null}

          <div className="lg:col-span-2">
            <button
              type="submit"
              disabled={loading || !storeId}
              className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-brand-red px-4 py-3 text-sm font-semibold text-white disabled:opacity-60 sm:w-auto"
            >
              <Save size={17} />
              Save config
            </button>
          </div>
        </form>
      </section>
      ) : null}
    </div>
  );
}

function NoStoresCard() {
  return (
    <section className="rounded-lg border border-dashed border-line bg-white p-5">
      <p className="text-sm font-medium text-charcoal">No stores available.</p>
      <p className="mt-1 text-sm text-muted">Create a store first, then trial queue configuration will appear here.</p>
    </section>
  );
}

function Field({ label, value, onChange, error, type = 'text', placeholder, min, step }) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-charcoal">{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        type={type}
        placeholder={placeholder}
        min={min}
        step={step}
        className={`mt-1 w-full rounded-lg border px-3 py-2.5 outline-none focus:ring-2 ${
          error ? 'border-rose-400 focus:border-rose-500 focus:ring-rose-100' : 'border-line focus:border-brand-red focus:ring-brand-soft'
        }`}
      />
      {error ? <p className="mt-1 text-xs text-rose-700">{error}</p> : null}
    </label>
  );
}
