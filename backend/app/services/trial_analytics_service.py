from collections import Counter
from datetime import datetime, time, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.trial_calendar import TrialCalendarEventType
from app.models.trial_queue_token import TrialQueueTokenStatus
from app.repositories.trial_analytics_repository import TrialAnalyticsRepository
from app.schemas.trial_analytics import *


class TrialAnalyticsService:
    def __init__(self, db: Session) -> None:
        self.repository = TrialAnalyticsRepository(db)

    def get_store_analytics(self, store_id: int, days: int) -> TrialStoreAnalyticsResponse:
        days = max(1, min(days, 90))
        store = self.repository.get_store(store_id)
        if store is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
        now = datetime.now(timezone.utc)
        start_date = now.date() - timedelta(days=days - 1)
        start_at = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
        today_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
        zones = self.repository.list_zones(store_id)
        studios = self.repository.list_studios(store_id)
        active_tokens = self.repository.list_active_tokens(store_id)
        tokens = self.repository.list_tokens_since(store_id, start_at)
        events = self.repository.list_calendar_events(store_id, start_date, now.date())
        metadata = self.repository.get_latest_model_metadata(store_id)
        zone_rows = self._zones(zones, studios, active_tokens, tokens, today_start, now)
        metrics = self._metrics(studios, active_tokens, tokens, today_start, now)
        event_dates = {event.event_date for event in events if event.event_type in (TrialCalendarEventType.PROMOTION, TrialCalendarEventType.SALE)}
        calendar_signals = [TrialAnalyticsCalendarSignal(event_date=e.event_date, event_type=self._value(e.event_type), name=e.name) for e in events]
        ml_summary = TrialAnalyticsMLSummary(
            status=metadata.status if metadata else "NOT_TRAINED",
            model_type=metadata.model_type if metadata else None,
            model_version=metadata.model_version if metadata else None,
            trained_at=metadata.trained_at if metadata else None,
            sample_size=metadata.sample_size if metadata else 0,
            mae=metadata.mae if metadata else None,
            r2_score=metadata.r2_score if metadata else None,
        )
        return TrialStoreAnalyticsResponse(
            store=TrialAnalyticsStoreSummary(id=store.id, store_number=store.store_number, name=store.name),
            days=days,
            generated_at=now,
            metrics=metrics,
            zones=zone_rows,
            studios=self._studios(studios, active_tokens, tokens, today_start),
            daily_trends=self._daily(tokens, start_date, days),
            peak_hours=[TrialAnalyticsPeakHour(hour=h, token_count=c) for h, c in sorted(Counter(t.created_at.hour for t in tokens).items(), key=lambda item: (-item[1], item[0]))[:6]],
            promotion_stats=self._promotion(tokens, event_dates),
            weekly_stats=self._weekly(tokens),
            hourly_stats=self._hourly(tokens),
            zone_stats=self._zone_stats(zones, tokens),
            customer_type_stats=self._customer_stats(tokens),
            item_bucket_stats=self._item_stats(tokens),
            calendar_signals=calendar_signals,
            ml_summary=ml_summary,
            insights=self._insights(metrics, zone_rows, calendar_signals, ml_summary),
        )

    def _metrics(self, studios, active, tokens, today_start, now):
        active_studios = [s for s in studios if s.is_active]
        busy = {t.assigned_studio_id for t in active if t.assigned_studio_id}
        today = [t for t in tokens if self._after(t.created_at, today_start)]
        return TrialAnalyticsMetricSummary(
            waiting_tokens=sum(t.status == TrialQueueTokenStatus.WAITING for t in active),
            called_tokens=sum(t.status == TrialQueueTokenStatus.CALLED for t in active),
            serving_tokens=sum(t.status == TrialQueueTokenStatus.SERVING for t in active),
            completed_today=sum(t.status == TrialQueueTokenStatus.COMPLETED and self._after(t.completed_at, today_start) for t in tokens),
            cancelled_today=sum(t.status == TrialQueueTokenStatus.CANCELLED and self._after(t.cancelled_at, today_start) for t in tokens),
            no_show_today=sum(t.status == TrialQueueTokenStatus.NO_SHOW and self._after(t.updated_at, today_start) for t in tokens),
            active_studios=len(active_studios), total_studios=len(studios),
            average_wait_minutes=self._round(self._avg([self._wait(t, now) for t in active])),
            average_service_minutes=self._round(self._avg([self._service(t) for t in tokens if t.status == TrialQueueTokenStatus.COMPLETED])),
            average_items_today=self._round(self._avg([t.item_count for t in today if t.item_count is not None])),
            cancellations_last_hour=sum(t.status == TrialQueueTokenStatus.CANCELLED and t.cancelled_at is not None and self._aware(t.cancelled_at) >= now - timedelta(hours=1) for t in tokens),
            studio_utilization_percent=self._percent(len(busy), len(active_studios)),
        )

    def _zones(self, zones, studios, active, tokens, today_start, now):
        rows = []
        for zone in zones:
            zs = [s for s in studios if s.trial_zone_id == zone.id]
            za = [t for t in active if t.trial_zone_id == zone.id]
            zt = [t for t in tokens if t.trial_zone_id == zone.id]
            today = [t for t in zt if self._after(t.created_at, today_start)]
            cancelled = [t for t in zt if t.status in (TrialQueueTokenStatus.CANCELLED, TrialQueueTokenStatus.NO_SHOW)]
            last = self._latest(zt + za)
            last_active = self._latest([t for t in za if t.status in (TrialQueueTokenStatus.CALLED, TrialQueueTokenStatus.SERVING)])
            active_studios = [s for s in zs if s.is_active]
            busy = {t.assigned_studio_id for t in za if t.assigned_studio_id}
            rows.append(TrialAnalyticsZoneSummary(
                zone_id=zone.id, zone_name=zone.name, zone_type=self._value(zone.zone_type), gender=self._value(zone.gender),
                waiting_tokens=sum(t.status == TrialQueueTokenStatus.WAITING for t in za),
                serving_tokens=sum(t.status in (TrialQueueTokenStatus.CALLED, TrialQueueTokenStatus.SERVING) for t in za),
                completed_today=sum(t.status == TrialQueueTokenStatus.COMPLETED and self._after(t.completed_at, today_start) for t in zt),
                cancelled_today=sum(t.status in (TrialQueueTokenStatus.CANCELLED, TrialQueueTokenStatus.NO_SHOW) and self._after(t.cancelled_at or t.updated_at, today_start) for t in zt),
                total_cancellations=len(cancelled),
                cancellations_last_hour=sum(self._aware(t.cancelled_at or t.updated_at) >= now - timedelta(hours=1) for t in cancelled if t.cancelled_at or t.updated_at),
                active_studios=len(active_studios), total_studios=len(zs),
                last_token_number=last.token_number if last else None,
                last_active_token_number=last_active.token_number if last_active else None,
                estimated_wait_last_token_minutes=self._round(self._wait(last, now) if last else 0),
                estimated_items_ahead=self._items_ahead(last, za),
                average_items_today=self._round(self._avg([t.item_count for t in today if t.item_count is not None])),
                average_wait_minutes=self._round(self._avg([self._wait(t, now) for t in za])),
                utilization_percent=self._percent(len(busy), len(active_studios)),
                active_studio_sessions=[TrialAnalyticsActiveStudioSession(studio_id=s.id, studio_name=s.name or f"Studio #{s.id}", assigned_token_number=(self._studio_token(s.id, za).token_number if self._studio_token(s.id, za) else None)) for s in active_studios],
            ))
        return rows

    def _studios(self, studios, active, tokens, today_start):
        rows = []
        for studio in studios:
            current = self._studio_token(studio.id, active)
            rows.append(TrialAnalyticsStudioSummary(
                studio_id=studio.id, zone_id=studio.trial_zone_id, studio_name=studio.name or f"Studio #{studio.id}", studio_type=self._value(studio.studio_type), is_active=studio.is_active,
                current_token_number=current.token_number if current else None,
                waiting_tokens=sum(t.assigned_studio_id == studio.id and t.status == TrialQueueTokenStatus.WAITING for t in active),
                serving_tokens=sum(t.assigned_studio_id == studio.id and t.status in (TrialQueueTokenStatus.CALLED, TrialQueueTokenStatus.SERVING) for t in active),
                completed_today=sum(t.assigned_studio_id == studio.id and t.status == TrialQueueTokenStatus.COMPLETED and self._after(t.completed_at, today_start) for t in tokens),
                utilization_percent=100.0 if studio.is_active and current else 0.0,
            ))
        return rows

    def _daily(self, tokens, start_date, days):
        rows = []
        for offset in range(days):
            day = start_date + timedelta(days=offset)
            created = [t for t in tokens if t.created_at.date() == day]
            completed = [t for t in tokens if t.status == TrialQueueTokenStatus.COMPLETED and t.completed_at and t.completed_at.date() == day]
            cancelled = [t for t in tokens if t.status in (TrialQueueTokenStatus.CANCELLED, TrialQueueTokenStatus.NO_SHOW) and (t.cancelled_at or t.updated_at).date() == day]
            rows.append(TrialAnalyticsDailyTrend(day=day, token_count=len(created), completed_count=len(completed), cancelled_count=len(cancelled), average_wait_minutes=self._round(self._avg([self._terminal_wait(t) for t in completed])), average_service_minutes=self._round(self._avg([self._service(t) for t in completed]))))
        return rows

    def _promotion(self, tokens, event_dates):
        rows = []
        for label, group in (("Promotion/Sale Day", [t for t in tokens if t.created_at.date() in event_dates]), ("Regular Day", [t for t in tokens if t.created_at.date() not in event_dates])):
            completed = [t for t in group if t.status == TrialQueueTokenStatus.COMPLETED]
            cancelled = [t for t in group if t.status in (TrialQueueTokenStatus.CANCELLED, TrialQueueTokenStatus.NO_SHOW)]
            rows.append(TrialAnalyticsPromotionStat(day_type=label, avg_footfall=self._round(len(group)), avg_wait_time=self._round(self._avg([self._terminal_wait(t) for t in group])), avg_items=self._round(self._avg([t.item_count for t in group if t.item_count is not None])), avg_service_time=self._round(self._avg([self._service(t) for t in group])), cancellations=len(cancelled), completion_rate=self._percent(len(completed), len(group))))
        return rows

    def _weekly(self, tokens):
        names = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
        rows = []
        for day, name in enumerate(names):
            group = [t for t in tokens if t.created_at.weekday() == day]
            cancelled = [t for t in group if t.status in (TrialQueueTokenStatus.CANCELLED, TrialQueueTokenStatus.NO_SHOW)]
            rows.append(TrialAnalyticsWeeklyStat(day_name=name, total_visits=len(group), avg_wait_time=self._round(self._avg([self._terminal_wait(t) for t in group])), avg_service_time=self._round(self._avg([self._service(t) for t in group])), cancellations=len(cancelled), cancellation_rate=self._percent(len(cancelled), len(group))))
        return rows

    def _hourly(self, tokens):
        return [TrialAnalyticsHourlyStat(hour=h, total_visits=len(g := [t for t in tokens if t.created_at.hour == h]), avg_wait_time=self._round(self._avg([self._terminal_wait(t) for t in g])), avg_service_time=self._round(self._avg([self._service(t) for t in g]))) for h in range(24)]

    def _zone_stats(self, zones, tokens):
        rows = []
        for zone in zones:
            group = [token for token in tokens if token.trial_zone_id == zone.id]
            rows.append(TrialAnalyticsZoneStat(
                zone_name=zone.name,
                total_trials=sum(token.status == TrialQueueTokenStatus.COMPLETED for token in group),
                cancellations=sum(token.status in (TrialQueueTokenStatus.CANCELLED, TrialQueueTokenStatus.NO_SHOW) for token in group),
                avg_wait_time=self._round(self._avg([self._terminal_wait(token) for token in group])),
                avg_service_time=self._round(self._avg([self._service(token) for token in group])),
                total_items=sum(token.item_count or 0 for token in group),
            ))
        return rows

    def _customer_stats(self, tokens):
        rows = []
        for kind in sorted({t.customer_type or "regular" for t in tokens}) or ["regular"]:
            group = [t for t in tokens if (t.customer_type or "regular") == kind]
            rows.append(TrialAnalyticsCustomerTypeStat(customer_type=kind, count=len(group), avg_wait=self._round(self._avg([self._terminal_wait(t) for t in group])), avg_service=self._round(self._avg([self._service(t) for t in group])), total_items=sum(t.item_count or 0 for t in group), cancellations=sum(t.status in (TrialQueueTokenStatus.CANCELLED, TrialQueueTokenStatus.NO_SHOW) for t in group)))
        return rows

    def _item_stats(self, tokens):
        buckets = (("0-5", lambda n: n <= 5), ("6-15", lambda n: 6 <= n <= 15), ("16-30", lambda n: 16 <= n <= 30), ("31+", lambda n: n >= 31))
        return [TrialAnalyticsItemBucketStat(range=label, count=len(g := [t for t in tokens if test(t.item_count or 0)]), avg_wait=self._round(self._avg([self._terminal_wait(t) for t in g])), avg_service=self._round(self._avg([self._service(t) for t in g]))) for label, test in buckets]

    def _insights(self, metrics, zones, signals, ml):
        rows = []
        if metrics.waiting_tokens > metrics.active_studios:
            rows.append(TrialAnalyticsInsight(level="warning", title="Queue pressure", detail="Waiting customers exceed active studios."))
        if metrics.average_wait_minutes >= 15:
            rows.append(TrialAnalyticsInsight(level="warning", title="Wait time", detail="Average wait is above 15 minutes."))
        if any(z.utilization_percent >= 90 for z in zones):
            rows.append(TrialAnalyticsInsight(level="info", title="Studio utilization", detail="At least one zone is near full studio utilization."))
        if signals:
            rows.append(TrialAnalyticsInsight(level="info", title="Calendar signal", detail="Promotion or calendar events are included in this range."))
        if ml.status != "READY":
            rows.append(TrialAnalyticsInsight(level="info", title="ML model", detail="Trial service-time model is not ready."))
        return rows or [TrialAnalyticsInsight(level="success", title="Operations stable", detail="No immediate queue pressure detected.")]

    @staticmethod
    def _aware(value):
        return value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value

    @classmethod
    def _after(cls, value, start):
        return value is not None and cls._aware(value) >= start

    @classmethod
    def _wait(cls, token, now):
        if token is None: return 0.0
        end = token.service_started_at or now
        return max((cls._aware(end) - cls._aware(token.created_at)).total_seconds() / 60, 0)

    @classmethod
    def _terminal_wait(cls, token):
        return cls._wait(token, cls._aware(token.service_started_at or token.calling_time or token.created_at))

    @classmethod
    def _service(cls, token):
        if token.service_started_at and token.completed_at: return max((cls._aware(token.completed_at) - cls._aware(token.service_started_at)).total_seconds() / 60, 0)
        return float(token.service_time_minutes or 0)

    @staticmethod
    def _latest(tokens):
        return max(tokens, key=lambda t: (t.created_at, t.id), default=None)

    @staticmethod
    def _studio_token(studio_id, tokens):
        return next((t for t in tokens if t.assigned_studio_id == studio_id and t.status in (TrialQueueTokenStatus.CALLED, TrialQueueTokenStatus.SERVING)), None)

    @staticmethod
    def _items_ahead(last, active):
        if not last: return 0
        return sum(t.item_count or 0 for t in active if t.id != last.id and t.id <= last.id)

    @staticmethod
    def _avg(values):
        values = [float(v) for v in values if v is not None]
        return sum(values) / len(values) if values else 0.0

    @staticmethod
    def _percent(part, whole):
        return round(part / whole * 100, 1) if whole else 0.0

    @staticmethod
    def _round(value):
        return round(float(value or 0), 1)

    @staticmethod
    def _value(value):
        return value.value if hasattr(value, "value") else str(value)
