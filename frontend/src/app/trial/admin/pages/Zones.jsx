import { Pencil, Plus, RefreshCw, Save, X } from 'lucide-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

import { getErrorMessage, showApiErrorToast } from '../../../../api/httpClient.js';
import { listStores } from '../../../../api/trial/storeApi.js';
import { createTrialZone, deleteTrialZone, listTrialZones, updateTrialZone } from '../../../../api/trial/zonesApi.js';
import { Select } from '../../../common/FormAndStatePrimitives.jsx';
import { QrDownloadButton } from '../../../common/QrDownloadButton.jsx';
import { buildPublicAppUrl } from '../../../common/qrDownloadUtils.js';
import { SectionHeader } from '../../../common/SectionHeader.jsx';

const emptyZone = {
  store_id: '',
  name: '',
  gender: '',
  is_active: true,
};

const FIELD_LIMITS = {
  name: 100,
};

const ZONES_PER_PAGE = 8;
const FIELD_ORDER = ['store_id', 'name', 'gender'];

const GENDER_OPTIONS = [
  { label: 'Select gender', value: '' },
  { label: 'Male', value: 'MALE' },
  { label: 'Female', value: 'FEMALE' },
  { label: 'Unisex', value: 'UNISEX' },
];

function getGenderLabel(gender) {
  return GENDER_OPTIONS.find((option) => option.value === gender)?.label || gender;
}

export function Zones() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [zones, setZones] = useState([]);
  const [stores, setStores] = useState([]);
  const [form, setForm] = useState(emptyZone);
  const [initialFormState, setInitialFormState] = useState(emptyZone);
  const [formErrors, setFormErrors] = useState({});
  const [editingZoneId, setEditingZoneId] = useState(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [pendingStatusChange, setPendingStatusChange] = useState(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const fieldRefs = useRef({});
  const storeFilter = searchParams.get('store_id') || '';

  const storeNameById = useMemo(() => {
    const map = new Map();
    for (const store of stores) {
      map.set(String(store.id), store.name);
    }
    return map;
  }, [stores]);

  const storeOptions = [
    { label: 'Select store', value: '' },
    ...stores.map((store) => ({
      label: `${store.name} (${store.store_number})`,
      value: String(store.id),
    })),
  ];

  const storeFilterOptions = [
    { label: 'All stores', value: '' },
    ...stores.map((store) => ({
      label: `${store.name} (${store.store_number})`,
      value: String(store.id),
    })),
  ];

  function setStoreFilter(value) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) {
        next.set('store_id', value);
      } else {
        next.delete('store_id');
      }
      return next;
    });
    setPage(1);
  }

  function toPayload(values) {
    return {
      store_id: Number(values.store_id),
      name: values.name.trim(),
      gender: values.gender,
      is_active: values.is_active,
    };
  }

  function validateZoneForm(values) {
    const errors = {};

    if (!values.store_id) {
      errors.store_id = 'Store is required.';
    }

    if (!values.name.trim()) {
      errors.name = 'Trial zone name is required.';
    } else if (values.name.trim().length > FIELD_LIMITS.name) {
      errors.name = `Trial zone name must be at most ${FIELD_LIMITS.name} characters.`;
    }

    if (!values.gender) {
      errors.gender = 'Gender is required.';
    }

    return errors;
  }

  function setFormField(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
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

  function focusFirstInvalidField(validationErrors) {
    const firstInvalidField = FIELD_ORDER.find((field) => validationErrors[field]);
    if (!firstInvalidField) return;

    window.requestAnimationFrame(() => {
      fieldRefs.current[firstInvalidField]?.focus();
    });
  }

  function beginEdit(zone) {
    if (isFormOpen && !confirmDiscardIfDirty()) {
      return;
    }

    const nextForm = {
      store_id: String(zone.store_id),
      name: zone.name || '',
      gender: zone.gender || '',
      is_active: Boolean(zone.is_active),
    };
    setEditingZoneId(zone.id);
    setForm(nextForm);
    setInitialFormState(nextForm);
    setFormErrors({});
    setIsFormOpen(true);
    setMessage('Editing trial zone details.');
  }

  function openCreateForm() {
    if (isFormOpen && !confirmDiscardIfDirty()) {
      return;
    }
    setEditingZoneId(null);
    setForm(emptyZone);
    setInitialFormState(emptyZone);
    setFormErrors({});
    setMessage('');
    setIsFormOpen(true);
  }

  function resetFormState(options = { force: false, closeForm: false }) {
    if (!options.force && !confirmDiscardIfDirty()) {
      return;
    }
    setEditingZoneId(null);
    setForm(emptyZone);
    setInitialFormState(emptyZone);
    setFormErrors({});
    if (options.closeForm) {
      setIsFormOpen(false);
    }
  }

  const loadZones = useCallback(async () => {
    setLoading(true);
    setMessage('');
    try {
      setZones(
        await listTrialZones({
          include_inactive: true,
          ...(storeFilter ? { store_id: Number(storeFilter) } : {}),
        })
      );
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [storeFilter]);

  async function loadStores() {
    try {
      setStores(await listStores({ include_inactive: true }));
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    }
  }

  useEffect(() => {
    loadZones();
  }, [loadZones]);

  useEffect(() => {
    loadStores();
  }, []);

  async function submitZone(event) {
    event.preventDefault();
    const validationErrors = validateZoneForm(form);
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
      if (editingZoneId) {
        await updateTrialZone(editingZoneId, payload);
        setMessage('Trial zone updated');
        resetFormState({ force: true, closeForm: false });
      } else {
        await createTrialZone(payload);
        setMessage('Trial zone created');
        resetFormState({ force: true, closeForm: true });
      }
      await loadZones();
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function deactivateZone(zoneId) {
    setLoading(true);
    setMessage('');
    try {
      await deleteTrialZone(zoneId);
      setMessage('Trial zone deactivated');
      await loadZones();
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function toggleZoneActive(zone) {
    setLoading(true);
    setMessage('');
    try {
      await updateTrialZone(zone.id, { is_active: !zone.is_active });
      setMessage(zone.is_active ? 'Trial zone deactivated' : 'Trial zone activated');
      await loadZones();
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  function openStatusConfirm(zone) {
    setPendingStatusChange({
      zone,
      mode: zone.is_active ? 'deactivate' : 'activate',
    });
  }

  function closeStatusConfirm() {
    setPendingStatusChange(null);
  }

  async function confirmStatusChange() {
    if (!pendingStatusChange) return;
    const { zone, mode } = pendingStatusChange;
    closeStatusConfirm();

    if (mode === 'deactivate') {
      await deactivateZone(zone.id);
      return;
    }

    await toggleZoneActive(zone);
  }

  const normalizedQuery = query.trim().toLowerCase();
  const filteredZones = zones.filter((zone) => {
    if (!normalizedQuery) return true;
    const storeName = storeNameById.get(String(zone.store_id)) || '';
    const haystack = `${zone.name || ''} ${storeName}`.toLowerCase();
    return haystack.includes(normalizedQuery);
  });

  const totalPages = Math.max(1, Math.ceil(filteredZones.length / ZONES_PER_PAGE));
  const safePage = Math.min(page, totalPages);
  const pageStart = (safePage - 1) * ZONES_PER_PAGE;
  const visibleZones = filteredZones.slice(pageStart, pageStart + ZONES_PER_PAGE);

  function goToPage(nextPage) {
    setPage(Math.max(1, Math.min(totalPages, nextPage)));
  }

  return (
    <div className={`grid gap-6 ${isFormOpen ? 'xl:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]' : ''}`}>
      {isFormOpen ? (
        <section id="trial-zone-form" className="rounded-lg border border-line bg-white p-5">
          <MobilePanelJump href="#trial-zone-directory" label="Back to trial zones" />
          <SectionHeader eyebrow="Trial zone setup" title={editingZoneId ? 'Update trial zone' : 'Create trial zone'} />
          <form className="mt-5 space-y-4" onSubmit={submitZone}>
            <div>
              <Select label="Store" value={form.store_id} options={storeOptions} onChange={(value) => setFormField('store_id', value)} />
              {formErrors.store_id ? <p className="mt-1 text-xs text-rose-700">{formErrors.store_id}</p> : null}
              <input
                ref={(el) => {
                  fieldRefs.current.store_id = el;
                }}
                tabIndex={-1}
                className="absolute h-0 w-0 opacity-0"
                aria-hidden="true"
                readOnly
              />
            </div>

            <Field
              label="Trial zone name"
              value={form.name}
              onChange={(value) => setFormField('name', value)}
              error={formErrors.name}
              maxLength={FIELD_LIMITS.name}
              inputRef={(el) => {
                fieldRefs.current.name = el;
              }}
            />

            <div>
              <Select label="Gender" value={form.gender} options={GENDER_OPTIONS} onChange={(value) => setFormField('gender', value)} />
              {formErrors.gender ? <p className="mt-1 text-xs text-rose-700">{formErrors.gender}</p> : null}
            </div>

            <label className="flex items-center justify-between rounded-lg border border-line px-3 py-3">
              <span className="text-sm font-medium text-charcoal">Trial zone active</span>
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
                {editingZoneId ? 'Update trial zone' : 'Save trial zone'}
              </button>
              {editingZoneId ? (
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

      <section id="trial-zone-directory" className="rounded-lg border border-line bg-white">
        <div className="flex items-center justify-between border-b border-line p-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-red">Trial zone directory</p>
            <h2 className="mt-1 text-xl font-semibold">Configured trial zones</h2>
          </div>
          <div className="flex items-center gap-2">
            {isFormOpen ? <MobilePanelJump href="#trial-zone-form" label="Go to form" compact /> : null}
            <button
              type="button"
              onClick={openCreateForm}
              className="inline-flex size-10 items-center justify-center rounded-lg bg-brand-red text-white sm:size-auto sm:gap-2 sm:px-3 sm:py-2 sm:text-sm sm:font-medium"
              title="Create trial zone"
              aria-label="Create trial zone"
            >
              <Plus size={16} />
              <span className="hidden sm:inline">Create trial zone</span>
            </button>
            <button type="button" onClick={loadZones} className="rounded-lg border border-line p-2 text-charcoal hover:border-brand-red" title="Refresh trial zones">
              <RefreshCw size={18} />
            </button>
          </div>
        </div>

        <div className="border-b border-line p-5">
          <div className="flex flex-wrap gap-3">
            <div className="min-w-[220px] flex-1">
              <Select label="Filter by store" value={storeFilter} options={storeFilterOptions} onChange={setStoreFilter} />
            </div>
            <label className="block min-w-[260px] flex-[2]">
              <span className="text-sm font-medium text-charcoal">Search trial zones</span>
              <input
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                  setPage(1);
                }}
                placeholder="Search by trial zone or store"
                className="mt-1 w-full rounded-lg border border-line px-3 py-2.5 outline-none focus:border-brand-red focus:ring-2 focus:ring-brand-soft"
              />
            </label>
          </div>
        </div>

        <div className="divide-y divide-brand-soft">
          {filteredZones.length === 0 ? (
            <p className="p-5 text-sm text-muted">No trial zones found.</p>
          ) : (
            visibleZones.map((zone) => {
              const isEditing = editingZoneId === zone.id;

              return (
                <div
                  key={zone.id}
                  className={`grid gap-3 p-5 lg:grid-cols-[1fr_auto] ${isEditing ? 'bg-brand-blush/50 ring-1 ring-inset ring-brand-soft' : ''}`}
                >
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-semibold">{zone.name}</h3>
                      <span className={`rounded-full px-2 py-1 text-xs ${zone.is_active ? 'bg-brand-blush text-success' : 'bg-rose-50 text-rose-700'}`}>
                        {zone.is_active ? 'Active' : 'Inactive'}
                      </span>
                      {isEditing ? <span className="rounded-full bg-brand-red px-2 py-1 text-xs font-semibold text-white">Editing</span> : null}
                    </div>
                    <p className="mt-1 text-sm text-charcoal">Store: {storeNameById.get(String(zone.store_id)) || `#${zone.store_id}`}</p>
                    <p className="mt-1 text-sm text-charcoal">Gender: {getGenderLabel(zone.gender)}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <ResourceLink to={`/app/trial/admin/zones?store_id=${zone.store_id}`} label="Store zones" />
                      <ResourceLink to={`/app/trial/admin/studios?trial_zone_id=${zone.id}`} label="Studios" />
                      <ResourceLink to={`/app/trial/admin/queue?trial_zone_id=${zone.id}`} label="Quick Trial" />
                      <QrDownloadButton
                        filename={`trial-store-${zone.store_id}-zone-${zone.id}-qr.png`}
                        value={buildPublicAppUrl('/app/trial/customer/create', {
                          store_id: zone.store_id,
                          trial_zone_id: zone.id,
                        })}
                      />
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-2 lg:justify-end">
                    <button
                      type="button"
                      onClick={() => beginEdit(zone)}
                      className={`inline-flex items-center justify-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium disabled:opacity-50 ${
                        isEditing ? 'border-brand-red bg-brand-blush text-brand-red' : 'border-line text-charcoal'
                      }`}
                      disabled={loading}
                    >
                      <Pencil size={16} />
                      {isEditing ? 'Editing' : 'Edit'}
                    </button>
                    <button
                      type="button"
                      onClick={() => openStatusConfirm(zone)}
                      className="inline-flex items-center justify-center gap-2 rounded-lg border border-rose-200 px-3 py-2 text-sm font-medium text-rose-700 disabled:opacity-50"
                      disabled={loading}
                    >
                      {zone.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {filteredZones.length > ZONES_PER_PAGE ? (
          <div className="flex items-center justify-between border-t border-line px-5 py-4">
            <p className="text-xs text-muted">
              Showing {pageStart + 1}-{Math.min(pageStart + ZONES_PER_PAGE, filteredZones.length)} of {filteredZones.length}
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
              {pendingStatusChange.mode === 'deactivate' ? 'Deactivate trial zone?' : 'Activate trial zone?'}
            </h3>
            <p className="mt-2 text-sm text-charcoal">
              {pendingStatusChange.mode === 'deactivate'
                ? `This will mark ${pendingStatusChange.zone.name} as inactive. Continue?`
                : `This will mark ${pendingStatusChange.zone.name} as active. Continue?`}
            </p>

            <div className="mt-5 flex justify-end gap-2">
              <button type="button" onClick={closeStatusConfirm} className="rounded-lg border border-line px-4 py-2 text-sm font-medium text-charcoal">
                Cancel
              </button>
              <button type="button" onClick={confirmStatusChange} className="rounded-lg bg-brand-red px-4 py-2 text-sm font-semibold text-white">
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

function Field({ label, value, onChange, error, maxLength, inputRef }) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-charcoal">{label}</span>
      <input
        ref={inputRef}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        maxLength={maxLength}
        className={`mt-1 w-full rounded-lg border px-3 py-2.5 outline-none focus:ring-2 ${
          error ? 'border-rose-400 focus:border-rose-500 focus:ring-rose-100' : 'border-line focus:border-brand-red focus:ring-brand-soft'
        }`}
      />
      {error ? <p className="mt-1 text-xs text-rose-700">{error}</p> : null}
    </label>
  );
}
