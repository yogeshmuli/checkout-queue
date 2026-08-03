from datetime import date, datetime

from pydantic import BaseModel


class TrialAnalyticsStoreSummary(BaseModel):
    id: int
    store_number: str
    name: str


class TrialAnalyticsMetricSummary(BaseModel):
    waiting_tokens: int
    called_tokens: int
    serving_tokens: int
    completed_today: int
    cancelled_today: int
    no_show_today: int
    active_studios: int
    total_studios: int
    average_wait_minutes: float
    average_service_minutes: float
    average_items_today: float
    cancellations_last_hour: int
    studio_utilization_percent: float


class TrialAnalyticsActiveStudioSession(BaseModel):
    studio_id: int
    studio_name: str
    assigned_token_number: str | None


class TrialAnalyticsZoneSummary(BaseModel):
    zone_id: int
    zone_name: str
    zone_type: str
    gender: str
    waiting_tokens: int
    serving_tokens: int
    completed_today: int
    cancelled_today: int
    total_cancellations: int
    cancellations_last_hour: int
    active_studios: int
    total_studios: int
    last_token_number: str | None
    last_active_token_number: str | None
    estimated_wait_last_token_minutes: float
    estimated_items_ahead: int
    average_items_today: float
    average_wait_minutes: float
    utilization_percent: float
    active_studio_sessions: list[TrialAnalyticsActiveStudioSession]


class TrialAnalyticsStudioSummary(BaseModel):
    studio_id: int
    zone_id: int
    studio_name: str
    studio_type: str
    is_active: bool
    current_token_number: str | None
    waiting_tokens: int
    serving_tokens: int
    completed_today: int
    utilization_percent: float


class TrialAnalyticsDailyTrend(BaseModel):
    day: date
    token_count: int
    completed_count: int
    cancelled_count: int
    average_wait_minutes: float
    average_service_minutes: float


class TrialAnalyticsPeakHour(BaseModel):
    hour: int
    token_count: int


class TrialAnalyticsPromotionStat(BaseModel):
    day_type: str
    avg_footfall: float
    avg_wait_time: float
    avg_items: float
    avg_service_time: float
    cancellations: int
    completion_rate: float


class TrialAnalyticsWeeklyStat(BaseModel):
    day_name: str
    total_visits: int
    avg_wait_time: float
    avg_service_time: float
    cancellations: int
    cancellation_rate: float


class TrialAnalyticsHourlyStat(BaseModel):
    hour: int
    total_visits: int
    avg_wait_time: float
    avg_service_time: float


class TrialAnalyticsZoneStat(BaseModel):
    zone_name: str
    total_trials: int
    cancellations: int
    avg_wait_time: float
    avg_service_time: float
    total_items: int


class TrialAnalyticsCustomerTypeStat(BaseModel):
    customer_type: str
    count: int
    avg_wait: float
    avg_service: float
    total_items: int
    cancellations: int


class TrialAnalyticsItemBucketStat(BaseModel):
    range: str
    count: int
    avg_wait: float
    avg_service: float


class TrialAnalyticsCalendarSignal(BaseModel):
    event_date: date
    event_type: str
    name: str | None


class TrialAnalyticsMLSummary(BaseModel):
    status: str
    model_type: str | None
    model_version: str | None
    trained_at: datetime | None
    sample_size: int
    mae: float | None
    r2_score: float | None


class TrialAnalyticsInsight(BaseModel):
    level: str
    title: str
    detail: str


class TrialStoreAnalyticsResponse(BaseModel):
    store: TrialAnalyticsStoreSummary
    days: int
    generated_at: datetime
    metrics: TrialAnalyticsMetricSummary
    zones: list[TrialAnalyticsZoneSummary]
    studios: list[TrialAnalyticsStudioSummary]
    daily_trends: list[TrialAnalyticsDailyTrend]
    peak_hours: list[TrialAnalyticsPeakHour]
    promotion_stats: list[TrialAnalyticsPromotionStat]
    weekly_stats: list[TrialAnalyticsWeeklyStat]
    hourly_stats: list[TrialAnalyticsHourlyStat]
    zone_stats: list[TrialAnalyticsZoneStat]
    customer_type_stats: list[TrialAnalyticsCustomerTypeStat]
    item_bucket_stats: list[TrialAnalyticsItemBucketStat]
    calendar_signals: list[TrialAnalyticsCalendarSignal]
    ml_summary: TrialAnalyticsMLSummary
    insights: list[TrialAnalyticsInsight]
