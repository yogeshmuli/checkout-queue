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
- Customer queue enrollment with rule-based wait-time estimate.
- React/Vite frontend scaffold with admin, staff, and customer role views.
- Customer token status lookup and staff queue processing APIs.
- Frontend integration for customer token status refresh and staff token transitions.
- Frontend integration for admin store, section, and staff CRUD flows.
- Counter management APIs and frontend admin counter CRUD flow.
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
  "token_number": "S1-001",
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
- Calculates queue position from waiting tokens ahead.
- Calculates estimated wait time from waiting tokens ahead, their item counts, and active counters.
- Stores the joining customer's item count so later customers get better estimates.
- Falls back to one active counter if no counter configuration is available.

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
- Frontend customer view refreshes this status every 30 seconds.

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
/app/admin
/app/staff
/app/customer
```

Result:

- `/app/customer` remains public and does not require authentication.
- `/app/login` is a shared login screen for admin and staff users.
- Authenticated admin users can access admin and staff workspaces and see all three workspace options.
- Authenticated staff users are routed directly to the staff workspace.

### 15. Admin Can Manage Stores From Frontend

As an admin, I can open the store management screen and call implemented store APIs.

Route:

```text
/app/admin/stores
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
/app/admin/sections
```

Result:

- Lists sections through `GET /api/v1/sections`.
- Creates sections through `POST /api/v1/sections`.
- Updates section details and active state through `PATCH /api/v1/sections/{section_id}`.
- Soft-deletes sections through `DELETE /api/v1/sections/{section_id}`.
- Enforces store linkage in UI and backend (`store_id` is required for sections).
- Constrains section type to `REGULAR`, `EXPRESS`, `SELF_CHECKOUT`, `RETURNS`, or `PRIORITY` and presents those choices as a dropdown in the admin UI.

### 15B. Admin Can Manage Staff From Frontend

As an admin, I can create, list, update, activate/deactivate staff users and assign them to stores, sections, and counters.

Route:

```text
/app/admin/staff
```

Result:

- Lists staff through `GET /api/v1/staff`.
- Creates staff through `POST /api/v1/staff`.
- Updates staff details, role, assignment, password, and active state through `PATCH /api/v1/staff/{staff_id}`.
- Soft-deletes staff through `DELETE /api/v1/staff/{staff_id}`.
- Stores staff passwords only as salted hashes.
- Validates duplicate email/phone and assignment consistency across store, section, and counter.
- Includes frontend field validation, search/filter, pagination, unsaved-change confirmation, and active/inactive status controls.

### 15C. Admin Can Manage Counters From Frontend

As an admin, I can create, list, update, and activate/deactivate counters mapped to sections.

Route:

```text
/app/admin/counters
```

Result:

- Lists counters through `GET /api/v1/counters`.
- Creates counters through `POST /api/v1/counters`.
- Updates counter details and active state through `PATCH /api/v1/counters/{counter_id}`.
- Soft-deletes counters through `DELETE /api/v1/counters/{counter_id}`.
- Enforces section linkage in UI and backend (`section_id` is required for counters).
- Supports store-filtered section selection in the admin form.
- Includes frontend field validation, search/filter, pagination, unsaved-change confirmation, and active/inactive status controls.

### 16. Customer Can Create And Track Token From Frontend

As a customer, I can enter checkout details and create a queue token from the mobile view.

Route:

```text
/app/customer
```

Result:

- Shows a first-step customer screen to select store/section before opening token creation.
- Shows active stores in a dropdown and populates section dropdown based on selected store.
- Loads store/section options from public API `GET /api/v1/queue/store-sections`.
- Includes active stores even when no section is configured yet (section remains optional for that case).
- Supports browser-camera QR scanning for store payloads.
- Supports installable PWA behavior with manifest/service-worker caching for home-screen install.
- Calls `POST /api/v1/queue/join`.
- Allows customer cancellation from token status through `POST /api/v1/queue/tokens/{token_id}/customer-cancel` with confirmation.
- Allows token lookup by mobile number from customer screen and navigation between lookup and token status views.
- Applies a shared top branding header across app routes (`/app/*`) for consistent QuT identity.
- Displays token number, queue position, current status, calling time, estimated wait, and calculation method.
- Polls `GET /api/v1/queue/status` every 30 seconds after token creation.

### 17. Staff Can Process Counter Queue From Frontend

As staff, I can login, view my counter queue, start the next token, complete a serving token, cancel tokens, and toggle counter active state.

Route:

```text
/app/staff
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
/app/admin/queue
```

Result:

- Lists queue tokens through `GET /api/v1/queue/tokens`.
- Filters queue tokens by store, section, counter, and token status.
- Shows token number, phone number, position, wait time, assignment, calling time, and item count.
- Lets admin call, start, complete, or cancel tokens from the admin queue screen.
- Uses bearer-token role guards for queue management actions.

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
- Applies post-event queue correction for early/late service completion so downstream waiting times move earlier/later accordingly.
- Reserves lane occupancy for `CALLED` customers until service begins, preventing premature advancement of waiting tokens.
- Prevents additive drift by avoiding incremental delta-shift updates and always recalculating `counters.next_available_time` from the rebuilt queue.
- Queue and counter scheduling timestamps are UTC-aware across model and migration updates.

### Database Models

Implemented models:

- `Store`
- `CheckoutSection`
- `Counter`
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

### Alembic Migrations

Implemented migrations:

- `6a025f451096_init.py`
- `20260507_0003_add_calling_time_to_queue_token.py`
- `4f3122197651_recording_service_time_in_token.py`
- `20260508_0004_make_counter_time_utc.py`
- `030389d488c1_removed_waiting_time.py`
- `20260514_0005_remove_staff_table_move_fields_to_users.py`
- `20260522_0006_convert_section_type_to_enum.py`

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

## Implemented Frontend Routes

```text
/
/app
/app/login
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

## Not Implemented Yet

- Store calendar APIs.
- Counter APIs.
- Alert configuration.
- Alert scheduler.
- WhatsApp/SMS integrations.
- Analytics APIs.
- ML training and prediction APIs.
- Demo seed data scripts.
- Frontend API integration for admin counters, calendar, alerts, analytics, and ML modules.

Latest frontend verification:

```text
npm run build
npm run lint
```

## Latest Verification

Current backend test status:

```text
24 passed
```
