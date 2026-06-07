# Checkout Queue Feature Tracker

This document tracks implemented backend capabilities from a user-story and API point of view.

## Current Status

The backend currently supports:

- Application health check.
- PostgreSQL-backed SQLAlchemy model setup.
- Database sync script.
- Alembic migration setup.
- User authentication.
- Store management APIs.
- Section management APIs.
- Staff management APIs.
- Store queue configuration APIs.
- Store calendar APIs.
- Store customer notification config and logs APIs.
- Trial Queue module APIs behind `ENABLE_TRIAL_QUEUE`.
- Demo Tools APIs behind `ENABLE_DEMO_TOOLS` for isolated ML training data.
- Trial admin calendar UI for store-level trial hours, holidays, and event signals.
- ML service-time training and prediction metadata APIs.
- Customer queue enrollment with rule-based wait-time estimate.
- React/Vite frontend scaffold with admin, staff, and customer role views.
- Customer token status lookup and staff queue processing APIs.
- Frontend integration for customer token status refresh and staff token transitions.
- Frontend integration for admin store, section, and staff CRUD flows.
- Frontend post-login product context selector for enabled modules.
- Counter management APIs and frontend admin counter CRUD flow.
- Checkout admin dashboard uses the Smart View layout with Live, History, and Foresights tabs plus Recharts-based history/ML charts.
- Installed PWA shell shows a floating refresh action for manual hard reloads.
- Shared mock-SMS customer notifications for Checkout and Trial called/next-soon events.
- QuT-inspired UI design system with red/blush/navy palette and Poppins/Inter typography.

## Implemented User Stories

### 1. User Can Register

As an admin, manager, cashier, or support user, I can register an account.

Endpoint:

```text
POST /api/v1/auth/register
```

Supported roles:

```text
SUPER_ADMIN
STORE_ADMIN
MANAGER
CASHIER
SUPPORT
TRIAL_ZONE_ASSISTANT
```

Example request:

```json
{
  "email": "admin@example.com",
  "password": "admin12345",
  "full_name": "Store Admin",
  "phone_number": "9876543210",
  "default_role": "STORE_ADMIN"
}
```

Result:

- Creates a user.
- Stores a salted password hash.
- Returns access and refresh tokens.

### 2. User Can Login

As a registered user, I can login and receive tokens.

Endpoint:

```text
POST /api/v1/auth/login
```

Example request:

```json
{
  "email": "admin@example.com",
  "password": "admin12345"
}
```

Result:

- Verifies the password.
- Updates `last_login_at`.
- Returns access and refresh tokens.

### 3. User Can Fetch Current Profile

As an authenticated user, I can fetch my current profile.

Endpoint:

```text
GET /api/v1/auth/me
```

Authentication:

```text
Authorization: Bearer <access_token>
```

### 4. User Can Logout

As an authenticated user, I can revoke a refresh token.

Endpoint:

```text
POST /api/v1/auth/logout
```

Example request:

```json
{
  "refresh_token": "<refresh_token>"
}
```

Result:

- Marks the refresh token as revoked if it exists.
- Returns success even if the token is already unknown.

### 5. Admin Can Create Store

As a store admin, manager, or super admin, I can create a store.

Endpoint:

```text
POST /api/v1/stores
```

Allowed roles:

```text
SUPER_ADMIN
STORE_ADMIN
MANAGER
```

Example request:

```json
{
  "store_number": "STORE-001",
  "name": "Main Checkout Store",
  "address": "MG Road, Pune",
  "manager_name": "Amit Sharma",
  "manager_phone": "9876543210",
  "spoc_name": "Priya Mehta",
  "spoc_phone": "9876543211",
  "is_active": true
}
```

Result:

- Creates a store.
- Rejects duplicate `store_number` with HTTP `409`.

### 6. Admin Can List Stores

As an authorized admin user, I can list stores.

Endpoint:

```text
GET /api/v1/stores
```

Optional query:

```text
GET /api/v1/stores?include_inactive=true
```

Default behavior:

- Returns active stores only.
- Includes inactive stores when `include_inactive=true`.

### 7. Admin Can View Store By ID

As an authorized admin user, I can view a single store.

Endpoint:

```text
GET /api/v1/stores/{store_id}
```

Result:

- Returns store details.
- Returns HTTP `404` when the store does not exist.

### 8. Admin Can Update Store

As an authorized admin user, I can partially update a store.

Endpoint:

```text
PATCH /api/v1/stores/{store_id}
```

Example request:

```json
{
  "name": "Updated Store Name",
  "manager_phone": "9876543212"
}
```

Result:

- Updates only provided fields.
- Rejects duplicate `store_number` with HTTP `409`.
- Returns HTTP `404` when the store does not exist.

### 9. Admin Can Soft Delete Store

As an authorized admin user, I can deactivate a store.

Endpoint:

```text
DELETE /api/v1/stores/{store_id}
```

Result:

- Sets `is_active = false`.
- Does not physically delete the store row.

### 10. Customer Can Join Checkout Queue

As a customer, I can join a checkout queue and receive a token number, queue position, and estimated wait time.

Endpoint:

```text
POST /api/v1/queue/join
```

Authentication:

```text
Public endpoint
```

Example request:

```json
{
  "store_id": 1,
  "section_id": 1,
  "phone_number": "9876543210",
  "item_count": 12,
  "basket_size": "medium",
  "cart_type": "basket",
  "is_still_shopping": true,
  "customer_type": "regular"
}
```

Example response:

```json
{
  "token_id": 1,
  "token_number": "S1-C1-001",
  "store_id": 1,
  "section_id": 1,
  "status": "WAITING",
  "position": 1,
  "estimated_wait_minutes": 0,
  "calculation_method": "RULE_BASED"
}
```

Result:

- Validates active store.
- Validates active checkout section when `section_id` is provided.
- Rejects duplicate active token for the same phone number in the same store with HTTP `409`.
- Creates a `WAITING` queue token.
- Resolves an effective item count before allocation: explicit `item_count`, otherwise basket-derived values (`small=9`, `medium=20`, `large=30`), otherwise store `default_item_count` when the customer is still shopping.
- Filters active counters by optional counter basket allocation bands before assignment: `SMALL` for fewer than 10 items, `MEDIUM` for 10-20 items, and `LARGE` for more than 20 items; unrestricted counters accept any item count.
- Generates token numbers with store/section token prefix plus the selected counter prefix and a per-counter sequence, for example `BILL-C1-001`.
- Supports a store-level shared queue mode where customers join one section queue, tokens remain unassigned until staff pulls them, token numbers use `{TokenPrefix}-Q-001`, and wait estimates simulate assignment to the earliest eligible active counter.
- Calculates queue position from waiting tokens ahead.
- Calculates estimated wait time from waiting tokens ahead, their item counts, active counters, and store-level service-time configuration.
- Uses the store token prefix configuration when generating token numbers.
- Blocks new token creation when the store calendar marks the store closed or today is an active holiday.
- Stores the resolved item count so later customers get better estimates.
- Rejects queue creation when no active counter is available for the requested basket size.

### 10A. Admin Can Configure Store Queue Rules

As an authorized admin or manager, I can configure token and service-time rules per store.

Endpoint:

```text
GET /api/v1/stores/{store_id}/config
PUT /api/v1/stores/{store_id}/config
```

Allowed roles:

```text
SUPER_ADMIN
STORE_ADMIN
MANAGER
```

Example request:

```json
{
  "token_id_prefix": "BILL",
  "base_service_minutes": 6,
  "per_item_service_minutes": 0.5,
  "min_service_minutes": 8,
  "default_item_count": 10,
  "shared_queue_enabled": false
}
```

Result:

- Stores queue configuration in the separate `store_configs` table.
- Auto-creates a default config for stores that do not have one yet.
- Applies the configured token prefix to new queue tokens.
- Applies configured base, per-item, and minimum service minutes to queue wait-time calculation.
- Applies the default item count when still-shopping customers provide neither item count nor basket size.
- Toggles shared section queue mode for stores that want counters to pull from one section queue instead of assigning counters at token creation.
- Exposes a frontend admin screen at `/app/checkout/admin/store-config?store_id={store_id}`.

### 11. Staff Can Process Queue Token Events

As cashier or manager-facing staff, I can update queue token lifecycle events such as called, serving, completed, and cancelled.

Endpoint:

```text
POST /api/v1/queue/events
POST /api/v1/queue/tokens/{token_id}/start
POST /api/v1/queue/tokens/{token_id}/complete
POST /api/v1/queue/tokens/{token_id}/cancel
```

Allowed roles:

```text
SUPER_ADMIN
STORE_ADMIN
MANAGER
CASHIER
```

Result:

- Updates queue token status for `CALLED`, `SERVING`, `COMPLETED`, and `CANCELLED` events.
- Sets event timestamps (`called_at`, `completed_at`, `cancelled_at`) and cancellation reason when applicable.
- Returns updated token event state for frontend synchronization.

### 12. Customer Can Track Token Status

As a customer, I can fetch current token status after creating a token.

Endpoint:

```text
GET /api/v1/queue/status?token_id={token_id}
GET /api/v1/queue/status?store_id={store_id}&phone_number={phone_number}
```

Result:

- Returns current token status, assigned counter, position, calling time, and computed wait minutes.
- Frontend customer view refreshes this status every 30 seconds and includes a compact manual refresh icon on the token status card.

### 13. Staff Can View And Update Counter Queue

As counter staff, I can view tokens assigned to my counter and set counter status.

Endpoints:

```text
GET   /api/v1/queue/counters/{counter_id}/tokens
PATCH /api/v1/queue/counters/{counter_id}/status
```

Result:

- Returns active counter queue tokens.
- Lets staff mark a counter active or inactive.
- Staff frontend uses these APIs after login.

### 14. User Can Open Role-Based Frontend Views

As a user, I can open a role-specific frontend workspace.

Routes:

```text
/
/app
/app/login
/app/checkout/admin
/app/checkout/staff
/app/checkout/customer
```

Result:

- Landing page presents Checkout Queue and Trial Queue as available product modules.
- Landing page "Open Workspace" sends users to `/app` so the context selector chooses the target module.
- Landing page displays a shared Equilateral footer with placeholder Terms, Privacy, Contact, and FAQ links.
- `/app/checkout/customer` remains public and does not require authentication.
- `/app/login` is a shared login screen for admin and staff users.
- Authenticated admin users can access admin and staff workspaces and see all three workspace options.
- Authenticated staff users are routed directly to the staff workspace.

### 15. Admin Can Manage Stores From Frontend

As an admin, I can open the store management screen and call implemented store APIs.

Route:

```text
/app/checkout/admin/stores
```

Result:

- Lists stores through `GET /api/v1/stores`.
- Creates stores through `POST /api/v1/stores`.
- Updates store details and active state through `PATCH /api/v1/stores/{store_id}`.
- Soft-deletes stores through `DELETE /api/v1/stores/{store_id}`.
- Applies frontend field validation aligned with backend constraints (required store number/name, max-length checks, 10-digit phone validation).
- Includes search/filter and pagination on the admin store directory screen.
- Warns users about unsaved form changes when leaving edit mode.

### 15A. Admin Can Manage Sections From Frontend

As an admin, I can create, list, update, activate/deactivate checkout sections mapped to stores.

Route:

```text
/app/checkout/admin/sections
```

Result:

- Lists sections through `GET /api/v1/sections`.
- Creates sections through `POST /api/v1/sections`.
- Updates section details and active state through `PATCH /api/v1/sections/{section_id}`.
- Soft-deletes sections through `DELETE /api/v1/sections/{section_id}`.
- Enforces store linkage in UI and backend (`store_id` is required for sections).
- Constrains section type to `REGULAR`, `EXPRESS`, `SELF_CHECKOUT`, `RETURNS`, or `PRIORITY` and presents those choices as a dropdown in the admin UI.
- Supports shareable store-filtered section links with `/app/checkout/admin/sections?store_id={store_id}`.
- Store and section rows link to related sections, counters, staff, and queue views with matching URL filters.

### 15B. Admin Can Manage Staff From Frontend

As an admin, I can create, list, update, activate/deactivate staff users and assign them to stores, sections, checkout counters, and trial zones.

Route:

```text
/app/checkout/admin/staff
```

Result:

- Lists staff through `GET /api/v1/staff`.
- Creates staff through `POST /api/v1/staff`.
- Updates staff details, role, assignment, password, and active state through `PATCH /api/v1/staff/{staff_id}`.
- Soft-deletes staff through `DELETE /api/v1/staff/{staff_id}`.
- Stores staff passwords only as salted hashes.
- Uses `Ganesh@123` as the admin UI default password when the create-staff password field is left blank.
- Validates duplicate email/phone and assignment consistency across store, section, counter, and studio.
- Enforces role-based assignment rules:
  - `TRIAL_ZONE_ASSISTANT` can be assigned only to trial zones (not checkout counters).
  - Non-trial roles can be assigned only to checkout counters (not trial zones).
  - Counter and studio assignment are mutually exclusive.
  - Studio assignment must belong to the selected store.
- Requires `TRIAL_ZONE_ASSISTANT` staff to have an assigned trial zone so Trial staff login can route to a usable workspace.
- Clears incompatible saved assignments during role updates, so changing a checkout staff member to `TRIAL_ZONE_ASSISTANT` removes stale checkout section/counter values before validating the trial zone assignment.
- Includes frontend field validation, search/filter, pagination, unsaved-change confirmation, and active/inactive status controls.
- Supports staff API filtering by `store_id`, `section_id`, `counter_id`, and Trial `zone_id`; Checkout admin shareable staff links remain store-, section-, and counter-filtered.
- Staff rows link back to related store sections, section counters, counter staff, studio staff, and queue views.

### 15C. Admin Can Manage Counters From Frontend

As an admin, I can create, list, update, and activate/deactivate counters mapped to sections.

Route:

```text
/app/checkout/admin/counters
```

Result:

- Lists counters through `GET /api/v1/counters`.
- Creates counters through `POST /api/v1/counters`.
- Updates counter details and active state through `PATCH /api/v1/counters/{counter_id}`.
- Soft-deletes counters through `DELETE /api/v1/counters/{counter_id}`.
- Enforces section linkage in UI and backend (`section_id` is required for counters).
- Constrains counter type to `REGULAR`, `EXPRESS`, `SELF_CHECKOUT`, `RETURNS_EXCHANGE`, or `PRIORITY` and presents those choices as a dropdown in the admin UI.
- Supports optional alphanumeric counter token prefixes, normalized to uppercase and unique within a section; blank prefixes fall back to `C{counter_id}`.
- Supports optional multi-band basket allocation (`SMALL`, `MEDIUM`, `LARGE`) so counters can be restricted to selected item-count ranges; blank allocation means any basket size.
- Supports store-filtered section selection in the admin form.
- Includes frontend field validation, search/filter, pagination, unsaved-change confirmation, and active/inactive status controls.
- Supports shareable section-filtered counter links with `/app/checkout/admin/counters?section_id={section_id}`.
- Supports shareable store-filtered counter links with `/app/checkout/admin/counters?store_id={store_id}`.
- Counter rows link to related section counters, assigned staff, and queue views.

### 16. Customer Can Create And Track Token From Frontend

As a customer, I can enter checkout details and create a queue token from the mobile view.

Route:

```text
/app/checkout/customer
```

Result:

- Shows a first-step customer screen to select store/section before opening token creation.
- Shows active stores in a dropdown and populates section dropdown based on selected store.
- Loads store/section options from public API `GET /api/v1/queue/store-sections`.
- Includes active stores even when no section is configured yet (section remains optional for that case).
- Uses QR-only store entry with browser-camera scanning or gallery image upload; the manual store/section selection form is hidden from customers, and a valid Checkout customer QR redirects to its complete encoded URL.
- Supports installable PWA behavior with manifest/service-worker caching for home-screen install.
- Calls `POST /api/v1/queue/join`.
- Allows customer cancellation from token status through `POST /api/v1/queue/tokens/{token_id}/customer-cancel` with a reusable in-app confirmation modal.
- Allows customers with `WAITING` or `CALLED` tokens to move to the end of the same counter lane through `POST /api/v1/queue/tokens/{token_id}/customer-move-last`; the old token is cancelled and the replacement token opens automatically.
- Allows token lookup by mobile number from customer screen and navigation between lookup and token status views.
- Applies a shared top branding header across app routes (`/app/*`) for consistent QuT identity.
- Displays token number, queue position, current status, calling time, estimated wait, and calculation method.
- Polls `GET /api/v1/queue/status` every 30 seconds after token creation.

### 17. Staff Can Process Counter Queue From Frontend

As staff, I can login, view my counter queue, start the next token, complete a serving token, cancel tokens, and toggle counter active state.

Route:

```text
/app/checkout/staff
```

Result:

- Logs in through `POST /api/v1/auth/login`.
- Loads counter queue through `GET /api/v1/queue/counters/{counter_id}/tokens`.
- Starts, completes, and cancels tokens through queue transition APIs.
- Updates counter status through `PATCH /api/v1/queue/counters/{counter_id}/status`.

### 18. Admin Can View And Manage Live Queue

As an admin or manager, I can view live queue tokens across stores, sections, and counters, filter the list, and move tokens through operational states.

Route:

```text
/app/checkout/admin/queue
```

Result:

- Lists queue tokens through `GET /api/v1/queue/tokens`.
- Filters queue tokens by store, section, counter, and token status.
- Shows token number, phone number, position, wait time, assignment, calling time, and item count.
- Lets admin call, start, complete, or cancel tokens from the admin queue screen.
- Uses bearer-token role guards for queue management actions.
- Queue filters are URL-backed so links from store, section, counter, and staff rows open the matching queue scope.

### 19. Admin Can Configure Store Calendar

As an authorized admin or manager, I can configure weekly store hours and holiday closures.

Endpoint:

```text
GET /api/v1/stores/{store_id}/calendar
PUT /api/v1/stores/{store_id}/calendar
```

Allowed roles:

```text
SUPER_ADMIN
STORE_ADMIN
MANAGER
```

Result:

- Stores weekly hours in `store_calendar_days`.
- Stores manually configured holiday dates in `store_holidays`.
- Stores calendar events in `store_calendar_events`, including `PROMOTION`, `SALE`, `HOLIDAY`, and `OTHER` event types.
- Seeds stores with always-open calendar defaults so existing queue behavior is preserved.
- Queue join rejects new tokens only when the configured calendar says the store is closed.
- Existing active tokens and staff queue processing continue unaffected.
- Exposes a frontend admin screen at `/app/checkout/admin/calendar?store_id={store_id}`.

### 20. Admin Can Train Store ML Service-Time Model

As an authorized admin or manager, I can train and inspect a store-specific service-time model.

Endpoint:

```text
POST /api/v1/ml/stores/{store_id}/train
GET  /api/v1/ml/stores/{store_id}/metadata
POST /api/v1/ml/stores/{store_id}/predict-service-time
```

Allowed roles:

```text
SUPER_ADMIN
STORE_ADMIN
MANAGER
```

Result:

- Uses completed queue tokens where `service_started_at` and `completed_at` are present.
- Requires at least 50 completed checkout records by default.
- Trains a store-specific RandomForest model artifact in `.joblib` format.
- Uses item count, section busyness, active section counter count, recent cancellation behavior, recent average service time, time of day, day of week, weekend flag, calendar promotion/sale flag, basket size, cart type, customer type, section, and assigned counter as prediction features.
- Persists metadata in `ml_model_metadata`, including trained time, sample size, MAE, R2, accuracy, data quality, and feature importance.
- Caches loaded model artifacts in process memory by store id, model version, artifact path, and file mtime.
- Queue token creation uses `ML_PREDICTED` service minutes when a ready model exists.
- Queue token creation falls back to the existing rule-based service-time calculation when no model is ready or prediction fails.
- Exposes a frontend admin screen at `/app/checkout/admin/ml?store_id={store_id}`.

Flow:

```text
Train model:
Admin ML page -> POST /api/v1/ml/stores/{store_id}/train
  -> MLTrainingService loads completed queue history
  -> service duration is calculated from completed_at - service_started_at
  -> contextual training features are extracted from queue history, section load, recent history, and store calendar events
  -> local model artifact is written under ML_MODEL_DIR
  -> ml_model_metadata stores model status and metrics

Use model:
Customer joins queue -> POST /api/v1/queue/join
  -> QueueService asks PredictionService for service-time prediction
  -> PredictionService reuses cached artifact when available
  -> if READY metadata and artifact work, token uses ML_PREDICTED
  -> otherwise token uses existing RULE_BASED service-time calculation
  -> QueueService still calculates counter assignment, calling_time, position, and wait time

View model:
Admin ML page -> GET /api/v1/ml/stores/{store_id}/metadata
  -> UI shows status, sample size, trained time, MAE, R2, accuracy, and data quality
```

## Implemented Technical Capabilities

### Backend Foundation

- FastAPI application factory.
- Central API router under `/api/v1`.
- CORS middleware.
- Health endpoint.
- PostgreSQL SQLAlchemy engine and session setup.
- `sync_database()` function.
- Manual sync script:

```bash
python3 -m scripts.sync_database
```

### Queue Operations

- Queue service uses deterministic per-counter schedule rebuild for waiting tokens.
- Recomputes `calling_time` from current lane truth (current serving token and pending waiting tokens) after queue lifecycle events.
- Rejects repeated call actions unless the Checkout/Trial token is still `WAITING`, preventing duplicate customer call transitions and duplicate called notifications from stale UI actions.
- Applies post-event queue correction for early/late service completion so downstream waiting times move earlier/later accordingly.
- Reserves lane occupancy for `CALLED` customers until service begins, preventing premature advancement of waiting tokens.
- Prevents additive drift by avoiding incremental delta-shift updates and always recalculating `counters.next_available_time` from the rebuilt queue.
- Queue and counter scheduling timestamps are UTC-aware across model and migration updates.
- Nightly cleanup job cancels all active Checkout and Trial tokens (`WAITING`, `CALLED`, `SERVING`) and resets checkout counter/trial studio availability for close-of-day queue purge.
- Run close-of-day cleanup from backend with `python3 -m app.scripts.nightly_queue_cleanup`; schedule it externally at `00:05` using cron, Kubernetes CronJob, or the deployment scheduler.
- FastAPI can also run the cleanup in-process through APScheduler when `ENABLE_IN_APP_SCHEDULER=true`; defaults run the cleanup daily at `00:05` in `SCHEDULER_TIMEZONE`.

### Customer Notifications

- Per-store notification config controls whether customer SMS notifications are enabled for called and next-soon events.
- Checkout and Trial token `CALLED` transitions create a `TOKEN_CALLED` notification log and send through the mock SMS client when enabled.
- APScheduler scans every minute for lane position `2` Checkout/Trial tokens and creates one `NEXT_SOON` notification per token.
- Notification logs prevent duplicates with `(module_type, token_id, notification_type)` and record `SENT`, `FAILED`, or `SKIPPED` status.
- Checkout and Trial admin workspaces include a Notifications page for config and recent log review.

### Database Models

Implemented models:

- `Store`
- `StoreCalendarDay`
- `StoreCalendarEvent`
- `StoreConfig`
- `StoreHoliday`
- `CheckoutSection`
- `Counter`
- `MLModelMetadata`
- `QueueToken`
- `User`
- `UserStoreAccess`
- `RefreshToken`

Notes:

- Operational assignment fields such as `store_id`, `section_id`, and `assigned_counter_id` are captured on `users`.

Implemented enums:

- `QueueTokenStatus`
- `UserRole`
- `CheckoutSectionType`
- `CounterType`
- `StoreCalendarEventType`

### Alembic Migrations

Implemented migrations:

- `6a025f451096_init.py`
- `20260507_0003_add_calling_time_to_queue_token.py`
- `4f3122197651_recording_service_time_in_token.py`
- `20260508_0004_make_counter_time_utc.py`
- `030389d488c1_removed_waiting_time.py`
- `20260514_0005_remove_staff_table_move_fields_to_users.py`
- `20260522_0006_convert_section_type_to_enum.py`
- `20260522_0007_add_store_configs.py`
- `20260522_0008_convert_counter_type_to_enum.py`
- `20260522_0009_add_store_calendar.py`
- `20260522_0010_add_ml_model_metadata.py`
- `20260522_0011_add_store_calendar_events.py`
- `20260524_0016_add_customer_notifications.py`
- `20260604_0018_add_counter_token_prefix.py`
- `20260604_0019_add_counter_basket_size_bands.py`
- `20260604_0020_add_store_config_default_item_count.py`
- `20260604_0021_add_shared_queue_flag.py`

### Authentication

Implemented:

- Salted password hashing.
- Password verification.
- Signed bearer access tokens.
- Hashed refresh token persistence.
- Refresh token revocation.
- Current user dependency.
- Role guard dependency.

## Implemented API List

### Health

```text
GET /api/v1/health
```

### Auth

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/auth/logout
```

### Stores

```text
POST   /api/v1/stores
GET    /api/v1/stores
GET    /api/v1/stores/{store_id}
PATCH  /api/v1/stores/{store_id}
DELETE /api/v1/stores/{store_id}
GET    /api/v1/stores/{store_id}/config
PUT    /api/v1/stores/{store_id}/config
GET    /api/v1/stores/{store_id}/calendar
PUT    /api/v1/stores/{store_id}/calendar
GET    /api/v1/stores/{store_id}/notification-config
PUT    /api/v1/stores/{store_id}/notification-config
GET    /api/v1/stores/{store_id}/notification-logs
```

### Queue

```text
POST  /api/v1/queue/join
GET   /api/v1/queue/status
GET   /api/v1/queue/store-sections
GET   /api/v1/queue/tokens
POST  /api/v1/queue/events
GET   /api/v1/queue/counters/{counter_id}/tokens
PATCH /api/v1/queue/counters/{counter_id}/status
POST  /api/v1/queue/tokens/{token_id}/start
POST  /api/v1/queue/tokens/{token_id}/complete
POST  /api/v1/queue/tokens/{token_id}/cancel
```

### Sections

```text
POST   /api/v1/sections
GET    /api/v1/sections
GET    /api/v1/sections/{section_id}
PATCH  /api/v1/sections/{section_id}
DELETE /api/v1/sections/{section_id}
```

### Counters

```text
POST   /api/v1/counters
GET    /api/v1/counters
GET    /api/v1/counters/{counter_id}
PATCH  /api/v1/counters/{counter_id}
DELETE /api/v1/counters/{counter_id}
```

### Staff

```text
POST   /api/v1/staff
GET    /api/v1/staff
GET    /api/v1/staff/{staff_id}
PATCH  /api/v1/staff/{staff_id}
DELETE /api/v1/staff/{staff_id}
```

### Machine Learning

```text
POST /api/v1/ml/stores/{store_id}/train
GET  /api/v1/ml/stores/{store_id}/metadata
POST /api/v1/ml/stores/{store_id}/predict-service-time
```

### Analytics

```text
GET /api/v1/analytics/stores/{store_id}?days={days}
```

The store analytics endpoint powers the admin smart dashboard. It returns live queue totals, counter utilization, section and counter breakdowns, live section cards, active counter sessions, last-token wait and item-ahead estimates, daily token trends, weekly/hourly segments, promotion/sale analysis, customer/item segments, calendar signals, latest ML model metadata, and generated operational insights.

Admin dashboard UI now supports URL-filterable store/range/view state with three tabs:

- Live: section-as-zone cards with last token, active/inactive counters, active counter token assignments, estimated wait, estimated items ahead, average wait/items, total cancellations, and last-hour cancellations.
- History: promotion-day, time/day, date-based, section, customer-type, and item-bucket analytics.
- Foresights: ML status, model sample count, churn/utilization signals, operational insights, and active counter pressure links.
- Store-scoped admin screens such as dashboard, config, calendar, ML, and notifications auto-select the first store when no valid `store_id` is present and hide detail forms when there are no stores.

### Trial Queue

```text
GET/POST/PATCH/DELETE /api/v1/trial/zones
GET/POST/PATCH/DELETE /api/v1/trial/studios
GET/PUT           /api/v1/stores/{store_id}/trial-config
GET/PUT           /api/v1/stores/{store_id}/trial-calendar
GET               /api/v1/trial/queue/store-zones
POST              /api/v1/trial/queue/join
GET               /api/v1/trial/queue/status
GET               /api/v1/trial/queue/tokens
POST              /api/v1/trial/queue/events
GET/PATCH         /api/v1/trial/queue/studios/{studio_id}/tokens|status
GET               /api/v1/trial/queue/zones/{zone_id}/studios
POST              /api/v1/trial/queue/tokens/{token_id}/start|complete|cancel
POST              /api/v1/ml/trial/stores/{store_id}/train
GET               /api/v1/ml/trial/stores/{store_id}/metadata
POST              /api/v1/ml/trial/stores/{store_id}/predict-service-time
```

The Trial Queue module shares stores, users, authentication, and role guards with Checkout Queue. It keeps its own zones, studios, configs, calendars, events, and trial queue tokens so the module can be sold and enabled separately.

Trial Queue frontend parity:

- Admin workspace under `/app/trial/admin` provides a dashboard plus stores, zones, studios, staff, config, and queue views.
- Trial admin sidebar/header and nested admin routes live in `trial/admin/AdminApp.jsx`, matching the Checkout admin module structure.
- Checkout and Trial admin headers show a `Change context` action when more than one product module is enabled, returning the user to the shared context selector.
- Checkout and Trial admin sidebars show the logged-in user email with a standard logout action in desktop and mobile navigation.
- Trial admin store, zone, studio, and config screens use the same CRUD layout pattern as Checkout admin, including filters, search, create/edit panels, refresh actions, validation, and active/inactive status controls where applicable.
- Trial admin calendar screen under `/app/trial/admin/calendar` supports store-level weekday hours, timezone, holidays, and promotional event management using Trial Calendar APIs.
- Trial admin ML screen under `/app/trial/admin/ml` trains and displays the latest Trial Queue RandomForest service-time model for a store.
- Trial admin queue screen under `/app/trial/admin/queue` now follows Checkout queue UX with live metrics, store/zone/studio/status filters, search, include-closed toggle, and token lifecycle actions (call/start/complete/cancel).
- Trial admin dashboard now uses a Smart View layout with sticky header tabs for Live, History, and Foresights; Live shows zone/studio queue cards, History shows collapsible Recharts graphs, and Foresights uses Trial ML metadata when the model is ready.
- Trial store-scoped admin screens such as dashboard, config, calendar, ML, and notifications auto-select the first store when no valid `store_id` is present and hide detail forms when there are no stores.
- Trial zones and studios can be created, edited, deactivated, and reactivated from admin UI, with required type fields (`zone_type`, `studio_type`) and trial-zone gender (`MALE`/`FEMALE`/`UNISEX`) for richer configuration.
- Customer workspace under `/app/trial/customer` now follows a routed flow similar to Checkout customer app: QR-only store entry with camera scan or gallery upload, complete encoded Trial customer URL redirect, create token, mobile lookup, and token status screens.
- Checkout and Trial customer routes are public; auth is enforced only for admin and staff module routes.
- Checkout and Trial customer headers link the brand logo back to the public landing page.
- Checkout and Trial customer token status cards include a compact manual refresh icon that reloads the latest token status from the backend.
- Checkout and Trial customer token status cards show custom-modal confirmed cancel and move-last actions for `WAITING` or `CALLED` tokens. Move-last cancels the old token, creates a replacement at the end of the same counter/studio lane, and opens the new status page.
- Trial customer token creation now captures customer gender and validates compatibility with trial-zone gender (`MALE`/`FEMALE`/`UNISEX`) before queue join.
- `TRIAL_ZONE_ASSISTANT` users are treated as Trial staff during login/context selection and are authorized for Trial staff queue APIs.
- Staff workspace under `/app/trial/staff` loads a zone console for `TRIAL_ZONE_ASSISTANT` users and store-scoped managers. The responsive console shows every studio in the selected zone as a horizontally scrollable tab-card row that expands across wider screens, preserves the last selected studio, and uses studio-specific queue/status APIs to start waiting tokens, complete/cancel active tokens, and mark studios active or inactive. Assigned trial staff automatically load their `assigned_zone_id`.
- Trial staff queue APIs enforce assistant zone scope and manager store scope on zone summaries, studio queues, studio status updates, and token actions.
- Checkout and Trial staff consoles show the assigned counter/studio name from staff queue APIs instead of exposing raw lane ids when a name exists.
- Checkout and Trial staff console headers use the same safe-area-aware sticky header behavior as customer queue screens.

Trial Queue ML:

- Uses separate `random_forest_trial_service_time_v1` metadata/artifacts from checkout ML, stored under `ML_MODEL_DIR/trial_store_{store_id}`.
- Trains only on completed `trial_queue_tokens` with `service_started_at` and `completed_at`, using actual trial service duration as the target.
- Feature set includes item count, trial-zone busy count, active studio count, recent cancellation rate, recent average service minutes, hour/day/weekend, trial promotion/sale flag, customer type, trial zone, assigned studio, zone type, zone gender, and studio type.
- Trial queue join uses Trial ML when a READY artifact predicts successfully; otherwise it keeps the existing `RULE_BASED` trial config fallback.
- Trial ML APIs are registered when either Checkout Queue or Trial Queue is enabled, so Trial-only deployments can still use `/api/v1/ml/trial/stores/{store_id}/...`.

### Demo Tools

```text
POST   /api/v1/demotools/ml-training-data
GET    /api/v1/demotools/ml-training-data/status
DELETE /api/v1/demotools/ml-training-data
```

Demo Tools are disabled unless `ENABLE_DEMO_TOOLS=true` and are restricted to `SUPER_ADMIN`. The ML training-data seed endpoint creates one isolated store with `store_number=DEMO-ML-STORE`, one checkout section with three counters, one trial zone with three studios, checkout/trial configs and calendars, promotion events, and enough completed/cancelled/no-show checkout and trial tokens to train both ML models. Each seed request also captures one UTC timestamp and derives ten pending Checkout tokens plus ten pending Trial tokens from it, including lane calling times and current availability, so staff consoles have a realistic live queue. Cleanup deletes only that demo store, related demo data, demo ML metadata, and demo artifact folders.

The shared `/app` context selector shows a Super Admin-only Demo Tools panel with status, create, recreate, and cleanup actions for the demo ML training dataset.

Training remains manual after seeding:

```text
POST /api/v1/ml/stores/{demo_store_id}/train
POST /api/v1/ml/trial/stores/{demo_store_id}/train
```

## Implemented Frontend Routes

```text
/
/app
/app/login
/app/checkout/admin
/app/checkout/admin/stores
/app/checkout/admin/store-config
/app/checkout/admin/sections
/app/checkout/admin/counters
/app/checkout/admin/staff
/app/checkout/admin/queue
/app/checkout/admin/calendar
/app/checkout/admin/ml
/app/checkout/admin/notifications
/app/checkout/admin/alerts
/app/checkout/staff
/app/checkout/customer
/app/trial/admin
/app/trial/admin/zones
/app/trial/admin/studios
/app/trial/admin/config
/app/trial/admin/calendar
/app/trial/admin/ml
/app/trial/admin/notifications
/app/trial/admin/queue
/app/trial/staff
/app/trial/customer
```

Checkout admin groups store setup screens under one `Configuration` sidebar item. The existing Stores, Store Config, Sections, Counters, Staff, and Calendar URLs remain shareable deep links and display a shared horizontal configuration tab bar. Switching between compatible tabs preserves the selected `store_id` filter while dropping page-specific filters.

Trial admin follows the same navigation structure: Stores, Config, Zones, Studios, Staff, and Calendar are grouped under one `Configuration` sidebar item and display shared horizontal tabs. Existing Trial admin URLs remain shareable deep links, and compatible tab switches preserve the selected `store_id` filter while dropping page-specific filters.

### Trial Backend Domain File Split

Trial backend code is organized into Checkout-style domain files for zones, studios, store config, calendar, and queue. Public API paths, database table names, request/response shapes, and frontend clients remain unchanged. Compatibility re-export modules keep older imports such as `app.models.trial` and `app.schemas.trial` working while new code can import from the domain modules directly.

## Not Implemented Yet

- Alert configuration.
- Alert scheduler.
- Real WhatsApp/SMS provider integrations.
- Demo seed data scripts.
- Frontend API integration for admin alerts.

Latest frontend verification:

```text
npm run build
npm run lint
```

## Latest Verification

Current backend test status:

```text
53 passed
```
