import { CalendarPlus, RefreshCw, Save, Trash2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { getErrorMessage, showApiErrorToast } from '../../../../api/httpClient.js';
import { getTrialCalendar, updateTrialCalendar } from '../../../../api/trial/calendarApi.js';
import { listStores } from '../../../../api/trial/storeApi.js';
import { Select } from '../../../common/FormAndStatePrimitives.jsx';
import { SectionHeader } from '../../../common/SectionHeader.jsx';

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const DEFAULT_DAY = {
  is_open: true,
  open_time: '00:00',
  close_time: '23:59',
};

const EVENT_TYPE_OPTIONS = [
  { label: 'Promotion', value: 'PROMOTION' },
  { label: 'Sale', value: 'SALE' },
  { label: 'Holiday event', value: 'HOLIDAY' },
  { label: 'Other', value: 'OTHER' },
];

function emptyDays() {
  return WEEKDAYS.map((_, weekday) => ({
    weekday,
    ...DEFAULT_DAY,
  }));
}

function toTimeValue(value) {
  return value ? String(value).slice(0, 5) : '';
}

function toForm(calendar) {
  const daysByWeekday = new Map((calendar?.days || []).map((day) => [day.weekday, day]));
  return {
    timezone: calendar?.timezone || 'Asia/Kolkata',
    days: WEEKDAYS.map((_, weekday) => {
      const day = daysByWeekday.get(weekday);
      return {
        weekday,
        is_open: day?.is_open ?? DEFAULT_DAY.is_open,
        open_time: toTimeValue(day?.open_time) || DEFAULT_DAY.open_time,
        close_time: toTimeValue(day?.close_time) || DEFAULT_DAY.close_time,
      };
    }),
    holidays: (calendar?.holidays || []).map((holiday) => ({
      holiday_date: holiday.holiday_date,
      name: holiday.name || '',
      is_active: holiday.is_active,
    })),
    events: (calendar?.events || []).map((eventItem) => ({
      event_date: eventItem.event_date,
      name: eventItem.name || '',
      event_type: eventItem.event_type || 'PROMOTION',
      is_active: eventItem.is_active,
    })),
  };
}

export function Calendar() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [stores, setStores] = useState([]);
  const [form, setForm] = useState({ timezone: 'Asia/Kolkata', days: emptyDays(), holidays: [], events: [] });
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [storesLoaded, setStoresLoaded] = useState(false);
  const storeId = searchParams.get('store_id') || '';

  const storeOptions = useMemo(
    () =>
      stores.length
        ? stores.map((store) => ({
        label: `${store.name} (${store.store_number})`,
        value: String(store.id),
      }))
        : [{ label: 'No stores found', value: '' }],
    [stores]
  );

  const selectedStore = useMemo(() => stores.find((store) => String(store.id) === storeId), [storeId, stores]);

  useEffect(() => {
    async function loadStores() {
      try {
        setStores(await listStores({ include_inactive: true }));
      } catch (error) {
        showApiErrorToast(error);
        setMessage(getErrorMessage(error));
      } finally {
        setStoresLoaded(true);
      }
    }

    loadStores();
  }, []);

  useEffect(() => {
    if (!stores.length) return;
    if (stores.some((store) => String(store.id) === String(storeId))) return;
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('store_id', String(stores[0].id));
      return next;
    });
  }, [setSearchParams, storeId, stores]);

  useEffect(() => {
    async function loadCalendar() {
      if (!storeId) {
        setForm({ timezone: 'Asia/Kolkata', days: emptyDays(), holidays: [], events: [] });
        return;
      }

      setLoading(true);
      setMessage('');
      try {
        setForm(toForm(await getTrialCalendar(storeId)));
      } catch (error) {
        showApiErrorToast(error);
        setMessage(getErrorMessage(error));
      } finally {
        setLoading(false);
      }
    }

    loadCalendar();
  }, [storeId]);

  function selectStore(value) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) {
        next.set('store_id', value);
      } else {
        next.delete('store_id');
      }
      return next;
    });
  }

  function updateDay(weekday, field, value) {
    setForm((prev) => ({
      ...prev,
      days: prev.days.map((day) => (day.weekday === weekday ? { ...day, [field]: value } : day)),
    }));
  }

  function addHoliday() {
    setForm((prev) => ({
      ...prev,
      holidays: [...prev.holidays, { holiday_date: '', name: '', is_active: true }],
    }));
  }

  function updateHoliday(index, field, value) {
    setForm((prev) => ({
      ...prev,
      holidays: prev.holidays.map((holiday, holidayIndex) => (holidayIndex === index ? { ...holiday, [field]: value } : holiday)),
    }));
  }

  function removeHoliday(index) {
    setForm((prev) => ({
      ...prev,
      holidays: prev.holidays.filter((_, holidayIndex) => holidayIndex !== index),
    }));
  }

  function addEvent() {
    setForm((prev) => ({
      ...prev,
      events: [...(prev.events || []), { event_date: '', name: '', event_type: 'PROMOTION', is_active: true }],
    }));
  }

  function updateEvent(index, field, value) {
    setForm((prev) => ({
      ...prev,
      events: (prev.events || []).map((eventItem, eventIndex) => (eventIndex === index ? { ...eventItem, [field]: value } : eventItem)),
    }));
  }

  function removeEvent(index) {
    setForm((prev) => ({
      ...prev,
      events: (prev.events || []).filter((_, eventIndex) => eventIndex !== index),
    }));
  }

  async function saveCalendar(event) {
    event.preventDefault();
    if (!storeId) {
      setMessage('Select a store before saving calendar settings.');
      return;
    }

    const invalidHoliday = form.holidays.find((holiday) => !holiday.holiday_date);
    if (invalidHoliday) {
      setMessage('Holiday date is required.');
      return;
    }

    const invalidEvent = (form.events || []).find((eventItem) => !eventItem.event_date);
    if (invalidEvent) {
      setMessage('Calendar event date is required.');
      return;
    }

    setLoading(true);
    setMessage('');
    try {
      const payload = {
        timezone: form.timezone.trim() || 'Asia/Kolkata',
        days: form.days.map((day) => ({
          weekday: day.weekday,
          is_open: day.is_open,
          open_time: day.open_time,
          close_time: day.close_time,
        })),
        holidays: form.holidays.map((holiday) => ({
          holiday_date: holiday.holiday_date,
          name: holiday.name.trim() || null,
          is_active: holiday.is_active,
        })),
        events: (form.events || []).map((eventItem) => ({
          event_date: eventItem.event_date,
          name: eventItem.name.trim() || null,
          event_type: eventItem.event_type,
          is_active: eventItem.is_active,
        })),
      };
      setForm(toForm(await updateTrialCalendar(storeId, payload)));
      setMessage('Trial calendar saved');
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="grid gap-6 xl:grid-cols-[2fr_1fr]" onSubmit={saveCalendar}>
      <section className="rounded-lg border border-line bg-white p-5">
        <SectionHeader eyebrow="Trial calendar" title={selectedStore ? `${selectedStore.name} trial hours` : 'Configure trial hours'} />

        <div className="mt-5 grid gap-4 md:grid-cols-[1fr_220px]">
          <Select label="Store" value={storeId} options={storeOptions} onChange={selectStore} disabled={!stores.length} />
          {selectedStore ? (
          <label className="block">
            <span className="text-sm font-medium text-charcoal">Timezone</span>
            <input
              value={form.timezone}
              onChange={(event) => setForm((prev) => ({ ...prev, timezone: event.target.value }))}
              className="mt-1 w-full rounded-lg border border-line px-3 py-2.5 outline-none focus:border-brand-red focus:ring-2 focus:ring-brand-soft"
            />
          </label>
          ) : null}
        </div>

        {storesLoaded && !stores.length ? (
          <p className="mt-5 rounded-lg border border-dashed border-line p-4 text-sm text-muted">Create a store first, then trial calendar settings will appear here.</p>
        ) : null}
        {message && !selectedStore ? <p className="mt-4 rounded-lg bg-brand-blush px-3 py-2 text-sm text-charcoal">{message}</p> : null}

        {selectedStore ? (
        <>
        <div className="mt-5 divide-y divide-brand-soft rounded-lg border border-line">
          {form.days.map((day) => (
            <div key={day.weekday} className="grid gap-3 p-4 md:grid-cols-[1fr_120px_120px_auto] md:items-center">
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={day.is_open}
                  onChange={(event) => updateDay(day.weekday, 'is_open', event.target.checked)}
                  className="size-5 accent-brand-red"
                />
                <span className="font-medium text-charcoal">{WEEKDAYS[day.weekday]}</span>
              </label>
              <input
                type="time"
                value={day.open_time}
                disabled={!day.is_open}
                onChange={(event) => updateDay(day.weekday, 'open_time', event.target.value)}
                className="rounded-lg border border-line px-3 py-2 text-sm outline-none focus:border-brand-red focus:ring-2 focus:ring-brand-soft disabled:bg-slate-50"
              />
              <input
                type="time"
                value={day.close_time}
                disabled={!day.is_open}
                onChange={(event) => updateDay(day.weekday, 'close_time', event.target.value)}
                className="rounded-lg border border-line px-3 py-2 text-sm outline-none focus:border-brand-red focus:ring-2 focus:ring-brand-soft disabled:bg-slate-50"
              />
              <span className={`rounded-full px-2 py-1 text-xs ${day.is_open ? 'bg-brand-blush text-success' : 'bg-rose-50 text-rose-700'}`}>
                {day.is_open ? 'Open' : 'Closed'}
              </span>
            </div>
          ))}
        </div>

        {message ? <p className="mt-4 rounded-lg bg-brand-blush px-3 py-2 text-sm text-charcoal">{message}</p> : null}

        <div className="mt-5 flex gap-2">
          <button
            type="submit"
            disabled={loading || !storeId}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-red px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
          >
            <Save size={17} />
            Save calendar
          </button>
          <button
            type="button"
            disabled={loading || !storeId}
            onClick={() => storeId && getTrialCalendar(storeId).then((calendar) => setForm(toForm(calendar)))}
            className="inline-flex items-center justify-center gap-2 rounded-lg border border-line px-4 py-3 text-sm font-medium text-charcoal disabled:opacity-60"
          >
            <RefreshCw size={17} />
            Reload
          </button>
        </div>
        </>
        ) : null}
      </section>

      {selectedStore ? (
      <div className="space-y-6">
        <section className="rounded-lg border border-line bg-white p-5">
          <SectionHeader
            eyebrow="Closed dates"
            title="Holidays"
            action={
              <button type="button" onClick={addHoliday} className="inline-flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-sm font-medium text-charcoal">
                <CalendarPlus size={16} />
                Add
              </button>
            }
          />

          <div className="mt-5 space-y-3">
            {form.holidays.length === 0 ? <p className="rounded-lg border border-dashed border-line p-4 text-sm text-muted">No holidays configured.</p> : null}
            {form.holidays.map((holiday, index) => (
              <div key={`${holiday.holiday_date}-${index}`} className="rounded-lg border border-line p-3">
                <div className="grid gap-3">
                  <input
                    type="date"
                    value={holiday.holiday_date}
                    onChange={(event) => updateHoliday(index, 'holiday_date', event.target.value)}
                    className="rounded-lg border border-line px-3 py-2 text-sm outline-none focus:border-brand-red focus:ring-2 focus:ring-brand-soft"
                  />
                  <input
                    value={holiday.name}
                    onChange={(event) => updateHoliday(index, 'name', event.target.value)}
                    placeholder="Holiday name"
                    className="rounded-lg border border-line px-3 py-2 text-sm outline-none focus:border-brand-red focus:ring-2 focus:ring-brand-soft"
                  />
                  <div className="flex items-center justify-between">
                    <label className="flex items-center gap-2 text-sm font-medium text-charcoal">
                      <input
                        type="checkbox"
                        checked={holiday.is_active}
                        onChange={(event) => updateHoliday(index, 'is_active', event.target.checked)}
                        className="size-4 accent-brand-red"
                      />
                      Active
                    </label>
                    <button type="button" onClick={() => removeHoliday(index)} className="rounded-lg border border-rose-200 p-2 text-rose-700" aria-label="Remove holiday">
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-lg border border-line bg-white p-5">
          <SectionHeader
            eyebrow="Demand signals"
            title="Promotional days"
            action={
              <button type="button" onClick={addEvent} className="inline-flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-sm font-medium text-charcoal">
                <CalendarPlus size={16} />
                Add
              </button>
            }
          />

          <div className="mt-5 space-y-3">
            {(form.events || []).length === 0 ? <p className="rounded-lg border border-dashed border-line p-4 text-sm text-muted">No promotional days configured.</p> : null}
            {(form.events || []).map((eventItem, index) => (
              <div key={`${eventItem.event_date}-${eventItem.event_type}-${index}`} className="rounded-lg border border-line p-3">
                <div className="grid gap-3">
                  <input
                    type="date"
                    value={eventItem.event_date}
                    onChange={(event) => updateEvent(index, 'event_date', event.target.value)}
                    className="rounded-lg border border-line px-3 py-2 text-sm outline-none focus:border-brand-red focus:ring-2 focus:ring-brand-soft"
                  />
                  <Select label="Type" value={eventItem.event_type} options={EVENT_TYPE_OPTIONS} onChange={(value) => updateEvent(index, 'event_type', value)} />
                  <input
                    value={eventItem.name}
                    onChange={(event) => updateEvent(index, 'name', event.target.value)}
                    placeholder="Event name"
                    className="rounded-lg border border-line px-3 py-2 text-sm outline-none focus:border-brand-red focus:ring-2 focus:ring-brand-soft"
                  />
                  <div className="flex items-center justify-between">
                    <label className="flex items-center gap-2 text-sm font-medium text-charcoal">
                      <input
                        type="checkbox"
                        checked={eventItem.is_active}
                        onChange={(event) => updateEvent(index, 'is_active', event.target.checked)}
                        className="size-4 accent-brand-red"
                      />
                      Active
                    </label>
                    <button type="button" onClick={() => removeEvent(index)} className="rounded-lg border border-rose-200 p-2 text-rose-700" aria-label="Remove event">
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
      ) : null}
    </form>
  );
}
