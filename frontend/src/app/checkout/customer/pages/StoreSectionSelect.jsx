import { ArrowLeft, Camera, ImageUp, QrCode } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import QrScanner from 'qr-scanner';
import { Link, useNavigate } from 'react-router-dom';

import brandLogo from '../../../../assets/images/equilateral_logo.png';

function getQrDestination(rawValue) {
  if (!rawValue) return null;

  try {
    const baseUrl = typeof window !== 'undefined' ? window.location.origin : undefined;
    const url = new URL(rawValue.trim(), baseUrl);
    const isHttpUrl = url.protocol === 'http:' || url.protocol === 'https:';
    const isCheckoutCustomerUrl = url.pathname.startsWith('/app/checkout/customer/');
    return isHttpUrl && isCheckoutCustomerUrl ? url : null;
  } catch {
    return null;
  }
}

export function StoreSectionSelect() {
  const [isScanning, setIsScanning] = useState(false);
  const [scanMessage, setScanMessage] = useState('');

  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const qrScannerRef = useRef(null);
  const navigate = useNavigate();

  function stopScanning() {
    qrScannerRef.current?.stop();

    setIsScanning(false);
  }

  function handleQrPayload(rawValue) {
    const destination = getQrDestination(rawValue || '');
    if (!destination) {
      setScanMessage('Invalid QR. Use a store QR code and try again.');
      return;
    }
    stopScanning();
    if (destination.origin === window.location.origin) {
      navigate(`${destination.pathname}${destination.search}${destination.hash}`);
      return;
    }
    window.location.assign(destination.href);
  }

  async function uploadQrImage(event) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;

    setScanMessage('');
    try {
      const scanResult = await QrScanner.scanImage(file, { returnDetailedScanResult: true });
      handleQrPayload(typeof scanResult === 'string' ? scanResult : scanResult?.data);
    } catch {
      setScanMessage('Unable to read a QR code from this image. Choose a clearer image and try again.');
    }
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
            handleQrPayload(rawValue);
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

  useEffect(() => {
    return () => {
      qrScannerRef.current?.destroy();
      qrScannerRef.current = null;
    };
  }, []);

  return (
    <main className="min-h-screen animate-fadeIn px-4 py-5">
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
              <p className="text-xs font-medium uppercase tracking-wide text-white/90 sm:text-sm">Customer check-in</p>
              <h1 className="text-xl font-semibold leading-tight sm:text-2xl">Scan store QR</h1>
            </div>
          </div>
          <p className="mt-3 text-sm text-white/95">Scan the QR code at the store or upload a saved QR image.</p>
        </header>

        <section className="mt-5 space-y-3 rounded-lg bg-white p-5 text-ink shadow-soft">
          <div className="flex items-center gap-2">
            <QrCode size={20} className="text-brand-red" />
            <h2 className="font-semibold">Scan or upload QR</h2>
          </div>

          <input ref={fileInputRef} type="file" accept="image/*" onChange={uploadQrImage} className="hidden" />

          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-brand-red/30 bg-brand-blush px-4 py-3 text-sm font-semibold text-brand-red hover:bg-white"
          >
            <ImageUp size={17} />
            Upload QR from gallery
          </button>

          <div className="flex items-center gap-3 py-1 text-xs font-medium uppercase tracking-wide text-muted">
            <span className="h-px flex-1 bg-line" />
            or scan with camera
            <span className="h-px flex-1 bg-line" />
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

          <p className="text-xs text-muted">Use the Checkout Queue QR code displayed at your store.</p>
        </section>

        <Link to="/app/checkout/customer/status" className="mt-4 block rounded-lg bg-brand-blush px-3 py-2 text-center text-sm font-medium text-brand-red">
          View existing token status
        </Link>
      </section>
    </main>
  );
}
