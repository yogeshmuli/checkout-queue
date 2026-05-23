from datetime import date, datetime

from pydantic import BaseModel


class AnalyticsStoreSummary(BaseModel):
    id: int
    store_number: str
    name: str


class AnalyticsMetricSummary(BaseModel):
    waiting_tokens: int
    called_tokens: int
    serving_tokens: int
    completed_today: int
    cancelled_today: int
    no_show_today: int
    active_counters: int
    total_counters: int
    average_wait_minutes: float
    average_service_minutes: float
    average_items_today: float
    cancellations_last_hour: int
    counter_utilization_percent: float


class AnalyticsActiveCounterSession(BaseModel):
    counter_id: int
    counter_name: str
    assigned_token_number: str | None


class AnalyticsSectionSummary(BaseModel):
    section_id: int
    section_name: str
    section_type: str
    waiting_tokens: int
    serving_tokens: int
    completed_today: int
    cancelled_today: int
    total_cancellations: int
    cancellations_last_hour: int
    active_counters: int
    total_counters: int
    last_token_number: str | None
    last_active_token_number: str | None
    estimated_wait_last_token_minutes: float
    estimated_items_ahead: int
    average_items_today: float
    average_wait_minutes: float
    utilization_percent: float
    active_counter_sessions: list[AnalyticsActiveCounterSession]


class AnalyticsCounterSummary(BaseModel):
    counter_id: int
    section_id: int
    counter_name: str
    counter_type: str
    is_active: bool
    current_token_number: str | None
    waiting_tokens: int
    serving_tokens: int
    completed_today: int
    utilization_percent: float


class AnalyticsDailyTrend(BaseModel):
    day: date
    token_count: int
    completed_count: int
    cancelled_count: int
    average_wait_minutes: float
    average_service_minutes: float


class AnalyticsPeakHour(BaseModel):
    hour: int
    token_count: int


class AnalyticsPromotionStat(BaseModel):
    day_type: str
    avg_footfall: float
    avg_wait_time: float
    avg_items: float
    avg_service_time: float
    cancellations: int
    completion_rate: float


class AnalyticsWeeklyStat(BaseModel):
    day_name: str
    total_visits: int
    avg_wait_time: float
    avg_service_time: float
    cancellations: int
    cancellation_rate: float


class AnalyticsHourlyStat(BaseModel):
    hour: int
    total_visits: int
    avg_wait_time: float
    avg_service_time: float


class AnalyticsZoneStat(BaseModel):
    zone_name: str
    total_trials: int
    cancellations: int
    avg_wait_time: float
    avg_service_time: float
    total_items: int


class AnalyticsCustomerTypeStat(BaseModel):
    customer_type: str
    count: int
    avg_wait: float
    avg_service: float
    total_items: int
    cancellations: int


class AnalyticsItemBucketStat(BaseModel):
    range: str
    count: int
    avg_wait: float
    avg_service: float


class AnalyticsCalendarSignal(BaseModel):
    event_date: date
    event_type: str
    name: str | None


class AnalyticsMLSummary(BaseModel):
    status: str
    model_type: str | None
    model_version: str | None
    trained_at: datetime | None
    sample_size: int
    mae: float | None
    r2_score: float | None


class AnalyticsInsight(BaseModel):
    level: str
    title: str
    detail: str


class StoreAnalyticsResponse(BaseModel):
    store: AnalyticsStoreSummary
    days: int
    generated_at: datetime
    metrics: AnalyticsMetricSummary
    sections: list[AnalyticsSectionSummary]
    counters: list[AnalyticsCounterSummary]
    daily_trends: list[AnalyticsDailyTrend]
    peak_hours: list[AnalyticsPeakHour]
    promotion_stats: list[AnalyticsPromotionStat]
    weekly_stats: list[AnalyticsWeeklyStat]
    hourly_stats: list[AnalyticsHourlyStat]
    zone_stats: list[AnalyticsZoneStat]
    customer_type_stats: list[AnalyticsCustomerTypeStat]
    item_bucket_stats: list[AnalyticsItemBucketStat]
    calendar_signals: list[AnalyticsCalendarSignal]
    ml_summary: AnalyticsMLSummary
    insights: list[AnalyticsInsight]
