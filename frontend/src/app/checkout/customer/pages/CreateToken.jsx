import { ArrowLeft, ShoppingBasket } from 'lucide-react';
import { useMemo, useRef, useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { toast } from 'react-toastify';

import brandLogo from '../../../../assets/images/equilateral_logo.png';
import { getErrorMessage, showApiErrorToast } from '../../../../api/httpClient.js';
import { joinQueue, listStoreSections } from '../../../../api/checkout/queueApi.js';
import { Field, Select } from '../../../common/FormAndStatePrimitives.jsx';
import { useQueueStore } from '../../../../store/queueStore.js';
import { defaultForm } from '../utils/customerUtils.js';

const SECTION_TYPE_LABELS = {
  REGULAR: 'Regular',
  EXPRESS: 'Express',
  SELF_CHECKOUT: 'Self Checkout',
  RETURNS: 'Returns',
  PRIORITY: 'Priority',
};

function getSectionTypeLabel(sectionType) {
  return SECTION_TYPE_LABELS[sectionType] || sectionType;
}

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

  // Prefill store_id and section_id from query params if present.
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const store_id = params.get('store_id');
    const section_id = params.get('section_id');
    setForm((f) => ({
      ...f,
      store_id: store_id || f.store_id,
      section_id: section_id || f.section_id,
    }));
  }, [location.search]);

  useEffect(() => {
    async function loadStoreNames() {
      setStoresLoading(true);
      setStoresLoaded(false);
      try {
        setStores(await listStoreSections());
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
  const selectedSection = useMemo(
    () => selectedStore?.sections?.find((section) => String(section.id) === String(form.section_id)),
    [form.section_id, selectedStore]
  );

  useEffect(() => {
    if (!storesLoaded || invalidQrRedirectedRef.current) return;
    if (!form.store_id && !form.section_id) return;

    const missingStore = Boolean(form.store_id) && !selectedStore;
    const missingSection = Boolean(form.section_id) && !selectedSection;
    if (!missingStore && !missingSection) return;

    invalidQrRedirectedRef.current = true;
    const warning = missingStore
      ? 'Selected store is no longer available. Please scan a valid checkout QR code.'
      : 'Selected checkout section is no longer available. Please scan a valid checkout QR code.';
    toast.warn(warning, { toastId: 'checkout-invalid-customer-qr' });
    navigate('/app/checkout/customer', { replace: true, state: { warning } });
  }, [form.section_id, form.store_id, navigate, selectedSection, selectedStore, storesLoaded]);

  const storeLabel = selectedStore?.name || (form.store_id ? `Store #${form.store_id}` : 'Store not selected');
  const sectionLabel = selectedSection
    ? `${selectedSection.name} (${getSectionTypeLabel(selectedSection.section_type)})`
    : form.section_id
      ? `Section #${form.section_id}`
      : 'No section selected';
  const qrStoreLabel = useMemo(() => `${storeLabel} · ${sectionLabel}`, [sectionLabel, storeLabel]);

  async function submitJoin(event) {
    event.preventDefault();
    setLoading(true);
    setMessage('');

    if (!form.is_still_shopping && !form.item_count && !form.basket_size) {
      setLoading(false);
      setMessage('Enter item count or select basket size when you are not still shopping.');
      return;
    }

    try {
      const token = await joinQueue({
        ...form,
        store_id: Number(form.store_id),
        section_id: form.section_id ? Number(form.section_id) : null,
        item_count: form.item_count ? Number(form.item_count) : null,
        basket_size: form.basket_size || null,
      });
      setLastToken(token);
      navigate(`/app/checkout/customer/status/${token.token_id}`);
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }
  function onChangeBasketSize(basket_size) {
    // if( form.item_count){
    //   setForm({...form, basket_size });
    //   return;
    // }
    let item_count;
    switch (basket_size) {
      case 'small':
        item_count = 9;
        break;
      case 'medium':
        item_count = 20;
        break;
      case 'large':
        item_count = 30;
        break;
      default:
        item_count = form.item_count;
    }
    setForm({ ...form, basket_size, item_count });
  }

  return (
    <main className="min-h-screen px-4 py-5  animate-fadeIn">
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
              <img src={brandLogo} alt="Checkout Queue logo" className="h-full w-full object-cover" />
            </Link>
            <div className="min-w-0">
              <p className="text-xs font-medium uppercase tracking-wide text-white/90 sm:text-sm">QR checkout queue</p>
              <h1 className="text-xl font-semibold leading-tight sm:text-2xl">Create token</h1>
            </div>
          </div>
          <p className="mt-3 text-sm text-white/95">{storesLoading ? 'Loading store details...' : qrStoreLabel}</p>
        </header>

        <form className="mt-5 space-y-4 rounded-lg bg-white p-5 text-ink shadow-soft" onSubmit={submitJoin}>
          <div className="flex items-center gap-2">
            <ShoppingBasket size={20} className="text-brand-red" />
            <h2 className="font-semibold">Checkout details</h2>
          </div>
          <Field label="Phone number" value={form.phone_number} onChange={(phone_number) => setForm({ ...form, phone_number })} />
          <div className="grid grid-cols-2 gap-3">
            <DetailTile label="Store" value={storesLoading ? 'Loading...' : storeLabel} />
            <DetailTile label="Section" value={storesLoading ? 'Loading...' : sectionLabel} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Items (optional)" value={form.item_count} onChange={(item_count) => setForm({ ...form, item_count })} />
            <Select
              label="Basket (optional)"
              value={form.basket_size}
              onChange={onChangeBasketSize}
              options={[
                { label: 'Select basket size', value: '' },
                { label: 'Small (< 9 items)', value: 'small' },
                { label: 'Medium (9-20 items)', value: 'medium' },
                { label: 'Large (> 20 items)', value: 'large' },
              ]}
            />
          </div>
          <label className="flex items-center justify-between rounded-lg border border-line px-3 py-3">
            <span className="text-sm font-medium text-charcoal">Still shopping</span>
            <input
              type="checkbox"
              checked={form.is_still_shopping}
              onChange={(event) => setForm({ ...form, is_still_shopping: event.target.checked })}
              className="size-5 accent-brand-red"
            />
          </label>
          {message ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{message}</p> : null}
          <Link to="/app/checkout/customer/status" className="block rounded-lg bg-brand-blush px-3 py-2 text-center text-sm font-medium text-brand-red">
            View existing token status
          </Link>
          <button type="submit" disabled={loading} className="w-full rounded-lg bg-brand-red px-4 py-3 text-sm font-semibold text-white disabled:opacity-60">
            Create token
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
