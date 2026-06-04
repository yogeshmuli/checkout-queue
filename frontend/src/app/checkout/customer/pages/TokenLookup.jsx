import { ArrowLeft, Search } from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import brandLogo from '../../../../assets/images/equilateral_logo.png';
import { getErrorMessage, showApiErrorToast } from '../../../../api/httpClient.js';
import { getTokenStatus } from '../../../../api/checkout/queueApi.js';
import { Field } from '../../../common/FormAndStatePrimitives.jsx';
import { useQueueStore } from '../../../../store/queueStore.js';

export function TokenLookup() {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const navigate = useNavigate();
  const { setLastToken } = useQueueStore();

  async function submitLookup(event) {
    event.preventDefault();
    setMessage('');

    if (!phoneNumber || phoneNumber.length !== 10) {
      setMessage('Please enter a valid 10-digit mobile number.');
      return;
    }

    setLoading(true);
    try {
      const token = await getTokenStatus({ phone_number: phoneNumber });
      setLastToken(token);
      navigate(`/app/checkout/customer/status/${token.token_id}`);
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
      setLastToken(null);
    } finally {
      setLoading(false);
    }
  }

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
              <img src={brandLogo} alt="Checkout Queue logo" className="h-full w-full object-cover" />
            </Link>
            <div className="min-w-0">
              <p className="text-xs font-medium uppercase tracking-wide text-white/90 sm:text-sm">Customer check-in</p>
              <h1 className="text-xl font-semibold leading-tight sm:text-2xl">Find token status</h1>
            </div>
          </div>
          <p className="mt-3 text-sm text-white/95">Enter mobile number to find your latest token.</p>
        </header>

        <form className="mt-5 space-y-4 rounded-lg bg-white p-5 text-ink shadow-soft" onSubmit={submitLookup}>
          <div className="flex items-center gap-2">
            <Search size={20} className="text-brand-red" />
            <h2 className="font-semibold">Lookup by mobile number</h2>
          </div>

          <Field label="Mobile number" value={phoneNumber} onChange={setPhoneNumber} />

          {message ? <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{message}</p> : null}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-brand-red px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
          >
            {loading ? 'Checking status...' : 'Check token status'}
          </button>

          <Link to="/app/checkout/customer" className="block rounded-lg bg-brand-blush px-3 py-2 text-center text-sm font-medium text-brand-red">
            Create new token
          </Link>
        </form>
      </section>
    </main>
  );
}
