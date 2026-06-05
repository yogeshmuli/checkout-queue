import math
import shutil
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.calendar import StoreCalendarDay, StoreCalendarEvent, StoreCalendarEventType
from app.models.checkout_section import CheckoutSection, CheckoutSectionType
from app.models.counter import Counter, CounterBasketSizeBand, CounterType
from app.models.queue_token import QueueToken, QueueTokenStatus
from app.models.store import Store
from app.models.store_config import StoreConfig
from app.models.trial_calendar import TrialCalendarDay, TrialCalendarEvent, TrialCalendarEventType
from app.models.trial_queue_token import TrialQueueToken, TrialQueueTokenStatus
from app.models.trial_store_config import TrialStoreConfig
from app.models.trial_studio import TrialStudio, TrialStudioType
from app.models.trial_zone import (
    TrialZone,
    TrialZoneGender,
    TrialZoneType,
)
from app.repositories.demo_tools_repository import DemoToolsRepository
from app.schemas.demo_tools import DemoToolCounts, DemoToolIds, DemoTrainingDataResponse


DEMO_STORE_NUMBER = "DEMO-ML-STORE"
DEMO_STORE_NAME = "Demo ML Training Store"
CHECKOUT_COMPLETED_SAMPLE_COUNT = 180
TRIAL_COMPLETED_SAMPLE_COUNT = 180
CHECKOUT_CANCELLED_SAMPLE_COUNT = 30
TRIAL_CANCELLED_SAMPLE_COUNT = 30
CHECKOUT_WAITING_SAMPLE_COUNT = 10
TRIAL_WAITING_SAMPLE_COUNT = 10
TIMEZONE_NAME = "Asia/Kolkata"


class DemoToolsService:
    def __init__(self, db: Session) -> None:
        self.repository = DemoToolsRepository(db)

    def seed_ml_training_data(self, replace: bool = False) -> DemoTrainingDataResponse:
        seeded_at = datetime.now(timezone.utc)
        existing_store = self.repository.get_store_by_number(DEMO_STORE_NUMBER)
        if existing_store is not None:
            if not replace:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Demo ML training store already exists. Use replace=true to recreate it.",
                )
            self._cleanup_store(existing_store)

        try:
            store = self._create_store(seeded_at)
            section = self._create_checkout_setup(store.id, seeded_at)
            counters = self.repository.checkout_counters_for_store(store.id)
            zone = self._create_trial_setup(store.id, seeded_at)
            studios = self.repository.trial_studios_for_store(store.id)
            self._create_checkout_history(store.id, section.id, counters, seeded_at)
            self._create_checkout_waiting_tokens(store.id, section.id, counters, seeded_at)
            self._create_trial_history(store.id, zone.id, studios, seeded_at)
            self._create_trial_waiting_tokens(store.id, zone.id, studios, seeded_at)
            self.repository.commit()
            self.repository.refresh(store)
            return self._build_response(store, "Demo ML training data created.")
        except Exception:
            self.repository.rollback()
            raise

    def get_ml_training_data_status(self) -> DemoTrainingDataResponse:
        store = self.repository.get_store_by_number(DEMO_STORE_NUMBER)
        if store is None:
            return DemoTrainingDataResponse(
                exists=False,
                store_number=DEMO_STORE_NUMBER,
                ids=DemoToolIds(),
                counts=DemoToolCounts(),
                message="Demo ML training data is not present.",
            )
        return self._build_response(store, "Demo ML training data is present.")

    def clean_ml_training_data(self) -> DemoTrainingDataResponse:
        store = self.repository.get_store_by_number(DEMO_STORE_NUMBER)
        if store is None:
            return DemoTrainingDataResponse(
                exists=False,
                store_number=DEMO_STORE_NUMBER,
                ids=DemoToolIds(),
                counts=DemoToolCounts(),
                message="No demo ML training data found. Nothing was removed.",
            )

        response = self._build_response(store, "Demo ML training data removed.")
        self._cleanup_store(store)
        self.repository.commit()
        return response.model_copy(update={"exists": False})

    def _create_store(self, seeded_at: datetime) -> Store:
        store = Store(
            store_number=DEMO_STORE_NUMBER,
            name=DEMO_STORE_NAME,
            address="Demo address for ML training data",
            manager_name="Demo Manager",
            manager_phone="9000000001",
            spoc_name="Demo SPOC",
            spoc_phone="9000000002",
            is_active=True,
        )
        self.repository.create(store)
        self.repository.create(StoreConfig(store_id=store.id, token_id_prefix="DML", base_service_minutes=4, per_item_service_minutes=0.35, min_service_minutes=5, default_item_count=10))
        self.repository.create(TrialStoreConfig(store_id=store.id, token_id_prefix="TDML", base_service_minutes=8, per_unit_service_minutes=1.2, min_service_minutes=10))

        for weekday in range(7):
            self.repository.create(StoreCalendarDay(store_id=store.id, weekday=weekday, is_open=True, open_time=time(8, 0), close_time=time(23, 0), timezone=TIMEZONE_NAME))
            self.repository.create(TrialCalendarDay(store_id=store.id, weekday=weekday, is_open=True, open_time=time(9, 0), close_time=time(22, 0), timezone=TIMEZONE_NAME))

        today = seeded_at.date()
        for offset in (3, 10, 17, 24):
            event_date = today - timedelta(days=offset)
            self.repository.create(StoreCalendarEvent(store_id=store.id, event_date=event_date, name="Demo promotion", event_type=StoreCalendarEventType.PROMOTION, is_active=True))
            self.repository.create(TrialCalendarEvent(store_id=store.id, event_date=event_date, name="Demo trial sale", event_type=TrialCalendarEventType.SALE, is_active=True))

        return store

    def _create_checkout_setup(self, store_id: int, seeded_at: datetime) -> CheckoutSection:
        section = CheckoutSection(store_id=store_id, name="Demo Checkout Section", section_type=CheckoutSectionType.REGULAR, is_active=True)
        self.repository.create(section)
        counter_bands = (
            [CounterBasketSizeBand.SMALL.value],
            [CounterBasketSizeBand.MEDIUM.value],
            [CounterBasketSizeBand.LARGE.value],
        )
        for index, counter_type in enumerate((CounterType.REGULAR, CounterType.EXPRESS, CounterType.PRIORITY), start=1):
            self.repository.create(
                Counter(
                    section_id=section.id,
                    counter_type=counter_type,
                    name=f"Demo Counter {index}",
                    token_prefix=f"C{index}",
                    basket_size_bands=counter_bands[index - 1],
                    is_active=True,
                    next_available_time=seeded_at,
                )
            )
        return section

    def _create_trial_setup(self, store_id: int, seeded_at: datetime) -> TrialZone:
        zone = TrialZone(
            store_id=store_id,
            name="Demo Trial Zone",
            zone_type=TrialZoneType.REGULAR,
            gender=TrialZoneGender.UNISEX,
            is_active=True,
        )
        self.repository.create(zone)
        for index, studio_type in enumerate((TrialStudioType.REGULAR, TrialStudioType.EXPRESS, TrialStudioType.PRIORITY), start=1):
            self.repository.create(
                TrialStudio(
                    trial_zone_id=zone.id,
                    name=f"Demo Studio {index}",
                    studio_type=studio_type,
                    is_active=True,
                    next_available_time=seeded_at,
                )
            )
        return zone

    def _create_checkout_history(self, store_id: int, section_id: int, counters: list[Counter], seeded_at: datetime) -> None:
        for index in range(CHECKOUT_COMPLETED_SAMPLE_COUNT):
            counter = counters[index % len(counters)]
            item_count = self._checkout_item_count(index)
            created_at = self._historical_join_time(index, seeded_at)
            service_minutes = self._checkout_service_minutes(index, item_count, counter.counter_type, seeded_at)
            started_at = created_at + timedelta(minutes=3 + (index % 9))
            completed_at = started_at + timedelta(minutes=service_minutes)
            self.repository.create(
                QueueToken(
                    store_id=store_id,
                    section_id=section_id,
                    assigned_counter_id=counter.id,
                    token_number=f"DML-C-{index + 1:04d}",
                    phone_number=f"8{index + 100000000:09d}"[-10:],
                    status=QueueTokenStatus.COMPLETED,
                    item_count=item_count,
                    basket_size=self._basket_size(item_count),
                    cart_type="cart" if item_count >= 18 else "basket",
                    customer_type=self._customer_type(index),
                    is_still_shopping=False,
                    calculation_method="DEMO_HISTORY",
                    service_time_minutes=service_minutes,
                    calling_time=started_at,
                    called_at=started_at - timedelta(minutes=1),
                    service_started_at=started_at,
                    completed_at=completed_at,
                    created_at=created_at,
                    updated_at=completed_at,
                )
            )

        for index in range(CHECKOUT_CANCELLED_SAMPLE_COUNT):
            counter = counters[index % len(counters)]
            created_at = self._historical_join_time(index + CHECKOUT_COMPLETED_SAMPLE_COUNT, seeded_at)
            cancelled_at = created_at + timedelta(minutes=2 + (index % 8))
            self.repository.create(
                QueueToken(
                    store_id=store_id,
                    section_id=section_id,
                    assigned_counter_id=counter.id,
                    token_number=f"DML-X-{index + 1:04d}",
                    phone_number=f"7{index + 100000000:09d}"[-10:],
                    status=QueueTokenStatus.NO_SHOW if index % 5 == 0 else QueueTokenStatus.CANCELLED,
                    item_count=self._checkout_item_count(index),
                    basket_size="medium",
                    cart_type="basket",
                    customer_type=self._customer_type(index),
                    calculation_method="DEMO_HISTORY",
                    calling_time=cancelled_at,
                    cancelled_at=cancelled_at,
                    cancellation_reason="Demo cancellation",
                    created_at=created_at,
                    updated_at=cancelled_at,
                )
            )

    def _create_checkout_waiting_tokens(self, store_id: int, section_id: int, counters: list[Counter], seeded_at: datetime) -> None:
        for index in range(CHECKOUT_WAITING_SAMPLE_COUNT):
            counter = min(counters, key=lambda candidate: candidate.next_available_time)
            item_count = self._checkout_item_count(index + CHECKOUT_COMPLETED_SAMPLE_COUNT + CHECKOUT_CANCELLED_SAMPLE_COUNT)
            calling_time = max(seeded_at, counter.next_available_time)
            service_minutes = self._checkout_service_minutes(index, item_count, counter.counter_type, seeded_at)
            counter.next_available_time = calling_time + timedelta(minutes=service_minutes)
            self.repository.create(
                QueueToken(
                    store_id=store_id,
                    section_id=section_id,
                    assigned_counter_id=counter.id,
                    token_number=f"DML-W-{index + 1:04d}",
                    phone_number=f"4{index + 100000000:09d}"[-10:],
                    status=QueueTokenStatus.WAITING,
                    item_count=item_count,
                    basket_size=self._basket_size(item_count),
                    cart_type="cart" if item_count >= 18 else "basket",
                    customer_type=self._customer_type(index),
                    is_still_shopping=False,
                    calculation_method="DEMO_ACTIVE",
                    service_time_minutes=service_minutes,
                    calling_time=calling_time,
                    created_at=seeded_at,
                    updated_at=seeded_at,
                )
            )

    def _create_trial_history(self, store_id: int, zone_id: int, studios: list[TrialStudio], seeded_at: datetime) -> None:
        for index in range(TRIAL_COMPLETED_SAMPLE_COUNT):
            studio = studios[index % len(studios)]
            item_count = 1 + (index % 8)
            created_at = self._historical_join_time(index, seeded_at, base_hour=11)
            service_minutes = self._trial_service_minutes(index, item_count, studio.studio_type, seeded_at)
            started_at = created_at + timedelta(minutes=4 + (index % 11))
            completed_at = started_at + timedelta(minutes=service_minutes)
            self.repository.create(
                TrialQueueToken(
                    store_id=store_id,
                    trial_zone_id=zone_id,
                    assigned_studio_id=studio.id,
                    token_number=f"TDML-C-{index + 1:04d}",
                    phone_number=f"6{index + 100000000:09d}"[-10:],
                    status=TrialQueueTokenStatus.COMPLETED,
                    item_count=item_count,
                    customer_type=self._customer_type(index),
                    calculation_method="DEMO_HISTORY",
                    service_time_minutes=service_minutes,
                    calling_time=started_at,
                    called_at=started_at - timedelta(minutes=1),
                    service_started_at=started_at,
                    completed_at=completed_at,
                    created_at=created_at,
                    updated_at=completed_at,
                )
            )

        for index in range(TRIAL_CANCELLED_SAMPLE_COUNT):
            studio = studios[index % len(studios)]
            created_at = self._historical_join_time(index + TRIAL_COMPLETED_SAMPLE_COUNT, seeded_at, base_hour=12)
            cancelled_at = created_at + timedelta(minutes=3 + (index % 6))
            self.repository.create(
                TrialQueueToken(
                    store_id=store_id,
                    trial_zone_id=zone_id,
                    assigned_studio_id=studio.id,
                    token_number=f"TDML-X-{index + 1:04d}",
                    phone_number=f"5{index + 100000000:09d}"[-10:],
                    status=TrialQueueTokenStatus.NO_SHOW if index % 6 == 0 else TrialQueueTokenStatus.CANCELLED,
                    item_count=1 + (index % 8),
                    customer_type=self._customer_type(index),
                    calculation_method="DEMO_HISTORY",
                    calling_time=cancelled_at,
                    cancelled_at=cancelled_at,
                    cancellation_reason="Demo cancellation",
                    created_at=created_at,
                    updated_at=cancelled_at,
                )
            )

    def _create_trial_waiting_tokens(self, store_id: int, zone_id: int, studios: list[TrialStudio], seeded_at: datetime) -> None:
        for index in range(TRIAL_WAITING_SAMPLE_COUNT):
            studio = min(studios, key=lambda candidate: candidate.next_available_time)
            item_count = 1 + (index % 8)
            calling_time = max(seeded_at, studio.next_available_time)
            service_minutes = self._trial_service_minutes(index, item_count, studio.studio_type, seeded_at)
            studio.next_available_time = calling_time + timedelta(minutes=service_minutes)
            self.repository.create(
                TrialQueueToken(
                    store_id=store_id,
                    trial_zone_id=zone_id,
                    assigned_studio_id=studio.id,
                    token_number=f"TDML-W-{index + 1:04d}",
                    phone_number=f"3{index + 100000000:09d}"[-10:],
                    status=TrialQueueTokenStatus.WAITING,
                    item_count=item_count,
                    customer_type=self._customer_type(index),
                    calculation_method="DEMO_ACTIVE",
                    service_time_minutes=service_minutes,
                    calling_time=calling_time,
                    created_at=seeded_at,
                    updated_at=seeded_at,
                )
            )

    def _cleanup_store(self, store: Store) -> None:
        store_id = store.id
        self.repository.delete_ml_metadata(store_id)
        self.repository.delete_store(store)
        self._remove_artifact_dir(Path(settings.ML_MODEL_DIR) / f"store_{store_id}")
        self._remove_artifact_dir(Path(settings.ML_MODEL_DIR) / f"trial_store_{store_id}")

    def _build_response(self, store: Store, message: str) -> DemoTrainingDataResponse:
        section = self.repository.checkout_section_for_store(store.id)
        counters = self.repository.checkout_counters_for_store(store.id)
        zone = self.repository.trial_zone_for_store(store.id)
        studios = self.repository.trial_studios_for_store(store.id)
        return DemoTrainingDataResponse(
            exists=True,
            store_number=DEMO_STORE_NUMBER,
            ids=DemoToolIds(
                store_id=store.id,
                checkout_section_id=section.id if section else None,
                checkout_counter_ids=[counter.id for counter in counters],
                trial_zone_id=zone.id if zone else None,
                trial_studio_ids=[studio.id for studio in studios],
            ),
            counts=DemoToolCounts(
                checkout_completed_tokens=self.repository.count_checkout_completed_tokens(store.id),
                checkout_terminal_tokens=self.repository.count_checkout_terminal_tokens(store.id),
                checkout_waiting_tokens=self.repository.count_checkout_waiting_tokens(store.id),
                trial_completed_tokens=self.repository.count_trial_completed_tokens(store.id),
                trial_terminal_tokens=self.repository.count_trial_terminal_tokens(store.id),
                trial_waiting_tokens=self.repository.count_trial_waiting_tokens(store.id),
                ml_metadata_rows=self.repository.count_ml_metadata(store.id),
            ),
            checkout_artifact_present=(Path(settings.ML_MODEL_DIR) / f"store_{store.id}").exists(),
            trial_artifact_present=(Path(settings.ML_MODEL_DIR) / f"trial_store_{store.id}").exists(),
            next_steps=[
                f"POST /api/v1/ml/stores/{store.id}/train",
                f"POST /api/v1/ml/trial/stores/{store.id}/train",
            ],
            message=message,
        )

    def _historical_join_time(self, index: int, seeded_at: datetime, base_hour: int = 10) -> datetime:
        day_offset = index % 30
        hour = base_hour + ((index * 5) % 12)
        minute = (index * 7) % 60
        return (seeded_at - timedelta(days=day_offset)).replace(hour=hour % 24, minute=minute, second=0, microsecond=0)

    def _checkout_item_count(self, index: int) -> int:
        return 1 + ((index * 7) % 42)

    def _basket_size(self, item_count: int) -> str:
        if item_count <= 8:
            return "small"
        if item_count <= 24:
            return "medium"
        return "large"

    def _customer_type(self, index: int) -> str:
        return ("regular", "loyalty", "priority", "new")[index % 4]

    def _checkout_service_minutes(self, index: int, item_count: int, counter_type: CounterType, seeded_at: datetime) -> int:
        multiplier = 0.22 if counter_type == CounterType.EXPRESS else 0.34 if counter_type == CounterType.PRIORITY else 0.28
        busy_penalty = (index % 6) * 0.6
        weekend_penalty = 2 if self._historical_join_time(index, seeded_at).weekday() >= 5 else 0
        return max(3, min(60, math.ceil(4 + (item_count * multiplier) + busy_penalty + weekend_penalty)))

    def _trial_service_minutes(self, index: int, item_count: int, studio_type: TrialStudioType, seeded_at: datetime) -> int:
        multiplier = 1.0 if studio_type == TrialStudioType.EXPRESS else 1.6 if studio_type == TrialStudioType.PRIORITY else 1.3
        busy_penalty = (index % 5) * 1.1
        weekend_penalty = 3 if self._historical_join_time(index, seeded_at).weekday() >= 5 else 0
        return max(6, min(90, math.ceil(8 + (item_count * multiplier) + busy_penalty + weekend_penalty)))

    def _remove_artifact_dir(self, path: Path) -> None:
        if path.exists():
            shutil.rmtree(path)
