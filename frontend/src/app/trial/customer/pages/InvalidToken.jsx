import { AlertTriangle } from 'lucide-react';
import { Link } from 'react-router-dom';

export function InvalidToken() {
  return (
    <main className="min-h-screen animate-fadeIn px-4 py-5">
      <section className="mx-auto max-w-md rounded-lg bg-white p-5 text-ink shadow-soft">
        <div className="flex items-center gap-2 text-rose-700">
          <AlertTriangle size={20} />
          <h1 className="text-lg font-semibold">Invalid token</h1>
        </div>
        <p className="mt-3 text-sm text-charcoal">Token ID is missing or invalid. Please create a new token or lookup an existing one.</p>
        <Link to="/app/trial/customer/create" className="mt-4 block rounded-lg bg-brand-red px-4 py-3 text-center text-sm font-semibold text-white">
          Go to create token
        </Link>
        <Link to="/app/trial/customer/status/lookup" className="mt-3 block rounded-lg bg-brand-blush px-4 py-3 text-center text-sm font-semibold text-brand-red">
          Lookup token by mobile
        </Link>
      </section>
    </main>
  );
}
