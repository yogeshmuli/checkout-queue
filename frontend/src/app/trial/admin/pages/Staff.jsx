import { Pencil, Plus, RefreshCw, Save, Trash2, X } from 'lucide-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { getErrorMessage, showApiErrorToast } from '../../../../api/httpClient.js';
import { createStaff, deleteStaff, listStaff, updateStaff } from '../../../../api/checkout/staffApi.js';
import { listStores } from '../../../../api/checkout/storeApi.js';
import { listTrialStudios } from '../../../../api/trial/studiosApi.js';
import { listTrialZones } from '../../../../api/trial/zonesApi.js';
import { Select } from '../../../common/FormAndStatePrimitives.jsx';
import { SectionHeader } from '../../../common/SectionHeader.jsx';

const emptyStaff = {
  email: '',
  password: '',
  full_name: '',
  phone_number: '',
  default_role: 'TRIAL_ZONE_ASSISTANT',
  store_id: '',
  assigned_zone_id: '',
  is_active: true,
};

const FIELD_LIMITS = {
  email: 255,
  password: 128,
  full_name: 150,
  phone: 10,
};

const DEFAULT_STAFF_PASSWORD = 'Ganesh@123';

const ROLE_OPTIONS = [
  { label: 'Trial zone assistant', value: 'TRIAL_ZONE_ASSISTANT' },
  { label: 'Manager', value: 'MANAGER' },
  { label: 'Store admin', value: 'STORE_ADMIN' },
  { label: 'Support', value: 'SUPPORT' },
  { label: 'Cashier', value: 'CASHIER' },
];

const STAFF_PER_PAGE = 8;
const FIELD_ORDER = ['email', 'password', 'full_name', 'phone_number', 'store_id', 'assigned_zone_id'];

export function Staff() {
  const [staff, setStaff] = useState([]);
  const [stores, setStores] = useState([]);
  const [zones, setZones] = useState([]);
  const [studios, setStudios] = useState([]);
  const [form, setForm] = useState(emptyStaff);
  const [initialFormState, setInitialFormState] = useState(emptyStaff);
  const [formErrors, setFormErrors] = useState({});
  const [editingStaffId, setEditingStaffId] = useState(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [pendingStatusChange, setPendingStatusChange] = useState(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');
  const [storeFilter, setStoreFilter] = useState('');
  const [zoneFilter, setZoneFilter] = useState('');
  const [page, setPage] = useState(1);
  const fieldRefs = useRef({});

  const isTrialAssistantRole = form.default_role === 'TRIAL_ZONE_ASSISTANT';

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

  // Trial staff API persists assigned_studio_id, so zone assignment maps to the zone's first active studio.
  const primaryStudioByZoneId = useMemo(() => {
    const map = new Map();
    for (const studio of studios) {
      const zoneKey = String(studio.trial_zone_id);
      if (!map.has(zoneKey) || studio.is_active) {
        map.set(zoneKey, studio);
      }
    }
    return map;
  }, [studios]);

  const studioById = useMemo(() => {
    const map = new Map();
    for (const studio of studios) {
      map.set(String(studio.id), studio);
    }
    return map;
  }, [studios]);

  const storeOptions = [
    { label: 'No store', value: '' },
    ...stores.map((store) => ({
      label: `${store.name} (${store.store_number})`,
      value: String(store.id),
    })),
  ];

  const zoneOptions = [
    { label: 'No zone', value: '' },
    ...zones
      .filter((zone) => !form.store_id || String(zone.store_id) === String(form.store_id))
      .filter((zone) => primaryStudioByZoneId.has(String(zone.id)))
      .map((zone) => ({
        label: `${zone.name} (${storeNameById.get(String(zone.store_id)) || `#${zone.store_id}`})`,
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
    { label: 'All zones', value: '' },
    ...zones
      .filter((zone) => !storeFilter || String(zone.store_id) === String(storeFilter))
      .map((zone) => ({
        label: `${zone.name} (${storeNameById.get(String(zone.store_id)) || `#${zone.store_id}`})`,
        value: String(zone.id),
      })),
  ];

  function sanitizePhone(value) {
    return value.replace(/\D/g, '').slice(0, FIELD_LIMITS.phone);
  }

  function toPayload(values) {
    const selectedStudio = values.assigned_zone_id ? primaryStudioByZoneId.get(String(values.assigned_zone_id)) : null;
    return {
      email: values.email.trim().toLowerCase(),
      full_name: values.full_name.trim(),
      phone_number: values.phone_number || null,
      default_role: values.default_role,
      store_id: values.store_id ? Number(values.store_id) : null,
      section_id: null,
      assigned_counter_id: null,
      assigned_studio_id: selectedStudio ? Number(selectedStudio.id) : null,
      is_active: values.is_active,
      ...(editingStaffId ? {} : { password: values.password.trim() || DEFAULT_STAFF_PASSWORD }),
      ...(editingStaffId && values.password.trim() ? { password: values.password.trim() } : {}),
    };
  }

  function validateStaffForm(values) {
    const errors = {};

    if (!values.email.trim()) {
      errors.email = 'Email is required.';
    } else if (values.email.trim().length > FIELD_LIMITS.email) {
      errors.email = `Email must be at most ${FIELD_LIMITS.email} characters.`;
    }

    if (values.password && values.password.length < 8) {
      errors.password = 'Password must be at least 8 characters.';
    } else if (values.password.length > FIELD_LIMITS.password) {
      errors.password = `Password must be at most ${FIELD_LIMITS.password} characters.`;
    }

    if (!values.full_name.trim()) {
      errors.full_name = 'Full name is required.';
    } else if (values.full_name.trim().length > FIELD_LIMITS.full_name) {
      errors.full_name = `Full name must be at most ${FIELD_LIMITS.full_name} characters.`;
    }

    if (values.phone_number && !/^\d{10}$/.test(values.phone_number)) {
      errors.phone_number = 'Phone number must be exactly 10 digits.';
    }

    if (values.default_role === 'TRIAL_ZONE_ASSISTANT' && !values.assigned_zone_id) {
      errors.assigned_zone_id = 'Assigned zone is required for Trial zone assistant.';
    }

    return errors;
  }

  function setFormField(field, value) {
    let nextValue = value;
    if (field === 'phone_number') {
      nextValue = sanitizePhone(value);
    }

    setForm((prev) => {
      const nextForm = { ...prev, [field]: nextValue };
      if (field === 'store_id' && prev.store_id !== nextValue) {
        nextForm.assigned_zone_id = '';
      }
      if (field === 'default_role' && prev.default_role !== nextValue && nextValue !== 'TRIAL_ZONE_ASSISTANT') {
        nextForm.assigned_zone_id = '';
      }
      return nextForm;
    });

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

  function beginEdit(staffUser) {
    if (isFormOpen && !confirmDiscardIfDirty()) {
      return;
    }

    const assignedStudio = staffUser.assigned_studio_id ? studioById.get(String(staffUser.assigned_studio_id)) : null;
    const assignedZoneId = assignedStudio ? String(assignedStudio.trial_zone_id) : '';

    const nextForm = {
      email: staffUser.email || '',
      password: '',
      full_name: staffUser.full_name || '',
      phone_number: staffUser.phone_number || '',
      default_role: staffUser.default_role || 'TRIAL_ZONE_ASSISTANT',
      store_id: staffUser.store_id ? String(staffUser.store_id) : '',
      assigned_zone_id: assignedZoneId,
      is_active: Boolean(staffUser.is_active),
    };

    setEditingStaffId(staffUser.id);
    setForm(nextForm);
    setInitialFormState(nextForm);
    setFormErrors({});
    setIsFormOpen(true);
    setMessage('Editing staff details.');
  }

  function openCreateForm() {
    if (isFormOpen && !confirmDiscardIfDirty()) {
      return;
    }
    setEditingStaffId(null);
    setForm(emptyStaff);
    setInitialFormState(emptyStaff);
    setFormErrors({});
    setMessage('');
    setIsFormOpen(true);
  }

  function resetFormState(options = { force: false, closeForm: false }) {
    if (!options.force && !confirmDiscardIfDirty()) {
      return;
    }
    setEditingStaffId(null);
    setForm(emptyStaff);
    setInitialFormState(emptyStaff);
    setFormErrors({});
    if (options.closeForm) {
      setIsFormOpen(false);
    }
  }

  const loadStaff = useCallback(async () => {
    setLoading(true);
    setMessage('');
    try {
      setStaff(await listStaff({ include_inactive: true }));
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, []);

  async function loadLookups() {
    try {
      const [storeRows, zoneRows, studioRows] = await Promise.all([
        listStores({ include_inactive: true }),
        listTrialZones({ include_inactive: true }),
        listTrialStudios({ include_inactive: true }),
      ]);
      setStores(storeRows);
      setZones(zoneRows);
      setStudios(studioRows);
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    }
  }

  useEffect(() => {
    loadStaff();
  }, [loadStaff]);

  useEffect(() => {
    loadLookups();
  }, []);

  async function submitStaff(event) {
    event.preventDefault();
    const validationErrors = validateStaffForm(form);
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
      if (editingStaffId) {
        await updateStaff(editingStaffId, payload);
        setMessage('Staff updated');
        resetFormState({ force: true, closeForm: false });
      } else {
        await createStaff(payload);
        setMessage('Staff created');
        resetFormState({ force: true, closeForm: true });
      }
      await loadStaff();
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function deactivateStaff(staffId) {
    setLoading(true);
    setMessage('');
    try {
      await deleteStaff(staffId);
      setMessage('Staff deactivated');
      await loadStaff();
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function toggleStaffActive(staffUser) {
    setLoading(true);
    setMessage('');
    try {
      await updateStaff(staffUser.id, { is_active: !staffUser.is_active });
      setMessage(staffUser.is_active ? 'Staff deactivated' : 'Staff activated');
      await loadStaff();
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  function openStatusConfirm(staffUser) {
    setPendingStatusChange({
      staffUser,
      mode: staffUser.is_active ? 'deactivate' : 'activate',
    });
  }

  function closeStatusConfirm() {
    setPendingStatusChange(null);
  }

  async function confirmStatusChange() {
    if (!pendingStatusChange) return;
    const { staffUser, mode } = pendingStatusChange;
    closeStatusConfirm();

    if (mode === 'deactivate') {
      await deactivateStaff(staffUser.id);
      return;
    }

    await toggleStaffActive(staffUser);
  }

  const normalizedQuery = query.trim().toLowerCase();
  const filteredStaff = staff.filter((staffUser) => {
    const assignedStudio = staffUser.assigned_studio_id ? studioById.get(String(staffUser.assigned_studio_id)) : null;
    const assignedZoneName = assignedStudio ? zoneNameById.get(String(assignedStudio.trial_zone_id)) || '' : '';

    if (storeFilter && String(staffUser.store_id || '') !== String(storeFilter)) {
      return false;
    }

    if (zoneFilter && assignedStudio && String(assignedStudio.trial_zone_id) !== String(zoneFilter)) {
      return false;
    }

    if (zoneFilter && !assignedStudio) {
      return false;
    }

    if (!normalizedQuery) return true;
    const storeName = storeNameById.get(String(staffUser.store_id)) || '';
    const haystack = `${staffUser.full_name || ''} ${staffUser.email || ''} ${staffUser.default_role || ''} ${storeName} ${assignedZoneName}`.toLowerCase();
    return haystack.includes(normalizedQuery);
  });

  const totalPages = Math.max(1, Math.ceil(filteredStaff.length / STAFF_PER_PAGE));
  const safePage = Math.min(page, totalPages);
  const pageStart = (safePage - 1) * STAFF_PER_PAGE;
  const visibleStaff = filteredStaff.slice(pageStart, pageStart + STAFF_PER_PAGE);

  function goToPage(nextPage) {
    setPage(Math.max(1, Math.min(totalPages, nextPage)));
  }

  return (
    <div className={`grid gap-6 ${isFormOpen ? 'xl:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]' : ''}`}>
      {isFormOpen ? (
        <section id="staff-form" className="rounded-lg border border-line bg-white p-5">
          <MobilePanelJump href="#staff-directory" label="Back to staff" />
          <SectionHeader eyebrow="Trial staff setup" title={editingStaffId ? 'Update staff' : 'Create staff'} />
          <form className="mt-5 space-y-4" onSubmit={submitStaff}>
            <Field
              label="Email"
              value={form.email}
              onChange={(value) => setFormField('email', value)}
              error={formErrors.email}
              maxLength={FIELD_LIMITS.email}
              inputRef={(el) => {
                fieldRefs.current.email = el;
              }}
            />
            <Field
              label="Password"
              value={form.password}
              onChange={(value) => setFormField('password', value)}
              error={formErrors.password}
              maxLength={FIELD_LIMITS.password}
              type="password"
              placeholder={editingStaffId ? 'Leave blank to keep current password' : ''}
              inputRef={(el) => {
                fieldRefs.current.password = el;
              }}
            />
            <Field
              label="Full name"
              value={form.full_name}
              onChange={(value) => setFormField('full_name', value)}
              error={formErrors.full_name}
              maxLength={FIELD_LIMITS.full_name}
              inputRef={(el) => {
                fieldRefs.current.full_name = el;
              }}
            />
            <Field
              label="Phone number"
              value={form.phone_number}
              onChange={(value) => setFormField('phone_number', value)}
              error={formErrors.phone_number}
              maxLength={FIELD_LIMITS.phone}
              inputMode="numeric"
              inputRef={(el) => {
                fieldRefs.current.phone_number = el;
              }}
            />
            <Select label="Role" value={form.default_role} options={ROLE_OPTIONS} onChange={(value) => setFormField('default_role', value)} />
            <div>
              <Select label="Store" value={form.store_id} options={storeOptions} onChange={(value) => setFormField('store_id', value)} />
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
                label="Assigned zone"
                value={form.assigned_zone_id}
                options={zoneOptions}
                onChange={(value) => setFormField('assigned_zone_id', value)}
                disabled={!isTrialAssistantRole}
              />
              <input
                ref={(el) => {
                  fieldRefs.current.assigned_zone_id = el;
                }}
                tabIndex={-1}
                className="absolute h-0 w-0 opacity-0"
                aria-hidden="true"
                readOnly
              />
              {formErrors.assigned_zone_id ? <p className="mt-1 text-xs text-rose-700">{formErrors.assigned_zone_id}</p> : null}
            </div>
            <label className="flex items-center justify-between rounded-lg border border-line px-3 py-3">
              <span className="text-sm font-medium text-charcoal">Staff active</span>
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
                {editingStaffId ? 'Update staff' : 'Save staff'}
              </button>
              {editingStaffId ? (
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

      <section id="staff-directory" className="rounded-lg border border-line bg-white">
        <div className="flex items-center justify-between border-b border-line p-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-red">Trial staff directory</p>
            <h2 className="mt-1 text-xl font-semibold">Configured staff</h2>
          </div>
          <div className="flex items-center gap-2">
            {isFormOpen ? <MobilePanelJump href="#staff-form" label="Go to form" compact /> : null}
            <button
              type="button"
              onClick={openCreateForm}
              className="inline-flex size-10 items-center justify-center rounded-lg bg-brand-red text-white sm:size-auto sm:gap-2 sm:px-3 sm:py-2 sm:text-sm sm:font-medium"
              title="Create staff"
              aria-label="Create staff"
            >
              <Plus size={16} />
              <span className="hidden sm:inline">Create staff</span>
            </button>
            <button type="button" onClick={loadStaff} className="rounded-lg border border-line p-2 text-charcoal hover:border-brand-red" title="Refresh staff">
              <RefreshCw size={18} />
            </button>
          </div>
        </div>

        <div className="border-b border-line p-5">
          <div className="flex flex-wrap gap-3">
            <div className="min-w-[220px] flex-1">
              <Select
                label="Filter by store"
                value={storeFilter}
                options={storeFilterOptions}
                onChange={(value) => {
                  setStoreFilter(value);
                  setZoneFilter('');
                  setPage(1);
                }}
              />
            </div>
            <div className="min-w-[220px] flex-1">
              <Select
                label="Filter by zone"
                value={zoneFilter}
                options={zoneFilterOptions}
                onChange={(value) => {
                  setZoneFilter(value);
                  setPage(1);
                }}
              />
            </div>
            <label className="block min-w-[260px] flex-[2]">
              <span className="text-sm font-medium text-charcoal">Search staff</span>
              <input
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                  setPage(1);
                }}
                placeholder="Search by name, email, role, store, or zone"
                className="mt-1 w-full rounded-lg border border-line px-3 py-2.5 outline-none focus:border-brand-red focus:ring-2 focus:ring-brand-soft"
              />
            </label>
          </div>
        </div>

        <div className="divide-y divide-brand-soft">
          {filteredStaff.length === 0 ? (
            <p className="p-5 text-sm text-muted">No staff found.</p>
          ) : (
            visibleStaff.map((staffUser) => {
              const isEditing = editingStaffId === staffUser.id;
              const assignedStudio = staffUser.assigned_studio_id ? studioById.get(String(staffUser.assigned_studio_id)) : null;
              const assignedZoneName = assignedStudio ? zoneNameById.get(String(assignedStudio.trial_zone_id)) || 'None' : 'None';

              return (
                <div
                  key={staffUser.id}
                  className={`grid gap-3 p-5 lg:grid-cols-[1fr_auto] ${isEditing ? 'bg-brand-blush/50 ring-1 ring-inset ring-brand-soft' : ''}`}
                >
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-semibold">{staffUser.full_name}</h3>
                      <span className="rounded-full bg-brand-blush px-2 py-1 text-xs text-charcoal">{staffUser.default_role}</span>
                      <span className={`rounded-full px-2 py-1 text-xs ${staffUser.is_active ? 'bg-brand-blush text-success' : 'bg-rose-50 text-rose-700'}`}>
                        {staffUser.is_active ? 'Active' : 'Inactive'}
                      </span>
                      {isEditing ? <span className="rounded-full bg-brand-red px-2 py-1 text-xs font-semibold text-white">Editing</span> : null}
                    </div>
                    <p className="mt-1 text-sm text-charcoal">{staffUser.email}</p>
                    <p className="mt-1 text-sm text-muted">Store: {storeNameById.get(String(staffUser.store_id)) || 'None'}</p>
                    <p className="mt-1 text-sm text-muted">Assigned zone: {assignedZoneName}</p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2 lg:justify-end">
                    <button
                      type="button"
                      onClick={() => beginEdit(staffUser)}
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
                      onClick={() => openStatusConfirm(staffUser)}
                      className="inline-flex items-center justify-center gap-2 rounded-lg border border-rose-200 px-3 py-2 text-sm font-medium text-rose-700 disabled:opacity-50"
                      disabled={loading}
                    >
                      <Trash2 size={16} />
                      {staffUser.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {filteredStaff.length > STAFF_PER_PAGE ? (
          <div className="flex items-center justify-between border-t border-line px-5 py-4">
            <p className="text-xs text-muted">
              Showing {pageStart + 1}-{Math.min(pageStart + STAFF_PER_PAGE, filteredStaff.length)} of {filteredStaff.length}
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
            <h3 className="text-lg font-semibold text-ink">{pendingStatusChange.mode === 'deactivate' ? 'Deactivate staff?' : 'Activate staff?'}</h3>
            <p className="mt-2 text-sm text-charcoal">
              {pendingStatusChange.mode === 'deactivate'
                ? `This will mark ${pendingStatusChange.staffUser.full_name} as inactive. Continue?`
                : `This will mark ${pendingStatusChange.staffUser.full_name} as active. Continue?`}
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

function Field({ label, value, onChange, error, maxLength, inputMode = 'text', type = 'text', placeholder = '', inputRef }) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-charcoal">{label}</span>
      <input
        ref={inputRef}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        maxLength={maxLength}
        inputMode={inputMode}
        type={type}
        placeholder={placeholder}
        className={`mt-1 w-full rounded-lg border px-3 py-2.5 outline-none focus:ring-2 ${
          error ? 'border-rose-400 focus:border-rose-500 focus:ring-rose-100' : 'border-line focus:border-brand-red focus:ring-brand-soft'
        }`}
      />
      {error ? <p className="mt-1 text-xs text-rose-700">{error}</p> : null}
    </label>
  );
}
