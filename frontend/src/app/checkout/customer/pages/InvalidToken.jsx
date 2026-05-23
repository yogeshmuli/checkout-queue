import { ArrowLeft } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

import brandLogo from '../../../../assets/images/equilateral_logo.png';
import { EmptyStateCard } from '../../../common/FormAndStatePrimitives.jsx';

export function InvalidToken() {
  const navigate = useNavigate();

  return (
    <main className="min-h-screen  px-4 py-5 ">
      <section className="mx-auto max-w-md">
        <header className="customer-sticky-header mb-5 rounded-xl border border-white/30 bg-brand-red p-4 text-white shadow-soft">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="flex size-10 shrink-0 items-center justify-center rounded-lg border border-white/30 text-white"
              aria-label="Go back"
              title="Go back"
            >
              <ArrowLeft size={18} />
            </button>
            <Link to="/app/checkout/customer" className="flex h-12 w-28 shrink-0 items-center justify-center rounded-md border border-white/40 bg-white/95 p-1 shadow-sm" aria-label="Customer home">
              <img src={brandLogo} alt="Checkout Queue logo" className="h-full w-full object-cover" />
            </Link>
            <div className="min-w-0">
              <p className="text-xs font-medium uppercase tracking-wide text-white/90 sm:text-sm">Customer check-in</p>
              <h1 className="text-xl font-semibold leading-tight sm:text-2xl">Token status</h1>
            </div>
          </div>
        </header>
        <EmptyStateCard
          message="Invalid or no token present in URL."
          ctaTo="/app/checkout/customer/status/lookup"
          ctaLabel="Find token by mobile"
        />
      </section>
    </main>
  );
}
