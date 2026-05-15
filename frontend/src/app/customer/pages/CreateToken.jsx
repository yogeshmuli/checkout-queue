import { ShoppingBasket } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import brandLogo from '../../../assets/images/equilateral_logo.png';
import { getErrorMessage } from '../../../api/httpClient.js';
import { joinQueue } from '../../../api/queueApi.js';
import { Field, Select } from '../../../app/common/FormAndStatePrimitives.jsx';
import { useQueueStore } from '../../../store/queueStore.js';
import { defaultForm } from '../utils/customerUtils.js';

export function CreateToken() {
  const [form, setForm] = useState(defaultForm);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const { setLastToken } = useQueueStore();
  const navigate = useNavigate();
  const qrStoreLabel = useMemo(() => `Store ${form.store_id} · Section ${form.section_id}`, [form.store_id, form.section_id]);

  async function submitJoin(event) {
    event.preventDefault();
    setLoading(true);
    setMessage('');
    try {
      const token = await joinQueue({
        ...form,
        store_id: Number(form.store_id),
        section_id: form.section_id ? Number(form.section_id) : null,
        item_count: form.item_count ? Number(form.item_count) : null,
      });
      setLastToken(token);
      navigate(`/app/customer/status/${token.token_id}`);
    } catch (error) {
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen px-4 py-5  animate-fadeIn">
      <section className="mx-auto max-w-md animate-slideUp">
        <header className="rounded-lg bg-brand-red  text-white p-4 text-ink glass-panel border-l-4 border-brand-red">
          <div className="flex items-center gap-3">
            <img src={brandLogo} alt="Checkout Queue logo" className="h-10 w-24 rounded-lg bg-white p-1 object-contain" />
            <div>
              <p className="text-sm text-white">QR checkout queue</p>
              <h1 className="text-2xl font-semibold">Join billing queue</h1>
            </div>
          </div>
          <p className="mt-3 text-sm text-white">{qrStoreLabel}</p>
        </header>

        <form className="mt-5 space-y-4 rounded-lg bg-white p-5 text-ink shadow-soft" onSubmit={submitJoin}>
          <div className="flex items-center gap-2">
            <ShoppingBasket size={20} className="text-brand-red" />
            <h2 className="font-semibold">Checkout details</h2>
          </div>
          <Field label="Phone number" value={form.phone_number} onChange={(phone_number) => setForm({ ...form, phone_number })} />
          <div className="grid grid-cols-2 gap-3">
            <Field label="Store" value={form.store_id} onChange={(store_id) => setForm({ ...form, store_id })} />
            <Field label="Section" value={form.section_id} onChange={(section_id) => setForm({ ...form, section_id })} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Items" value={form.item_count} onChange={(item_count) => setForm({ ...form, item_count })} />
            <Select label="Basket" value={form.basket_size} onChange={(basket_size) => setForm({ ...form, basket_size })} options={['small', 'medium', 'large']} />
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
          <Link to="/app/customer/status" className="block rounded-lg bg-brand-blush px-3 py-2 text-center text-sm font-medium text-brand-red">
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
