from collections import Counter as ValueCounter
from datetime import datetime, time, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.calendar import StoreCalendarEventType
from app.models.queue_token import QueueToken, QueueTokenStatus
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import (
    AnalyticsActiveCounterSession,
    AnalyticsCalendarSignal,
    AnalyticsCounterSummary,
    AnalyticsCustomerTypeStat,
    AnalyticsDailyTrend,
    AnalyticsHourlyStat,
    AnalyticsInsight,
    AnalyticsItemBucketStat,
    AnalyticsMetricSummary,
    AnalyticsMLSummary,
    AnalyticsPeakHour,
    AnalyticsPromotionStat,
    AnalyticsSectionSummary,
    AnalyticsStoreSummary,
    AnalyticsWeeklyStat,
    AnalyticsZoneStat,
    StoreAnalyticsResponse,
)
from app.services.static_analytics_provider import StaticAnalyticsProvider


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.repository = AnalyticsRepository(db)

    def get_store_analytics(self, store_id: int, days: int) -> StoreAnalyticsResponse:
        normalized_days = max(1, min(days, 90))
        store = self.repository.get_store(store_id)
        if store is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

        if normalized_days > 1 and settings.CHECKOUT_ANALYTICS_HISTORY_MODE == "static":
            return StaticAnalyticsProvider().checkout(
                store,
                normalized_days,
                self.repository.get_latest_model_metadata(store_id),
            )

        now = datetime.now(timezone.utc)
        start_date = (now.date() - timedelta(days=normalized_days - 1))
        start_at = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
        today_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)

        sections = self.repository.list_sections(store_id)
        counters = self.repository.list_counters(store_id)
        active_tokens = self.repository.list_active_tokens(store_id)
        period_tokens = self.repository.list_tokens_since(store_id, start_at)
        events = self.repository.list_calendar_events(store_id, start_date, now.date())
        model_metadata = self.repository.get_latest_model_metadata(store_id)

        section_rows = self._build_section_rows(sections, counters, active_tokens, period_tokens, today_start, now)
        counter_rows = self._build_counter_rows(counters, active_tokens, period_tokens, today_start)
        metrics = self._build_metrics(counters, active_tokens, period_tokens, today_start, now)
        daily_trends = self._build_daily_trends(period_tokens, start_date, normalized_days)
        peak_hours = self._build_peak_hours(period_tokens)
        event_dates = {event.event_date for event in events if event.event_type in (StoreCalendarEventType.PROMOTION, StoreCalendarEventType.SALE)}
        calendar_signals = [
            AnalyticsCalendarSignal(
                event_date=event.event_date,
                event_type=event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type),
                name=event.name,
            )
            for event in events
        ]
        ml_summary = AnalyticsMLSummary(
            status=model_metadata.status if model_metadata else "NOT_TRAINED",
            model_type=model_metadata.model_type if model_metadata else None,
            model_version=model_metadata.model_version if model_metadata else None,
            trained_at=model_metadata.trained_at if model_metadata else None,
            sample_size=model_metadata.sample_size if model_metadata else 0,
            mae=model_metadata.mae if model_metadata else None,
            r2_score=model_metadata.r2_score if model_metadata else None,
        )

        return StoreAnalyticsResponse(
            store=AnalyticsStoreSummary(id=store.id, store_number=store.store_number, name=store.name),
            days=normalized_days,
            generated_at=now,
            metrics=metrics,
            sections=section_rows,
            counters=counter_rows,
            daily_trends=daily_trends,
            peak_hours=peak_hours,
            promotion_stats=self._build_promotion_stats(period_tokens, event_dates),
            weekly_stats=self._build_weekly_stats(period_tokens),
            hourly_stats=self._build_hourly_stats(period_tokens),
            zone_stats=self._build_zone_stats(section_rows, period_tokens),
            customer_type_stats=self._build_customer_type_stats(period_tokens),
            item_bucket_stats=self._build_item_bucket_stats(period_tokens),
            calendar_signals=calendar_signals,
            ml_summary=ml_summary,
            insights=self._build_insights(metrics, section_rows, calendar_signals, ml_summary),
        )

    def _build_metrics(
        self,
        counters,
        active_tokens: list[QueueToken],
        period_tokens: list[QueueToken],
        today_start: datetime,
        now: datetime,
    ) -> AnalyticsMetricSummary:
        active_counters = [counter for counter in counters if counter.is_active]
        busy_counter_ids = {token.assigned_counter_id for token in active_tokens if token.assigned_counter_id is not None}
        today_tokens = [token for token in period_tokens if self._at_or_after(token.created_at, today_start)]
        return AnalyticsMetricSummary(
            waiting_tokens=sum(1 for token in active_tokens if token.status == QueueTokenStatus.WAITING),
            called_tokens=sum(1 for token in active_tokens if token.status == QueueTokenStatus.CALLED),
            serving_tokens=sum(1 for token in active_tokens if token.status == QueueTokenStatus.SERVING),
            completed_today=sum(1 for token in period_tokens if token.status == QueueTokenStatus.COMPLETED and self._at_or_after(token.completed_at, today_start)),
            cancelled_today=sum(1 for token in period_tokens if token.status == QueueTokenStatus.CANCELLED and self._at_or_after(token.cancelled_at, today_start)),
            no_show_today=sum(1 for token in period_tokens if token.status == QueueTokenStatus.NO_SHOW and self._at_or_after(token.updated_at, today_start)),
            active_counters=len(active_counters),
            total_counters=len(counters),
            average_wait_minutes=self._round(self._average([self._current_wait_minutes(token, now) for token in active_tokens])),
            average_service_minutes=self._round(self._average_service_minutes(period_tokens)),
            average_items_today=self._round(self._average([token.item_count for token in today_tokens if token.item_count is not None])),
            cancellations_last_hour=sum(
                1
                for token in period_tokens
                if token.status == QueueTokenStatus.CANCELLED
                and token.cancelled_at is not None
                and token.cancelled_at >= now - timedelta(hours=1)
            ),
            counter_utilization_percent=self._percent(len(busy_counter_ids), len(active_counters)),
        )

    def _build_section_rows(self, sections, counters, active_tokens, period_tokens, today_start, now) -> list[AnalyticsSectionSummary]:
        rows = []
        for section in sections:
            section_counters = [counter for counter in counters if counter.section_id == section.id]
            active_section_counters = [counter for counter in section_counters if counter.is_active]
            active_section_tokens = [token for token in active_tokens if token.section_id == section.id]
            section_period_tokens = [token for token in period_tokens if token.section_id == section.id]
            section_today_tokens = [token for token in section_period_tokens if self._at_or_after(token.created_at, today_start)]
            section_cancelled_tokens = [
                token for token in section_period_tokens if token.status == QueueTokenStatus.CANCELLED and token.cancelled_at is not None
            ]
            busy_counter_ids = {token.assigned_counter_id for token in active_section_tokens if token.assigned_counter_id is not None}
            last_token = self._latest_token(section_period_tokens + active_section_tokens)
            last_active_token = self._latest_token(
                [
                    token
                    for token in active_section_tokens
                    if token.status in (QueueTokenStatus.CALLED, QueueTokenStatus.SERVING)
                    and any(counter.id == token.assigned_counter_id and counter.is_active for counter in section_counters)
                ]
            )
            rows.append(
                AnalyticsSectionSummary(
                    section_id=section.id,
                    section_name=section.name,
                    section_type=section.section_type.value if hasattr(section.section_type, "value") else str(section.section_type),
                    waiting_tokens=sum(1 for token in active_section_tokens if token.status == QueueTokenStatus.WAITING),
                    serving_tokens=sum(1 for token in active_section_tokens if token.status in (QueueTokenStatus.CALLED, QueueTokenStatus.SERVING)),
                    completed_today=sum(
                        1
                        for token in period_tokens
                        if token.section_id == section.id and token.status == QueueTokenStatus.COMPLETED and self._at_or_after(token.completed_at, today_start)
                    ),
                    cancelled_today=sum(
                        1
                        for token in period_tokens
                        if token.section_id == section.id and token.status == QueueTokenStatus.CANCELLED and self._at_or_after(token.cancelled_at, today_start)
                    ),
                    total_cancellations=len(section_cancelled_tokens),
                    cancellations_last_hour=sum(1 for token in section_cancelled_tokens if token.cancelled_at >= now - timedelta(hours=1)),
                    active_counters=len(active_section_counters),
                    total_counters=len(section_counters),
                    last_token_number=last_token.token_number if last_token else None,
                    last_active_token_number=last_active_token.token_number if last_active_token else None,
                    estimated_wait_last_token_minutes=self._round(self._current_wait_minutes(last_token, now) if last_token else 0),
                    estimated_items_ahead=self._items_ahead(last_token, active_section_tokens) if last_token else 0,
                    average_items_today=self._round(self._average([token.item_count for token in section_today_tokens if token.item_count is not None])),
                    average_wait_minutes=self._round(self._average([self._current_wait_minutes(token, now) for token in active_section_tokens])),
                    utilization_percent=self._percent(len(busy_counter_ids), len(active_section_counters)),
                    active_counter_sessions=[
                        AnalyticsActiveCounterSession(
                            counter_id=counter.id,
                            counter_name=counter.name or f"Counter #{counter.id}",
                            assigned_token_number=self._counter_current_token(counter.id, active_section_tokens).token_number
                            if self._counter_current_token(counter.id, active_section_tokens)
                            else None,
                        )
                        for counter in active_section_counters
                    ],
                )
            )
        return rows

    def _build_counter_rows(self, counters, active_tokens, period_tokens, today_start) -> list[AnalyticsCounterSummary]:
        rows = []
        for counter in counters:
            counter_active_tokens = [token for token in active_tokens if token.assigned_counter_id == counter.id]
            current_token = next((token for token in counter_active_tokens if token.status in (QueueTokenStatus.CALLED, QueueTokenStatus.SERVING)), None)
            rows.append(
                AnalyticsCounterSummary(
                    counter_id=counter.id,
                    section_id=counter.section_id,
                    counter_name=counter.name or f"Counter #{counter.id}",
                    counter_type=counter.counter_type.value if hasattr(counter.counter_type, "value") else str(counter.counter_type),
                    is_active=counter.is_active,
                    current_token_number=current_token.token_number if current_token else None,
                    waiting_tokens=sum(1 for token in counter_active_tokens if token.status == QueueTokenStatus.WAITING),
                    serving_tokens=sum(1 for token in counter_active_tokens if token.status in (QueueTokenStatus.CALLED, QueueTokenStatus.SERVING)),
                    completed_today=sum(
                        1
                        for token in period_tokens
                        if token.assigned_counter_id == counter.id
                        and token.status == QueueTokenStatus.COMPLETED
                        and self._at_or_after(token.completed_at, today_start)
                    ),
                    utilization_percent=100.0 if counter.is_active and counter_active_tokens else 0.0,
                )
            )
        return rows

    def _build_daily_trends(self, period_tokens: list[QueueToken], start_date, days: int) -> list[AnalyticsDailyTrend]:
        rows = []
        for offset in range(days):
            day = start_date + timedelta(days=offset)
            day_tokens = [token for token in period_tokens if token.created_at.date() == day]
            completed_tokens = [token for token in period_tokens if token.status == QueueTokenStatus.COMPLETED and token.completed_at and token.completed_at.date() == day]
            cancelled_tokens = [token for token in period_tokens if token.status == QueueTokenStatus.CANCELLED and token.cancelled_at and token.cancelled_at.date() == day]
            rows.append(
                AnalyticsDailyTrend(
                    day=day,
                    token_count=len(day_tokens),
                    completed_count=len(completed_tokens),
                    cancelled_count=len(cancelled_tokens),
                    average_wait_minutes=self._round(self._average([self._terminal_wait_minutes(token) for token in completed_tokens])),
                    average_service_minutes=self._round(self._average_service_minutes(completed_tokens)),
                )
            )
        return rows

    def _build_peak_hours(self, period_tokens: list[QueueToken]) -> list[AnalyticsPeakHour]:
        hour_counts = ValueCounter(token.created_at.hour for token in period_tokens)
        return [
            AnalyticsPeakHour(hour=hour, token_count=count)
            for hour, count in sorted(hour_counts.items(), key=lambda item: (-item[1], item[0]))[:6]
        ]

    def _build_promotion_stats(self, period_tokens: list[QueueToken], event_dates: set) -> list[AnalyticsPromotionStat]:
        rows = []
        for day_type, tokens in (
            ("Promotion/Sale Day", [token for token in period_tokens if token.created_at.date() in event_dates]),
            ("Regular Day", [token for token in period_tokens if token.created_at.date() not in event_dates]),
        ):
            completed = [token for token in tokens if token.status == QueueTokenStatus.COMPLETED]
            cancellations = [token for token in tokens if token.status == QueueTokenStatus.CANCELLED]
            rows.append(
                AnalyticsPromotionStat(
                    day_type=day_type,
                    avg_footfall=self._round(len(tokens)),
                    avg_wait_time=self._round(self._average([self._token_wait_minutes(token) for token in tokens])),
                    avg_items=self._round(self._average([token.item_count for token in tokens if token.item_count is not None])),
                    avg_service_time=self._round(self._average_service_minutes(tokens)),
                    cancellations=len(cancellations),
                    completion_rate=self._percent(len(completed), len(tokens)),
                )
            )
        return rows

    def _build_weekly_stats(self, period_tokens: list[QueueToken]) -> list[AnalyticsWeeklyStat]:
        day_names = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
        rows = []
        for weekday, day_name in enumerate(day_names):
            tokens = [token for token in period_tokens if token.created_at.weekday() == weekday]
            cancellations = [token for token in tokens if token.status == QueueTokenStatus.CANCELLED]
            rows.append(
                AnalyticsWeeklyStat(
                    day_name=day_name,
                    total_visits=len(tokens),
                    avg_wait_time=self._round(self._average([self._token_wait_minutes(token) for token in tokens])),
                    avg_service_time=self._round(self._average_service_minutes(tokens)),
                    cancellations=len(cancellations),
                    cancellation_rate=self._percent(len(cancellations), len(tokens)),
                )
            )
        return rows

    def _build_hourly_stats(self, period_tokens: list[QueueToken]) -> list[AnalyticsHourlyStat]:
        rows = []
        for hour in range(24):
            tokens = [token for token in period_tokens if token.created_at.hour == hour]
            rows.append(
                AnalyticsHourlyStat(
                    hour=hour,
                    total_visits=len(tokens),
                    avg_wait_time=self._round(self._average([self._token_wait_minutes(token) for token in tokens])),
                    avg_service_time=self._round(self._average_service_minutes(tokens)),
                )
            )
        return rows

    def _build_zone_stats(self, sections: list[AnalyticsSectionSummary], period_tokens: list[QueueToken]) -> list[AnalyticsZoneStat]:
        rows = []
        for section in sections:
            tokens = [token for token in period_tokens if token.section_id == section.section_id]
            rows.append(
                AnalyticsZoneStat(
                    zone_name=section.section_name,
                    total_trials=sum(1 for token in tokens if token.status == QueueTokenStatus.COMPLETED),
                    cancellations=sum(1 for token in tokens if token.status == QueueTokenStatus.CANCELLED),
                    avg_wait_time=self._round(self._average([self._token_wait_minutes(token) for token in tokens])),
                    avg_service_time=self._round(self._average_service_minutes(tokens)),
                    total_items=sum(token.item_count or 0 for token in tokens),
                )
            )
        return rows

    def _build_customer_type_stats(self, period_tokens: list[QueueToken]) -> list[AnalyticsCustomerTypeStat]:
        customer_types = sorted({token.customer_type or "regular" for token in period_tokens}) or ["regular"]
        rows = []
        for customer_type in customer_types:
            tokens = [token for token in period_tokens if (token.customer_type or "regular") == customer_type]
            rows.append(
                AnalyticsCustomerTypeStat(
                    customer_type=customer_type,
                    count=len(tokens),
                    avg_wait=self._round(self._average([self._token_wait_minutes(token) for token in tokens])),
                    avg_service=self._round(self._average_service_minutes(tokens)),
                    total_items=sum(token.item_count or 0 for token in tokens),
                    cancellations=sum(1 for token in tokens if token.status == QueueTokenStatus.CANCELLED),
                )
            )
        return rows

    def _build_item_bucket_stats(self, period_tokens: list[QueueToken]) -> list[AnalyticsItemBucketStat]:
        buckets = (
            ("0-5", lambda count: count <= 5),
            ("6-15", lambda count: 6 <= count <= 15),
            ("16-30", lambda count: 16 <= count <= 30),
            ("31+", lambda count: count >= 31),
        )
        rows = []
        for label, predicate in buckets:
            tokens = [token for token in period_tokens if predicate(token.item_count or 0)]
            rows.append(
                AnalyticsItemBucketStat(
                    range=label,
                    count=len(tokens),
                    avg_wait=self._round(self._average([self._token_wait_minutes(token) for token in tokens])),
                    avg_service=self._round(self._average_service_minutes(tokens)),
                )
            )
        return rows

    def _build_insights(self, metrics, sections, calendar_signals, ml_summary) -> list[AnalyticsInsight]:
        insights: list[AnalyticsInsight] = []
        busiest_section = max(sections, key=lambda section: section.waiting_tokens, default=None)
        if busiest_section and busiest_section.waiting_tokens > 0:
            insights.append(
                AnalyticsInsight(
                    level="warning" if busiest_section.utilization_percent >= 80 else "info",
                    title=f"{busiest_section.section_name} has the most waiting tokens",
                    detail=f"{busiest_section.waiting_tokens} waiting with {busiest_section.utilization_percent:.0f}% counter utilization.",
                )
            )
        if metrics.active_counters < metrics.total_counters and metrics.waiting_tokens > 0:
            insights.append(
                AnalyticsInsight(
                    level="warning",
                    title="Inactive counters available",
                    detail=f"{metrics.total_counters - metrics.active_counters} counters are inactive while tokens are waiting.",
                )
            )
        if any(signal.event_type in (StoreCalendarEventType.PROMOTION.value, StoreCalendarEventType.SALE.value) for signal in calendar_signals):
            insights.append(
                AnalyticsInsight(
                    level="info",
                    title="Promotion or sale signal is active in this range",
                    detail="Compare token volume and wait times against regular days before staffing decisions.",
                )
            )
        if ml_summary.status != "READY":
            insights.append(
                AnalyticsInsight(
                    level="info",
                    title="ML prediction is not ready",
                    detail="Queue wait estimates will continue using the configured rule-based fallback.",
                )
            )
        return insights

    def _current_wait_minutes(self, token: QueueToken, now: datetime) -> float | None:
        if token is None or token.calling_time is None:
            return None
        return max((token.calling_time - now).total_seconds() / 60, 0)

    def _terminal_wait_minutes(self, token: QueueToken) -> float | None:
        if token.service_started_at is None:
            return None
        return max((token.service_started_at - token.created_at).total_seconds() / 60, 0)

    def _token_wait_minutes(self, token: QueueToken) -> float | None:
        if token.service_started_at is not None:
            return self._terminal_wait_minutes(token)
        if token.calling_time is not None:
            return max((token.calling_time - token.created_at).total_seconds() / 60, 0)
        return None

    def _average_service_minutes(self, tokens: list[QueueToken]) -> float:
        values = []
        for token in tokens:
            if token.service_started_at and token.completed_at:
                values.append(max((token.completed_at - token.service_started_at).total_seconds() / 60, 0))
            elif token.service_time_minutes is not None:
                values.append(float(token.service_time_minutes))
        return self._average(values)

    def _average(self, values) -> float:
        filtered = [value for value in values if value is not None]
        if not filtered:
            return 0.0
        return sum(filtered) / len(filtered)

    def _percent(self, numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return self._round((numerator / denominator) * 100)

    def _round(self, value: float) -> float:
        return round(float(value), 1)

    def _at_or_after(self, value: datetime | None, floor: datetime) -> bool:
        return value is not None and value >= floor

    def _latest_token(self, tokens: list[QueueToken]) -> QueueToken | None:
        if not tokens:
            return None
        return max(tokens, key=lambda token: (token.created_at, token.id))

    def _counter_current_token(self, counter_id: int, active_tokens: list[QueueToken]) -> QueueToken | None:
        tokens = [
            token
            for token in active_tokens
            if token.assigned_counter_id == counter_id and token.status in (QueueTokenStatus.CALLED, QueueTokenStatus.SERVING)
        ]
        return self._latest_token(tokens)

    def _items_ahead(self, token: QueueToken, active_tokens: list[QueueToken]) -> int:
        items = 0
        for active_token in active_tokens:
            if active_token.id == token.id:
                continue
            if active_token.calling_time and token.calling_time and active_token.calling_time <= token.calling_time:
                items += active_token.item_count or 0
            elif active_token.calling_time is None and active_token.created_at <= token.created_at:
                items += active_token.item_count or 0
        return items
