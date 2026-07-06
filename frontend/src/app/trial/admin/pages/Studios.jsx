import { Pencil, Plus, RefreshCw, Save, X } from 'lucide-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

import { getErrorMessage, showApiErrorToast } from '../../../../api/httpClient.js';
import { createTrialStudio, deleteTrialStudio, listTrialStudios, updateTrialStudio } from '../../../../api/trial/studiosApi.js';
import { listStores } from '../../../../api/trial/storeApi.js';
import { listTrialZones } from '../../../../api/trial/zonesApi.js';
import { Select } from '../../../common/FormAndStatePrimitives.jsx';
import { SectionHeader } from '../../../common/SectionHeader.jsx';

const emptyStudio = {
  store_id: '',
  trial_zone_id: '',
  studio_type: 'REGULAR',
  name: '',
  is_active: true,
};

const FIELD_LIMITS = {
  name: 100,
};

const STUDIOS_PER_PAGE = 8;
const DEFAULT_STUDIO_TYPE = 'REGULAR';
const FIELD_ORDER = ['store_id', 'trial_zone_id', 'name'];

const STUDIO_TYPE_OPTIONS = [
  { label: 'Select studio type', value: '' },
  { label: 'Regular', value: 'REGULAR' },
  { label: 'Express', value: 'EXPRESS' },
  { label: 'Priority', value: 'PRIORITY' },
];

function getStudioTypeLabel(studioType) {
  return STUDIO_TYPE_OPTIONS.find((option) => option.value === studioType)?.label || studioType;
}

export function Studios() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [studios, setStudios] = useState([]);
  const [stores, setStores] = useState([]);
  const [zones, setZones] = useState([]);
  const [form, setForm] = useState(emptyStudio);
  const [initialFormState, setInitialFormState] = useState(emptyStudio);
  const [formErrors, setFormErrors] = useState({});
  const [editingStudioId, setEditingStudioId] = useState(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [pendingStatusChange, setPendingStatusChange] = useState(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const fieldRefs = useRef({});
  const storeFilter = searchParams.get('store_id') || '';
  const zoneFilter = searchParams.get('trial_zone_id') || '';

  const zoneById = useMemo(() => {
    const map = new Map();
    for (const zone of zones) {
      map.set(String(zone.id), zone);
    }
    return map;
  }, [zones]);

  const storeNameById = useMemo(() => {
    const map = new Map();
    for (const store of stores) {
      map.set(String(store.id), store.name);
    }
    return map;
  }, [stores]);

  const zoneNameById = useMemo(() => {
    const map = new Map();
    for (const zone of zones) {
      map.set(String(zone.id), zone.name);
    }
    return map;
  }, [zones]);

  const storeOptions = [
    { label: 'Select store', value: '' },
    ...stores.map((store) => ({
      label: `${store.name} (${store.store_number})`,
      value: String(store.id),
    })),
  ];

  const zoneOptions = [
    { label: 'Select trial zone', value: '' },
    ...zones
      .filter((zone) => !form.store_id || String(zone.store_id) === form.store_id)
      .map((zone) => ({
        label: zone.name,
        value: String(zone.id),
      })),
  ];

  const storeFilterOptions = [
    { label: 'All stores', value: '' },
    ...stores.map((store) => ({
      label: `${store.name} (${store.store_number})`,
      value: String(store.id),
    })),
  ];

  const zoneFilterOptions = [
    { label: 'All trial zones', value: '' },
    ...zones
      .filter((zone) => !storeFilter || String(zone.store_id) === storeFilter)
      .map((zone) => ({
        label: `${zone.name} (${storeNameById.get(String(zone.store_id)) || `#${zone.store_id}`})`,
        value: String(zone.id),
      })),
  ];

  function setStudioFilter(field, value) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) {
        next.set(field, value);
      } else {
        next.delete(field);
      }
      if (field === 'store_id') {
        next.delete('trial_zone_id');
      }
      return next;
    });
    setPage(1);
  }

  function toPayload(values) {
    return {
      trial_zone_id: Number(values.trial_zone_id),
      studio_type: values.studio_type || DEFAULT_STUDIO_TYPE,
      name: values.name.trim() || null,
      is_active: values.is_active,
    };
  }

  function validateStudioForm(values) {
    const errors = {};

    if (!values.store_id) {
      errors.store_id = 'Store is required.';
    }

    if (!values.trial_zone_id) {
      errors.trial_zone_id = 'Trial zone is required.';
    }

    if (values.name.trim().length > FIELD_LIMITS.name) {
      errors.name = `Studio name must be at most ${FIELD_LIMITS.name} characters.`;
    }

    return errors;
  }

  function setFormField(field, value) {
    setForm((prev) => {
      if (field === 'store_id') {
        return { ...prev, store_id: value, trial_zone_id: '' };
      }
      return { ...prev, [field]: value };
    });

    setFormErrors((prev) => {
      const nextErrors = { ...prev };
      delete nextErrors[field];
      if (field === 'store_id') {
        delete nextErrors.trial_zone_id;
      }
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

  function beginEdit(studio) {
    if (isFormOpen && !confirmDiscardIfDirty()) {
      return;
    }

    const relatedZone = zoneById.get(String(studio.trial_zone_id));
    const nextForm = {
      store_id: relatedZone ? String(relatedZone.store_id) : '',
      trial_zone_id: String(studio.trial_zone_id),
      studio_type: studio.studio_type || DEFAULT_STUDIO_TYPE,
      name: studio.name || '',
      is_active: Boolean(studio.is_active),
    };

    setEditingStudioId(studio.id);
    setForm(nextForm);
    setInitialFormState(nextForm);
    setFormErrors({});
    setIsFormOpen(true);
    setMessage('Editing studio details.');
  }

  function openCreateForm() {
    if (isFormOpen && !confirmDiscardIfDirty()) {
      return;
    }

    setEditingStudioId(null);
    setForm(emptyStudio);
    setInitialFormState(emptyStudio);
    setFormErrors({});
    setMessage('');
    setIsFormOpen(true);
  }

  function resetFormState(options = { force: false, closeForm: false }) {
    if (!options.force && !confirmDiscardIfDirty()) {
      return;
    }

    setEditingStudioId(null);
    setForm(emptyStudio);
    setInitialFormState(emptyStudio);
    setFormErrors({});
    if (options.closeForm) {
      setIsFormOpen(false);
    }
  }

  const loadStudios = useCallback(async () => {
    setLoading(true);
    setMessage('');
    try {
      setStudios(
        await listTrialStudios({
          include_inactive: true,
          ...(storeFilter ? { store_id: Number(storeFilter) } : {}),
          ...(zoneFilter ? { trial_zone_id: Number(zoneFilter) } : {}),
        })
      );
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [storeFilter, zoneFilter]);

  async function loadStores() {
    try {
      setStores(await listStores({ include_inactive: true }));
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    }
  }

  async function loadZones() {
    try {
      setZones(await listTrialZones({ include_inactive: true }));
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    }
  }

  useEffect(() => {
    loadStudios();
  }, [loadStudios]);

  useEffect(() => {
    loadStores();
    loadZones();
  }, []);

  async function submitStudio(event) {
    event.preventDefault();
    const validationErrors = validateStudioForm(form);
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
      if (editingStudioId) {
        await updateTrialStudio(editingStudioId, payload);
        setMessage('Studio updated');
        resetFormState({ force: true, closeForm: false });
      } else {
        await createTrialStudio(payload);
        setMessage('Studio created');
        resetFormState({ force: true, closeForm: true });
      }
      await loadStudios();
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function deactivateStudio(studioId) {
    setLoading(true);
    setMessage('');
    try {
      await deleteTrialStudio(studioId);
      setMessage('Studio deactivated');
      await loadStudios();
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function toggleStudioActive(studio) {
    setLoading(true);
    setMessage('');
    try {
      await updateTrialStudio(studio.id, { is_active: !studio.is_active });
      setMessage(studio.is_active ? 'Studio deactivated' : 'Studio activated');
      await loadStudios();
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  function openStatusConfirm(studio) {
    setPendingStatusChange({
      studio,
      mode: studio.is_active ? 'deactivate' : 'activate',
    });
  }

  function closeStatusConfirm() {
    setPendingStatusChange(null);
  }

  async function confirmStatusChange() {
    if (!pendingStatusChange) return;
    const { studio, mode } = pendingStatusChange;
    closeStatusConfirm();

    if (mode === 'deactivate') {
      await deactivateStudio(studio.id);
      return;
    }

    await toggleStudioActive(studio);
  }

  const normalizedQuery = query.trim().toLowerCase();
  const filteredStudios = studios.filter((studio) => {
    if (!normalizedQuery) return true;

    const zone = zoneById.get(String(studio.trial_zone_id));
    const zoneName = zone?.name || '';
    const storeName = zone ? storeNameById.get(String(zone.store_id)) || '' : '';
    const haystack = `${studio.name || ''} ${zoneName} ${storeName}`.toLowerCase();
    return haystack.includes(normalizedQuery);
  });

  const totalPages = Math.max(1, Math.ceil(filteredStudios.length / STUDIOS_PER_PAGE));
  const safePage = Math.min(page, totalPages);
  const pageStart = (safePage - 1) * STUDIOS_PER_PAGE;
  const visibleStudios = filteredStudios.slice(pageStart, pageStart + STUDIOS_PER_PAGE);

  function goToPage(nextPage) {
    setPage(Math.max(1, Math.min(totalPages, nextPage)));
  }

  return (
    <div className={`grid gap-6 ${isFormOpen ? 'xl:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]' : ''}`}>
      {isFormOpen ? (
        <section id="studio-form" className="rounded-lg border border-line bg-white p-5">
          <MobilePanelJump href="#studio-directory" label="Back to studios" />
          <SectionHeader eyebrow="Studio setup" title={editingStudioId ? 'Update studio' : 'Create studio'} />
          <form className="mt-5 space-y-4" onSubmit={submitStudio}>
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

            <div>
              <Select label="Trial zone" value={form.trial_zone_id} options={zoneOptions} onChange={(value) => setFormField('trial_zone_id', value)} />
              {formErrors.trial_zone_id ? <p className="mt-1 text-xs text-rose-700">{formErrors.trial_zone_id}</p> : null}
              <input
                ref={(el) => {
                  fieldRefs.current.trial_zone_id = el;
                }}
                tabIndex={-1}
                className="absolute h-0 w-0 opacity-0"
                aria-hidden="true"
                readOnly
              />
            </div>

            <Field
              label="Studio name"
              value={form.name}
              onChange={(value) => setFormField('name', value)}
              error={formErrors.name}
              maxLength={FIELD_LIMITS.name}
              inputRef={(el) => {
                fieldRefs.current.name = el;
              }}
            />

            {/* <div>
              <Select label="Studio type" value={form.studio_type} options={STUDIO_TYPE_OPTIONS} onChange={(value) => setFormField('studio_type', value)} />
              {formErrors.studio_type ? <p className="mt-1 text-xs text-rose-700">{formErrors.studio_type}</p> : null}
            </div> */}

            <label className="flex items-center justify-between rounded-lg border border-line px-3 py-3">
              <span className="text-sm font-medium text-charcoal">Studio active</span>
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
                {editingStudioId ? 'Update studio' : 'Save studio'}
              </button>
              {editingStudioId ? (
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

      <section id="studio-directory" className="rounded-lg border border-line bg-white">
        <div className="flex items-center justify-between border-b border-line p-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-red">Studio directory</p>
            <h2 className="mt-1 text-xl font-semibold">Configured studios</h2>
          </div>
          <div className="flex items-center gap-2">
            {isFormOpen ? <MobilePanelJump href="#studio-form" label="Go to form" compact /> : null}
            <button
              type="button"
              onClick={openCreateForm}
              className="inline-flex size-10 items-center justify-center rounded-lg bg-brand-red text-white sm:size-auto sm:gap-2 sm:px-3 sm:py-2 sm:text-sm sm:font-medium"
              title="Create studio"
              aria-label="Create studio"
            >
              <Plus size={16} />
              <span className="hidden sm:inline">Create studio</span>
            </button>
            <button type="button" onClick={loadStudios} className="rounded-lg border border-line p-2 text-charcoal hover:border-brand-red" title="Refresh studios">
              <RefreshCw size={18} />
            </button>
          </div>
        </div>

        <div className="border-b border-line p-5">
          <div className="flex flex-wrap gap-3">
            <div className="min-w-[220px] flex-1">
              <Select label="Filter by store" value={storeFilter} options={storeFilterOptions} onChange={(value) => setStudioFilter('store_id', value)} />
            </div>
            <div className="min-w-[220px] flex-1">
              <Select label="Filter by trial zone" value={zoneFilter} options={zoneFilterOptions} onChange={(value) => setStudioFilter('trial_zone_id', value)} />
            </div>
            <label className="block min-w-[260px] flex-[2]">
              <span className="text-sm font-medium text-charcoal">Search studios</span>
              <input
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                  setPage(1);
                }}
                placeholder="Search by studio, trial zone, or store"
                className="mt-1 w-full rounded-lg border border-line px-3 py-2.5 outline-none focus:border-brand-red focus:ring-2 focus:ring-brand-soft"
              />
            </label>
          </div>
        </div>

        <div className="divide-y divide-brand-soft">
          {filteredStudios.length === 0 ? (
            <p className="p-5 text-sm text-muted">No studios found.</p>
          ) : (
            visibleStudios.map((studio) => {
              const isEditing = editingStudioId === studio.id;
              const zone = zoneById.get(String(studio.trial_zone_id));
              const zoneName = zoneNameById.get(String(studio.trial_zone_id)) || `#${studio.trial_zone_id}`;
              const storeName = zone ? storeNameById.get(String(zone.store_id)) : null;
              const studioName = studio.name || `Studio #${studio.id}`;

              return (
                <div
                  key={studio.id}
                  className={`grid gap-3 p-5 lg:grid-cols-[1fr_auto] ${isEditing ? 'bg-brand-blush/50 ring-1 ring-inset ring-brand-soft' : ''}`}
                >
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-semibold">{studioName}</h3>
                      <span className={`rounded-full px-2 py-1 text-xs ${studio.is_active ? 'bg-brand-blush text-success' : 'bg-rose-50 text-rose-700'}`}>
                        {studio.is_active ? 'Active' : 'Inactive'}
                      </span>
                      {isEditing ? <span className="rounded-full bg-brand-red px-2 py-1 text-xs font-semibold text-white">Editing</span> : null}
                    </div>
                    <p className="mt-1 text-sm text-charcoal">
                      Trial zone: {zoneName}
                      {storeName ? ` | Store: ${storeName}` : ''}
                    </p>
                    <p className="mt-1 text-sm text-charcoal">Type: {getStudioTypeLabel(studio.studio_type)}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {zone ? <ResourceLink to={`/app/trial/admin/zones?store_id=${zone.store_id}`} label="Store zones" /> : null}
                      <ResourceLink to={`/app/trial/admin/studios?trial_zone_id=${studio.trial_zone_id}`} label="Zone studios" />
                      <ResourceLink to={`/app/trial/admin/queue?studio_id=${studio.id}`} label="Trial queue" />
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-2 lg:justify-end">
                    <button
                      type="button"
                      onClick={() => beginEdit(studio)}
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
                      onClick={() => openStatusConfirm(studio)}
                      className="inline-flex items-center justify-center gap-2 rounded-lg border border-rose-200 px-3 py-2 text-sm font-medium text-rose-700 disabled:opacity-50"
                      disabled={loading}
                    >
                      {studio.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {filteredStudios.length > STUDIOS_PER_PAGE ? (
          <div className="flex items-center justify-between border-t border-line px-5 py-4">
            <p className="text-xs text-muted">
              Showing {pageStart + 1}-{Math.min(pageStart + STUDIOS_PER_PAGE, filteredStudios.length)} of {filteredStudios.length}
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
              {pendingStatusChange.mode === 'deactivate' ? 'Deactivate studio?' : 'Activate studio?'}
            </h3>
            <p className="mt-2 text-sm text-charcoal">
              {pendingStatusChange.mode === 'deactivate'
                ? `This will mark ${pendingStatusChange.studio.name || `Studio #${pendingStatusChange.studio.id}`} as inactive. Continue?`
                : `This will mark ${pendingStatusChange.studio.name || `Studio #${pendingStatusChange.studio.id}`} as active. Continue?`}
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
