import { ArrowLeft, Camera, QrCode, RefreshCw, Store } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import QrScanner from 'qr-scanner';
import { Link, useNavigate } from 'react-router-dom';

import brandLogo from '../../../../assets/images/equilateral_logo.png';
import { getErrorMessage, showApiErrorToast } from '../../../../api/httpClient.js';
import { listTrialStoreZones } from '../../../../api/trial/queueApi.js';
import { Select } from '../../../common/FormAndStatePrimitives.jsx';

function parseQrPayload(rawValue) {
  if (!rawValue) return null;

  try {
    const url = new URL(rawValue);
    const store_id = url.searchParams.get('store_id') || '';
    const trial_zone_id = url.searchParams.get('trial_zone_id') || '';
    const token_id = url.searchParams.get('token_id') || '';
    if (store_id) {
      return { store_id, trial_zone_id, token_id };
    }
  } catch {
    return null;
  }

  return null;
}

export function StoreZoneSelect() {
  const [form, setForm] = useState({ store_id: '', trial_zone_id: '' });
  const [stores, setStores] = useState([]);
  const [storesLoading, setStoresLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [scanMessage, setScanMessage] = useState('');

  const videoRef = useRef(null);
  const qrScannerRef = useRef(null);
  const navigate = useNavigate();

  async function loadStoreZones() {
    setStoresLoading(true);
    try {
      const data = await listTrialStoreZones();
      setStores(data);
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setStoresLoading(false);
    }
  }

  function goToCreateToken({ store_id, trial_zone_id }) {
    const params = new URLSearchParams();
    params.set('store_id', store_id);
    if (trial_zone_id) params.set('trial_zone_id', trial_zone_id);
    navigate(`/app/trial/customer/create?${params.toString()}`);
  }

  function stopScanning() {
    qrScannerRef.current?.stop();
    setIsScanning(false);
  }

  async function startScanning() {
    setScanMessage('');

    if (!navigator.mediaDevices?.getUserMedia) {
      setScanMessage('Camera access is not available on this device/browser.');
      return;
    }

    try {
      if (!videoRef.current) {
        setScanMessage('Unable to start camera preview.');
        stopScanning();
        return;
      }

      if (!qrScannerRef.current) {
        qrScannerRef.current = new QrScanner(
          videoRef.current,
          (scanResult) => {
            const rawValue = typeof scanResult === 'string' ? scanResult : scanResult?.data;
            const parsed = parseQrPayload(rawValue || '');
            if (!parsed?.store_id) {
              setScanMessage('Invalid QR. Use a URL QR with store_id and optional trial_zone_id/token_id query params.');
              return;
            }
            stopScanning();
            if (parsed.token_id) {
              navigate(`/app/trial/customer/status/${parsed.token_id}`);
              return;
            }
            goToCreateToken(parsed);
          },
          {
            preferredCamera: 'environment',
            returnDetailedScanResult: true,
          }
        );
      }

      await qrScannerRef.current.start();
      setIsScanning(true);
    } catch {
      stopScanning();
      setScanMessage('Unable to access camera. Please allow camera permission and retry.');
    }
  }

  function submitForm(event) {
    event.preventDefault();
    setMessage('');

    if (!form.store_id) {
      setMessage('Store is required.');
      return;
    }

    goToCreateToken(form);
  }

  const selectedStore = stores.find((store) => String(store.id) === String(form.store_id));

  const storeOptions = [
    { label: storesLoading ? 'Loading stores...' : 'Select store', value: '' },
    ...stores.map((store) => ({
      label: `${store.name} (${store.store_number})`,
      value: String(store.id),
    })),
  ];

  const zoneOptions = [
    {
      label: selectedStore ? (selectedStore.zones?.length ? 'Select trial zone' : 'No active trial zones available') : 'Select store first',
      value: '',
    },
    ...((selectedStore?.zones || []).map((zone) => ({
      label: `${zone.name} (${zone.gender || 'UNISEX'})`,
      value: String(zone.id),
    }))),
  ];

  useEffect(() => {
    loadStoreZones();

    function handleVisibilityChange() {
      if (!document.hidden) {
        loadStoreZones();
      }
    }

    function handleWindowFocus() {
      loadStoreZones();
    }

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleWindowFocus);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleWindowFocus);
    };
  }, []);

  useEffect(() => {
    return () => {
      qrScannerRef.current?.destroy();
      qrScannerRef.current = null;
    };
  }, []);

  return (
    <main className="min-h-screen animate-fadeIn px-4 py-5">
      <section className="mx-auto max-w-md animate-slideUp">
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
              <p className="text-xs font-medium uppercase tracking-wide text-white/90 sm:text-sm">Trial customer</p>
              <h1 className="text-xl font-semibold leading-tight sm:text-2xl">Select store</h1>
            </div>
          </div>
          <p className="mt-3 text-sm text-white/95">Use form entry or scan a trial queue QR code.</p>
        </header>

        <form className="mt-5 space-y-4 rounded-lg bg-white p-5 text-ink shadow-soft" onSubmit={submitForm}>
          <div className="flex items-center gap-2">
            <Store size={20} className="text-brand-red" />
            <h2 className="font-semibold">Manual selection</h2>
            <button
              type="button"
              onClick={loadStoreZones}
              className="ml-auto rounded-lg border border-line p-2 text-charcoal hover:border-brand-red"
              title="Refresh stores"
            >
              <RefreshCw size={16} />
            </button>
          </div>

          <div className="grid grid-cols-1 gap-3">
            <Select
              label="Store"
              value={form.store_id}
              options={storeOptions}
              onChange={(store_id) => {
                setForm({ store_id, trial_zone_id: '' });
                setMessage('');
              }}
            />
            <Select label="Trial zone" value={form.trial_zone_id} options={zoneOptions} onChange={(trial_zone_id) => setForm({ ...form, trial_zone_id })} />
          </div>

          {message ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{message}</p> : null}

          <button type="submit" className="w-full rounded-lg bg-brand-red px-4 py-3 text-sm font-semibold text-white disabled:opacity-60">
            Continue to token form
          </button>
        </form>

        <section className="mt-4 space-y-3 rounded-lg bg-white p-5 text-ink shadow-soft">
          <div className="flex items-center gap-2">
            <QrCode size={20} className="text-brand-red" />
            <h2 className="font-semibold">Scan QR</h2>
          </div>

          <div className="overflow-hidden rounded-lg border border-line bg-slate-100">
            <video ref={videoRef} className="aspect-video w-full bg-slate-200 object-cover" autoPlay muted playsInline />
          </div>

          {scanMessage ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{scanMessage}</p> : null}

          <div className="flex gap-2">
            <button
              type="button"
              onClick={startScanning}
              disabled={isScanning}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-red px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
            >
              <Camera size={16} />
              Start camera scan
            </button>
            <button
              type="button"
              onClick={stopScanning}
              disabled={!isScanning}
              className="w-full rounded-lg bg-brand-blush px-4 py-3 text-sm font-semibold text-brand-red disabled:opacity-60"
            >
              Stop
            </button>
          </div>

          <p className="text-xs text-muted">Supported QR format: URL containing `store_id` and optional `trial_zone_id`/`token_id` query params.</p>
        </section>

        <Link to="/app/trial/customer/status" className="mt-4 block rounded-lg bg-brand-blush px-3 py-2 text-center text-sm font-medium text-brand-red">
          View existing token status
        </Link>
      </section>
    </main>
  );
}
