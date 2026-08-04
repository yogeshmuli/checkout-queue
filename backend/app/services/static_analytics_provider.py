import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from app.schemas.analytics import (
    AnalyticsActiveCounterSession, AnalyticsCalendarSignal, AnalyticsCounterSummary,
    AnalyticsCustomerTypeStat, AnalyticsDailyTrend, AnalyticsHourlyStat, AnalyticsInsight,
    AnalyticsItemBucketStat, AnalyticsMetricSummary, AnalyticsMLSummary, AnalyticsPeakHour,
    AnalyticsPromotionStat, AnalyticsSectionSummary, AnalyticsStoreSummary, AnalyticsWeeklyStat,
    AnalyticsZoneStat, StoreAnalyticsResponse,
)
from app.schemas.trial_analytics import (
    TrialAnalyticsActiveStudioSession, TrialAnalyticsCalendarSignal, TrialAnalyticsCustomerTypeStat,
    TrialAnalyticsDailyTrend, TrialAnalyticsHourlyStat, TrialAnalyticsInsight,
    TrialAnalyticsItemBucketStat, TrialAnalyticsMetricSummary, TrialAnalyticsMLSummary,
    TrialAnalyticsPeakHour, TrialAnalyticsPromotionStat, TrialAnalyticsStoreSummary,
    TrialAnalyticsStudioSummary, TrialAnalyticsWeeklyStat, TrialAnalyticsZoneStat,
    TrialAnalyticsZoneSummary, TrialStoreAnalyticsResponse,
)

STATIC_DATA_PATH = Path(__file__).resolve().parents[1] / "static_analytics_data.json"


def load_static_analytics_data():
    with STATIC_DATA_PATH.open(encoding="utf-8") as fixture:
        return json.load(fixture)


class StaticAnalyticsProvider:
    def __init__(self):
        self.data = load_static_analytics_data()

    @staticmethod
    def _round(value):
        return float(Decimal(str(value or 0)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))

    @staticmethod
    def _average(rows, key):
        if not rows:
            return 0.0
        value = sum(Decimal(str(row[key])) for row in rows) / Decimal(len(rows))
        return float(value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))

    @staticmethod
    def _metadata(metadata, model):
        values = dict(
            status=metadata.status if metadata else "NOT_TRAINED",
            model_type=metadata.model_type if metadata else None,
            model_version=metadata.model_version if metadata else None,
            trained_at=metadata.trained_at if metadata else None,
            sample_size=metadata.sample_size if metadata else 0,
            mae=metadata.mae if metadata else None,
            r2_score=metadata.r2_score if metadata else None,
        )
        return model(**values)

    def _range(self, days, today):
        selected = self.data["date_based_analytics"][-days:]
        start = today - timedelta(days=len(selected) - 1)
        return [(start + timedelta(days=index), row) for index, row in enumerate(selected)]

    def _shared(self, days, today, models):
        rows = self._range(days, today)
        daily_model, peak_model, promo_model, weekly_model, hourly_model, calendar_model = models
        daily = [daily_model(day=day, token_count=row["check_ins"], completed_count=row["completed"], cancelled_count=row["cancellations"], average_wait_minutes=row["avg_wait_minutes"], average_service_minutes=row["avg_service_minutes"]) for day, row in rows]
        promotion = [promo_model(
            day_type=row["day_type"], avg_footfall=row["avg_footfall"], avg_wait_time=row["avg_wait_minutes"],
            avg_items=row["avg_items"], avg_service_time=row["avg_service_minutes"],
            cancellations=row["total_cancellations"], completion_rate=row["completion_rate_percent"],
        ) for row in self.data["promotion_day_analysis"]]
        weekly = [weekly_model(
            day_name=row["day_name"], total_visits=row["avg_visits"], avg_wait_time=row["avg_wait_minutes"],
            avg_service_time=row["avg_service_minutes"], cancellations=row["cancellations"],
            cancellation_rate=row["cancellation_rate_percent"],
        ) for row in self.data["segmented_analysis"]["weekly_patterns"]]
        hourly_source = self.data["segmented_analysis"]["hourly_performance"]
        hourly = [hourly_model(hour=row["hour"], total_visits=row["traffic"], avg_wait_time=row["avg_wait_minutes"], avg_service_time=row["avg_service_minutes"]) for row in hourly_source]
        peaks = [peak_model(hour=row["hour"], token_count=row["traffic"]) for row in sorted(hourly_source, key=lambda row: (-row["traffic"], row["hour"]))[:6]]
        signals = [calendar_model(event_date=day, event_type="PROMOTION", name="Static promotion day") for day, row in rows if row["is_promotion_day"]]
        return rows, daily, peaks, promotion, weekly, hourly, signals

    def checkout(self, store, days, metadata, now=None):
        now = now or datetime.now(timezone.utc)
        shared = self._shared(days, now.date(), (AnalyticsDailyTrend, AnalyticsPeakHour, AnalyticsPromotionStat, AnalyticsWeeklyStat, AnalyticsHourlyStat, AnalyticsCalendarSignal))
        rows, daily, peaks, promotion, weekly, hourly, signals = shared
        sections = []
        counters = []
        zone_stats = []
        for index, row in enumerate(self.data["zone_based_analytics"], start=1):
            section_name = f"Section {index}"
            sections.append(AnalyticsSectionSummary(
                section_id=index, section_name=section_name, section_type="REGULAR", waiting_tokens=0,
                serving_tokens=0, completed_today=row["completed"], cancelled_today=row["cancellations"],
                total_cancellations=row["cancellations"], cancellations_last_hour=0, active_counters=1,
                total_counters=1, last_token_number=None, last_active_token_number=None,
                estimated_wait_last_token_minutes=row["avg_wait_minutes"], estimated_items_ahead=0,
                average_items_today=row["avg_items"], average_wait_minutes=row["avg_wait_minutes"], utilization_percent=0,
                active_counter_sessions=[AnalyticsActiveCounterSession(counter_id=index, counter_name=f"Counter {index}", assigned_token_number=None)],
            ))
            counters.append(AnalyticsCounterSummary(
                counter_id=index, section_id=index, counter_name=f"Counter {index}", counter_type="REGULAR",
                is_active=True, current_token_number=None, waiting_tokens=0, serving_tokens=0,
                completed_today=row["completed"], utilization_percent=0,
            ))
            zone_stats.append(AnalyticsZoneStat(zone_name=section_name, total_trials=row["trials"], cancellations=row["cancellations"], avg_wait_time=row["avg_wait_minutes"], avg_service_time=row["avg_service_minutes"], total_items=round(row["trials"] * row["avg_items"])))
        last = rows[-1][1]
        metrics = AnalyticsMetricSummary(
            waiting_tokens=0, called_tokens=0, serving_tokens=0, completed_today=last["completed"],
            cancelled_today=last["cancellations"], no_show_today=0, active_counters=4, total_counters=4,
            average_wait_minutes=last["avg_wait_minutes"], average_service_minutes=self._average([row for _, row in rows], "avg_service_minutes"),
            average_items_today=last["avg_items"], cancellations_last_hour=0, counter_utilization_percent=0,
        )
        return StoreAnalyticsResponse(
            store=AnalyticsStoreSummary(id=store.id, store_number=store.store_number, name=store.name),
            days=days, generated_at=now, metrics=metrics, sections=sections, counters=counters,
            daily_trends=daily, peak_hours=peaks, promotion_stats=promotion, weekly_stats=weekly,
            hourly_stats=hourly, zone_stats=zone_stats,
            customer_type_stats=[AnalyticsCustomerTypeStat(customer_type=row["customer_type"], count=row["check_ins"], avg_wait=row["avg_wait_minutes"], avg_service=row["avg_service_minutes"], total_items=round(row["check_ins"] * row["avg_items"]), cancellations=row["cancellations"]) for row in self.data["gender_and_item_analytics"]["customer_types"]],
            item_bucket_stats=[AnalyticsItemBucketStat(range=row["item_range"], count=row["customers"], avg_wait=row["avg_wait_minutes"], avg_service=row["avg_service_minutes"]) for row in self.data["gender_and_item_analytics"]["item_buckets"]],
            calendar_signals=signals, ml_summary=self._metadata(metadata, AnalyticsMLSummary),
            insights=[AnalyticsInsight(level="info", title="Static history", detail="Historical analytics are sourced from the configured static dataset.")],
        )

    def trial(self, store, days, metadata, now=None):
        now = now or datetime.now(timezone.utc)
        shared = self._shared(days, now.date(), (TrialAnalyticsDailyTrend, TrialAnalyticsPeakHour, TrialAnalyticsPromotionStat, TrialAnalyticsWeeklyStat, TrialAnalyticsHourlyStat, TrialAnalyticsCalendarSignal))
        rows, daily, peaks, promotion, weekly, hourly, signals = shared
        zones = []
        studios = []
        zone_stats = []
        for index, row in enumerate(self.data["zone_based_analytics"], start=1):
            zones.append(TrialAnalyticsZoneSummary(
                zone_id=index, zone_name=row["zone_name"], zone_type="REGULAR", gender=row["gender"],
                waiting_tokens=0, serving_tokens=0, completed_today=row["completed"], cancelled_today=row["cancellations"],
                total_cancellations=row["cancellations"], cancellations_last_hour=0, active_studios=1,
                total_studios=1, last_token_number=None, last_active_token_number=None,
                estimated_wait_last_token_minutes=row["avg_wait_minutes"], estimated_items_ahead=0,
                average_items_today=row["avg_items"], average_wait_minutes=row["avg_wait_minutes"], utilization_percent=0,
                active_studio_sessions=[TrialAnalyticsActiveStudioSession(studio_id=index, studio_name=f"Studio {index}", assigned_token_number=None)],
            ))
            studios.append(TrialAnalyticsStudioSummary(
                studio_id=index, zone_id=index, studio_name=f"Studio {index}", studio_type="REGULAR",
                is_active=True, current_token_number=None, waiting_tokens=0, serving_tokens=0,
                completed_today=row["completed"], utilization_percent=0,
            ))
            zone_stats.append(TrialAnalyticsZoneStat(zone_name=row["zone_name"], total_trials=row["trials"], cancellations=row["cancellations"], avg_wait_time=row["avg_wait_minutes"], avg_service_time=row["avg_service_minutes"], total_items=round(row["trials"] * row["avg_items"])))
        last = rows[-1][1]
        metrics = TrialAnalyticsMetricSummary(
            waiting_tokens=0, called_tokens=0, serving_tokens=0, completed_today=last["completed"],
            cancelled_today=last["cancellations"], no_show_today=0, active_studios=4, total_studios=4,
            average_wait_minutes=last["avg_wait_minutes"], average_service_minutes=self._average([row for _, row in rows], "avg_service_minutes"),
            average_items_today=last["avg_items"], cancellations_last_hour=0, studio_utilization_percent=0,
        )
        return TrialStoreAnalyticsResponse(
            store=TrialAnalyticsStoreSummary(id=store.id, store_number=store.store_number, name=store.name),
            days=days, generated_at=now, metrics=metrics, zones=zones, studios=studios,
            daily_trends=daily, peak_hours=peaks, promotion_stats=promotion, weekly_stats=weekly,
            hourly_stats=hourly, zone_stats=zone_stats,
            customer_type_stats=[TrialAnalyticsCustomerTypeStat(customer_type=row["customer_type"], count=row["check_ins"], avg_wait=row["avg_wait_minutes"], avg_service=row["avg_service_minutes"], total_items=round(row["check_ins"] * row["avg_items"]), cancellations=row["cancellations"]) for row in self.data["gender_and_item_analytics"]["customer_types"]],
            item_bucket_stats=[TrialAnalyticsItemBucketStat(range=row["item_range"], count=row["customers"], avg_wait=row["avg_wait_minutes"], avg_service=row["avg_service_minutes"]) for row in self.data["gender_and_item_analytics"]["item_buckets"]],
            calendar_signals=signals, ml_summary=self._metadata(metadata, TrialAnalyticsMLSummary),
            insights=[TrialAnalyticsInsight(level="info", title="Static history", detail="Historical analytics are sourced from the configured static dataset.")],
        )
