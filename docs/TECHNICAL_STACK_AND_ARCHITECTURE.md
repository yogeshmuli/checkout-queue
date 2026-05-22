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
- Fall back to rule-based prediction if ML is unavailable

The ML model should predict checkout service time for a customer. Full queue wait time should be calculated separately using:

- Customers ahead in queue.
- Active counters.
- Current serving tokens.
- Predicted service time per waiting customer.
- Recent cancellation/no-show behavior.

## 6. Suggested Database Tables

| Table | Purpose |
| --- | --- |
| `users` | Login identity, password hash, default role, account status, and optional operational assignment fields (`store_id`, `section_id`, `assigned_counter_id`) |
| `user_store_access` | User-to-store role mapping for admins, managers, and cashiers |
| `refresh_tokens` | Hashed refresh tokens for revocation and session lifecycle |
| `stores` | Store profile, store number, contact details |
| `store_calendars` | Working days and open/close time |
| `store_holidays` | Holiday dates |
| `store_events` | Promotion, sale, and peak-event dates |
| `checkout_sections` | Checkout sections with enum-backed type: regular, express, self-checkout, returns, priority |
| `counter_types` | Counter type counts and active/inactive counters |
| `queue_tokens` | Customer checkout queue entries |
| `queue_status_events` | Token state transitions for audit and analytics |
| `alert_configs` | Wait-time, token-ahead, utilization, and escalation settings |
| `notification_logs` | SMS, WhatsApp, call notification attempts |
| `support_tickets` | Customer or staff support tickets |
| `ml_model_metadata` | Store model training metadata |

## 7. API Surface

Recommended API prefix:

```text
/api/v1
```

Suggested endpoint groups:

```text
/api/v1/stores
/api/v1/auth
/api/v1/stores/{store_id}/calendar
/api/v1/stores/{store_id}/sections
/api/v1/stores/{store_id}/staff
/api/v1/queue
/api/v1/cashier
/api/v1/alerts
/api/v1/analytics
/api/v1/ml
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
POST   /api/v1/stores/{store_id}/sections
POST   /api/v1/stores/{store_id}/staff
GET    /api/v1/analytics/stores/{store_id}
POST   /api/v1/ml/stores/{store_id}/train
```

## 8. Frontend Application Structure

The React app should be organized around user roles:

- Customer pages for queue joining, token lookup, cancellation, support, FAQ, and contact.
- Cashier pages for login and live queue operations.
- Admin pages for store setup, sections, counters, staff, alerts, analytics, and ML model metadata.

Implemented frontend routing:

```text
/
/app
/app/admin
/app/admin/stores
/app/admin/sections
/app/admin/counters
/app/admin/staff
/app/admin/queue
/app/admin/calendar
/app/admin/alerts
/app/staff
/app/customer
```

Frontend API handling should be centralized under `src/api/` so pages and components do not manually build URLs or duplicate error handling.

Current frontend implementation:

- `AdminApp` provides the admin portal shell and dashboard view.
- `AdminStores` connects to the implemented store APIs.
- `StaffApp` provides a mobile-first counter operations console integrated with auth and queue transition APIs.
- `CustomerApp` connects to `POST /api/v1/queue/join`, displays token details after enrollment, and polls token status.
- `RoleRedirect` lets a user open the admin, staff, or customer workspace and keeps the preferred role in Zustand/local storage.

## 9. Request Flow Examples

### Customer Joins Queue

```text
React Join Queue Page
  -> POST /api/v1/queue/join
    -> queue_routes.py
      -> queue_service.py
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
- People waiting.
- Total items in queue.
- Average items per customer.
- Active counters.
- Counter utilization rate.
- Recent cancellation/no-show rate.
- Check-in hour.
- Day of week.
- Promotion/sale day flag.
- Checkout section type.

Output:

- Predicted service time for the customer.
- Prediction metadata such as method, model version, and confidence-related fields where available.

The queue wait estimate should combine predicted service times for customers ahead of the current customer and divide expected workload across active counters.

## 11. Background Jobs

Recommended background jobs:

| Job | Frequency / Trigger | Purpose |
| --- | --- | --- |
| Alert scheduler | Every 30 seconds | Check wait-time, token-ahead, and utilization alerts |
| ML retraining check | After checkout completion | Retrain when enough new completed records exist |
| Demo seed job | Manual script | Create demo store, sections, counters, history, and active queue |
| Queue cleanup job | Manual or scheduled | Mark stale called tokens as no-show if required |

For production, move scheduled work to Celery, RQ, APScheduler, or a separate worker container.

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
