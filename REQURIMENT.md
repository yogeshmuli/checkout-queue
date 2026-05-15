# Checkout Queue App Requirements and Specifications

Derived from `REQUIREMENTS_AND_SPECS.md`, adapted for a retail checkout/billing queue instead of a trial-room queue.

## 1. Product Overview

The Checkout Queue App is a retail queue management platform for store checkout counters. It lets customers join a billing queue, receive a token and estimated checkout wait time, track or cancel their token, and lets cashiers or floor staff call customers to available counters. Store administrators can configure stores, checkout sections, billing counters, cashier staff, queue rules, alerts, calendars, and machine-learning checkout-time prediction.

Primary value proposition:

- Reduce checkout crowding and uncertainty.
- Let customers continue shopping until their billing turn is near.
- Improve cashier utilization and billing-lane throughput.
- Provide live queue visibility, alerts, and operational analytics.
- Use rule-based or machine-learning estimates for checkout service time.

## 2. User Roles

### Customer

- Selects or is assigned a store context.
- Joins a checkout queue by entering phone number, basket size/item count, optional cart type, and shopping status.
- Receives token number, queue position, assigned checkout section if applicable, and estimated wait time.
- Tracks token status by phone number.
- Cancels a waiting token with a reason.
- Receives SMS, WhatsApp, or call notifications when the turn is near.

### Cashier / Checkout Attendant

- Logs in using store number, checkout section/counter login code, and password.
- Views the checkout dashboard for assigned counters or section.
- Sees waiting, called/serving, completed, and cancelled tokens.
- Calls the next customer.
- Assigns a token to a billing counter.
- Updates basket/item count when needed.
- Marks checkout as completed.
- Monitors active counters and predicted billing finish times.

### Store Admin / Manager

- Creates and selects stores.
- Manages store profile and contact information.
- Configures store calendar, holidays, rush days, and promotion/sale dates.
- Creates checkout sections and billing counter types.
- Adds and deletes cashier/staff records.
- Configures queue segmentation, token rules, pooling, and prediction method.
- Configures customer alerts and escalation alerts.
- Triggers ML model training and views ML metadata.
- Reviews live checkout dashboard and historic analytics.

### Support User

- Submits a support ticket through the app/API.

## 3. Functional Requirements

### Store Management

- System must list all stores.
- System must create a store with store number, name, address, manager contact, and SPOC contact.
- System must prevent duplicate store numbers.
- System must read, update, and delete a store.
- System must persist store-related calendar, queue, alert, checkout sections, counters, staff, and checkout queue entries.

### Store Calendar

- System must configure working days as all days or custom days.
- System must store opening and closing time.
- System must support holiday configuration by manual selection, CSV upload, or calendar API mode.
- System must support promotion, sale, and peak-event dates.
- Promotion/sale dates must be available as prediction and analytics features.

### Checkout Sections and Counters

- System must support configurable checkout sections, for example:
  - regular checkout
  - express checkout
  - self-checkout
  - returns/exchange counter
  - priority checkout
- Each section must have a login code or name and a 6-character password for attendant access.
- Sections can be active or inactive.
- Each section can contain one or more billing counter types.
- Counter type configuration must include total counters, active counters, and inactive counters.
- System must create, update, read, and delete checkout sections and counter types.

### Staff Management

- System must add staff/cashiers to a store.
- Staff must include name, phone number, and optional assigned checkout section or counter.
- System must delete staff.
- System should track staff history such as assignment changes, login events, and counter activity.

### Customer Checkout Queue Join

- Customer must provide:
  - `store_id`
  - checkout `section_id` or selected queue type when applicable
  - 10-digit phone number
  - optional item count or basket size
  - optional cart/basket type
  - whether still shopping
  - optional customer type, such as regular, priority, senior, staff-assisted
- System must reject duplicate active checkout tokens for the same phone number where applicable.
- System must generate a token number.
- System must calculate queue position.
- System must calculate estimated checkout wait time using configured prediction method.
- System must return the calculation method used for the estimate.
- System should send WhatsApp/SMS notification when notification configuration is available.

### Queue Status

- System must provide store-wide checkout queue status.
- Queue status must include:
  - checkout section id/name
  - now serving token or tokens
  - waiting list
  - estimated wait time in minutes
  - total/active counters
  - last token and last token wait time
  - total cancellations/no-shows
  - cancellations in last hour
  - counter utilization

### Cashier Workflow

- Cashier must log in with store number, checkout section/counter name, and password.
- System must return section/counter data on successful login.
- Cashier dashboard must show:
  - section metadata
  - generated counter states
  - waiting list
  - cancelled list
  - completed list
  - active serving tokens
- Cashier can call next customer in a checkout section.
- Cashier can assign a token to a billing counter.
- Cashier can update item count or basket size for a token.
- Cashier can mark a checkout as completed.
- Completion should queue automatic ML retraining checks in the background.

### Token Status and Cancellation

- Customer can fetch active token status by phone number.
- Token status must include token number, checkout section, status, position, wait time, item count/basket size, store id, section id, and calculation method.
- Customer can cancel a token with a reason.
- Cancelled tokens should be marked `CANCELLED`, store reason/timestamp, and return a response with negative or empty position/wait placeholders.

### Alerts and Notifications

- Store alert config must support:
  - alert by wait time
  - alert by token-ahead count
  - alert when checkout counter utilization is high
  - customer alert mode: SMS, WhatsApp, or call
  - escalation recipient name/phone
  - escalation alert mode
- Backend scheduler must run alert checks every 30 seconds.
- WhatsApp webhook must accept customer replies and update queue/customer reply state.
- System should support reminder messages when a customer is close to being called.

### Analytics

- Dashboard must support live view, historic analysis, and foresights/segmented view.
- Historic analytics must support a configurable day range.
- Analytics response must include:
  - daily checkout trends
  - section/counter stats
  - basket-size or item-count stats
  - cashier/staff throughput stats where available
  - weekly stats
  - hourly stats
  - promotion/sale day stats
  - cancellation/no-show stats
  - ML insights when available

### Machine Learning

- System must train a store-specific model when enough completed checkout history exists.
- Minimum training sample size: 50 completed checkout records.
- Model predicts checkout service time, not the full queue wait by itself.
- Full wait estimate is calculated separately using queue state, active counters, and predicted service times of customers ahead.
- Features should include:
  - item count or basket size
  - people waiting
  - total items in queue
  - average items per customer
  - people currently being served
  - active counters
  - counter utilization rate
  - recent cancellation/no-show rate
  - average checkout service time
  - check-in hour
  - day of week
  - promotion/sale day flag
  - checkout section type
  - optional payment mode if captured
- Model metadata must include last trained time, sample size, MAE, R2 score, accuracy score, feature importance, and data quality score.
- If model is unavailable or prediction fails, system must fall back to non-ML calculation.

### Demo and Seed Data

- Docker setup must support an initialization script that:
  - creates a default store
  - creates checkout sections and counters
  - generates at least 30 days of completed checkout history
  - injects an active checkout queue
  - trains ML models
- Demo scripts must support cleaning active checkout queue and reinjecting live queue data.

## 4. Non-Functional Requirements

### Performance

- Dashboard requests should complete within 15 seconds.
- Frontend token status should auto-refresh every 5 seconds after a successful lookup.
- Alert scheduler should run every 30 seconds.
- ML models should be cached in memory after first load.
- Queue updates should feel near real-time for cashier and customer views.

### Reliability

- Backend must create database tables on startup.
- Docker Compose must use database healthchecks before backend startup.
- ML model files and database data must persist through Docker volumes.
- API must return structured HTTP errors for not found, duplicate active token, invalid credentials, and insufficient ML data cases.
- Queue completion and cancellation must be idempotent enough to avoid duplicate state transitions from repeated clicks.

### Security

- Checkout section/counter passwords must be constrained to 6 characters unless replaced by stronger auth.
- Phone numbers must be constrained to 10 digits for the India-focused implementation.
- Admin and cashier capabilities should require authenticated sessions in production.
- CORS should be restricted for production deployments.
- Customer token lookup should expose only queue data required for the customer experience.

### Usability

- Frontend must provide responsive pages for customer kiosk/mobile use, cashier dashboard, admin settings, status tracking, help/FAQ/contact, and dashboard views.
- Customer status and cashier views should visibly indicate whether an estimate is AI-based or standard/rule-based.
- Cashier screens must emphasize speed: call next, assign counter, update item count, and complete checkout should be reachable with minimal clicks.
- Customer screens must be simple enough for self-service usage in-store.

## 5. Technical Specifications

### Architecture

- Frontend: Next.js, React, TypeScript, Tailwind CSS, motion/animation library, icon library, charting library.
- Backend: FastAPI or equivalent REST API, ORM, schema validation, background scheduler.
- Database: PostgreSQL for production and Docker; local development may use SQLite only for quick demos.
- ML: pandas/scikit-learn-compatible training pipeline, persisted model files, metadata JSON files.
- Notifications: Twilio or equivalent SMS/WhatsApp/call integration.
- Containerization: Docker Compose with backend, frontend, database, and persistent model/database volumes.

### Suggested Frontend Routes

- `/` - launch page.
- `/store-selector` - store selection.
- `/create-store` - create store flow.
- `/store-config` - store settings, checkout sections, counters, staff, queue and alerts.
- `/customer-check-in` or `/checkout-join` - customer checkout queue registration.
- `/check-status` - customer token tracking and cancellation.
- `/cashier-view` - cashier login and counter operations.
- `/dashboard` - live checkout dashboard, historic analytics, foresights.
- `/help`, `/faq`, `/contact`, `/terms`, `/privacy` - support/legal/help pages.

### Suggested Backend API Base

All backend routes should be mounted under `/api`.

Suggested checkout-specific endpoints:

- `GET /api/stores/`
- `POST /api/stores/`
- `GET /api/stores/{store_id}`
- `PUT /api/stores/{store_id}`
- `DELETE /api/stores/{store_id}`
- `POST /api/stores/{store_id}/queue-config`
- `POST /api/stores/{store_id}/calendar`
- `POST /api/stores/{store_id}/promotion-calendar`
- `POST /api/stores/{store_id}/alert-config`
- `POST /api/stores/{store_id}/checkout-sections`
- `GET /api/stores/{store_id}/checkout-sections`
- `GET /api/checkout-sections/{section_id}`
- `PUT /api/checkout-sections/{section_id}`
- `DELETE /api/checkout-sections/{section_id}`
- `POST /api/checkout-sections/{section_id}/counter-types`
- `PUT /api/counter-types/{counter_type_id}`
- `DELETE /api/counter-types/{counter_type_id}`
- `GET /api/stores/{store_id}/staff`
- `POST /api/stores/{store_id}/staff`
- `DELETE /api/staff/{staff_id}`
- `POST /api/checkout/check-in`
- `GET /api/stores/{store_id}/checkout-status`
- `POST /api/cashier-login`
- `GET /api/cashier-dashboard/{section_id}`
- `POST /api/checkout-sections/{section_id}/call-next`
- `POST /api/checkout/assign-token`
- `PUT /api/checkout/update-items/{token_number}`
- `POST /api/checkout/complete/{token_number}`
- `GET /api/checkout/status/{phone_number}`
- `POST /api/whatsapp-webhook`
- `POST /api/checkout/cancel`
- `GET /api/stores/{store_id}/analytics?days={days}`
- `POST /api/stores/{store_id}/train-models`
- `GET /api/stores/{store_id}/ml-metadata`
- `POST /api/support/ticket`

### Core Data Model

Primary tables/models:

- `store_details`
- `store_calendar`
- `checkout_sections`
- `counter_types`
- `staff`
- `staff_history`
- `queue_config`
- `alert_config`
- `checkout_queue_entries`
- `cashier_logins`

Suggested enums:

- Checkout section type: `Regular`, `Express`, `Self Checkout`, `Returns`, `Priority`
- Working days type: `All Days of Week`, `Custom`
- Holiday config type: manual calendar, holiday CSV, calendar API
- Queue segmentation: separate by section, pooled checkout queue, express versus regular, priority queue
- Alert logic: wait time, token ahead, counter utilization
- Alert mode: SMS, WhatsApp, call
- Queue status: `WAITING`, `SERVING`, `COMPLETED`, `CANCELLED`, `NO_SHOW`
- Prediction method: `machine_learning`, `Rule Based`, `AI - Random Forest`, `AI - XGBoost`

### Deployment Specs

Docker Compose should include:

- `backend`
  - exposes a stable backend host port
  - runs the API server
  - persists ML models in a named volume
- `frontend`
  - exposes a stable frontend host port
  - points to the backend API using environment configuration, not a hardcoded URL
- `db`
  - PostgreSQL
  - uses healthcheck
  - persists data in a named volume

Expected local URLs should be documented in the project README and kept aligned with actual code configuration.

## 6. Migration Notes From Trial Queue to Checkout Queue

- Rename trial-room language to checkout language:
  - trial zone -> checkout section
  - studio/trial room -> billing counter
  - attendant -> cashier or checkout attendant
  - trial completion -> checkout completion
  - items to try -> basket item count
- Rework ML target from trial-room service time to checkout billing service time.
- Replace gender-based trial segmentation with checkout section/priority/basket-size segmentation.
- Preserve reusable modules where practical:
  - store management
  - queue token generation
  - status tracking
  - alerts
  - analytics
  - ML metadata
  - Docker setup
- Update UI labels, route names, database table names, API endpoint names, and seed/demo scripts.
- Keep both product specs separate until implementation begins, so trial queue and checkout queue can be compared cleanly.

## 7. Acceptance Criteria

- A store admin can create/select a store and configure checkout sections, counters, staff, calendar, queue, and alerts.
- A customer can join a checkout queue and receive a token, position, and wait estimate.
- The system rejects duplicate active checkout tokens where applicable.
- A customer can track checkout token status by phone number with live refresh.
- A customer can cancel a waiting checkout token with a reason.
- A cashier can log into a checkout section, call next, assign tokens to counters, update item count, and mark checkout complete.
- Store dashboard shows live checkout queue/counter data and historic analytics.
- ML training succeeds when at least 50 valid completed checkout records exist.
- ML metadata is available after successful training.
- System falls back to rule-based estimates when ML model is missing or fails.
- Docker startup plus setup script produces a usable checkout-queue demo instance.
