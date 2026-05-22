import math
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.queue_token import QueueToken, QueueTokenStatus
from app.models.store_config import StoreConfig
from app.repositories.queue_repository import QueueRepository
from app.schemas.queue import (
    CounterQueueResponse,
    CounterStatusUpdateRequest,
    QueueEventRequest,
    QueueEventResponse,
    QueueEventType,
    QueueJoinRequest,
    QueueJoinResponse,
    QueueStoreResponse,
    QueueStoreSectionResponse,
    QueueTokenResponse,
)


class QueueService:
    BASE_SERVICE_MINUTES = 4
    PER_ITEM_SERVICE_MINUTES = 0.25
    MIN_SERVICE_MINUTES = 5
    CALCULATION_METHOD = "RULE_BASED"
    TERMINAL_STATUSES = (
        QueueTokenStatus.COMPLETED,
        QueueTokenStatus.CANCELLED,
        QueueTokenStatus.NO_SHOW,
    )

    def __init__(self, db: Session) -> None:
        self.repository = QueueRepository(db)

    def join_queue(self, payload: QueueJoinRequest) -> QueueJoinResponse:
        """Join a customer into queue by assigning the best available counter first.

        Flow:
        1. Validate store/section and duplicate active token.
        2. Pick the counter with minimum wait (earliest next_available_time).
        3. Calculate service time and wait time for the new customer.
        4. Update selected counter availability.
        5. Persist queue token with assigned counter and calling_time.
        """
        store = self.repository.get_store(payload.store_id)
        if store is None or not store.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active store not found")
        if not self._is_store_open_for_queue(payload.store_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Store is closed for queue joining")

        if payload.section_id is not None:
            section = self.repository.get_section(payload.section_id)
            if section is None or not section.is_active or section.store_id != payload.store_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active checkout section not found")

        active_token = self.repository.get_active_token_for_phone(payload.store_id, payload.phone_number)
        if active_token is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Active token already exists for phone")

        store_config = self._get_store_config(payload.store_id)
        counters = self.repository.list_active_counters(payload.store_id, payload.section_id)
        if not counters:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="No active counters available")

        now = datetime.now(timezone.utc)

        # Rebuild each counter lane before selection so stale historical drift is discarded.
        for counter in counters:
            self._rebuild_counter_schedule(counter.id, now)

        selected_counter = min(counters, key=lambda c: self._normalize_to_utc(c.next_available_time))
        calling_time = max(now, self._normalize_to_utc(selected_counter.next_available_time))
        service_minutes = self._estimate_service_minutes(payload.item_count, store_config)
        service_time = timedelta(minutes=service_minutes)
        wait_minutes = max(0, math.ceil((calling_time - now).total_seconds() / 60))

        # Position is lane-specific: count waiting tokens already assigned to this counter.
        position = self._calculate_counter_position(selected_counter.id, calling_time)

        # Reserve the selected counter slot for this token.
        selected_counter.next_available_time = calling_time + service_time

        token_number = self._generate_token_number(payload.store_id, payload.section_id, store_config)

        token = QueueToken(
            store_id=payload.store_id,
            section_id=payload.section_id,
            assigned_counter_id=selected_counter.id,
            token_number=token_number,
            phone_number=payload.phone_number,
            status=QueueTokenStatus.WAITING,
            item_count=payload.item_count,
            basket_size=payload.basket_size,
            cart_type=payload.cart_type,
            customer_type=payload.customer_type,
            calling_time=calling_time,
            is_still_shopping=payload.is_still_shopping,
     
            service_time_minutes=service_minutes,
            calculation_method=self.CALCULATION_METHOD,
        )
        self.repository.create_token(token)
        self.repository.commit()
        self.repository.refresh(token)

        return QueueJoinResponse(
            token_id=token.id,
            token_number=token.token_number,
            store_id=token.store_id,
            section_id=token.section_id,
            assigned_counter_id=token.assigned_counter_id,
            status=token.status,
            position=position,
            estimated_wait_minutes=wait_minutes,
            calculation_method=self.CALCULATION_METHOD,
            calling_time=calling_time,
        )

    def get_token_status(
        self,
        token_id: int | None = None,
        store_id: int | None = None,
        phone_number: str | None = None,
    ) -> QueueTokenResponse:
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")

        return self._build_token_response(token)

    def list_store_sections(self) -> list[QueueStoreResponse]:
        stores = self.repository.list_active_stores_with_sections()
        response: list[QueueStoreResponse] = []

        for store in stores:
            active_sections = [
                QueueStoreSectionResponse(
                    id=section.id,
                    name=section.name,
                    section_type=section.section_type,
                )
                for section in store.checkout_sections
                if section.is_active
            ]

            response.append(
                QueueStoreResponse(
                    id=store.id,
                    store_number=store.store_number,
                    name=store.name,
                    sections=active_sections,
                )
            )

        return response

    def get_counter_queue(self, counter_id: int) -> CounterQueueResponse:
        counter = self.repository.get_counter(counter_id)
        if counter is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Counter not found")

        tokens = self.repository.list_tokens_for_counter(counter_id)
        return CounterQueueResponse(
            counter_id=counter.id,
            is_active=counter.is_active,
            next_available_time=self._normalize_to_utc(counter.next_available_time),
            tokens=[self._build_token_response(token) for token in tokens],
        )

    def list_queue_tokens(
        self,
        store_id: int | None = None,
        section_id: int | None = None,
        counter_id: int | None = None,
        token_status: QueueTokenStatus | None = None,
        include_terminal: bool = False,
    ) -> list[QueueTokenResponse]:
        tokens = self.repository.list_queue_tokens(
            store_id=store_id,
            section_id=section_id,
            counter_id=counter_id,
            status=token_status,
            include_terminal=include_terminal,
        )
        return [self._build_token_response(token) for token in tokens]

    def update_counter_status(self, counter_id: int, payload: CounterStatusUpdateRequest) -> CounterQueueResponse:
        counter = self.repository.get_counter(counter_id)
        if counter is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Counter not found")

        counter.is_active = payload.is_active
        if payload.is_active:
            counter.next_available_time = max(
                datetime.now(timezone.utc),
                self._normalize_to_utc(counter.next_available_time),
            )
        self.repository.commit()
        self.repository.refresh(counter)
        return self.get_counter_queue(counter_id)

    def start_token(self, token_id: int) -> QueueEventResponse:
        token = self.process_queue_event(token_id, QueueTokenStatus.SERVING)
        return self._build_event_response(token)

    def complete_token(self, token_id: int) -> QueueEventResponse:
        token = self.process_queue_event(token_id, QueueTokenStatus.COMPLETED)
        return self._build_event_response(token)

    def cancel_token(self, token_id: int, cancellation_reason: str | None = None) -> QueueEventResponse:
        token = self.process_queue_event(token_id, QueueTokenStatus.CANCELLED, cancellation_reason)
        return self._build_event_response(token)

    def cancel_token_by_customer(self, token_id: int) -> QueueEventResponse:
        token = self.repository.get_token(token_id)
        if token is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")

        if token.status in self.TERMINAL_STATUSES:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Token is already in terminal state")

        if token.status == QueueTokenStatus.SERVING:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Serving token cannot be cancelled by customer")

        updated = self.process_queue_event(token_id, QueueTokenStatus.CANCELLED, "Cancelled by customer")
        return self._build_event_response(updated)

    def handle_queue_event(self, payload: QueueEventRequest) -> QueueEventResponse:
        status_map = {
            QueueEventType.CALLED: QueueTokenStatus.CALLED,
            QueueEventType.SERVING: QueueTokenStatus.SERVING,
            QueueEventType.COMPLETED: QueueTokenStatus.COMPLETED,
            QueueEventType.CANCELLED: QueueTokenStatus.CANCELLED,
        }
        target_status = status_map[payload.event]

        token = self.repository.get_token(payload.token_id)
        if token is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")

        if token.status in self.TERMINAL_STATUSES and token.status != target_status:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Token is already in terminal state")

        updated_token = self.process_queue_event(
            token_id=payload.token_id,
            new_status=target_status,
            cancellation_reason=payload.cancellation_reason,
        )
        return self._build_event_response(updated_token)
    
    def process_queue_event(
        self,
        token_id: int,
        new_status: QueueTokenStatus,
        cancellation_reason: str | None = None,
    ) -> QueueToken:
        """Update token status for queue lifecycle events."""
        token = self.repository.get_token(token_id)
        if token is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")

        token.status = new_status
        now_utc = datetime.now(timezone.utc)

        if new_status == QueueTokenStatus.CALLED:
            token.called_at = now_utc
            token.calling_time = now_utc

        elif new_status == QueueTokenStatus.SERVING:
            token.service_started_at = now_utc
            if token.called_at is None:
                token.called_at = now_utc

        elif new_status == QueueTokenStatus.COMPLETED:
            token.completed_at = now_utc

        elif new_status in (QueueTokenStatus.CANCELLED, QueueTokenStatus.NO_SHOW):
            token.cancelled_at = now_utc
            token.cancellation_reason = cancellation_reason or new_status.value

        if token.assigned_counter_id is not None:
            self._rebuild_counter_schedule(token.assigned_counter_id, now_utc)

        self.repository.commit()
        self.repository.refresh(token)
        return token

    def _build_event_response(self, token: QueueToken) -> QueueEventResponse:
        return QueueEventResponse(
            token_id=token.id,
            status=token.status,
            assigned_counter_id=token.assigned_counter_id,
            called_at=token.called_at,
            service_started_at=token.service_started_at,
            completed_at=token.completed_at,
            cancelled_at=token.cancelled_at,
            cancellation_reason=token.cancellation_reason,
            calling_time=token.calling_time,
            estimated_wait_minutes=self._estimate_wait_from_calling_time(token.calling_time),
        )

    def _build_token_response(self, token: QueueToken) -> QueueTokenResponse:
        return QueueTokenResponse(
            token_id=token.id,
            token_number=token.token_number,
            store_id=token.store_id,
            section_id=token.section_id,
            assigned_counter_id=token.assigned_counter_id,
            phone_number=token.phone_number,
            status=token.status,
            position=self._calculate_token_position(token),
            item_count=token.item_count,
            basket_size=token.basket_size,
            cart_type=token.cart_type,
            customer_type=token.customer_type,
            calculation_method=token.calculation_method,
            service_time_minutes=token.service_time_minutes,
            calling_time=token.calling_time,
            called_at=token.called_at,
            service_started_at=token.service_started_at,
            completed_at=token.completed_at,
            cancelled_at=token.cancelled_at,
            cancellation_reason=token.cancellation_reason,
            estimated_wait_minutes=self._estimate_wait_from_calling_time(token.calling_time),
        )

 
    def _estimate_service_minutes(self, item_count: int | None, config: StoreConfig | None = None) -> int:
        base_service_minutes = config.base_service_minutes if config is not None else self.BASE_SERVICE_MINUTES
        per_item_service_minutes = config.per_item_service_minutes if config is not None else self.PER_ITEM_SERVICE_MINUTES
        min_service_minutes = config.min_service_minutes if config is not None else self.MIN_SERVICE_MINUTES
        item_based_service_time = base_service_minutes + ((item_count or 0) * per_item_service_minutes)
        service_time = max(min_service_minutes, math.ceil(item_based_service_time))
        return service_time

    def _calculate_counter_position(
        self,
        counter_id: int,
        calling_time: datetime,
    ) -> int:
        waiting_tokens = self.repository.list_waiting_tokens(counter_id)
        tokens_ahead = [
            token
            for token in waiting_tokens
            if token.calling_time is not None
            and self._normalize_to_utc(token.calling_time) <= calling_time
        ]
        return len(tokens_ahead) + 1

    def _calculate_token_position(self, token: QueueToken) -> int:
        if token.status in self.TERMINAL_STATUSES:
            return 0
        if token.assigned_counter_id is None or token.calling_time is None:
            return 1
        return self._calculate_counter_position(token.assigned_counter_id, self._normalize_to_utc(token.calling_time))

    def _estimate_wait_from_calling_time(self, calling_time: datetime | None) -> int:
        if calling_time is None:
            return 0
        now = datetime.now(timezone.utc)
        return max(0, math.ceil((self._normalize_to_utc(calling_time) - now).total_seconds() / 60))

    def _normalize_to_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _generate_token_number(
        self,
        store_id: int,
        section_id: int | None,
        config: StoreConfig | None = None,
    ) -> str:
        existing_token_count = self.repository.count_tokens_for_numbering(store_id, section_id)
        prefix = config.token_id_prefix if config is not None and config.token_id_prefix else None
        if prefix is None:
            prefix = f"S{section_id}" if section_id is not None else f"ST{store_id}"
        return f"{prefix}-{existing_token_count + 1:03d}"

    def _rebuild_counter_schedule(self, counter_id: int, reference_time: datetime | None = None) -> None:
        """Deterministically recompute waiting schedule for one counter lane.

        The rebuild starts from current truth:
        - if someone is SERVING: anchor at their expected end time (or now if already overrun)
        - else if someone is CALLED: reserve their expected slot from called time
        - otherwise: anchor at now
        Then all WAITING tokens are assigned sequential `calling_time` values.
        """
        counter = self.repository.get_counter(counter_id)
        if counter is None:
            return

        now_utc = reference_time or datetime.now(timezone.utc)
        lane_anchor = now_utc

        serving_token = self.repository.get_current_serving_customer_for_counter(counter_id)
        if serving_token is not None:
            service_start = serving_token.service_started_at or serving_token.called_at or now_utc
            service_start_utc = self._normalize_to_utc(service_start)
            expected_end = service_start_utc + timedelta(minutes=self._token_service_minutes(serving_token))
            lane_anchor = max(now_utc, expected_end)
        else:
            called_token = self.repository.get_current_called_customer_for_counter(counter_id)
            if called_token is not None:
                called_time = called_token.called_at or called_token.calling_time or now_utc
                called_time_utc = self._normalize_to_utc(called_time)
                expected_end = called_time_utc + timedelta(minutes=self._token_service_minutes(called_token))
                lane_anchor = max(now_utc, expected_end)

        waiting_tokens = self.repository.list_waiting_tokens(counter_id)
        cursor = lane_anchor
        for waiting_token in waiting_tokens:
            waiting_token.calling_time = cursor
            cursor = cursor + timedelta(minutes=self._token_service_minutes(waiting_token))

        counter.next_available_time = cursor

    def _token_service_minutes(self, token: QueueToken) -> int:
        if token.service_time_minutes is not None:
            return max(1, token.service_time_minutes)
        return self._estimate_service_minutes(token.item_count, self._get_store_config(token.store_id))

    def _get_store_config(self, store_id: int) -> StoreConfig | None:
        return self.repository.get_store_config(store_id)

    def _is_store_open_for_queue(self, store_id: int) -> bool:
        days = self.repository.list_calendar_days(store_id)
        if not days:
            return True

        timezone_name = days[0].timezone or "Asia/Kolkata"
        try:
            store_tz = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            store_tz = ZoneInfo("Asia/Kolkata")

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

    def purge_queue(self, store_id: int, section_id: int | None) -> None:
        '''Utility to purge all waiting tokens for a given lane (store+section) - used for testing and stale token cleanup'''
        counters = self.repository.list_active_counters(store_id, section_id)
        for counter in counters:
            waiting_tokens = self.repository.list_waiting_tokens(counter.id)
            for token in waiting_tokens:
                token.status = QueueTokenStatus.CANCELLED
                token.cancelled_at = datetime.now(timezone.utc)
                token.cancellation_reason = "Purged by system"
            counter.next_available_time = datetime.now(timezone.utc)
        self.repository.commit()
