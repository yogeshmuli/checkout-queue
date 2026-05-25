import math
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.trial import TrialCalendarDay, TrialCalendarEvent, TrialHoliday, TrialQueueToken, TrialQueueTokenStatus, TrialStoreConfig, TrialStudio, TrialZone, TrialZoneGender
from app.schemas.ml import TrialServiceTimePredictionRequest
from app.repositories.trial_repository import TrialRepository
from app.schemas.trial import (
    TrialCalendarDayResponse,
    TrialCalendarEventResponse,
    TrialCalendarResponse,
    TrialCalendarUpdateRequest,
    TrialHolidayResponse,
    TrialQueueEventRequest,
    TrialQueueEventResponse,
    TrialQueueEventType,
    TrialQueueJoinRequest,
    TrialQueueJoinResponse,
    TrialQueueTokenResponse,
    TrialStoreConfigResponse,
    TrialStoreConfigUpdateRequest,
    TrialStoreResponse,
    TrialStoreZoneResponse,
    TrialStudioCreateRequest,
    TrialStudioQueueResponse,
    TrialStudioResponse,
    TrialStudioStatusUpdateRequest,
    TrialStudioUpdateRequest,
    TrialZoneCreateRequest,
    TrialZoneResponse,
    TrialZoneUpdateRequest,
)
from app.services.notification_service import NotificationService
from app.services.trial_prediction_service import TrialPredictionService


DEFAULT_TIMEZONE = "Asia/Kolkata"
DEFAULT_OPEN_TIME = time(0, 0)
DEFAULT_CLOSE_TIME = time(23, 59)


class TrialService:
    BASE_SERVICE_MINUTES = 8
    PER_UNIT_SERVICE_MINUTES = 1.0
    MIN_SERVICE_MINUTES = 10
    CALCULATION_METHOD = "RULE_BASED"
    TERMINAL_STATUSES = (TrialQueueTokenStatus.COMPLETED, TrialQueueTokenStatus.CANCELLED, TrialQueueTokenStatus.NO_SHOW)

    def __init__(self, db: Session) -> None:
        self.repository = TrialRepository(db)

    def create_zone(self, payload: TrialZoneCreateRequest) -> TrialZone:
        self._ensure_store_exists(payload.store_id)
        name = payload.name.strip()
        if self.repository.get_zone_by_store_and_name(payload.store_id, name) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Trial zone name already exists for this store")
        zone = TrialZone(
            store_id=payload.store_id,
            name=name,
            zone_type=payload.zone_type,
            gender=payload.gender,
            is_active=payload.is_active,
        )
        self.repository.create(zone)
        self.repository.commit()
        self.repository.refresh(zone)
        return zone

    def list_zones(self, include_inactive: bool = False, store_id: int | None = None) -> list[TrialZone]:
        return self.repository.list_zones(include_inactive=include_inactive, store_id=store_id)

    def get_zone(self, zone_id: int) -> TrialZone:
        zone = self.repository.get_zone(zone_id)
        if zone is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial zone not found")
        return zone

    def update_zone(self, zone_id: int, payload: TrialZoneUpdateRequest) -> TrialZone:
        zone = self.get_zone(zone_id)
        update_data = payload.model_dump(exclude_unset=True)
        store_id = update_data.get("store_id", zone.store_id)
        self._ensure_store_exists(store_id)
        if "name" in update_data:
            update_data["name"] = update_data["name"].strip()
            existing = self.repository.get_zone_by_store_and_name(store_id, update_data["name"])
            if existing is not None and existing.id != zone.id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Trial zone name already exists for this store")
        for field, value in update_data.items():
            setattr(zone, field, value)
        self.repository.commit()
        self.repository.refresh(zone)
        return zone

    def deactivate_zone(self, zone_id: int) -> TrialZone:
        zone = self.get_zone(zone_id)
        zone.is_active = False
        self.repository.commit()
        self.repository.refresh(zone)
        return zone

    def create_studio(self, payload: TrialStudioCreateRequest) -> TrialStudio:
        zone = self.get_zone(payload.trial_zone_id)
        name = payload.name.strip() if payload.name else None
        if name and self.repository.get_studio_by_zone_and_name(zone.id, name) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Studio name already exists for this trial zone")
        studio = TrialStudio(
            trial_zone_id=zone.id,
            name=name,
            studio_type=payload.studio_type,
            is_active=payload.is_active,
            next_available_time=datetime.now(timezone.utc),
        )
        self.repository.create(studio)
        self.repository.commit()
        self.repository.refresh(studio)
        return studio

    def list_studios(self, include_inactive: bool = False, store_id: int | None = None, trial_zone_id: int | None = None) -> list[TrialStudio]:
        return self.repository.list_studios(include_inactive=include_inactive, store_id=store_id, trial_zone_id=trial_zone_id)

    def get_studio(self, studio_id: int) -> TrialStudio:
        studio = self.repository.get_studio(studio_id)
        if studio is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Studio not found")
        return studio

    def update_studio(self, studio_id: int, payload: TrialStudioUpdateRequest) -> TrialStudio:
        studio = self.get_studio(studio_id)
        update_data = payload.model_dump(exclude_unset=True)
        zone_id = update_data.get("trial_zone_id", studio.trial_zone_id)
        self.get_zone(zone_id)
        if "name" in update_data:
            update_data["name"] = update_data["name"].strip() if update_data["name"] else None
            if update_data["name"]:
                existing = self.repository.get_studio_by_zone_and_name(zone_id, update_data["name"])
                if existing is not None and existing.id != studio.id:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Studio name already exists for this trial zone")
        for field, value in update_data.items():
            setattr(studio, field, value)
        self.repository.commit()
        self.repository.refresh(studio)
        return studio

    def deactivate_studio(self, studio_id: int) -> TrialStudio:
        studio = self.get_studio(studio_id)
        studio.is_active = False
        self.repository.commit()
        self.repository.refresh(studio)
        return studio

    def get_config(self, store_id: int) -> TrialStoreConfig:
        self._ensure_store_exists(store_id)
        config = self.repository.get_config(store_id)
        if config is None:
            config = TrialStoreConfig(store_id=store_id)
            self.repository.create(config)
            self.repository.commit()
            self.repository.refresh(config)
        return config

    def update_config(self, store_id: int, payload: TrialStoreConfigUpdateRequest) -> TrialStoreConfig:
        config = self.get_config(store_id)
        update_data = payload.model_dump()
        if update_data.get("token_id_prefix") is not None:
            update_data["token_id_prefix"] = update_data["token_id_prefix"].strip().upper() or None
        for field, value in update_data.items():
            setattr(config, field, value)
        self.repository.commit()
        self.repository.refresh(config)
        return config

    def get_calendar(self, store_id: int) -> TrialCalendarResponse:
        self._ensure_store_exists(store_id)
        days = self._ensure_default_days(store_id)
        self.repository.commit()
        return self._build_calendar_response(store_id, days, self.repository.list_holidays(store_id), self.repository.list_events(store_id))

    def update_calendar(self, store_id: int, payload: TrialCalendarUpdateRequest) -> TrialCalendarResponse:
        self._ensure_store_exists(store_id)
        self._validate_timezone(payload.timezone)
        weekdays = [day.weekday for day in payload.days]
        if len(set(weekdays)) != 7 or set(weekdays) != set(range(7)):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Trial calendar must include weekdays 0 through 6")
        for day_payload in payload.days:
            day = self.repository.get_day(store_id, day_payload.weekday)
            if day is None:
                day = TrialCalendarDay(store_id=store_id, weekday=day_payload.weekday)
                self.repository.create(day)
            day.is_open = day_payload.is_open
            day.open_time = day_payload.open_time
            day.close_time = day_payload.close_time
            day.timezone = payload.timezone
        self.repository.delete_holidays(store_id)
        for holiday_payload in payload.holidays:
            self.repository.create(TrialHoliday(store_id=store_id, holiday_date=holiday_payload.holiday_date, name=holiday_payload.name, is_active=holiday_payload.is_active))
        if payload.events is not None:
            self.repository.delete_events(store_id)
            for event_payload in payload.events:
                self.repository.create(TrialCalendarEvent(store_id=store_id, event_date=event_payload.event_date, name=event_payload.name, event_type=event_payload.event_type, is_active=event_payload.is_active))
        self.repository.commit()
        return self._build_calendar_response(store_id, self.repository.list_days(store_id), self.repository.list_holidays(store_id), self.repository.list_events(store_id))

    def join_queue(self, payload: TrialQueueJoinRequest) -> TrialQueueJoinResponse:
        store = self.repository.get_store(payload.store_id)
        if store is None or not store.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active store not found")
        if not self._is_store_open(payload.store_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Store is closed for trial queue joining")
        if payload.trial_zone_id is not None:
            zone = self.repository.get_zone(payload.trial_zone_id)
            if zone is None or not zone.is_active or zone.store_id != payload.store_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active trial zone not found")
            if payload.customer_gender is not None and zone.gender not in (TrialZoneGender.UNISEX, payload.customer_gender):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Selected trial zone does not support customer gender")
        if self.repository.get_active_token_for_phone(payload.store_id, payload.phone_number) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Active trial token already exists for phone")

        studios = self.repository.list_active_studios(payload.store_id, payload.trial_zone_id)
        if payload.trial_zone_id is None and payload.customer_gender is not None:
            eligible_zone_ids = {
                zone.id
                for zone in self.repository.list_zones(include_inactive=False, store_id=payload.store_id)
                if zone.gender in (TrialZoneGender.UNISEX, payload.customer_gender)
            }
            studios = [studio for studio in studios if studio.trial_zone_id in eligible_zone_ids]
        if not studios:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="No active studios available")
        now = datetime.now(timezone.utc)
        for studio in studios:
            self._rebuild_studio_schedule(studio.id, now)
        selected = min(studios, key=lambda studio: self._normalize_to_utc(studio.next_available_time))
        calling_time = max(now, self._normalize_to_utc(selected.next_available_time))
        config = self.get_config(payload.store_id)
        prediction = TrialPredictionService(self.repository).predict_service_time(
            payload.store_id,
            TrialServiceTimePredictionRequest(
                trial_zone_id=payload.trial_zone_id,
                assigned_studio_id=selected.id,
                item_count=payload.item_count,
                customer_type=payload.customer_type,
                requested_at=now,
            ),
        )
        calculation_method = prediction.calculation_method if prediction is not None else self.CALCULATION_METHOD
        service_minutes = prediction.service_time_minutes if prediction is not None else self._estimate_service_minutes(payload.item_count, config)
        wait_minutes = max(0, math.ceil((calling_time - now).total_seconds() / 60))
        position = self._calculate_studio_position(selected.id, calling_time)
        selected.next_available_time = calling_time + timedelta(minutes=service_minutes)
        token = TrialQueueToken(
            store_id=payload.store_id,
            trial_zone_id=payload.trial_zone_id,
            assigned_studio_id=selected.id,
            token_number=self._generate_token_number(payload.store_id, payload.trial_zone_id, config),
            phone_number=payload.phone_number,
            status=TrialQueueTokenStatus.WAITING,
            item_count=payload.item_count,
            customer_type=payload.customer_type,
            service_time_minutes=service_minutes,
            calculation_method=calculation_method,
            calling_time=calling_time,
        )
        self.repository.create(token)
        self.repository.commit()
        self.repository.refresh(token)
        return TrialQueueJoinResponse(
            token_id=token.id,
            token_number=token.token_number,
            store_id=token.store_id,
            trial_zone_id=token.trial_zone_id,
            assigned_studio_id=token.assigned_studio_id,
            status=token.status,
            position=position,
            estimated_wait_minutes=wait_minutes,
            calculation_method=calculation_method,
            calling_time=calling_time,
        )

    def list_store_zones(self) -> list[TrialStoreResponse]:
        stores = self.repository.list_active_stores_with_zones()
        return [
            TrialStoreResponse(
                id=store.id,
                store_number=store.store_number,
                name=store.name,
                zones=[
                    TrialStoreZoneResponse(id=zone.id, name=zone.name, zone_type=zone.zone_type, gender=zone.gender)
                    for zone in store.trial_zones
                    if zone.is_active
                ],
            )
            for store in stores
        ]

    def get_token_status(self, token_id: int | None = None, store_id: int | None = None, phone_number: str | None = None) -> TrialQueueTokenResponse:
        token = self.repository.get_token(token_id) if token_id is not None else None
        if token is None and store_id is not None and phone_number is not None:
            token = self.repository.get_latest_token_for_phone(store_id, phone_number)
        if token is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial token not found")
        return self._build_token_response(token)

    def list_queue_tokens(self, store_id=None, trial_zone_id=None, studio_id=None, token_status=None, include_terminal=False) -> list[TrialQueueTokenResponse]:
        return [
            self._build_token_response(token)
            for token in self.repository.list_queue_tokens(store_id, trial_zone_id, studio_id, token_status, include_terminal)
        ]

    def get_studio_queue(self, studio_id: int) -> TrialStudioQueueResponse:
        studio = self.get_studio(studio_id)
        return TrialStudioQueueResponse(studio_id=studio.id, studio_name=studio.name, is_active=studio.is_active, next_available_time=self._normalize_to_utc(studio.next_available_time), tokens=[self._build_token_response(token) for token in self.repository.list_tokens_for_studio(studio.id)])

    def update_studio_status(self, studio_id: int, payload: TrialStudioStatusUpdateRequest) -> TrialStudioQueueResponse:
        studio = self.get_studio(studio_id)
        studio.is_active = payload.is_active
        if payload.is_active:
            studio.next_available_time = max(datetime.now(timezone.utc), self._normalize_to_utc(studio.next_available_time))
        self.repository.commit()
        return self.get_studio_queue(studio_id)

    def handle_queue_event(self, payload: TrialQueueEventRequest) -> TrialQueueEventResponse:
        status_map = {
            TrialQueueEventType.CALLED: TrialQueueTokenStatus.CALLED,
            TrialQueueEventType.SERVING: TrialQueueTokenStatus.SERVING,
            TrialQueueEventType.COMPLETED: TrialQueueTokenStatus.COMPLETED,
            TrialQueueEventType.CANCELLED: TrialQueueTokenStatus.CANCELLED,
        }
        return self._build_event_response(self.process_queue_event(payload.token_id, status_map[payload.event], payload.cancellation_reason))

    def start_token(self, token_id: int) -> TrialQueueEventResponse:
        return self._build_event_response(self.process_queue_event(token_id, TrialQueueTokenStatus.SERVING))

    def complete_token(self, token_id: int) -> TrialQueueEventResponse:
        return self._build_event_response(self.process_queue_event(token_id, TrialQueueTokenStatus.COMPLETED))

    def cancel_token(self, token_id: int, reason: str | None = None) -> TrialQueueEventResponse:
        return self._build_event_response(self.process_queue_event(token_id, TrialQueueTokenStatus.CANCELLED, reason))

    def process_queue_event(self, token_id: int, new_status: TrialQueueTokenStatus, cancellation_reason: str | None = None) -> TrialQueueToken:
        token = self.repository.get_token(token_id)
        if token is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial token not found")
        if token.status in self.TERMINAL_STATUSES and token.status != new_status:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Trial token is already in terminal state")
        if new_status == TrialQueueTokenStatus.CALLED and token.status != TrialQueueTokenStatus.WAITING:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only waiting trial token can be called")
        now = datetime.now(timezone.utc)
        token.status = new_status
        if new_status == TrialQueueTokenStatus.CALLED:
            token.called_at = now
            token.calling_time = now
        elif new_status == TrialQueueTokenStatus.SERVING:
            token.service_started_at = now
            token.called_at = token.called_at or now
        elif new_status == TrialQueueTokenStatus.COMPLETED:
            token.completed_at = now
        elif new_status in (TrialQueueTokenStatus.CANCELLED, TrialQueueTokenStatus.NO_SHOW):
            token.cancelled_at = now
            token.cancellation_reason = cancellation_reason or new_status.value
        if token.assigned_studio_id is not None:
            self._rebuild_studio_schedule(token.assigned_studio_id, now)
        self.repository.commit()
        self.repository.refresh(token)
        if new_status == TrialQueueTokenStatus.CALLED and getattr(self.repository, "db", None) is not None:
            NotificationService(self.repository.db).notify_trial_called(token)
        return token

    def _ensure_store_exists(self, store_id: int) -> None:
        if self.repository.get_store(store_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

    def _ensure_default_days(self, store_id: int) -> list[TrialCalendarDay]:
        days = self.repository.list_days(store_id)
        if days:
            return days
        days = [TrialCalendarDay(store_id=store_id, weekday=weekday, is_open=True, open_time=DEFAULT_OPEN_TIME, close_time=DEFAULT_CLOSE_TIME, timezone=DEFAULT_TIMEZONE) for weekday in range(7)]
        for day in days:
            self.repository.create(day)
        self.repository.flush()
        return days

    def _build_calendar_response(self, store_id, days, holidays, events) -> TrialCalendarResponse:
        return TrialCalendarResponse(
            store_id=store_id,
            timezone=days[0].timezone if days else DEFAULT_TIMEZONE,
            days=[TrialCalendarDayResponse(id=day.id, weekday=day.weekday, is_open=day.is_open, open_time=day.open_time, close_time=day.close_time, timezone=day.timezone) for day in sorted(days, key=lambda day: day.weekday)],
            holidays=[TrialHolidayResponse(id=holiday.id, holiday_date=holiday.holiday_date, name=holiday.name, is_active=holiday.is_active, created_at=holiday.created_at, updated_at=holiday.updated_at) for holiday in holidays],
            events=[TrialCalendarEventResponse(id=event.id, event_date=event.event_date, name=event.name, event_type=event.event_type, is_active=event.is_active, created_at=event.created_at, updated_at=event.updated_at) for event in events],
        )

    def _is_store_open(self, store_id: int) -> bool:
        days = self.repository.list_days(store_id)
        if not days:
            return True
        store_tz = self._timezone_or_default(days[0].timezone or DEFAULT_TIMEZONE)
        local_now = datetime.now(timezone.utc).astimezone(store_tz)
        if self.repository.get_active_holiday(store_id, local_now.date()) is not None:
            return False
        day = next((calendar_day for calendar_day in days if calendar_day.weekday == local_now.weekday()), None)
        if day is None:
            return True
        if not day.is_open:
            return False
        local_time = local_now.time().replace(tzinfo=None)
        if day.open_time <= day.close_time:
            return day.open_time <= local_time <= day.close_time
        return local_time >= day.open_time or local_time <= day.close_time

    def _estimate_service_minutes(self, item_count: int | None, config: TrialStoreConfig | None) -> int:
        base = config.base_service_minutes if config else self.BASE_SERVICE_MINUTES
        per_unit = config.per_unit_service_minutes if config else self.PER_UNIT_SERVICE_MINUTES
        minimum = config.min_service_minutes if config else self.MIN_SERVICE_MINUTES
        return max(minimum, math.ceil(base + ((item_count or 0) * per_unit)))

    def _generate_token_number(self, store_id: int, zone_id: int | None, config: TrialStoreConfig | None) -> str:
        prefix = config.token_id_prefix if config and config.token_id_prefix else (f"TZ{zone_id}" if zone_id else f"TR{store_id}")
        return f"{prefix}-{self.repository.count_tokens_for_numbering(store_id, zone_id) + 1:03d}"

    def _rebuild_studio_schedule(self, studio_id: int, reference_time: datetime | None = None) -> None:
        studio = self.repository.get_studio(studio_id)
        if studio is None:
            return
        now = reference_time or datetime.now(timezone.utc)
        anchor = now
        serving = self.repository.get_current_serving_token(studio_id)
        if serving is not None:
            start = serving.service_started_at or serving.called_at or now
            anchor = max(now, self._normalize_to_utc(start) + timedelta(minutes=self._token_service_minutes(serving)))
        else:
            called = self.repository.get_current_called_token(studio_id)
            if called is not None:
                called_time = called.called_at or called.calling_time or now
                anchor = max(now, self._normalize_to_utc(called_time) + timedelta(minutes=self._token_service_minutes(called)))
        cursor = anchor
        for waiting in self.repository.list_waiting_tokens(studio_id):
            waiting.calling_time = cursor
            cursor += timedelta(minutes=self._token_service_minutes(waiting))
        studio.next_available_time = cursor

    def _token_service_minutes(self, token: TrialQueueToken) -> int:
        if token.service_time_minutes is not None:
            return max(1, token.service_time_minutes)
        return self._estimate_service_minutes(token.item_count, self.repository.get_config(token.store_id))

    def _calculate_studio_position(self, studio_id: int, calling_time: datetime) -> int:
        return len([token for token in self.repository.list_waiting_tokens(studio_id) if token.calling_time and self._normalize_to_utc(token.calling_time) <= calling_time]) + 1

    def _calculate_token_position(self, token: TrialQueueToken) -> int:
        if token.status in self.TERMINAL_STATUSES:
            return 0
        if token.assigned_studio_id is None or token.calling_time is None:
            return 1
        return self._calculate_studio_position(token.assigned_studio_id, self._normalize_to_utc(token.calling_time))

    def _build_token_response(self, token: TrialQueueToken) -> TrialQueueTokenResponse:
        return TrialQueueTokenResponse(
            token_id=token.id,
            token_number=token.token_number,
            store_id=token.store_id,
            trial_zone_id=token.trial_zone_id,
            assigned_studio_id=token.assigned_studio_id,
            phone_number=token.phone_number,
            status=token.status,
            position=self._calculate_token_position(token),
            item_count=token.item_count,
            customer_type=token.customer_type,
            calculation_method=token.calculation_method,
            service_time_minutes=token.service_time_minutes,
            calling_time=token.calling_time,
            called_at=token.called_at,
            service_started_at=token.service_started_at,
            completed_at=token.completed_at,
            cancelled_at=token.cancelled_at,
            created_at=token.created_at,
            updated_at=token.updated_at,
            cancellation_reason=token.cancellation_reason,
            estimated_wait_minutes=self._estimate_wait(token.calling_time),
        )

    def _build_event_response(self, token: TrialQueueToken) -> TrialQueueEventResponse:
        return TrialQueueEventResponse(token_id=token.id, status=token.status, assigned_studio_id=token.assigned_studio_id, called_at=token.called_at, service_started_at=token.service_started_at, completed_at=token.completed_at, cancelled_at=token.cancelled_at, cancellation_reason=token.cancellation_reason, calling_time=token.calling_time, estimated_wait_minutes=self._estimate_wait(token.calling_time))

    def _estimate_wait(self, calling_time: datetime | None) -> int:
        if calling_time is None:
            return 0
        return max(0, math.ceil((self._normalize_to_utc(calling_time) - datetime.now(timezone.utc)).total_seconds() / 60))

    def _normalize_to_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _validate_timezone(self, timezone_name: str) -> None:
        try:
            ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid timezone") from exc

    def _timezone_or_default(self, timezone_name: str) -> ZoneInfo:
        try:
            return ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            return ZoneInfo(DEFAULT_TIMEZONE)
