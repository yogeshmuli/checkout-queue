import { Pencil, Plus, RefreshCw, Save, Trash2, X } from 'lucide-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

import { createCounter, deleteCounter, listCounters, updateCounter } from '../../../api/counterApi.js';
import { getErrorMessage, showApiErrorToast } from '../../../api/httpClient.js';
import { listSections } from '../../../api/sectionApi.js';
import { listStores } from '../../../api/storeApi.js';
import { Select } from '../../common/FormAndStatePrimitives.jsx';
import { SectionHeader } from '../../common/SectionHeader.jsx';

const emptyCounter = {
  store_id: '',
  section_id: '',
  counter_type: '',
  name: '',
  is_active: true,
};

const FIELD_LIMITS = {
  name: 100,
};

const COUNTER_TYPE_OPTIONS = [
  { label: 'Select counter type', value: '' },
  { label: 'Regular', value: 'REGULAR' },
  { label: 'Express', value: 'EXPRESS' },
  { label: 'Self Checkout', value: 'SELF_CHECKOUT' },
  { label: 'Returns / Exchange', value: 'RETURNS_EXCHANGE' },
  { label: 'Priority', value: 'PRIORITY' },
];

const COUNTERS_PER_PAGE = 8;
const FIELD_ORDER = ['store_id', 'section_id', 'counter_type', 'name'];

function getCounterTypeLabel(counterType) {
  return COUNTER_TYPE_OPTIONS.find((option) => option.value === counterType)?.label || counterType;
}

export function Counters() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [counters, setCounters] = useState([]);
  const [stores, setStores] = useState([]);
  const [sections, setSections] = useState([]);
  const [form, setForm] = useState(emptyCounter);
  const [initialFormState, setInitialFormState] = useState(emptyCounter);
  const [formErrors, setFormErrors] = useState({});
  const [editingCounterId, setEditingCounterId] = useState(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [pendingStatusChange, setPendingStatusChange] = useState(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const fieldRefs = useRef({});
  const storeFilter = searchParams.get('store_id') || '';
  const sectionFilter = searchParams.get('section_id') || '';

  const sectionById = useMemo(() => {
    const map = new Map();
    for (const section of sections) {
      map.set(String(section.id), section);
    }
    return map;
  }, [sections]);

  const storeNameById = useMemo(() => {
    const map = new Map();
    for (const store of stores) {
      map.set(String(store.id), store.name);
    }
    return map;
  }, [stores]);

  const sectionNameById = useMemo(() => {
    const map = new Map();
    for (const section of sections) {
      map.set(String(section.id), section.name);
    }
    return map;
  }, [sections]);

  const storeOptions = [
    { label: 'Select store', value: '' },
    ...stores.map((store) => ({
      label: `${store.name} (${store.store_number})`,
      value: String(store.id),
    })),
  ];

  const sectionOptions = [
    { label: 'Select section', value: '' },
    ...sections
      .filter((section) => !form.store_id || String(section.store_id) === form.store_id)
      .map((section) => ({
        label: `${section.name} (${section.section_type})`,
        value: String(section.id),
      })),
  ];

  const storeFilterOptions = [
    { label: 'All stores', value: '' },
    ...stores.map((store) => ({
      label: `${store.name} (${store.store_number})`,
      value: String(store.id),
    })),
  ];

  const sectionFilterOptions = [
    { label: 'All sections', value: '' },
    ...sections
      .filter((section) => !storeFilter || String(section.store_id) === storeFilter)
      .map((section) => ({
        label: `${section.name} (${storeNameById.get(String(section.store_id)) || `#${section.store_id}`})`,
        value: String(section.id),
      })),
  ];

  function setCounterFilter(field, value) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) {
        next.set(field, value);
      } else {
        next.delete(field);
      }
      if (field === 'store_id') {
        next.delete('section_id');
      }
      return next;
    });
    setPage(1);
  }

  function toPayload(values) {
    return {
      section_id: Number(values.section_id),
      counter_type: values.counter_type,
      name: values.name.trim() || null,
      is_active: values.is_active,
    };
  }

  function validateCounterForm(values) {
    const errors = {};

    if (!values.store_id) {
      errors.store_id = 'Store is required.';
    }

    if (!values.section_id) {
      errors.section_id = 'Section is required.';
    }

    if (!values.counter_type) {
      errors.counter_type = 'Counter type is required.';
    }

    if (values.name.trim().length > FIELD_LIMITS.name) {
      errors.name = `Counter name must be at most ${FIELD_LIMITS.name} characters.`;
    }

    return errors;
  }

  function setFormField(field, value) {
    setForm((prev) => {
      if (field === 'store_id') {
        return { ...prev, store_id: value, section_id: '' };
      }
      return { ...prev, [field]: value };
    });

    setFormErrors((prev) => {
      const nextErrors = { ...prev };
      delete nextErrors[field];
      if (field === 'store_id') {
        delete nextErrors.section_id;
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

  function beginEdit(counter) {
    if (isFormOpen && !confirmDiscardIfDirty()) {
      return;
    }

    const relatedSection = sectionById.get(String(counter.section_id));
    const nextForm = {
      store_id: relatedSection ? String(relatedSection.store_id) : '',
      section_id: String(counter.section_id),
      counter_type: counter.counter_type || '',
      name: counter.name || '',
      is_active: Boolean(counter.is_active),
    };

    setEditingCounterId(counter.id);
    setForm(nextForm);
    setInitialFormState(nextForm);
    setFormErrors({});
    setIsFormOpen(true);
    setMessage('Editing counter details.');
  }

  function openCreateForm() {
    if (isFormOpen && !confirmDiscardIfDirty()) {
      return;
    }

    setEditingCounterId(null);
    setForm(emptyCounter);
    setInitialFormState(emptyCounter);
    setFormErrors({});
    setMessage('');
    setIsFormOpen(true);
  }

  function resetFormState(options = { force: false, closeForm: false }) {
    if (!options.force && !confirmDiscardIfDirty()) {
      return;
    }

    setEditingCounterId(null);
    setForm(emptyCounter);
    setInitialFormState(emptyCounter);
    setFormErrors({});
    if (options.closeForm) {
      setIsFormOpen(false);
    }
  }

  const loadCounters = useCallback(async () => {
    setLoading(true);
    setMessage('');
    try {
      setCounters(
        await listCounters({
          include_inactive: true,
          ...(storeFilter ? { store_id: Number(storeFilter) } : {}),
          ...(sectionFilter ? { section_id: Number(sectionFilter) } : {}),
        })
      );
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [sectionFilter, storeFilter]);

  async function loadStores() {
    try {
      setStores(await listStores({ include_inactive: true }));
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    }
  }

  async function loadSections() {
    try {
      setSections(await listSections({ include_inactive: true }));
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    }
  }

  useEffect(() => {
    loadCounters();
  }, [loadCounters]);

  useEffect(() => {
    loadStores();
    loadSections();
  }, []);

  async function submitCounter(event) {
    event.preventDefault();
    const validationErrors = validateCounterForm(form);
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
      if (editingCounterId) {
        await updateCounter(editingCounterId, payload);
        setMessage('Counter updated');
        resetFormState({ force: true, closeForm: false });
      } else {
        await createCounter(payload);
        setMessage('Counter created');
        resetFormState({ force: true, closeForm: true });
      }
      await loadCounters();
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function deactivateCounter(counterId) {
    setLoading(true);
    setMessage('');
    try {
      await deleteCounter(counterId);
      setMessage('Counter deactivated');
      await loadCounters();
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function toggleCounterActive(counter) {
    setLoading(true);
    setMessage('');
    try {
      await updateCounter(counter.id, { is_active: !counter.is_active });
      setMessage(counter.is_active ? 'Counter deactivated' : 'Counter activated');
      await loadCounters();
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  function openStatusConfirm(counter) {
    setPendingStatusChange({
      counter,
      mode: counter.is_active ? 'deactivate' : 'activate',
    });
  }

  function closeStatusConfirm() {
    setPendingStatusChange(null);
  }

  async function confirmStatusChange() {
    if (!pendingStatusChange) return;
    const { counter, mode } = pendingStatusChange;
    closeStatusConfirm();

    if (mode === 'deactivate') {
      await deactivateCounter(counter.id);
      return;
    }

    await toggleCounterActive(counter);
  }

  const normalizedQuery = query.trim().toLowerCase();
  const filteredCounters = counters.filter((counter) => {
    if (!normalizedQuery) return true;

    const section = sectionById.get(String(counter.section_id));
    const sectionName = section?.name || '';
    const storeName = section ? storeNameById.get(String(section.store_id)) || '' : '';
    const counterTypeLabel = getCounterTypeLabel(counter.counter_type);
    const haystack = `${counter.name || ''} ${counter.counter_type || ''} ${counterTypeLabel} ${sectionName} ${storeName}`.toLowerCase();
    return haystack.includes(normalizedQuery);
  });

  const totalPages = Math.max(1, Math.ceil(filteredCounters.length / COUNTERS_PER_PAGE));
  const safePage = Math.min(page, totalPages);
  const pageStart = (safePage - 1) * COUNTERS_PER_PAGE;
  const visibleCounters = filteredCounters.slice(pageStart, pageStart + COUNTERS_PER_PAGE);

  function goToPage(nextPage) {
    setPage(Math.max(1, Math.min(totalPages, nextPage)));
  }

  return (
    <div className={`grid gap-6 ${isFormOpen ? 'xl:grid-cols-[2fr_1fr]' : ''}`}>
      {isFormOpen ? (
        <section id="counter-form" className="rounded-lg border border-line bg-white p-5">
          <MobilePanelJump href="#counter-directory" label="Back to counters" />
          <SectionHeader eyebrow="Counter setup" title={editingCounterId ? 'Update counter' : 'Create counter'} />
          <form className="mt-5 space-y-4" onSubmit={submitCounter}>
            <div>
              <Select
                label="Store"
                value={form.store_id}
                options={storeOptions}
                onChange={(value) => setFormField('store_id', value)}
              />
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
              <Select
                label="Section"
                value={form.section_id}
                options={sectionOptions}
                onChange={(value) => setFormField('section_id', value)}
              />
              {formErrors.section_id ? <p className="mt-1 text-xs text-rose-700">{formErrors.section_id}</p> : null}
              <input
                ref={(el) => {
                  fieldRefs.current.section_id = el;
                }}
                tabIndex={-1}
                className="absolute h-0 w-0 opacity-0"
                aria-hidden="true"
                readOnly
              />
            </div>

            <div>
              <Select
                label="Counter type"
                value={form.counter_type}
                options={COUNTER_TYPE_OPTIONS}
                onChange={(value) => setFormField('counter_type', value)}
              />
              {formErrors.counter_type ? <p className="mt-1 text-xs text-rose-700">{formErrors.counter_type}</p> : null}
              <input
                ref={(el) => {
                  fieldRefs.current.counter_type = el;
                }}
                tabIndex={-1}
                className="absolute h-0 w-0 opacity-0"
                aria-hidden="true"
                readOnly
              />
            </div>

            <Field
              label="Counter name"
              value={form.name}
              onChange={(value) => setFormField('name', value)}
              error={formErrors.name}
              maxLength={FIELD_LIMITS.name}
              inputRef={(el) => {
                fieldRefs.current.name = el;
              }}
            />

            <label className="flex items-center justify-between rounded-lg border border-line px-3 py-3">
              <span className="text-sm font-medium text-charcoal">Counter active</span>
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
                {editingCounterId ? 'Update counter' : 'Save counter'}
              </button>
              {editingCounterId ? (
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

      <section id="counter-directory" className="rounded-lg border border-line bg-white">
        <div className="flex items-center justify-between border-b border-line p-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-red">Counter directory</p>
            <h2 className="mt-1 text-xl font-semibold">Configured counters</h2>
          </div>
          <div className="flex items-center gap-2">
            {isFormOpen ? <MobilePanelJump href="#counter-form" label="Go to form" compact /> : null}
            <button
              type="button"
              onClick={openCreateForm}
              className="inline-flex size-10 items-center justify-center rounded-lg bg-brand-red text-white sm:size-auto sm:gap-2 sm:px-3 sm:py-2 sm:text-sm sm:font-medium"
              title="Create counter"
              aria-label="Create counter"
            >
              <Plus size={16} />
              <span className="hidden sm:inline">Create counter</span>
            </button>
            <button type="button" onClick={loadCounters} className="rounded-lg border border-line p-2 text-charcoal hover:border-brand-red" title="Refresh counters">
              <RefreshCw size={18} />
            </button>
          </div>
        </div>

        <div className="border-b border-line p-5">
          <div className="grid gap-3 lg:grid-cols-[280px_320px_1fr]">
            <Select label="Filter by store" value={storeFilter} options={storeFilterOptions} onChange={(value) => setCounterFilter('store_id', value)} />
            <Select label="Filter by section" value={sectionFilter} options={sectionFilterOptions} onChange={(value) => setCounterFilter('section_id', value)} />
            <label className="block">
              <span className="text-sm font-medium text-charcoal">Search counters</span>
              <input
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                  setPage(1);
                }}
                placeholder="Search by counter, type, section, or store"
                className="mt-1 w-full rounded-lg border border-line px-3 py-2.5 outline-none focus:border-brand-red focus:ring-2 focus:ring-brand-soft"
              />
            </label>
          </div>
        </div>

        <div className="divide-y divide-brand-soft">
          {filteredCounters.length === 0 ? (
            <p className="p-5 text-sm text-muted">No counters found.</p>
          ) : (
            visibleCounters.map((counter) => {
              const isEditing = editingCounterId === counter.id;
              const section = sectionById.get(String(counter.section_id));
              const sectionName = sectionNameById.get(String(counter.section_id)) || `#${counter.section_id}`;
              const storeName = section ? storeNameById.get(String(section.store_id)) : null;

              return (
                <div
                  key={counter.id}
                  className={`grid gap-3 p-5 lg:grid-cols-[1fr_auto] ${isEditing ? 'bg-brand-blush/50 ring-1 ring-inset ring-brand-soft' : ''}`}
                >
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-semibold">{counter.name || `Counter #${counter.id}`}</h3>
                      <span className="rounded-full bg-brand-blush px-2 py-1 text-xs text-charcoal">{getCounterTypeLabel(counter.counter_type)}</span>
                      <span className={`rounded-full px-2 py-1 text-xs ${counter.is_active ? 'bg-brand-blush text-success' : 'bg-rose-50 text-rose-700'}`}>
                        {counter.is_active ? 'Active' : 'Inactive'}
                      </span>
                      {isEditing ? <span className="rounded-full bg-brand-red px-2 py-1 text-xs font-semibold text-white">Editing</span> : null}
                    </div>
                    <p className="mt-1 text-sm text-charcoal">
                      Section: {sectionName}
                      {storeName ? ` | Store: ${storeName}` : ''}
                    </p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {section ? <ResourceLink to={`/app/admin/sections?store_id=${section.store_id}`} label="Store sections" /> : null}
                      <ResourceLink to={`/app/admin/counters?section_id=${counter.section_id}`} label="Section counters" />
                      <ResourceLink to={`/app/admin/staff?counter_id=${counter.id}`} label="Staff" />
                      <ResourceLink to={`/app/admin/queue?counter_id=${counter.id}`} label="Queue" />
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-2 lg:justify-end">
                    <button
                      type="button"
                      onClick={() => beginEdit(counter)}
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
                      onClick={() => openStatusConfirm(counter)}
                      className="inline-flex items-center justify-center gap-2 rounded-lg border border-rose-200 px-3 py-2 text-sm font-medium text-rose-700 disabled:opacity-50"
                      disabled={loading}
                    >
                      <Trash2 size={16} />
                      {counter.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {filteredCounters.length > COUNTERS_PER_PAGE ? (
          <div className="flex items-center justify-between border-t border-line px-5 py-4">
            <p className="text-xs text-muted">
              Showing {pageStart + 1}-{Math.min(pageStart + COUNTERS_PER_PAGE, filteredCounters.length)} of {filteredCounters.length}
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
              {pendingStatusChange.mode === 'deactivate' ? 'Deactivate counter?' : 'Activate counter?'}
            </h3>
            <p className="mt-2 text-sm text-charcoal">
              {pendingStatusChange.mode === 'deactivate'
                ? `This will mark ${pendingStatusChange.counter.name || `Counter #${pendingStatusChange.counter.id}`} as inactive. Continue?`
                : `This will mark ${pendingStatusChange.counter.name || `Counter #${pendingStatusChange.counter.id}`} as active. Continue?`}
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
