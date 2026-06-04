# Checkout Queue App - Technical Stack and Architecture

## 1. Purpose

This document proposes the technical stack, folder structure, and backend architecture for the Checkout Queue App described in `REQURIMENT.md`.

The application will support customer checkout queue registration, cashier queue operations, store administration, alerts, analytics, and machine-learning based checkout-time prediction.

## 2. Recommended Technical Stack

### Frontend

| Area | Technology |
| --- | --- |
| Framework | React |
| Build Tool | Vite |
| PWA | vite-plugin-pwa with web app manifest and service worker |
| Language | JavaScript |
| Routing | React Router |
| API Client | Axios |
| State Management | Zustand |
| Forms | React Hook Form |
| Validation | Zod or Yup |
| Charts / Analytics | Recharts or Apache ECharts |
| Styling | Tailwind CSS |
| Typography | Poppins for headings/UI, Inter fallback for body text |
| Testing | Vitest, React Testing Library |

### Backend

| Area | Technology |
| --- | --- |
| Framework | FastAPI |
| Language | Python |
| API Server | Uvicorn |
| ORM | SQLAlchemy ORM |
| Migrations | Alembic |
| Data Validation | Pydantic |
| Authentication | JWT-based auth for admin/cashier sessions |
| Background Jobs | FastAPI background tasks initially; Celery/RQ/APScheduler if scheduling grows |
| ML | scikit-learn |
| Model Storage | Local volume or object storage |
| Testing | Pytest |

### Database and Infrastructure

| Area | Technology |
| --- | --- |
| Primary DB | PostgreSQL |
| Local Development | Docker Compose |
| Cache / Queue, optional | Redis |
| Deployment | Docker containers |
| Reverse Proxy, optional | Nginx |
| Observability | Structured logging, health check endpoint, metrics-ready service layout |

## 3. Proposed Folder Structure

```text
checkout-que/
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── security.py
│   │   │   ├── exceptions.py
│   │   │   └── logging.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── store.py
│   │   │   ├── store_config.py
│   │   │   ├── calendar.py
│   │   │   ├── checkout_section.py
│   │   │   ├── counter.py
│   │   │   ├── staff.py
│   │   │   ├── queue_token.py
│   │   │   ├── alert_config.py
│   │   │   ├── support_ticket.py
│   │   │   └── ml_model_metadata.py
│   │   ├── schemas/
│   │   │   ├── store.py
│   │   │   ├── store_config.py
│   │   │   ├── calendar.py
│   │   │   ├── checkout_section.py
│   │   │   ├── counter.py
│   │   │   ├── staff.py
│   │   │   ├── queue.py
│   │   │   ├── alert.py
│   │   │   ├── analytics.py
│   │   │   ├── auth.py
│   │   │   └── support.py
│   │   ├── routes/
│   │   │   ├── api.py
│   │   │   ├── auth_routes.py
│   │   │   ├── store_routes.py
│   │   │   ├── store_config_routes.py
│   │   │   ├── calendar_routes.py
│   │   │   ├── section_routes.py
│   │   │   ├── staff_routes.py
│   │   │   ├── queue_routes.py
│   │   │   ├── cashier_routes.py
│   │   │   ├── alert_routes.py
│   │   │   ├── analytics_routes.py
│   │   │   ├── ml_routes.py
│   │   │   ├── webhook_routes.py
│   │   │   └── support_routes.py
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── store_service.py
│   │   │   ├── store_config_service.py
│   │   │   ├── calendar_service.py
│   │   │   ├── section_service.py
│   │   │   ├── staff_service.py
│   │   │   ├── queue_service.py
│   │   │   ├── cashier_service.py
│   │   │   ├── alert_service.py
│   │   │   ├── analytics_service.py
│   │   │   ├── prediction_service.py
│   │   │   ├── ml_training_service.py
│   │   │   ├── notification_service.py
│   │   │   └── support_service.py
│   │   ├── repositories/
│   │   │   ├── auth_repository.py
│   │   │   ├── store_repository.py
│   │   │   ├── store_config_repository.py
│   │   │   ├── calendar_repository.py
│   │   │   ├── section_repository.py
│   │   │   ├── counter_repository.py
│   │   │   ├── staff_repository.py
│   │   │   ├── queue_repository.py
│   │   │   ├── alert_repository.py
│   │   │   ├── analytics_repository.py
│   │   │   ├── ml_repository.py
│   │   │   └── support_repository.py
│   │   ├── jobs/
│   │   │   ├── alert_scheduler.py
│   │   │   ├── ml_retraining_job.py
│   │   │   └── demo_seed_job.py
│   │   ├── ml/
│   │   │   ├── features.py
│   │   │   ├── trainer.py
│   │   │   ├── predictor.py
│   │   │   └── model_store.py
│   │   ├── integrations/
│   │   │   ├── sms_client.py
│   │   │   ├── whatsapp_client.py
│   │   │   └── calendar_client.py
│   │   └── utils/
│   │       ├── token_generator.py
│   │       ├── time_utils.py
│   │       └── pagination.py
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   ├── scripts/
│   │   ├── seed_demo_data.py
│   │   ├── clean_active_queue.py
│   │   └── train_models.py
│   ├── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── api/
│   │   │   ├── httpClient.js
│   │   │   ├── authApi.js
│   │   │   ├── storeApi.js
│   │   │   ├── queueApi.js
│   │   ├── app/
│   │   │   ├── common/
│   │   │   │   ├── MetricTile.jsx
│   │   │   │   ├── RoleRedirect.jsx
│   │   │   │   └── SectionHeader.jsx
│   │   │   ├── customer/
│   │   │   │   └── CustomerApp.jsx
│   │   │   ├── staff/
│   │   │   │   └── StaffApp.jsx
│   │   │   └── admin/
│   │   │       ├── AdminApp.jsx
│   │   │       └── AdminStores.jsx
│   │   ├── store/
│   │   │   ├── authStore.js
│   │   │   └── queueStore.js
│   │   └── styles/
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── docs/
│   └── TECHNICAL_STACK_AND_ARCHITECTURE.md
├── docker-compose.yml
├── .env.example
└── README.md
```

## 4. Backend Architecture

The FastAPI backend should use a three-layer application structure:

```text
Routes -> Services -> Repositories -> SQLAlchemy Models -> Database
```

### Routes Layer

The routes layer owns HTTP concerns only.

Responsibilities:

- Define API endpoints.
- Validate request and response schemas with Pydantic.
- Map service exceptions to HTTP responses.
- Handle authentication dependencies.
- Avoid business logic and direct database queries.

Example route modules:

- `auth_routes.py`
- `store_routes.py`
- `queue_routes.py`
- `cashier_routes.py`
- `analytics_routes.py`
- `ml_routes.py`
- `webhook_routes.py`

### Services Layer

The services layer owns business rules and orchestration.

Responsibilities:

- Generate checkout tokens.
- Prevent duplicate active tokens.
- Calculate queue position.
- Calculate rule-based or ML-assisted wait time.
- Call notification integrations.
- Orchestrate cashier actions such as call next, assign counter, and complete checkout.
- Trigger ML retraining checks after checkout completion.
- Keep operations idempotent where repeated clicks may occur.

Example service modules:

- `queue_service.py`
- `cashier_service.py`
- `prediction_service.py`
- `ml_training_service.py`
- `alert_service.py`
- `analytics_service.py`

### Repository Layer

The repository layer owns database access.

Responsibilities:

- Encapsulate SQLAlchemy queries.
- Create, read, update, and delete database records.
- Provide query methods for services.
- Keep HTTP and business workflow details out of database code.

Example repository modules:

- `auth_repository.py`
- `store_repository.py`
- `queue_repository.py`
- `analytics_repository.py`
- `ml_repository.py`

## 5. Core Domain Modules

### Authentication and Authorization

Entities:

- User
- User store access
- Refresh token
- Optional user assignment details (`store_id`, `section_id`, `assigned_counter_id`)

Main APIs:

- Register user
- Log in user
- Fetch current authenticated user
- Log out by revoking refresh token

Auth rules:

- `users` owns login identity, password hash, account status, and default role.
- Operational assignment fields are captured directly in `users`.
- `user_store_access` maps users to stores and store-specific roles.
- Access tokens are signed bearer tokens for API authorization.
- Refresh tokens are stored hashed and can be revoked during logout.
- Supported roles are `SUPER_ADMIN`, `STORE_ADMIN`, `MANAGER`, `CASHIER`, and `SUPPORT`.

### Store Management

Entities:

- Store
- Store calendar
- Holidays
- Promotion or sale dates
- Alert configuration

Main APIs:

- List stores
- Create store
- Read store by id
- Update store
- Soft delete store by marking `is_active = false`
- Configure store calendar
- Configure alerts

### Checkout Configuration

Entities:

- Checkout section
- Billing counter type
- Counter state
- Staff or cashier

Main APIs:

- Create section
- Update section
- Activate or deactivate section
- Configure counter types
- Add or delete staff

### Customer Queue

Entities:

- Queue token
- Queue status history
- Customer reply state

Main APIs:

- Join checkout queue
- Track token by phone number
- Cancel token
- Get store-wide queue status

Implemented first:

- `POST /api/v1/queue/join`
- `GET /api/v1/queue/status`
- `GET /api/v1/queue/counters/{counter_id}/tokens`
- `PATCH /api/v1/queue/counters/{counter_id}/status`
- `POST /api/v1/queue/tokens/{token_id}/start`
- `POST /api/v1/queue/tokens/{token_id}/complete`
- `POST /api/v1/queue/tokens/{token_id}/cancel`
- Public API for customer enrollment.
- Uses rule-based wait-time calculation.
- Schedules tokens using counter `next_available_time` and returns computed wait time from `calling_time`.
- Rejects duplicate active token for the same phone number and store.
- Rejects queue join when no active counter setup is available.

Queue token statuses:

```text
WAITING
CALLED
SERVING
COMPLETED
CANCELLED
NO_SHOW
```

### Cashier Workflow

Main APIs:

- Cashier login
- Get cashier dashboard
- Call next customer
- Assign token to counter
- Update item count or basket size
- Complete checkout

### Alerts and Notifications

Main APIs:

- Configure alert settings
- Run scheduled alert checks
- Send customer reminder
- Handle WhatsApp webhook replies
- Send escalation alerts

### Analytics

Main APIs:

- Live dashboard
- Historic analytics by date range
- Section/counter stats
- Basket-size or item-count trends
- Cashier throughput stats
- Promotion/sale day analysis
- Cancellation/no-show stats

### Machine Learning

Main APIs:

- Train store-specific model
- Get model metadata
- Predict checkout service time
- Train and predict Trial Queue service time with separate trial-specific features and artifacts
- Fall back to rule-based prediction if ML is unavailable

The ML model should predict checkout service duration for a customer token. It should not directly own the full queue wait estimate. Queue wait time should continue to be calculated by the queue scheduling service using:

- Customers ahead in queue.
- Active counters.
- Current serving tokens.
- Predicted service time per waiting customer.
- Recent cancellation/no-show behavior.

The first ML implementation should be hybrid:

- Use ML only when enough completed checkout history and a trained model are available.
- Use separate Trial Queue ML only when enough completed trial history and a trained trial model are available.
- Fall back to the store's rule-based service-time configuration when ML is disabled, unavailable, stale, under-trained, or fails at runtime.
- Train from completed queue tokens where `service_started_at` and `completed_at` are present.
- Use actual service duration from `completed_at - service_started_at` as the target value.
- Use PostgreSQL-backed repositories as the only source for application training data.

## 6. Suggested Database Tables

| Table | Purpose |
| --- | --- |
| `users` | Login identity, password hash, default role, account status, and optional operational assignment fields (`store_id`, `section_id`, `assigned_counter_id`) |
| `user_store_access` | User-to-store role mapping for admins, managers, and cashiers |
| `refresh_tokens` | Hashed refresh tokens for revocation and session lifecycle |
| `stores` | Store profile, store number, contact details |
| `store_configs` | Store-level token prefix and rule-based service-time settings |
| `store_calendar_days` | Store weekly working days, open/close time, and timezone |
| `store_calendar_events` | Store calendar events such as promotion, sale, holiday, or other special dates |
| `store_holidays` | Holiday dates |
| `store_events` | Promotion, sale, and peak-event dates |
| `store_notification_configs` | Per-store customer notification toggles and message templates |
| `checkout_sections` | Checkout sections with enum-backed type: regular, express, self-checkout, returns, priority |
| `counter_types` | Counter type counts and active/inactive counters, constrained to regular, express, self-checkout, returns/exchange, or priority behavior |
| `queue_tokens` | Customer checkout queue entries |
| `queue_status_events` | Token state transitions for audit and analytics |
| `alert_configs` | Wait-time, token-ahead, utilization, and escalation settings |
| `notification_logs` | SMS notification attempts for checkout/trial called and next-soon events |
| `support_tickets` | Customer or staff support tickets |
| `ml_model_metadata` | Store model training metadata |
| `trial_zones` | Trial Queue zones linked to shared stores |
| `trial_studios` | Trial Queue service locations linked to trial zones |
| `trial_store_configs` | Store-level Trial Queue token and service-time settings |
| `trial_calendar_days` | Trial-specific weekly store hours |
| `trial_holidays` | Trial-specific holiday closures |
| `trial_calendar_events` | Trial-specific promotion, sale, holiday, or other event dates |
| `trial_queue_tokens` | Customer Trial Queue entries |

## 7. API Surface

Recommended API prefix:

```text
/api/v1
```

Suggested endpoint groups:

```text
/api/v1/stores
/api/v1/stores/{store_id}/config
/api/v1/auth
/api/v1/stores/{store_id}/calendar
/api/v1/stores/{store_id}/sections
/api/v1/stores/{store_id}/staff
/api/v1/queue
/api/v1/cashier
/api/v1/alerts
/api/v1/analytics
/api/v1/ml
/api/v1/trial
/api/v1/demotools
/api/v1/webhooks
/api/v1/support
```

Example auth endpoints:

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/auth/logout
```

Example customer endpoints:

```text
POST /api/v1/queue/join
GET  /api/v1/queue/status?token_id=1
GET  /api/v1/queue/status?store_id=1&phone_number=9876543210
GET  /api/v1/stores/{store_id}/queue-status
```

Example cashier endpoints:

```text
POST  /api/v1/auth/login
GET   /api/v1/queue/counters/{counter_id}/tokens
PATCH /api/v1/queue/counters/{counter_id}/status
POST  /api/v1/queue/tokens/{token_id}/start
POST  /api/v1/queue/tokens/{token_id}/complete
POST  /api/v1/queue/tokens/{token_id}/cancel
```

Example admin endpoints:

```text
POST   /api/v1/stores
GET    /api/v1/stores
GET    /api/v1/stores/{store_id}
PATCH  /api/v1/stores/{store_id}
DELETE /api/v1/stores/{store_id}
GET    /api/v1/stores/{store_id}/config
PUT    /api/v1/stores/{store_id}/config
GET    /api/v1/stores/{store_id}/notification-config
PUT    /api/v1/stores/{store_id}/notification-config
GET    /api/v1/stores/{store_id}/notification-logs
POST   /api/v1/stores/{store_id}/sections
POST   /api/v1/stores/{store_id}/staff
GET    /api/v1/analytics/stores/{store_id}
POST   /api/v1/ml/stores/{store_id}/train
GET    /api/v1/ml/stores/{store_id}/metadata
POST   /api/v1/ml/stores/{store_id}/predict-service-time
POST   /api/v1/ml/trial/stores/{store_id}/train
GET    /api/v1/ml/trial/stores/{store_id}/metadata
POST   /api/v1/ml/trial/stores/{store_id}/predict-service-time
```

Example Demo Tools endpoints:

```text
POST   /api/v1/demotools/ml-training-data?replace=false
GET    /api/v1/demotools/ml-training-data/status
DELETE /api/v1/demotools/ml-training-data
```

Demo Tools are registered only when `ENABLE_DEMO_TOOLS=true` and are restricted to `SUPER_ADMIN`. They create and clean an isolated ML training store identified by `store_number=DEMO-ML-STORE`; cleanup removes that store, demo ML metadata, and demo artifact directories only. Each seed request uses one captured UTC timestamp for historical dates, lane availability, and ten pending tokens per app so Checkout and Trial staff consoles receive deterministic current-time live queues.

## 8. Frontend Application Structure

The React app should be organized around product modules and then user roles:

- Checkout module files live under `frontend/src/app/checkout`, with `admin`, `staff`, and `customer` subtrees.
- Trial module files live under `frontend/src/app/trial`, with `admin`, `staff`, and `customer` subtrees.
- Shared shell, auth, selector, UI primitives, and role helpers stay under `frontend/src/app/common`.

Implemented frontend routing:

```text
/
/app
/app/checkout/admin
/app/checkout/admin/stores
/app/checkout/admin/store-config
/app/checkout/admin/sections
/app/checkout/admin/counters
/app/checkout/admin/staff
/app/checkout/admin/queue
/app/checkout/admin/calendar
/app/checkout/admin/ml
/app/checkout/admin/alerts
/app/checkout/staff
/app/checkout/customer
/app/trial/admin
/app/trial/admin/zones
/app/trial/admin/studios
/app/trial/admin/config
/app/trial/admin/calendar
/app/trial/admin/ml
/app/trial/admin/queue
/app/trial/staff
/app/trial/customer
```

Frontend API handling should be centralized under `src/api/` so pages and components do not manually build URLs or duplicate error handling:

- Shared API infrastructure stays at `frontend/src/api/httpClient.js` and `frontend/src/api/authApi.js`.
- Checkout module API clients live under `frontend/src/api/checkout`.
- Trial module API clients live under `frontend/src/api/trial`, split by resource such as queue, zones, studios, config, calendar, and ML.

Current frontend implementation:

- `checkout/admin/AdminApp` provides the checkout admin portal shell, sidebar, header, and admin route outlet.
- `checkout/CheckoutApp` owns checkout admin, staff, and customer nested routing under `/app/checkout/*`.
- Admin store, section, counter, staff, queue, store config, calendar, and ML pages connect to their implemented APIs.
- `checkout/staff/StaffApp` provides a mobile-first counter operations console integrated with auth and queue transition APIs.
- `checkout/customer/CustomerApp` connects to `POST /api/v1/queue/join`, displays token details after enrollment, and polls token status.
- `ContextSelector` lets logged-in users choose Checkout Queue or Trial Queue when multiple product modules are enabled.
- `TrialApp` owns separate trial admin, staff, and customer route trees under `/app/trial/*`.
- `trial/admin/AdminApp` provides the trial admin portal shell, sidebar, header, and nested admin routes, matching the checkout admin module pattern.
- Trial assistants persist `users.assigned_zone_id` rather than a studio assignment. Trial tokens remain assigned to individual studios for scheduling, while the Trial staff workspace aggregates studio queues through `/api/v1/trial/queue/zones/{zone_id}/studios`.
- Trial staff API authorization scopes `TRIAL_ZONE_ASSISTANT` users to their assigned zone and managers to zones inside their assigned store.
- Trial admin ML connects to `/api/v1/ml/trial/stores/{store_id}/train|metadata` and displays the latest trial service-time model.

## 9. Request Flow Examples

### Customer Joins Queue

```text
React Join Queue Page
  -> POST /api/v1/queue/join
      -> queue_routes.py
      -> queue_service.py
        -> calendar_repository.py checks store hours and active holidays
        -> queue_repository.py checks duplicate active token
        -> prediction_service.py calculates estimated wait
        -> queue_repository.py saves token
        -> notification_service.py sends optional SMS/WhatsApp
      -> returns token number, position, wait time, and method
```

### Cashier Calls Next Customer

```text
React Cashier Dashboard
  -> POST /api/v1/cashier/call-next
    -> cashier_routes.py
      -> cashier_service.py
        -> queue_repository.py finds next eligible token
        -> queue_repository.py marks token CALLED/SERVING
        -> notification_service.py sends reminder if enabled
      -> returns updated dashboard state
```

### Checkout Completion

```text
React Cashier Dashboard
  -> POST /api/v1/cashier/tokens/{token_id}/complete
    -> cashier_routes.py
      -> cashier_service.py
        -> queue_repository.py marks token COMPLETED
        -> analytics_repository.py records service duration data
        -> ml_training_service.py checks retraining threshold
      -> returns completed token summary
```

## 10. Prediction Architecture

The prediction service should support two modes:

### Rule-Based Mode

Used when ML is disabled, unavailable, or there is insufficient completed checkout history.

Inputs:

- Active counters.
- People waiting.
- People currently being served.
- Average checkout service time.
- Item count or basket size.
- Section type.

### ML-Assisted Mode

Used when the store has a trained model with enough completed samples.

Inputs:

- Item count or basket size.
- Cart type.
- Customer type.
- Store, section, and assigned counter.
- Check-in hour.
- Day of week.
- Weekend flag.
- Store calendar or promotion/sale day flag when available.
- Checkout section type.

Output:

- Predicted service time for the customer.
- Prediction metadata such as method, model version, and confidence-related fields where available.

The prediction service should return only service-duration data. `QueueService` should then combine predicted or fallback service times with the current per-counter lane schedule to calculate `calling_time` and estimated wait.

The current implementation uses a scikit-learn `RandomForestRegressor` pipeline saved as a `.joblib` artifact. The earlier JSON linear artifact format may still be read for old metadata rows, but new training writes `random_forest_service_time_v2` artifacts.

### Current ML Feature Flow

The implemented ML feature is store-specific and predicts only service duration. It does not directly decide queue position, counter assignment, calling time, or full customer wait time.

Training flow:

```text
Admin UI /app/checkout/admin/ml?store_id={store_id}
  -> POST /api/v1/ml/stores/{store_id}/train
    -> ml_routes.py
      -> MLTrainingService
        -> MLRepository validates store
        -> MLRepository loads completed queue_tokens
        -> service duration = completed_at - service_started_at
        -> trainer builds operational features from queue history, section busyness, recent cancellation/service history, local time, and calendar events
        -> trainer fits RandomForestRegressor model
        -> artifact is written under ML_MODEL_DIR/store_{store_id}
        -> metadata is saved in ml_model_metadata
      -> returns latest ML metadata
```

Prediction flow during customer queue join:

```text
Customer create token
  -> POST /api/v1/queue/join
    -> queue_routes.py
      -> QueueService
        -> validates active store, section, calendar, duplicate token, active counters
        -> PredictionService asks QueueRepository for latest READY metadata
        -> PredictionService reuses cached artifact when store/model/path/mtime match
        -> otherwise PredictionService loads artifact from ML_MODEL_DIR and caches it
        -> if artifact exists and prediction succeeds:
             service_time_minutes = ML prediction
             calculation_method = ML_PREDICTED
        -> otherwise:
             service_time_minutes = store rule-based config
             calculation_method = RULE_BASED
        -> QueueService schedules the token on the best available counter
        -> QueueService calculates calling_time and estimated_wait_minutes
      -> returns queue token response
```

Metadata/status flow:

```text
Admin UI /app/checkout/admin/ml?store_id={store_id}
  -> GET /api/v1/ml/stores/{store_id}/metadata
    -> MLTrainingService
      -> MLRepository returns latest metadata row
    -> UI shows status, sample size, MAE, R2, accuracy, data quality, and version
```

Important behavior:

- Training requires at least `ML_MIN_TRAINING_SAMPLES`, currently `50`, completed checkout records.
- Only records with both `service_started_at` and `completed_at` are used.
- V2 model features include item count, section busy count, active section counters, recent cancellation rate, recent average service time, hour, day of week, weekend flag, promotion/sale flag, basket size, cart type, customer type, section, and assigned counter.
- Promotion/sale flags come from active store calendar events.
- The prediction target is checkout service minutes, not wait minutes.
- Queue wait remains deterministic and counter-based.
- If ML is missing, under-trained, stale, broken, or the artifact cannot be read, queue creation continues with rule-based estimation.
- Model artifacts live under `ML_MODEL_DIR`; metadata lives in PostgreSQL.
- Loaded model artifacts are cached in process memory by store id, model version, artifact path, and file mtime. A newly trained model gets a new version/path, and an overwritten artifact gets a new mtime, so stale cache entries are naturally bypassed.
- `queue_tokens.calculation_method` records whether the token used `ML_PREDICTED` or `RULE_BASED`.

Trial ML flow:

```text
Admin UI /app/trial/admin/ml?store_id={store_id}
  -> POST /api/v1/ml/trial/stores/{store_id}/train
    -> TrialMLTrainingService
      -> TrialRepository validates store
      -> TrialRepository loads completed trial_queue_tokens
      -> service duration = completed_at - service_started_at
      -> trainer builds features from trial zone load, active studios, recent trial history, local time, trial calendar events, zone/studio types, zone gender, and customer type
      -> trainer fits RandomForestRegressor model
      -> artifact is written under ML_MODEL_DIR/trial_store_{store_id}
      -> metadata is saved in ml_model_metadata with model_type=random_forest_trial_service_time_v1
```

During `POST /api/v1/trial/queue/join`, `TrialService` asks `TrialPredictionService` for a service-time prediction after selecting the best studio. If a READY trial artifact exists and prediction succeeds, `trial_queue_tokens.service_time_minutes` uses the ML result and `calculation_method=ML_PREDICTED`; otherwise the existing trial store config remains the `RULE_BASED` fallback.

## 11. Background Jobs

Recommended background jobs:

| Job | Frequency / Trigger | Purpose |
| --- | --- | --- |
| Alert scheduler | Every 30 seconds | Check wait-time, token-ahead, and utilization alerts |
| ML retraining check | After checkout completion | Retrain when enough new completed records exist |
| Demo seed job | Manual script | Create demo store, sections, counters, history, and active queue |
| Demo Tools ML seed API | Manual protected API | Create and clean isolated checkout/trial ML training data |
| Nightly queue cleanup | Daily at 00:05 local deployment time | Cancel active Checkout and Trial tokens and reset counter/studio availability after store close |
| Next-soon notification scan | Every 1 minute | Send one mock SMS when Checkout/Trial tokens reach lane position 2 |

Nightly queue cleanup can run in-process through APScheduler when `ENABLE_IN_APP_SCHEDULER=true`. The default settings run it daily at `00:05` in `SCHEDULER_TIMEZONE`:

```text
ENABLE_IN_APP_SCHEDULER=true
NIGHTLY_QUEUE_CLEANUP_HOUR=0
NIGHTLY_QUEUE_CLEANUP_MINUTE=5
SCHEDULER_TIMEZONE=Asia/Kolkata
```

The same cleanup remains available as an external-scheduler entrypoint:

```bash
cd backend
python3 -m app.scripts.nightly_queue_cleanup
```

The job calls `QueueCleanupService.run_nightly_cleanup()`, marks all `WAITING`, `CALLED`, and `SERVING` checkout/trial tokens as `CANCELLED` with reason `Nightly queue cleanup`, and resets `counters.next_available_time` plus `trial_studios.next_available_time` to the cleanup timestamp. For production deployments with multiple API workers, prefer disabling the in-app scheduler and scheduling the script with cron or a container scheduler, for example:

```cron
5 0 * * * cd /path/to/backend && python3 -m app.scripts.nightly_queue_cleanup
```

For production, move scheduled work to Celery, RQ, APScheduler, or a separate worker container.

Customer notifications use `NotificationService` with a mock SMS client in v1. Checkout and Trial `CALLED` status transitions send `TOKEN_CALLED` when the store notification config is enabled. APScheduler also runs a one-minute `NEXT_SOON` scan that finds position-2 tokens in each counter/studio lane and writes one notification log per token/type.

## 12. Security and Validation

Important validations:

- Store number must be unique.
- Phone number must be exactly 10 digits.
- User passwords must be stored as salted hashes, never as plain text.
- Access tokens must be signed and time-limited.
- Refresh tokens must be stored hashed and revoked on logout.
- Checkout section password must be exactly 6 characters if the legacy section-code flow is still enabled.
- Duplicate active tokens for the same phone number should be rejected where applicable.
- Admin and cashier actions should require authenticated bearer tokens.
- Customer token lookup should return only customer-safe queue information.
- CORS should be restricted to trusted frontend domains in production.

## 13. Deployment Architecture

Recommended local Docker Compose services:

```text
frontend
backend
postgres
redis, optional
```

Recommended persistent volumes:

```text
postgres_data
ml_models
```

Startup order:

```text
postgres healthcheck passes
  -> backend starts and applies migrations or creates tables
    -> frontend starts and calls backend API
```

## 14. Initial Implementation Milestones

1. Create backend FastAPI skeleton with database connection, health check, and route registration.
2. Create SQLAlchemy models and Alembic migrations for stores, sections, counters, staff, and queue tokens.
3. Implement store management APIs.
4. Implement customer queue join, status lookup, and cancellation.
5. Implement cashier login and dashboard workflow.
6. Implement rule-based wait-time prediction.
7. Create React/Vite frontend pages for customer, cashier, and admin flows.
8. Add alert configuration and scheduler.
9. Add analytics endpoints and dashboard charts.
10. Add ML training, metadata, model caching, and ML-assisted prediction.
11. Add demo seed scripts and Docker Compose.
12. Add tests for service logic, repositories, and critical API flows.
