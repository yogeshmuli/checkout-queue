import { QrCode } from 'lucide-react';
import QRCode from 'qrcode';
import { useState } from 'react';

export function QrDownloadButton({ filename, label = 'Download QR', value }) {
  const [isDownloading, setIsDownloading] = useState(false);

  async function downloadQr() {
    setIsDownloading(true);
    try {
      const dataUrl = await QRCode.toDataURL(value, {
        errorCorrectionLevel: 'M',
        margin: 2,
        scale: 8,
        width: 512,
      });
      const link = document.createElement('a');
      link.href = dataUrl;
      link.download = filename;
      link.rel = 'noopener';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } finally {
      setIsDownloading(false);
    }
  }

  return (
    <button
      type="button"
      onClick={downloadQr}
      disabled={isDownloading}
      className="inline-flex items-center gap-1 rounded-lg border border-line px-3 py-1.5 text-xs font-medium text-charcoal hover:border-brand-red hover:text-brand-red disabled:opacity-60"
      title={value}
    >
      <QrCode size={14} />
      {isDownloading ? 'Generating...' : label}
    </button>
  );
}
