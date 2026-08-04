import math
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.counter import Counter, CounterBasketSizeBand
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
from app.schemas.ml import ServiceTimePredictionRequest
from app.services.notification_service import NotificationService
from app.services.prediction_service import PredictionService


class QueueService:
    BASE_SERVICE_MINUTES = 4
    PER_ITEM_SERVICE_MINUTES = 0.25
    MIN_SERVICE_MINUTES = 5
    DEFAULT_ITEM_COUNT = 10
    CALCULATION_METHOD = "RULE_BASED"
    BASKET_SIZE_ITEM_COUNTS = {
        "small": 9,
        "medium": 20,
        "large": 30,
    }
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
        shared_queue_enabled = self._is_shared_queue_enabled(store_config)
        if shared_queue_enabled and payload.section_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Section is required for shared queue stores")

        active_counters = self.repository.list_active_counters(payload.store_id, payload.section_id)
        if not active_counters:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="No active counters available")
        effective_item_count = self._resolve_effective_item_count(payload, store_config)
        counters = self._filter_counters_for_basket_size(active_counters, effective_item_count)
        if not counters:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No active counters available for this basket size",
            )

        now = datetime.now(timezone.utc)

        if shared_queue_enabled:
            return self._join_shared_queue(payload, store_config, active_counters, effective_item_count, now)

        # Rebuild each counter lane before selection so stale historical drift is discarded.
        for counter in counters:
            self._rebuild_counter_schedule(counter.id, now)

        selected_counter = min(counters, key=lambda c: self._normalize_to_utc(c.next_available_time))
        calling_time = max(now, self._normalize_to_utc(selected_counter.next_available_time))
        service_minutes, calculation_method = self._predict_service_time(payload, selected_counter.id, now, store_config, effective_item_count)
        service_time = timedelta(minutes=service_minutes)
        wait_minutes = max(0, math.ceil((calling_time - now).total_seconds() / 60))

        # Position is lane-specific: count waiting tokens already assigned to this counter.
        position = self._calculate_counter_position(selected_counter.id, calling_time)

        # Reserve the selected counter slot for this token.
        selected_counter.next_available_time = calling_time + service_time

        token_number = self._generate_token_number(payload.store_id, payload.section_id, selected_counter, store_config)

        token = QueueToken(
            store_id=payload.store_id,
            section_id=payload.section_id,
            assigned_counter_id=selected_counter.id,
            token_number=token_number,
            phone_number=payload.phone_number,
            status=QueueTokenStatus.WAITING,
            item_count=effective_item_count,
            basket_size=payload.basket_size,
            cart_type=payload.cart_type,
            customer_type=payload.customer_type,
            calling_time=calling_time,
            is_still_shopping=payload.is_still_shopping,
     
            service_time_minutes=service_minutes,
            calculation_method=calculation_method,
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
            calculation_method=calculation_method,
            calling_time=calling_time,
        )

    def _join_shared_queue(
        self,
        payload: QueueJoinRequest,
        store_config: StoreConfig | None,
        counters: list[Counter],
        effective_item_count: int | None,
        now: datetime,
    ) -> QueueJoinResponse:
        section_id = payload.section_id
        if section_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Section is required for shared queue stores")

        service_minutes, calculation_method = self._predict_service_time(payload, None, now, store_config, effective_item_count)
        token = QueueToken(
            store_id=payload.store_id,
            section_id=section_id,
            assigned_counter_id=None,
            token_number=self._generate_shared_token_number(payload.store_id, section_id, store_config),
            phone_number=payload.phone_number,
            status=QueueTokenStatus.WAITING,
            item_count=effective_item_count,
            basket_size=payload.basket_size,
            cart_type=payload.cart_type,
            customer_type=payload.customer_type,
            calling_time=now,
            is_still_shopping=payload.is_still_shopping,
            service_time_minutes=service_minutes,
            calculation_method=calculation_method,
        )
        self.repository.create_token(token)
        self._rebuild_shared_section_schedule(payload.store_id, section_id, now, counters)
        self.repository.commit()
        self.repository.refresh(token)

        return QueueJoinResponse(
            token_id=token.id,
            token_number=token.token_number,
            store_id=token.store_id,
            section_id=token.section_id,
            assigned_counter_id=token.assigned_counter_id,
            status=token.status,
            position=self._calculate_shared_position(token),
            estimated_wait_minutes=self._estimate_wait_from_calling_time(token.calling_time),
            calculation_method=calculation_method,
            calling_time=token.calling_time,
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
        section = self.repository.get_section(counter.section_id)
        if section is not None and self._is_store_shared_queue_enabled(section.store_id):
            self._rebuild_shared_section_schedule(section.store_id, section.id)
            shared_tokens = [
                token
                for token in self.repository.list_shared_waiting_tokens(section.store_id, section.id)
                if self._counter_accepts_token(counter, token)
            ]
            token_ids = {token.id for token in tokens}
            tokens = tokens + [token for token in shared_tokens if token.id not in token_ids]
            tokens = sorted(tokens, key=lambda token: (token.calling_time or datetime.max.replace(tzinfo=timezone.utc), token.id or 0))
        return CounterQueueResponse(
            counter_id=counter.id,
            counter_name=counter.name,
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
        section = self.repository.get_section(counter.section_id)
        if section is not None and self._is_store_shared_queue_enabled(section.store_id):
            self._rebuild_shared_section_schedule(section.store_id, section.id)
        self.repository.commit()
        self.repository.refresh(counter)
        return self.get_counter_queue(counter_id)

    def start_token(self, token_id: int) -> QueueEventResponse:
        token = self.process_queue_event(token_id, QueueTokenStatus.SERVING)
        return self._build_event_response(token)

    def call_next_token_for_counter(self, counter_id: int) -> QueueEventResponse:
        counter, token = self._get_next_waiting_token_for_counter(counter_id)
        updated = self.process_queue_event(token.id, QueueTokenStatus.CALLED, target_counter_id=counter.id)
        return self._build_event_response(updated)

    def start_next_token_for_counter(self, counter_id: int) -> QueueEventResponse:
        counter, token = self._get_next_waiting_token_for_counter(counter_id)
        updated = self.process_queue_event(token.id, QueueTokenStatus.SERVING, target_counter_id=counter.id)
        return self._build_event_response(updated)

    def _get_next_waiting_token_for_counter(self, counter_id: int) -> tuple[Counter, QueueToken]:
        counter = self.repository.get_counter(counter_id)
        if counter is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Counter not found")
        if not counter.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Counter is inactive")

        section = self.repository.get_section(counter.section_id)
        if section is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checkout section not found")

        if self._is_store_shared_queue_enabled(section.store_id):
            self._rebuild_shared_section_schedule(section.store_id, section.id)
            waiting_tokens = [
                token
                for token in self.repository.list_shared_waiting_tokens(section.store_id, section.id)
                if self._counter_accepts_token(counter, token)
            ]
        else:
            waiting_tokens = self.repository.list_waiting_tokens(counter.id)

        if not waiting_tokens:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No waiting tokens available for this counter")

        return counter, waiting_tokens[0]

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

        self._ensure_customer_action_allowed(token)

        updated = self.process_queue_event(token_id, QueueTokenStatus.CANCELLED, "Cancelled by customer")
        return self._build_event_response(updated)

    def move_token_last_by_customer(self, token_id: int) -> QueueTokenResponse:
        token = self.repository.get_token(token_id)
        if token is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")
        self._ensure_customer_action_allowed(token)
        config = self._get_store_config(token.store_id)
        if self._is_shared_queue_enabled(config):
            if token.section_id is None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Token is not assigned to a shared section")
            return self._move_shared_token_last_by_customer(token, config)

        if token.assigned_counter_id is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Token is not assigned to a counter")

        counter = self.repository.get_counter(token.assigned_counter_id)
        if counter is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Counter not found")

        now_utc = datetime.now(timezone.utc)
        token.status = QueueTokenStatus.CANCELLED
        token.cancelled_at = now_utc
        token.cancellation_reason = "Moved to end by customer"

        self._rebuild_counter_schedule(counter.id, now_utc)

        service_minutes = self._token_service_minutes(token)
        calling_time = max(now_utc, self._normalize_to_utc(counter.next_available_time))
        replacement = QueueToken(
            store_id=token.store_id,
            section_id=token.section_id,
            assigned_counter_id=counter.id,
            token_number=self._generate_token_number(token.store_id, token.section_id, counter, config),
            phone_number=token.phone_number,
            status=QueueTokenStatus.WAITING,
            item_count=token.item_count,
            basket_size=token.basket_size,
            cart_type=token.cart_type,
            customer_type=token.customer_type,
            is_still_shopping=token.is_still_shopping,
            calculation_method=token.calculation_method or self.CALCULATION_METHOD,
            service_time_minutes=service_minutes,
            calling_time=calling_time,
        )
        counter.next_available_time = calling_time + timedelta(minutes=service_minutes)
        self.repository.create_token(replacement)
        self.repository.commit()
        self.repository.refresh(replacement)
        return self._build_token_response(replacement)

    def _move_shared_token_last_by_customer(self, token: QueueToken, config: StoreConfig | None) -> QueueTokenResponse:
        now_utc = datetime.now(timezone.utc)
        token.status = QueueTokenStatus.CANCELLED
        token.cancelled_at = now_utc
        token.cancellation_reason = "Moved to end by customer"

        section_id = token.section_id
        if section_id is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Token is not assigned to a shared section")

        replacement = QueueToken(
            store_id=token.store_id,
            section_id=section_id,
            assigned_counter_id=None,
            token_number=self._generate_shared_token_number(token.store_id, section_id, config),
            phone_number=token.phone_number,
            status=QueueTokenStatus.WAITING,
            item_count=token.item_count,
            basket_size=token.basket_size,
            cart_type=token.cart_type,
            customer_type=token.customer_type,
            is_still_shopping=token.is_still_shopping,
            calculation_method=token.calculation_method or self.CALCULATION_METHOD,
            service_time_minutes=self._token_service_minutes(token),
            calling_time=now_utc,
        )
        self.repository.create_token(replacement)
        self._rebuild_shared_section_schedule(token.store_id, section_id, now_utc)
        self.repository.commit()
        self.repository.refresh(replacement)
        return self._build_token_response(replacement)

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
        target_counter_id: int | None = None,
    ) -> QueueToken:
        """Update token status for queue lifecycle events."""
        token = self.repository.get_token(token_id)
        if token is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")

        if new_status == QueueTokenStatus.CALLED and token.status != QueueTokenStatus.WAITING:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only waiting token can be called")

        now_utc = datetime.now(timezone.utc)
        shared_queue_enabled = self._is_store_shared_queue_enabled(token.store_id)

        if (
            shared_queue_enabled
            and token.assigned_counter_id is None
            and new_status in (QueueTokenStatus.CALLED, QueueTokenStatus.SERVING)
        ):
            counter = self._resolve_shared_counter_for_token(token, target_counter_id, now_utc)
            token.assigned_counter_id = counter.id

        token.status = new_status

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
        if shared_queue_enabled and token.section_id is not None:
            self._rebuild_shared_section_schedule(token.store_id, token.section_id, now_utc)

        self.repository.commit()
        self.repository.refresh(token)
        if new_status == QueueTokenStatus.CALLED and getattr(self.repository, "db", None) is not None:
            NotificationService(self.repository.db).notify_checkout_called(token)
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

    def _ensure_customer_action_allowed(self, token: QueueToken) -> None:
        if token.status in self.TERMINAL_STATUSES:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Token is already in terminal state")
        if token.status == QueueTokenStatus.SERVING:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Serving token cannot be changed by customer")
        if token.status not in (QueueTokenStatus.WAITING, QueueTokenStatus.CALLED):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Token cannot be changed by customer")

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
            assigned_counter=token.assigned_counter,
        )

 
    def _estimate_service_minutes(self, item_count: int | None, config: StoreConfig | None = None) -> int:
        base_service_minutes = config.base_service_minutes if config is not None else self.BASE_SERVICE_MINUTES
        per_item_service_minutes = config.per_item_service_minutes if config is not None else self.PER_ITEM_SERVICE_MINUTES
        min_service_minutes = config.min_service_minutes if config is not None else self.MIN_SERVICE_MINUTES
        item_based_service_time = base_service_minutes + ((item_count or 0) * per_item_service_minutes)
        service_time = max(min_service_minutes, math.ceil(item_based_service_time))
        return service_time

    def _predict_service_time(
        self,
        payload: QueueJoinRequest,
        assigned_counter_id: int | None,
        requested_at: datetime,
        config: StoreConfig | None = None,
        item_count: int | None = None,
    ) -> tuple[int, str]:
        prediction = PredictionService(self.repository).predict_service_time(
            payload.store_id,
            ServiceTimePredictionRequest(
                section_id=payload.section_id,
                assigned_counter_id=assigned_counter_id,
                item_count=item_count,
                basket_size=payload.basket_size,
                cart_type=payload.cart_type,
                customer_type=payload.customer_type,
                requested_at=requested_at,
            ),
        )
        if prediction is not None:
            return prediction.service_time_minutes, prediction.calculation_method
        return self._estimate_service_minutes(item_count, config), self.CALCULATION_METHOD

    def _calculate_counter_position(
        self,
        counter_id: int,
        calling_time: datetime,
        token_id: int | None = None,
    ) -> int:
        waiting_tokens = self.repository.list_waiting_tokens(counter_id)
        normalized_calling_time = self._normalize_to_utc(calling_time)
        tokens_ahead = [
            token
            for token in waiting_tokens
            if token.calling_time is not None
            and (
                (
                    token_id is None
                    and self._normalize_to_utc(token.calling_time) <= normalized_calling_time
                )
                or (
                    token_id is not None
                    and token.id != token_id
                    and (
                        self._normalize_to_utc(token.calling_time) < normalized_calling_time
                        or (
                            self._normalize_to_utc(token.calling_time) == normalized_calling_time
                            and (token.id or 0) < token_id
                        )
                    )
                )
            )
        ]
        return len(tokens_ahead) + 1

    def _calculate_token_position(self, token: QueueToken) -> int:
        if token.status in self.TERMINAL_STATUSES:
            return 0
        if token.assigned_counter_id is None and token.section_id is not None and self._is_store_shared_queue_enabled(token.store_id):
            return self._calculate_shared_position(token)
        if token.assigned_counter_id is None or token.calling_time is None:
            return 1
        return self._calculate_counter_position(token.assigned_counter_id, self._normalize_to_utc(token.calling_time), token.id)

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
        counter,
        config: StoreConfig | None = None,
    ) -> str:
        existing_token_count = self.repository.count_tokens_for_numbering(counter.id)
        prefix = config.token_id_prefix if config is not None and config.token_id_prefix else None
        if prefix is None:
            prefix = f"S{section_id}" if section_id is not None else f"ST{store_id}"
        counter_prefix = counter.token_prefix if counter.token_prefix else f"C{counter.id}"
        return f"{prefix}-{counter_prefix}-{existing_token_count + 1:03d}"

    def _generate_shared_token_number(self, store_id: int, section_id: int, config: StoreConfig | None = None) -> str:
        existing_token_count = self.repository.count_shared_tokens_for_numbering(store_id, section_id)
        prefix = config.token_id_prefix if config is not None and config.token_id_prefix else None
        if prefix is None:
            prefix = f"S{section_id}" if section_id is not None else f"ST{store_id}"
        return f"{prefix}-Q-{existing_token_count + 1:03d}"

    def _calculate_shared_position(self, token: QueueToken) -> int:
        if token.status in self.TERMINAL_STATUSES:
            return 0
        if token.section_id is None:
            return 1
        waiting_tokens = self.repository.list_shared_waiting_tokens(token.store_id, token.section_id)
        if token.calling_time is None:
            return next((index + 1 for index, waiting in enumerate(waiting_tokens) if waiting.id == token.id), 1)
        token_calling_time = self._normalize_to_utc(token.calling_time)
        tokens_ahead = [
            waiting
            for waiting in waiting_tokens
            if waiting.calling_time is not None
            and (
                self._normalize_to_utc(waiting.calling_time) < token_calling_time
                or (
                    self._normalize_to_utc(waiting.calling_time) == token_calling_time
                    and (waiting.id or 0) <= (token.id or 0)
                )
            )
        ]
        return len(tokens_ahead) or 1

    def _counter_lane_anchor(self, counter_id: int, reference_time: datetime) -> datetime:
        lane_anchor = reference_time
        serving_token = self.repository.get_current_serving_customer_for_counter(counter_id)
        if serving_token is not None:
            service_start = serving_token.service_started_at or serving_token.called_at or reference_time
            expected_end = self._normalize_to_utc(service_start) + timedelta(minutes=self._token_service_minutes(serving_token))
            return max(reference_time, expected_end)

        called_token = self.repository.get_current_called_customer_for_counter(counter_id)
        if called_token is not None:
            called_time = called_token.called_at or called_token.calling_time or reference_time
            expected_end = self._normalize_to_utc(called_time) + timedelta(minutes=self._token_service_minutes(called_token))
            lane_anchor = max(reference_time, expected_end)
        return lane_anchor

    def _rebuild_shared_section_schedule(
        self,
        store_id: int,
        section_id: int,
        reference_time: datetime | None = None,
        counters: list[Counter] | None = None,
    ) -> None:
        now_utc = reference_time or datetime.now(timezone.utc)
        active_counters = counters if counters is not None else self.repository.list_active_counters(store_id, section_id)
        if not active_counters:
            return

        counter_cursors = {
            counter.id: self._counter_lane_anchor(counter.id, now_utc)
            for counter in active_counters
        }
        waiting_tokens = self.repository.list_shared_waiting_tokens(store_id, section_id)
        for waiting_token in waiting_tokens:
            eligible_counters = [counter for counter in active_counters if self._counter_accepts_token(counter, waiting_token)]
            if not eligible_counters:
                waiting_token.calling_time = None
                continue
            selected_counter = min(eligible_counters, key=lambda counter: (counter_cursors[counter.id], counter.id))
            waiting_token.calling_time = counter_cursors[selected_counter.id]
            counter_cursors[selected_counter.id] = counter_cursors[selected_counter.id] + timedelta(
                minutes=self._token_service_minutes(waiting_token)
            )

        for counter in active_counters:
            counter.next_available_time = counter_cursors[counter.id]

    def _resolve_shared_counter_for_token(
        self,
        token: QueueToken,
        target_counter_id: int | None,
        reference_time: datetime,
    ) -> Counter:
        if token.section_id is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Token is not assigned to a shared section")

        active_counters = self.repository.list_active_counters(token.store_id, token.section_id)
        if target_counter_id is not None:
            counter = next((candidate for candidate in active_counters if candidate.id == target_counter_id), None)
            if counter is None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Counter cannot serve this shared token")
            if not self._counter_accepts_token(counter, token):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Counter cannot serve this basket size")
            return counter

        eligible_counters = [counter for counter in active_counters if self._counter_accepts_token(counter, token)]
        if not eligible_counters:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="No active counters available for this basket size")
        counter_cursors = {
            counter.id: self._counter_lane_anchor(counter.id, reference_time)
            for counter in eligible_counters
        }
        return min(eligible_counters, key=lambda counter: (counter_cursors[counter.id], counter.id))

    def _counter_accepts_token(self, counter: Counter, token: QueueToken) -> bool:
        return counter in self._filter_counters_for_basket_size([counter], token.item_count)

    def _is_shared_queue_enabled(self, config: StoreConfig | None) -> bool:
        return bool(getattr(config, "shared_queue_enabled", False))

    def _is_store_shared_queue_enabled(self, store_id: int) -> bool:
        return self._is_shared_queue_enabled(self._get_store_config(store_id))

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
        waiting_tokens = self.repository.list_waiting_tokens(counter_id)
        cursor = self._counter_lane_anchor(counter_id, now_utc)
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

    def _resolve_effective_item_count(self, payload: QueueJoinRequest, config: StoreConfig | None) -> int | None:
        if payload.item_count is not None:
            return payload.item_count

        basket_item_count = self._item_count_from_basket_size(payload.basket_size)
        if basket_item_count is not None:
            return basket_item_count

        if payload.is_still_shopping:
            if config is None:
                return self.DEFAULT_ITEM_COUNT
            default_item_count = getattr(config, "default_item_count", None)
            return default_item_count if default_item_count is not None else self.DEFAULT_ITEM_COUNT

        return None

    def _item_count_from_basket_size(self, basket_size: str | None) -> int | None:
        if basket_size is None:
            return None
        return self.BASKET_SIZE_ITEM_COUNTS.get(basket_size.strip().lower())

    def _filter_counters_for_basket_size(self, counters: list[Counter], item_count: int | None) -> list[Counter]:
        item_band = self._basket_size_band_for_item_count(item_count)
        eligible_counters: list[Counter] = []
        for counter in counters:
            configured_bands = getattr(counter, "basket_size_bands", None) or []
            if not configured_bands:
                eligible_counters.append(counter)
                continue
            if item_band is not None and item_band in {self._basket_band_value(band) for band in configured_bands}:
                eligible_counters.append(counter)
        return eligible_counters

    def _basket_size_band_for_item_count(self, item_count: int | None) -> str | None:
        if item_count is None:
            return None
        if item_count < 10:
            return CounterBasketSizeBand.SMALL.value
        if item_count <= 20:
            return CounterBasketSizeBand.MEDIUM.value
        return CounterBasketSizeBand.LARGE.value

    def _basket_band_value(self, band: CounterBasketSizeBand | str) -> str:
        return band.value if isinstance(band, CounterBasketSizeBand) else str(band).strip().upper()

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
