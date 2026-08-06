import { Pencil, Plus, RefreshCw, Save, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

import { getErrorMessage, showApiErrorToast } from '../../../../api/httpClient.js';
import { createStore, deleteStore, listStores, updateStore } from '../../../../api/trial/storeApi.js';
import { SectionHeader } from '../../../common/SectionHeader.jsx';
import { useAuthStore } from '../../../../store/authStore.js';

const emptyStore = {
  store_number: '',
  name: '',
  address: '',
  manager_name: '',
  manager_phone: '',
  spoc_name: '',
  spoc_phone: '',
  is_active: true,
};

const FIELD_LIMITS = {
  store_number: 50,
  name: 150,
  manager_name: 150,
  spoc_name: 150,
  phone: 10,
};

const STORES_PER_PAGE = 8;
const FIELD_ORDER = ['store_number', 'name', 'address', 'manager_name', 'manager_phone', 'spoc_name', 'spoc_phone'];

export function Stores() {
  const isSuperAdmin = useAuthStore((state) => state.user?.default_role === 'SUPER_ADMIN');
  const [stores, setStores] = useState([]);
  const [form, setForm] = useState(emptyStore);
  const [initialFormState, setInitialFormState] = useState(emptyStore);
  const [formErrors, setFormErrors] = useState({});
  const [editingStoreId, setEditingStoreId] = useState(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [pendingStatusChange, setPendingStatusChange] = useState(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const fieldRefs = useRef({});

  function sanitizePhone(value) {
    return value.replace(/\D/g, '').slice(0, FIELD_LIMITS.phone);
  }

  function toPayload(values) {
    return {
      store_number: values.store_number.trim(),
      name: values.name.trim(),
      address: values.address.trim() || null,
      manager_name: values.manager_name.trim() || null,
      manager_phone: values.manager_phone || null,
      spoc_name: values.spoc_name.trim() || null,
      spoc_phone: values.spoc_phone || null,
      is_active: values.is_active,
    };
  }

  function validateStoreForm(values) {
    const errors = {};

    if (!values.store_number.trim()) {
      errors.store_number = 'Store number is required.';
    } else if (values.store_number.trim().length > FIELD_LIMITS.store_number) {
      errors.store_number = `Store number must be at most ${FIELD_LIMITS.store_number} characters.`;
    }

    if (!values.name.trim()) {
      errors.name = 'Store name is required.';
    } else if (values.name.trim().length > FIELD_LIMITS.name) {
      errors.name = `Store name must be at most ${FIELD_LIMITS.name} characters.`;
    }

    if (values.manager_name.trim().length > FIELD_LIMITS.manager_name) {
      errors.manager_name = `Manager name must be at most ${FIELD_LIMITS.manager_name} characters.`;
    }

    if (values.spoc_name.trim().length > FIELD_LIMITS.spoc_name) {
      errors.spoc_name = `SPOC name must be at most ${FIELD_LIMITS.spoc_name} characters.`;
    }

    if (values.manager_phone && !/^\d{10}$/.test(values.manager_phone)) {
      errors.manager_phone = 'Manager phone must be exactly 10 digits.';
    }

    if (values.spoc_phone && !/^\d{10}$/.test(values.spoc_phone)) {
      errors.spoc_phone = 'SPOC phone must be exactly 10 digits.';
    }

    return errors;
  }

  function setFormField(field, value) {
    const nextValue = field === 'manager_phone' || field === 'spoc_phone' ? sanitizePhone(value) : value;
    setForm((prev) => ({ ...prev, [field]: nextValue }));
    setFormErrors((prev) => {
      if (!prev[field]) return prev;
      const nextErrors = { ...prev };
      delete nextErrors[field];
      return nextErrors;
    });
  }

  const hasUnsavedChanges = JSON.stringify(form) !== JSON.stringify(initialFormState);

  function confirmDiscardIfDirty() {
    if (!hasUnsavedChanges) return true;
    return window.confirm('You have unsaved changes. Discard them?');
  }

  function beginEdit(store) {
    if (isFormOpen && !confirmDiscardIfDirty()) {
      return;
    }

    const nextForm = {
      store_number: store.store_number || '',
      name: store.name || '',
      address: store.address || '',
      manager_name: store.manager_name || '',
      manager_phone: store.manager_phone || '',
      spoc_name: store.spoc_name || '',
      spoc_phone: store.spoc_phone || '',
      is_active: Boolean(store.is_active),
    };
    setEditingStoreId(store.id);
    setForm(nextForm);
    setInitialFormState(nextForm);
    setFormErrors({});
    setIsFormOpen(true);
    setMessage('Editing store details.');
  }

  function openCreateForm() {
    if (isFormOpen && !confirmDiscardIfDirty()) {
      return;
    }
    setEditingStoreId(null);
    setForm(emptyStore);
    setInitialFormState(emptyStore);
    setFormErrors({});
    setMessage('');
    setIsFormOpen(true);
  }

  function resetFormState(options = { force: false, closeForm: false }) {
    if (!options.force && !confirmDiscardIfDirty()) {
      return;
    }
    setEditingStoreId(null);
    setForm(emptyStore);
    setInitialFormState(emptyStore);
    setFormErrors({});
    if (options.closeForm) {
      setIsFormOpen(false);
    }
  }

  async function loadStores() {
    setLoading(true);
    setMessage('');
    try {
      setStores(await listStores({ include_inactive: true }));
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadStores();
  }, []);

  async function submitStore(event) {
    event.preventDefault();
    const validationErrors = validateStoreForm(form);
    if (Object.keys(validationErrors).length > 0) {
      setFormErrors(validationErrors);
      setMessage('Please fix validation errors before saving.');
      focusFirstInvalidField(validationErrors);
      return;
    }

    setLoading(true);
    setMessage('');
    try {
      const payload = toPayload(form);
      if (editingStoreId) {
        await updateStore(editingStoreId, payload);
        setMessage('Store updated');
        resetFormState({ force: true, closeForm: false });
      } else {
        await createStore(payload);
        setMessage('Store created');
        resetFormState({ force: true, closeForm: true });
      }
      await loadStores();
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function deactivateStore(storeId) {
    setLoading(true);
    setMessage('');
    try {
      await deleteStore(storeId);
      setMessage('Store deactivated');
      await loadStores();
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function toggleStoreActive(store) {
    setLoading(true);
    setMessage('');
    try {
      await updateStore(store.id, { is_active: !store.is_active });
      setMessage(store.is_active ? 'Store deactivated' : 'Store activated');
      await loadStores();
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  function openStatusConfirm(store) {
    setPendingStatusChange({
      store,
      mode: store.is_active ? 'deactivate' : 'activate',
    });
  }

  function closeStatusConfirm() {
    setPendingStatusChange(null);
  }

  async function confirmStatusChange() {
    if (!pendingStatusChange) return;
    const { store, mode } = pendingStatusChange;
    closeStatusConfirm();

    if (mode === 'deactivate') {
      await deactivateStore(store.id);
      return;
    }

    await toggleStoreActive(store);
  }

  const normalizedQuery = query.trim().toLowerCase();
  const filteredStores = stores.filter((store) => {
    if (!normalizedQuery) return true;
    const haystack = `${store.name || ''} ${store.store_number || ''}`.toLowerCase();
    return haystack.includes(normalizedQuery);
  });

  const totalPages = Math.max(1, Math.ceil(filteredStores.length / STORES_PER_PAGE));
  const safePage = Math.min(page, totalPages);
  const pageStart = (safePage - 1) * STORES_PER_PAGE;
  const visibleStores = filteredStores.slice(pageStart, pageStart + STORES_PER_PAGE);

  function goToPage(nextPage) {
    setPage(Math.max(1, Math.min(totalPages, nextPage)));
  }

  function focusFirstInvalidField(validationErrors) {
    const firstInvalidField = FIELD_ORDER.find((field) => validationErrors[field]);
    if (!firstInvalidField) return;

    // Wait for validation state render before focusing.
    window.requestAnimationFrame(() => {
      fieldRefs.current[firstInvalidField]?.focus();
    });
  }

  return (
    <div className={`grid gap-6 ${isFormOpen ? 'xl:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]' : ''}`}>
      {isFormOpen ? (
        <section id="store-form" className="rounded-lg border border-line bg-white p-5">
          <MobilePanelJump href="#store-directory" label="Back to stores" />
          <SectionHeader eyebrow="Store setup" title={editingStoreId ? 'Update store' : 'Create store'} />
          <form className="mt-5 space-y-4" onSubmit={submitStore}>
            <Field
              label="Store number"
              value={form.store_number}
              onChange={(value) => setFormField('store_number', value)}
              error={formErrors.store_number}
              maxLength={FIELD_LIMITS.store_number}
              inputRef={(el) => {
                fieldRefs.current.store_number = el;
              }}
            />
            <Field
              label="Store name"
              value={form.name}
              onChange={(value) => setFormField('name', value)}
              error={formErrors.name}
              maxLength={FIELD_LIMITS.name}
              inputRef={(el) => {
                fieldRefs.current.name = el;
              }}
            />
            <Field
              label="Address"
              value={form.address}
              onChange={(value) => setFormField('address', value)}
              inputRef={(el) => {
                fieldRefs.current.address = el;
              }}
            />
            <Field
              label="Manager name"
              value={form.manager_name}
              onChange={(value) => setFormField('manager_name', value)}
              error={formErrors.manager_name}
              maxLength={FIELD_LIMITS.manager_name}
              inputRef={(el) => {
                fieldRefs.current.manager_name = el;
              }}
            />
            <Field
              label="Manager phone"
              value={form.manager_phone}
              onChange={(value) => setFormField('manager_phone', value)}
              error={formErrors.manager_phone}
              maxLength={FIELD_LIMITS.phone}
              inputMode="numeric"
              inputRef={(el) => {
                fieldRefs.current.manager_phone = el;
              }}
            />
            <Field
              label="SPOC name"
              value={form.spoc_name}
              onChange={(value) => setFormField('spoc_name', value)}
              error={formErrors.spoc_name}
              maxLength={FIELD_LIMITS.spoc_name}
              inputRef={(el) => {
                fieldRefs.current.spoc_name = el;
              }}
            />
            <Field
              label="SPOC phone"
              value={form.spoc_phone}
              onChange={(value) => setFormField('spoc_phone', value)}
              error={formErrors.spoc_phone}
              maxLength={FIELD_LIMITS.phone}
              inputMode="numeric"
              inputRef={(el) => {
                fieldRefs.current.spoc_phone = el;
              }}
            />
            <label className="flex items-center justify-between rounded-lg border border-line px-3 py-3">
              <span className="text-sm font-medium text-charcoal">Store active</span>
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(event) => setForm((prev) => ({ ...prev, is_active: event.target.checked }))}
                className="size-5 accent-brand-red"
              />
            </label>
            {message ? <p className="rounded-lg bg-brand-blush px-3 py-2 text-sm text-charcoal">{message}</p> : null}
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={loading}
                className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-brand-red px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
              >
                <Save size={17} />
                {editingStoreId ? 'Update store' : 'Save store'}
              </button>
              {editingStoreId ? (
                <button
                  type="button"
                  onClick={() => resetFormState({ closeForm: true })}
                  disabled={loading}
                  className="inline-flex items-center justify-center gap-2 rounded-lg border border-line px-4 py-3 text-sm font-medium text-charcoal disabled:opacity-60"
                >
                  <X size={16} />
                  Cancel
                </button>
              ) : null}
            </div>
          </form>
        </section>
      ) : null}

      <section id="store-directory" className="rounded-lg border border-line bg-white">
        <div className="flex items-center justify-between border-b border-line p-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-red">Store directory</p>
            <h2 className="mt-1 text-xl font-semibold">Configured stores</h2>
          </div>
          <div className="flex items-center gap-2">
            {isFormOpen ? <MobilePanelJump href="#store-form" label="Go to form" compact /> : null}
            {isSuperAdmin ? <button
              type="button"
              onClick={openCreateForm}
              className="inline-flex size-10 items-center justify-center rounded-lg bg-brand-red text-white sm:size-auto sm:gap-2 sm:px-3 sm:py-2 sm:text-sm sm:font-medium"
              title="Create store"
              aria-label="Create store"
            >
              <Plus size={16} />
              <span className="hidden sm:inline">Create store</span>
            </button> : null}
            <button type="button" onClick={loadStores} className="rounded-lg border border-line p-2 text-charcoal hover:border-brand-red" title="Refresh stores">
              <RefreshCw size={18} />
            </button>
          </div>
        </div>
        <div className="border-b border-line p-5">
          <label className="block">
            <span className="text-sm font-medium text-charcoal">Search stores</span>
            <input
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setPage(1);
              }}
              placeholder="Search by name or store number"
              className="mt-1 w-full rounded-lg border border-line px-3 py-2.5 outline-none focus:border-brand-red focus:ring-2 focus:ring-brand-soft"
            />
          </label>
        </div>
        <div className="divide-y divide-brand-soft">
          {filteredStores.length === 0 ? (
            <p className="p-5 text-sm text-muted">No stores found.</p>
          ) : (
            visibleStores.map((store) => {
              const isEditing = editingStoreId === store.id;

              return (
              <div
                key={store.id}
                className={`grid gap-3 p-5 lg:grid-cols-[1fr_auto] ${isEditing ? 'bg-brand-blush/50 ring-1 ring-inset ring-brand-soft' : ''}`}
              >
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-semibold">{store.name}</h3>
                    <span className="rounded-full bg-brand-blush px-2 py-1 text-xs text-charcoal">{store.store_number}</span>
                    <span className={`rounded-full px-2 py-1 text-xs ${store.is_active ? 'bg-brand-blush text-success' : 'bg-rose-50 text-rose-700'}`}>
                      {store.is_active ? 'Active' : 'Inactive'}
                    </span>
                    {isEditing ? <span className="rounded-full bg-brand-red px-2 py-1 text-xs font-semibold text-white">Editing</span> : null}
                  </div>
                  <p className="mt-1 text-sm text-charcoal">{store.address || 'No address'}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <ResourceLink to={`/app/trial/admin/zones?store_id=${store.id}`} label="Trial zones" />
                    <ResourceLink to={`/app/trial/admin/studios?store_id=${store.id}`} label="Studios" />
                    <ResourceLink to={`/app/trial/admin/queue?store_id=${store.id}`} label="Quick Trial" />
                    <ResourceLink to={`/app/trial/admin/config?store_id=${store.id}`} label="Trial config" />
                    <ResourceLink to={`/app/trial/admin/calendar?store_id=${store.id}`} label="Trial calendar" />
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2 lg:justify-end">
                  <button
                    type="button"
                    onClick={() => beginEdit(store)}
                    className={`inline-flex items-center justify-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium disabled:opacity-50 ${
                      isEditing ? 'border-brand-red bg-brand-blush text-brand-red' : 'border-line text-charcoal'
                    }`}
                    disabled={loading}
                  >
                    <Pencil size={16} />
                    {isEditing ? 'Editing' : 'Edit'}
                  </button>
                  {isSuperAdmin ? <button
                    type="button"
                    onClick={() => openStatusConfirm(store)}
                    className="inline-flex items-center justify-center gap-2 rounded-lg border border-rose-200 px-3 py-2 text-sm font-medium text-rose-700 disabled:opacity-50"
                    disabled={loading}
                  >
                    {store.is_active ? 'Deactivate' : 'Activate'}
                  </button> : null}
                </div>
              </div>
            );
            })
          )}
        </div>
        {filteredStores.length > STORES_PER_PAGE ? (
          <div className="flex items-center justify-between border-t border-line px-5 py-4">
            <p className="text-xs text-muted">
              Showing {pageStart + 1}-{Math.min(pageStart + STORES_PER_PAGE, filteredStores.length)} of {filteredStores.length}
            </p>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => goToPage(safePage - 1)}
                disabled={safePage <= 1}
                className="rounded-lg border border-line px-3 py-1.5 text-sm text-charcoal disabled:opacity-50"
              >
                Prev
              </button>
              <span className="text-sm text-charcoal">
                {safePage} / {totalPages}
              </span>
              <button
                type="button"
                onClick={() => goToPage(safePage + 1)}
                disabled={safePage >= totalPages}
                className="rounded-lg border border-line px-3 py-1.5 text-sm text-charcoal disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        ) : null}
      </section>

      {pendingStatusChange ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 px-4">
          <div className="w-full max-w-md rounded-lg bg-white p-5 shadow-soft">
            <h3 className="text-lg font-semibold text-ink">
              {pendingStatusChange.mode === 'deactivate' ? 'Deactivate store?' : 'Activate store?'}
            </h3>
            <p className="mt-2 text-sm text-charcoal">
              {pendingStatusChange.mode === 'deactivate'
                ? `This will mark ${pendingStatusChange.store.name} as inactive. Continue?`
                : `This will mark ${pendingStatusChange.store.name} as active. Continue?`}
            </p>

            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={closeStatusConfirm}
                className="rounded-lg border border-line px-4 py-2 text-sm font-medium text-charcoal"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmStatusChange}
                className="rounded-lg bg-brand-red px-4 py-2 text-sm font-semibold text-white"
              >
                {pendingStatusChange.mode === 'deactivate' ? 'Deactivate' : 'Activate'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function MobilePanelJump({ href, label, compact = false }) {
  return (
    <a
      href={href}
      className={`${compact ? '' : 'mb-4 '}inline-flex h-10 items-center justify-center rounded-lg border border-line px-3 text-sm font-medium text-charcoal lg:hidden`}
      title={label}
      aria-label={label}
    >
      <span className="sm:hidden">Form</span>
      <span className="hidden sm:inline">{label}</span>
    </a>
  );
}

function ResourceLink({ to, label }) {
  return (
    <Link to={to} className="rounded-lg border border-line px-3 py-1.5 text-xs font-medium text-charcoal hover:border-brand-red hover:text-brand-red">
      {label}
    </Link>
  );
}

function Field({ label, value, onChange, error, maxLength, inputMode = 'text', inputRef }) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-charcoal">{label}</span>
      <input
        ref={inputRef}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        maxLength={maxLength}
        inputMode={inputMode}
        className={`mt-1 w-full rounded-lg border px-3 py-2.5 outline-none focus:ring-2 ${
          error ? 'border-rose-400 focus:border-rose-500 focus:ring-rose-100' : 'border-line focus:border-brand-red focus:ring-brand-soft'
        }`}
      />
      {error ? <p className="mt-1 text-xs text-rose-700">{error}</p> : null}
    </label>
  );
}
