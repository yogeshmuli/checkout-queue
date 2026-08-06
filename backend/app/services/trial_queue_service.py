import math
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.authorization import authorized_store_ids, ensure_store_access
from app.models.trial_queue_token import TrialQueueToken, TrialQueueTokenStatus
from app.models.trial_store_config import TrialStoreConfig
from app.models.trial_studio import TrialStudio
from app.models.trial_zone import TrialZone, TrialZoneGender
from app.models.user import User, UserRole
from app.repositories.trial_queue_repository import TrialQueueRepository
from app.schemas.ml import TrialServiceTimePredictionRequest
from app.schemas.trial_queue import (
    TrialQueueEventRequest,
    TrialQueueEventResponse,
    TrialQueueEventType,
    TrialQueueJoinRequest,
    TrialQueueJoinResponse,
    TrialQueueTokenResponse,
    TrialStoreResponse,
    TrialStoreZoneResponse,
    TrialStudioQueueResponse,
    TrialStudioStatusUpdateRequest,
    TrialTokenStartRequest,
    TrialZoneStudioQueuesResponse,
)
from app.services.notification_service import NotificationService
from app.services.trial_calendar_service import DEFAULT_TIMEZONE
from app.services.trial_prediction_service import TrialPredictionService


class TrialQueueService:
    BASE_SERVICE_MINUTES = 8
    PER_UNIT_SERVICE_MINUTES = 1.0
    MIN_SERVICE_MINUTES = 10
    CALCULATION_METHOD = "RULE_BASED"
    TERMINAL_STATUSES = (TrialQueueTokenStatus.COMPLETED, TrialQueueTokenStatus.CANCELLED, TrialQueueTokenStatus.NO_SHOW)

    def __init__(self, db: Session) -> None:
        self.repository = TrialQueueRepository(db)

    def join_queue(self, payload: TrialQueueJoinRequest) -> TrialQueueJoinResponse:
        store = self.repository.get_store(payload.store_id)
        if store is None or not store.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active store not found")
        if not self._is_store_open(payload.store_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Store is closed for trial queue joining")
        if self.repository.get_active_token_for_phone(payload.store_id, payload.phone_number) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Active trial token already exists for phone")

        zone = self._select_zone_for_join(payload)
        studios = self.repository.list_active_studios(payload.store_id, zone.id)
        if not studios:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="No active studios available")
        now = datetime.now(timezone.utc)
        config = self.get_config(payload.store_id)
        prediction = TrialPredictionService(self.repository).predict_service_time(
            payload.store_id,
            TrialServiceTimePredictionRequest(
                trial_zone_id=zone.id,
                assigned_studio_id=None,
                item_count=payload.item_count,
                customer_type=payload.customer_type,
                requested_at=now,
            ),
        )
        calculation_method = prediction.calculation_method if prediction is not None else self.CALCULATION_METHOD
        service_minutes = prediction.service_time_minutes if prediction is not None else self._estimate_service_minutes(payload.item_count, config)
        slots = self._zone_schedule_slots(zone.id, now)
        calling_time = max(now, min(slots))
        wait_minutes = max(0, math.ceil((calling_time - now).total_seconds() / 60))
        position = self._calculate_zone_position(zone.id, calling_time)
        token = TrialQueueToken(
            store_id=payload.store_id,
            trial_zone_id=zone.id,
            assigned_studio_id=None,
            token_number=self._generate_token_number(payload.store_id, zone.id, config),
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
        if token_id is not None:
            token = self.repository.get_token(token_id)
        elif store_id is not None and phone_number is not None:
            token = self.repository.get_latest_token_for_phone(store_id, phone_number)
        elif phone_number is not None:
            token = self.repository.get_latest_token_by_phone(phone_number)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide token_id, or phone_number, or both store_id and phone_number",
            )

        if token is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial token not found")
        return self._build_token_response(token)

    def list_queue_tokens(self, store_id=None, trial_zone_id=None, studio_id=None, token_status=None, include_terminal=False, current_user: User | None = None) -> list[TrialQueueTokenResponse]:
        if current_user is not None:
            store_id, trial_zone_id = self._scope_queue_filters(store_id, trial_zone_id, studio_id, current_user)
        store_ids = authorized_store_ids(getattr(self.repository, "db", None), current_user) if current_user else None
        args = [store_id, trial_zone_id, studio_id, token_status, include_terminal]
        if store_ids is not None and hasattr(self.repository, "db"):
            args.append(store_ids)
        return [
            self._build_token_response(token)
            for token in self.repository.list_queue_tokens(*args)
        ]

    def get_zone_studio_queues(self, zone_id: int, current_user: User | None = None) -> TrialZoneStudioQueuesResponse:
        zone = self.get_zone(zone_id)
        self._ensure_zone_access(zone, current_user)
        self._rebuild_zone_schedule(zone.id)
        return TrialZoneStudioQueuesResponse(
            zone_id=zone.id,
            zone_name=zone.name,
            store_id=zone.store_id,
            tokens=[self._build_token_response(token) for token in self.repository.list_active_tokens_for_zone(zone.id)],
            studios=[self.get_studio_queue(studio.id, current_user=current_user) for studio in self.repository.list_studios(include_inactive=True, trial_zone_id=zone.id)],
        )

    def get_studio_queue(self, studio_id: int, current_user: User | None = None) -> TrialStudioQueueResponse:
        studio = self.get_studio(studio_id)
        self._ensure_studio_access(studio, current_user)
        return TrialStudioQueueResponse(studio_id=studio.id, studio_name=studio.name, is_active=studio.is_active, next_available_time=self._normalize_to_utc(studio.next_available_time), tokens=[self._build_token_response(token) for token in self.repository.list_tokens_for_studio(studio.id)])

    def update_studio_status(self, studio_id: int, payload: TrialStudioStatusUpdateRequest, current_user: User | None = None) -> TrialStudioQueueResponse:
        studio = self.get_studio(studio_id)
        self._ensure_studio_access(studio, current_user)
        studio.is_active = payload.is_active
        if payload.is_active:
            studio.next_available_time = max(datetime.now(timezone.utc), self._normalize_to_utc(studio.next_available_time))
        self.repository.commit()
        return self.get_studio_queue(studio_id, current_user=current_user)

    def handle_queue_event(self, payload: TrialQueueEventRequest, current_user: User | None = None) -> TrialQueueEventResponse:
        status_map = {
            TrialQueueEventType.CALLED: TrialQueueTokenStatus.CALLED,
            TrialQueueEventType.SERVING: TrialQueueTokenStatus.SERVING,
            TrialQueueEventType.COMPLETED: TrialQueueTokenStatus.COMPLETED,
            TrialQueueEventType.CANCELLED: TrialQueueTokenStatus.CANCELLED,
        }
        return self._build_event_response(self.process_queue_event(payload.token_id, status_map[payload.event], payload.cancellation_reason, current_user=current_user, studio_id=payload.studio_id))

    def start_token(self, token_id: int, payload: TrialTokenStartRequest, current_user: User | None = None) -> TrialQueueEventResponse:
        return self._build_event_response(self.process_queue_event(token_id, TrialQueueTokenStatus.SERVING, current_user=current_user, studio_id=payload.studio_id))

    def call_next_token_for_zone(self, zone_id: int, current_user: User | None = None) -> TrialQueueEventResponse:
        zone = self.get_zone(zone_id)
        self._ensure_zone_access(zone, current_user)
        if not zone.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Trial zone is inactive")
        if self.repository.get_current_called_token_for_zone(zone.id) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Trial zone already has a called token")
        if not self._list_vacant_active_studios(zone):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No vacant active studios available for this trial zone")

        self._rebuild_zone_schedule(zone.id)
        waiting_tokens = self.repository.list_waiting_tokens_for_zone(zone.id)
        if not waiting_tokens:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No waiting tokens available for this trial zone")

        updated = self.process_queue_event(waiting_tokens[0].id, TrialQueueTokenStatus.CALLED, current_user=current_user)
        return self._build_event_response(updated)

    def complete_token(self, token_id: int, current_user: User | None = None) -> TrialQueueEventResponse:
        return self._build_event_response(self.process_queue_event(token_id, TrialQueueTokenStatus.COMPLETED, current_user=current_user))

    def cancel_token(self, token_id: int, reason: str | None = None, current_user: User | None = None) -> TrialQueueEventResponse:
        return self._build_event_response(self.process_queue_event(token_id, TrialQueueTokenStatus.CANCELLED, reason, current_user=current_user))

    def cancel_token_by_customer(self, token_id: int) -> TrialQueueEventResponse:
        token = self.repository.get_token(token_id)
        if token is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial token not found")
        self._ensure_customer_action_allowed(token)
        return self._build_event_response(self.process_queue_event(token_id, TrialQueueTokenStatus.CANCELLED, "Cancelled by customer"))

    def move_token_last_by_customer(self, token_id: int) -> TrialQueueTokenResponse:
        token = self.repository.get_token(token_id)
        if token is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial token not found")
        self._ensure_customer_action_allowed(token)
        if token.trial_zone_id is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Trial token is not assigned to a zone")

        now = datetime.now(timezone.utc)
        token.status = TrialQueueTokenStatus.CANCELLED
        token.cancelled_at = now
        token.cancellation_reason = "Moved to end by customer"

        service_minutes = self._token_service_minutes(token)
        calling_time = max(now, min(self._zone_schedule_slots(token.trial_zone_id, now)))
        config = self.repository.get_config(token.store_id)
        replacement = TrialQueueToken(
            store_id=token.store_id,
            trial_zone_id=token.trial_zone_id,
            assigned_studio_id=None,
            token_number=self._generate_token_number(token.store_id, token.trial_zone_id, config),
            phone_number=token.phone_number,
            status=TrialQueueTokenStatus.WAITING,
            item_count=token.item_count,
            customer_type=token.customer_type,
            service_time_minutes=service_minutes,
            calculation_method=token.calculation_method or self.CALCULATION_METHOD,
            calling_time=calling_time,
            created_at=now,
            updated_at=now,
        )
        self.repository.create(replacement)
        self.repository.commit()
        self.repository.refresh(replacement)
        return self._build_token_response(replacement)

    def process_queue_event(self, token_id: int, new_status: TrialQueueTokenStatus, cancellation_reason: str | None = None, current_user: User | None = None, studio_id: int | None = None) -> TrialQueueToken:
        token = self.repository.get_token(token_id)
        if token is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial token not found")
        self._ensure_token_access(token, current_user)
        if token.status in self.TERMINAL_STATUSES and token.status != new_status:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Trial token is already in terminal state")
        if new_status == TrialQueueTokenStatus.CALLED and token.status != TrialQueueTokenStatus.WAITING:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only waiting trial token can be called")
        if new_status == TrialQueueTokenStatus.CALLED and token.trial_zone_id is not None:
            called_token = self.repository.get_current_called_token_for_zone(token.trial_zone_id)
            if called_token is not None and called_token.id != token.id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Trial zone already has a called token")
        if new_status == TrialQueueTokenStatus.SERVING and token.status not in (TrialQueueTokenStatus.WAITING, TrialQueueTokenStatus.CALLED):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only waiting or called trial token can be started")
        if new_status == TrialQueueTokenStatus.SERVING:
            self._assign_service_studio(token, studio_id)
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
        if token.trial_zone_id is not None:
            self.repository.flush()
            self._rebuild_zone_schedule(token.trial_zone_id, now)
        self.repository.commit()
        self.repository.refresh(token)
        if new_status == TrialQueueTokenStatus.CALLED and getattr(self.repository, "db", None) is not None:
            NotificationService(self.repository.db).notify_trial_called(token)
        return token

    def get_zone(self, zone_id: int) -> TrialZone:
        zone = self.repository.get_zone(zone_id)
        if zone is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial zone not found")
        return zone

    def get_studio(self, studio_id: int) -> TrialStudio:
        studio = self.repository.get_studio(studio_id)
        if studio is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Studio not found")
        return studio

    def get_config(self, store_id: int) -> TrialStoreConfig:
        config = self.repository.get_config(store_id)
        if config is None:
            config = TrialStoreConfig(store_id=store_id)
            self.repository.create(config)
            self.repository.commit()
            self.repository.refresh(config)
        return config

    def _select_zone_for_join(self, payload: TrialQueueJoinRequest) -> TrialZone:
        if payload.trial_zone_id is not None:
            zone = self.repository.get_zone(payload.trial_zone_id)
            if zone is None or not zone.is_active or zone.store_id != payload.store_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active trial zone not found")
            if zone.gender != TrialZoneGender.UNISEX and payload.customer_gender is None:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Customer gender is required for selected trial zone")
            if payload.customer_gender is not None and zone.gender not in (TrialZoneGender.UNISEX, payload.customer_gender):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Selected trial zone does not support customer gender")
            return zone

        zones = [
            zone
            for zone in self.repository.list_zones(include_inactive=False, store_id=payload.store_id)
            if payload.customer_gender is None or zone.gender in (TrialZoneGender.UNISEX, payload.customer_gender)
        ]
        if not zones:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active trial zone not found")
        return zones[0]

    def _assign_service_studio(self, token: TrialQueueToken, studio_id: int | None) -> None:
        if studio_id is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Studio is required to start trial service")
        if token.trial_zone_id is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Trial token is not assigned to a zone")
        studio = self.repository.get_studio(studio_id)
        if studio is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Studio not found")
        if not studio.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Studio is inactive")
        if studio.trial_zone_id != token.trial_zone_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Studio does not belong to token trial zone")
        serving_token = self.repository.get_current_serving_token(studio.id)
        if serving_token is not None and serving_token.id != token.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Studio is already serving a trial token")
        token.assigned_studio_id = studio.id

    def _list_vacant_active_studios(self, zone: TrialZone) -> list[TrialStudio]:
        return [
            studio
            for studio in self.repository.list_active_studios(zone.store_id, zone.id)
            if self.repository.get_current_serving_token(studio.id) is None
        ]

    def _ensure_customer_action_allowed(self, token: TrialQueueToken) -> None:
        if token.status in self.TERMINAL_STATUSES:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Trial token is already in terminal state")
        if token.status == TrialQueueTokenStatus.SERVING:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Serving trial token cannot be changed by customer")
        if token.status not in (TrialQueueTokenStatus.WAITING, TrialQueueTokenStatus.CALLED):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Trial token cannot be changed by customer")

    def _scope_queue_filters(self, store_id, trial_zone_id, studio_id, current_user: User):
        if studio_id is not None:
            self._ensure_studio_access(self.get_studio(studio_id), current_user)
        if current_user.default_role == UserRole.TRIAL_ZONE_ASSISTANT:
            if current_user.assigned_zone_id is None:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Trial zone assignment required")
            if trial_zone_id is not None and trial_zone_id != current_user.assigned_zone_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Trial zone access denied")
            zone = self.get_zone(current_user.assigned_zone_id)
            if store_id is not None and store_id != zone.store_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Store access denied")
            return zone.store_id, current_user.assigned_zone_id
        if current_user.default_role in (UserRole.STORE_ADMIN, UserRole.MANAGER):
            if store_id is not None:
                ensure_store_access(self.repository.db, current_user, store_id)
            if trial_zone_id is not None:
                self._ensure_zone_access(self.get_zone(trial_zone_id), current_user)
            return store_id, trial_zone_id
        return store_id, trial_zone_id

    def _ensure_token_access(self, token: TrialQueueToken, current_user: User | None) -> None:
        if current_user is None:
            return
        if token.assigned_studio_id is not None:
            self._ensure_studio_access(self.get_studio(token.assigned_studio_id), current_user)
        elif token.trial_zone_id is not None:
            self._ensure_zone_access(self.get_zone(token.trial_zone_id), current_user)

    def _ensure_studio_access(self, studio: TrialStudio, current_user: User | None) -> None:
        if current_user is None:
            return
        self._ensure_zone_access(self.get_zone(studio.trial_zone_id), current_user)

    def _ensure_zone_access(self, zone: TrialZone, current_user: User | None) -> None:
        if current_user is None:
            return
        if current_user.default_role == UserRole.TRIAL_ZONE_ASSISTANT and current_user.assigned_zone_id != zone.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Trial zone access denied")
        if current_user.default_role in (UserRole.STORE_ADMIN, UserRole.MANAGER):
            if hasattr(self.repository, "db"):
                ensure_store_access(self.repository.db, current_user, zone.store_id)
            elif current_user.store_id != zone.store_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Store access denied")

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

    def _zone_schedule_slots(self, zone_id: int, reference_time: datetime | None = None) -> list[datetime]:
        slots = list(self._rebuild_zone_schedule(zone_id, reference_time).values())
        if not slots:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="No active studios available")
        return slots

    def _studio_lane_anchor(self, studio_id: int, reference_time: datetime) -> datetime:
        serving = self.repository.get_current_serving_token(studio_id)
        if serving is None:
            serving = self.repository.get_current_called_token(studio_id)
        if serving is None:
            return reference_time
        start = serving.service_started_at or serving.called_at or serving.calling_time or reference_time
        return max(reference_time, self._normalize_to_utc(start) + timedelta(minutes=self._token_service_minutes(serving)))

    def _rebuild_zone_schedule(self, zone_id: int, reference_time: datetime | None = None) -> dict[int, datetime]:
        zone = self.get_zone(zone_id)
        now = reference_time or datetime.now(timezone.utc)
        active_studios = self.repository.list_active_studios(zone.store_id, zone.id)
        if not active_studios:
            return {}

        studio_cursors = {studio.id: self._studio_lane_anchor(studio.id, now) for studio in active_studios}
        active_tokens = self.repository.list_active_tokens_for_zone(zone.id)
        unassigned_called = [
            token
            for token in active_tokens
            if token.status == TrialQueueTokenStatus.CALLED and token.assigned_studio_id is None
        ]
        for token in unassigned_called:
            selected_studio_id = min(studio_cursors, key=lambda studio_id: (studio_cursors[studio_id], studio_id))
            start = token.called_at or token.calling_time or now
            studio_cursors[selected_studio_id] = max(studio_cursors[selected_studio_id], self._normalize_to_utc(start), now) + timedelta(
                minutes=self._token_service_minutes(token)
            )

        for waiting in self.repository.list_waiting_tokens_for_zone(zone.id):
            selected_studio_id = min(studio_cursors, key=lambda studio_id: (studio_cursors[studio_id], studio_id))
            waiting.calling_time = max(now, studio_cursors[selected_studio_id])
            studio_cursors[selected_studio_id] = waiting.calling_time + timedelta(minutes=self._token_service_minutes(waiting))

        for studio in active_studios:
            studio.next_available_time = studio_cursors[studio.id]

        return studio_cursors

    def _calculate_studio_position(self, studio_id: int, calling_time: datetime) -> int:
        return len([token for token in self.repository.list_waiting_tokens(studio_id) if token.calling_time and self._normalize_to_utc(token.calling_time) <= calling_time]) + 1

    def _calculate_zone_position(self, zone_id: int, calling_time: datetime) -> int:
        return len([token for token in self.repository.list_waiting_tokens_for_zone(zone_id) if token.calling_time and self._normalize_to_utc(token.calling_time) <= calling_time]) + 1

    def _calculate_token_position(self, token: TrialQueueToken) -> int:
        if token.status in self.TERMINAL_STATUSES:
            return 0
        if token.trial_zone_id is None or token.calling_time is None:
            return 1
        if token.status != TrialQueueTokenStatus.WAITING:
            return 1
        token_time = self._normalize_to_utc(token.calling_time)
        token_id = token.id or 0
        return len(
            [
                waiting
                for waiting in self.repository.list_waiting_tokens_for_zone(token.trial_zone_id)
                if waiting.calling_time
                and (
                    self._normalize_to_utc(waiting.calling_time) < token_time
                    or (self._normalize_to_utc(waiting.calling_time) == token_time and (waiting.id or 0) <= token_id)
                )
            ]
        )

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
            assigned_studio=token.assigned_studio
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

    def _timezone_or_default(self, timezone_name: str):
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        try:
            return ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            return ZoneInfo(DEFAULT_TIMEZONE)
