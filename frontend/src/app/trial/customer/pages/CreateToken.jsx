import { ArrowLeft, ShoppingBasket } from 'lucide-react';
import { useMemo, useRef, useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { toast } from 'react-toastify';

import brandLogo from '../../../../assets/images/equilateral_logo.png';
import { getErrorMessage, showApiErrorToast } from '../../../../api/httpClient.js';
import { joinTrialQueue, listTrialStoreZones } from '../../../../api/trial/queueApi.js';
import { Field, Select } from '../../../common/FormAndStatePrimitives.jsx';
import { useQueueStore } from '../../../../store/queueStore.js';
import { defaultForm } from '../utils/customerUtils.js';

export function CreateToken() {
  const [form, setForm] = useState(defaultForm);
  const [stores, setStores] = useState([]);
  const [storesLoading, setStoresLoading] = useState(false);
  const [storesLoaded, setStoresLoaded] = useState(false);
  const invalidQrRedirectedRef = useRef(false);
  const location = useLocation();
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const { setLastToken } = useQueueStore();
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const store_id = params.get('store_id');
    const trial_zone_id = params.get('trial_zone_id');
    setForm((f) => ({
      ...f,
      store_id: store_id || f.store_id,
      trial_zone_id: trial_zone_id || f.trial_zone_id,
    }));
  }, [location.search]);

  useEffect(() => {
    async function loadStoreNames() {
      setStoresLoading(true);
      setStoresLoaded(false);
      try {
        setStores(await listTrialStoreZones());
        setStoresLoaded(true);
      } catch (error) {
        showApiErrorToast(error);
        setMessage(getErrorMessage(error));
      } finally {
        setStoresLoading(false);
      }
    }

    loadStoreNames();
  }, []);

  const selectedStore = useMemo(() => stores.find((store) => String(store.id) === String(form.store_id)), [form.store_id, stores]);
  const selectedZone = useMemo(
    () => selectedStore?.zones?.find((zone) => String(zone.id) === String(form.trial_zone_id)),
    [form.trial_zone_id, selectedStore]
  );

  useEffect(() => {
    if (!storesLoaded || invalidQrRedirectedRef.current) return;
    if (!form.store_id && !form.trial_zone_id) return;

    const missingStore = Boolean(form.store_id) && !selectedStore;
    const missingZone = Boolean(form.trial_zone_id) && !selectedZone;
    if (!missingStore && !missingZone) return;

    invalidQrRedirectedRef.current = true;
    const warning = missingStore
      ? 'Selected store is no longer available. Please scan a valid trial QR code.'
      : 'Selected trial zone is no longer available. Please scan a valid trial QR code.';
    toast.warn(warning, { toastId: 'trial-invalid-customer-qr' });
    navigate('/app/trial/customer', { replace: true, state: { warning } });
  }, [form.store_id, form.trial_zone_id, navigate, selectedStore, selectedZone, storesLoaded]);

  const storeLabel = selectedStore?.name || (form.store_id ? `Store #${form.store_id}` : 'Store not selected');
  const zoneLabel = selectedZone
    ? selectedZone.name
    : form.trial_zone_id
      ? `Zone #${form.trial_zone_id}`
      : 'No trial zone selected';

  async function submitJoin(event) {
    event.preventDefault();
    setLoading(true);
    setMessage('');

    if (!form.customer_gender) {
      setLoading(false);
      setMessage('Please select gender.');
      return;
    }

    if (selectedZone?.gender && selectedZone.gender !== 'UNISEX' && selectedZone.gender !== form.customer_gender) {
      setLoading(false);
      setMessage(`Selected trial zone is for ${selectedZone.gender.toLowerCase()} customers.`);
      return;
    }

    try {
      const token = await joinTrialQueue({
        store_id: Number(form.store_id),
        trial_zone_id: form.trial_zone_id ? Number(form.trial_zone_id) : null,
        phone_number: form.phone_number,
        item_count: form.item_count ? Number(form.item_count) : null,
        customer_gender: form.customer_gender,
        customer_type: form.customer_type || 'regular',
      });
      setLastToken(token);
      navigate(`/app/trial/customer/status/${token.token_id}`);
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen px-4 py-5 animate-fadeIn">
      <section className="mx-auto max-w-md">
        <header className="customer-sticky-header glass-panel rounded-xl border border-white/30 bg-brand-red p-4 text-white shadow-soft">
          <div className="flex items-start gap-3">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="flex size-10 shrink-0 items-center justify-center rounded-lg border border-white/30 text-white"
              aria-label="Go back"
              title="Go back"
            >
              <ArrowLeft size={18} />
            </button>
            <Link to="/" className="flex h-12 w-28 shrink-0 items-center justify-center rounded-md border border-white/40 bg-white/95 p-1 shadow-sm" aria-label="Go to landing page">
              <img src={brandLogo} alt="Trial Queue logo" className="h-full w-full object-cover" />
            </Link>
            <div className="min-w-0">
              <p className="text-xs font-medium uppercase tracking-wide text-white/90 sm:text-sm">Trial queue</p>
              <h1 className="text-xl font-semibold leading-tight sm:text-2xl">Create token</h1>
            </div>
          </div>
          <p className="mt-3 text-sm text-white/95">{storesLoading ? 'Loading store details...' : `${storeLabel} · ${zoneLabel}`}</p>
        </header>

        <form className="mt-5 space-y-4 rounded-lg bg-white p-5 text-ink shadow-soft" onSubmit={submitJoin}>
          <div className="flex items-center gap-2">
            <ShoppingBasket size={20} className="text-brand-red" />
            <h2 className="font-semibold">Trial details</h2>
          </div>

          <Field label="Phone number" value={form.phone_number} onChange={(phone_number) => setForm({ ...form, phone_number })} />

          <div className="grid grid-cols-2 gap-3">
            <DetailTile label="Store" value={storesLoading ? 'Loading...' : storeLabel} />
            <DetailTile label="Trial zone" value={storesLoading ? 'Loading...' : zoneLabel} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Item count" value={form.item_count} onChange={(item_count) => setForm({ ...form, item_count })} />
            <Select
              label="Gender"
              value={form.customer_gender}
              onChange={(customer_gender) => setForm({ ...form, customer_gender })}
              options={[
                { label: 'Select gender', value: '' },
                { label: 'Male', value: 'MALE' },
                { label: 'Female', value: 'FEMALE' },
              ]}
            />
          </div>

          <div className="grid grid-cols-1 gap-3">
            <Select
              label="Customer type"
              value={form.customer_type}
              onChange={(customer_type) => setForm({ ...form, customer_type })}
              options={[
                { label: 'Regular', value: 'regular' },
                { label: 'Priority', value: 'priority' },
              ]}
            />
          </div>

          {message ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{message}</p> : null}

          <Link to="/app/trial/customer/status" className="block rounded-lg bg-brand-blush px-3 py-2 text-center text-sm font-medium text-brand-red">
            View existing token status
          </Link>

          <button type="submit" disabled={loading} className="w-full rounded-lg bg-brand-red px-4 py-3 text-sm font-semibold text-white disabled:opacity-60">
            {loading ? 'Creating token...' : 'Create token'}
          </button>
        </form>
      </section>
    </main>
  );
}

function DetailTile({ label, value }) {
  return (
    <div className="rounded-lg border border-line px-3 py-2.5">
      <p className="text-xs font-medium text-muted">{label}</p>
      <p className="mt-1 truncate text-sm font-semibold text-charcoal" title={value}>
        {value}
      </p>
    </div>
  );
}
