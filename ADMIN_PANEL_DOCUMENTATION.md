# ADMIN PANEL — Complete Technical Documentation
**Project:** Golden Star Travel & Tours  
**Generated from:** Actual codebase scan (no assumptions)  
**Purpose:** Reference for adding new sections (e.g., Airline Ticketing) to the existing admin panel

---

## Table of Contents
1. [Admin Panel Overview](#1-admin-panel-overview)
2. [Permission / Access Control Pattern](#2-permission--access-control-pattern)
3. [Per-Section Breakdown](#3-per-section-breakdown)
4. [Frontend Pattern](#4-frontend-pattern)
5. [Common Reusable Components](#5-common-reusable-components)
6. [Sidebar / Navigation Structure](#6-sidebar--navigation-structure)
7. [Naming Conventions](#7-naming-conventions)
8. [Gaps / Inconsistencies](#8-gaps--inconsistencies)

---

## 1. Admin Panel Overview

The admin panel is a **Single Page Application (SPA)** embedded inside one large Django-rendered HTML template (`overview.html`). Navigation is handled via a JavaScript `switchTab()` function — no page reload occurs when switching between sections. The **only exception** is the Blog Management section, which is a **separate page** (`blogs_list.html`).

### Major Sections & URL Paths

| # | Section Name | URL Path | Template |
|---|---|---|---|
| 1 | Dashboard Overview (Stats + Charts) | `/dashboard/admin/` | `dashboard/admin/overview.html` |
| 2 | Financial Analytics | `/dashboard/admin/` (tab: `analytics`) | Same SPA |
| 3 | Packages | `/dashboard/admin/` (tab: `packages`) | Same SPA |
| 4 | Bookings | `/dashboard/admin/` (tab: `bookings`) | Same SPA |
| 5 | Visas | `/dashboard/admin/` (tab: `visas`) | Same SPA |
| 6 | Flights | `/dashboard/admin/` (tab: `flights`) | Same SPA |
| 7 | Manage Accounts (Active/Suspended Agents) | `/dashboard/admin/` (tab: `manage-accounts`) | Same SPA |
| 8 | Pending Accounts (Pending/Rejected Agents) | `/dashboard/admin/` (tab: `pending-accounts`) | Same SPA |
| 9 | Manage Reviews | `/dashboard/admin/` (tab: `reviews`) | Same SPA |
| 10 | Achievements | `/dashboard/admin/` (tab: `achievements`) | Same SPA |
| 11 | Custom Inquiries | `/dashboard/admin/` (tab: `custom-inquiries`) | Same SPA |
| 12 | System Reports | `/dashboard/admin/` (tab: `reports`) | Same SPA |
| 13 | Manage Blog Articles | `/dashboard/admin/blogs/` | `dashboard/admin/blogs_list.html` (separate page) |
| 14 | Agent Detail View (Ledger) | `/dashboard/admin/agents/<agent_id>/view/` | `dashboard/admin/agent_detail.html` |
| 15 | Approval Letters (print) | `/approval-letter/package/<pk>/`, `/approval-letter/visa/<pk>/`, `/approval-letter/ticket/<pk>/` | `letters/approval_letter.html` |

---

## 2. Permission / Access Control Pattern

### The Core Function: `is_admin(user)`

**There are THREE nearly identical implementations of `is_admin` in the codebase:**

**Instance 1 — `core_admin/apps/accounts/views.py:477`:**
```python
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == 'super_admin')
```

**Instance 2 — `core_admin/apps/content/views.py:78`:**
```python
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == 'super_admin')
```

**Instance 3 — `core_admin/apps/blog/admin_views.py:16`:**
```python
def is_admin(user):
    """Check if user has super_admin role or is superuser."""
    return user.is_authenticated and (user.is_superuser or getattr(user, 'role', '') == 'super_admin')
```

**Internal helper `_is_super_admin` — `core_admin/apps/accounts/views.py:2330`:**
```python
def _is_super_admin(user):
    return user.is_authenticated and (user.is_superuser or getattr(user, 'role', None) == 'super_admin')
```

> **Note:** `_is_super_admin` is used only in the newer duplicate view functions (lines 2336+). The primary active views use `@user_passes_test(is_admin)`.

### How the Pattern Is Applied (Standard Pattern)

Every admin API view follows this exact decorator stack:

```python
# Read-only API (GET only):
@user_passes_test(is_admin)
def admin_some_api(request):
    ...

# Mutating API (POST/DELETE):
@csrf_exempt
@user_passes_test(is_admin)
def admin_some_action_api(request, pk):
    ...
```

**Exact real example from `core_admin/apps/accounts/views.py:541`:**
```python
@csrf_exempt
@user_passes_test(is_admin)
def admin_approve_agent(request, agent_id):
    if request.method == 'POST':
        agent = get_object_or_404(User, id=agent_id, role='agent')
        agent.approval_status = 'approved'
        agent.save()
        send_agent_status_email(agent, 'approved')
        return JsonResponse({'success': True, 'status': 'approved'})
    return JsonResponse({'success': False}, status=400)
```

### User Model Role Field

File: `core_admin/apps/accounts/models.py:4-10`

```python
class User(AbstractUser):
    ROLE_CHOICES = (
        ('super_admin', 'Super Admin'),
        ('agent', 'Agent'),
        ('customer', 'Customer'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
```

Admin access: `user.is_superuser == True` **OR** `user.role == 'super_admin'`

### Secondary Permission Pattern (newer duplicate views only)

```python
@login_required
@never_cache
def admin_clients_list_api(request):
    if not _is_super_admin(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)
```

**For new sections: Use the standard Pattern A** (`@user_passes_test(is_admin)`) — do NOT use Pattern B.

---

## 3. Per-Section Breakdown

---

### 3.1 Agents — Manage Accounts + Pending Accounts

**Tab IDs:** `manage-accounts` | `pending-accounts`  
**Data Source:** `User.objects.filter(role='agent')`

#### List View

Both tabs use the same API:

| Endpoint | Method | URL | View | File:Line |
|---|---|---|---|---|
| Agent List API | GET | `/dashboard/admin/api/agents/` | `admin_dashboard_api` | `accounts/views.py:487` |

**Response shape:**
```json
{
  "agents": [
    {
      "id", "username", "first_name", "last_name", "email", "phone",
      "company_name", "profile_photo_url", "id_card_front_url", "id_card_back_url",
      "approval_status", "is_verified_partner", "address", "date_joined", "wallet_balance"
    }
  ],
  "customers": [...],
  "counts": {
    "total", "pending", "approved", "rejected", "suspended", "customers_total"
  }
}
```

**Table columns (Manage Accounts tab):**
Company Name + sub-detail (username, manager name, balance) | Email + Phone + Address | Date Joined | Status Badge | Actions

**Table columns (Pending Accounts tab):**
Company Name + username | Email + Phone + Address | Documents (profile photo, ID front/back preview buttons) | Date Joined | Status Badge | Actions

#### Create / Edit

Not available in admin panel — agents register via public signup (`/auth/signup/`).

#### Delete

Not available — admin can only Approve / Reject / Suspend.

#### Status Toggle (Approve / Reject / Suspend)

| Action | URL | Method | View | File:Line |
|---|---|---|---|---|
| Approve | `/dashboard/admin/api/agents/<agent_id>/approve/` | POST | `admin_approve_agent` | `accounts/views.py:543` |
| Reject | `/dashboard/admin/api/agents/<agent_id>/reject/` | POST | `admin_reject_agent` | `accounts/views.py:555` |
| Suspend | `/dashboard/admin/api/agents/<agent_id>/suspend/` | POST | `admin_suspend_agent` | `accounts/views.py:1202` |
| Toggle Badge | `/dashboard/admin/api/agents/<agent_id>/toggle-badge/` | POST | `admin_toggle_agent_verification_badge` | `accounts/views.py:2131` |

**On Approve/Reject/Suspend:** An HTML email is sent automatically via thread pool (`send_agent_status_email`).  
**Request shape:** No body needed — action determined by URL.  
**Response shape:** `{"success": true, "status": "approved"}`

#### Agent Detail View (Ledger)

Clicking "View Data" redirects to a separate full page:
- URL: `/dashboard/admin/agents/<agent_id>/view/`
- Template: `core_admin/templates/dashboard/admin/agent_detail.html`
- View: `admin_agent_detail_view` at `accounts/views.py:1359`

---

### 3.2 Packages

**Tab ID:** `packages`

#### List View

| Endpoint | Method | URL | View | File:Line |
|---|---|---|---|---|
| List Packages | GET | `/dashboard/admin/api/packages/` | `admin_packages_api` | `accounts/views.py:583` |

**Table columns:** Title + Description + Airline + Routes + Hotel Distances + AI Indexed badge | Category | Duration | Price | AI Index status | Actions (Edit / Delete)

**Fields returned:**
```
id, title, description, price, category, duration_days, price_sharing, price_quad,
price_triple, price_double, price_child, price_infant, discount_percentage,
discount_amount, original_price, airline, airline_logo, flight_routes,
makkah_hotel_name, makkah_hotel_distance, makkah_hotel_images,
madinah_hotel_name, madinah_hotel_distance, madinah_hotel_images,
luggage_weight, images, addons, total_seats, available_seats, has_embedding
```

#### Create / Edit — Modal

- **Pattern:** Modal (`#package-modal`)
- **Create endpoint:** POST `/dashboard/admin/api/packages/` → `admin_packages_api` (`accounts/views.py:583`)
- **Edit endpoint:** POST `/dashboard/admin/api/packages/<pk>/` → `admin_package_detail_api` (`accounts/views.py:741`)
- **Submission:** `FormData` (multipart), supports file uploads (`images_files`, `airline_logo`)
- **Side effect:** AI vector embedding regenerated via `EmbeddingsService` after save

#### Delete

- **Confirmation:** `confirm()` browser dialog
- **Endpoint:** DELETE `/dashboard/admin/api/packages/<pk>/` → `admin_package_detail_api` (`accounts/views.py:741`)

#### API Summary

| Action | Method | URL | Body Format |
|---|---|---|---|
| List | GET | `/dashboard/admin/api/packages/` | — |
| Create | POST | `/dashboard/admin/api/packages/` | `FormData` (multipart) |
| Edit | POST | `/dashboard/admin/api/packages/<pk>/` | `FormData` (multipart) |
| Delete | DELETE | `/dashboard/admin/api/packages/<pk>/` | — |

---

### 3.3 Bookings

**Tab ID:** `bookings`

#### List View

| Endpoint | Method | URL | View | File:Line |
|---|---|---|---|---|
| List Bookings | GET | `/dashboard/admin/api/bookings/` | `admin_bookings_api` | `accounts/views.py:1151` |

**Table columns:** Username + Email | Package Title | Booking Type | Sharing Category | Adults/Children | Discount | Total Price | Status Badge | Actions

**Fields returned:**
```
id, username, email, package_title, booking_type, sharing_category,
adults_count, children_count, discount_applied, notes, status, total_price, created_at
```

#### Create / Edit

Not in admin panel. Bookings submitted via public `submit_package_booking_api`.

#### Status Update

- **Pattern:** Inline dropdown in table row
- **Endpoint:** POST `/dashboard/admin/api/bookings/<pk>/` → `admin_booking_status_api` (`accounts/views.py:1174`)
- **Status values:** `pending`, `confirmed`, `cancelled`, `rejected`
- **Side effect:** `package.available_seats` auto-decremented when status → `confirmed`; restored when reverted

**Request body:**
```
Content-Type: application/x-www-form-urlencoded
status=confirmed
```
**Response:** `{"success": true, "status": "confirmed", "available_seats": 12}`

---

### 3.4 Visas

**Tab ID:** `visas`  
Two sub-sections: Visa Applications + Visa Packages (catalog)

#### 3.4.1 Visa Applications

| Endpoint | Method | URL | View | File:Line |
|---|---|---|---|---|
| List | GET | `/dashboard/admin/api/visas/` | `admin_visas_api` | `accounts/views.py:845` |
| Update Status | POST | `/dashboard/admin/api/visas/<pk>/` | `admin_visa_status_api` | `accounts/views.py:866` |

**Table columns:** Username + Email | Phone | Country | Visa Type | Passport Number | Notes | Status | Actions

**Status values:** `pending`, `processing`, `approved`, `rejected`

**Request body:** `Content-Type: application/x-www-form-urlencoded` → `status=approved`

#### 3.4.2 Visa Packages (Catalog)

| Action | Method | URL | View | File:Line |
|---|---|---|---|---|
| List | GET | `/dashboard/admin/api/visa-packages/` | `admin_visa_packages_api` | `accounts/views.py:877` |
| Create | POST | `/dashboard/admin/api/visa-packages/` | `admin_visa_packages_api` | `accounts/views.py:877` |
| Edit | POST | `/dashboard/admin/api/visa-packages/<pk>/` | `admin_visa_package_detail_api` | `accounts/views.py:939` |
| Delete | DELETE | `/dashboard/admin/api/visa-packages/<pk>/` | `admin_visa_package_detail_api` | `accounts/views.py:939` |

**Fields:** `country, title, visa_type, processing_time, stay_validity, visa_validity, entry_type, price, original_price, required_documents, description, banner_image, is_popular`

**Create/Edit pattern:** Modal with `FormData` submission.

---

### 3.5 Flights

**Tab ID:** `flights`  
Two sub-sections: Flight Quote Requests + Flight Ticket Offers (catalog)

#### 3.5.1 Flight Quote Requests

| Endpoint | Method | URL | View | File:Line |
|---|---|---|---|---|
| List | GET | `/dashboard/admin/api/flights/` | `admin_flights_api` | `accounts/views.py:968` |
| Quote / Cancel | POST | `/dashboard/admin/api/flights/<pk>/` | `admin_flight_status_api` | `accounts/views.py:988` |

**Table columns:** Username + Email | Route (departure ⇄ destination) | Departure + Return Date | Price Quote | Status | Actions (Quote / Cancel)

**Status update (quote):**
```
Content-Type: application/x-www-form-urlencoded
status=quoted&price_quote=145000
```
**Response:** `{"success": true, "status": "quoted", "price_quote": "145000.00"}`

#### 3.5.2 Flight Ticket Offers (Catalog)

| Action | Method | URL | View | File:Line |
|---|---|---|---|---|
| List | GET | `/dashboard/admin/api/flight-tickets/` | `admin_flight_tickets_api` | `accounts/views.py:1002` |
| Create | POST | `/dashboard/admin/api/flight-tickets/` | `admin_flight_tickets_api` | `accounts/views.py:1002` |
| Edit | POST | `/dashboard/admin/api/flight-tickets/<pk>/` | `admin_flight_ticket_detail_api` | `accounts/views.py:1102` |
| Delete | DELETE | `/dashboard/admin/api/flight-tickets/<pk>/` | `admin_flight_ticket_detail_api` | `accounts/views.py:1102` |

**Fields:** `airline_name, airline_code, airline_logo, flight_number, departure_city, departure_airport_code, destination_city, destination_airport_code, departure_time_str, arrival_time_str, duration_str, flight_type, ticket_class, price, price_20kg, price_30kg, price_40kg, original_price, baggage_checkin, baggage_hand, is_refundable, cancellation_fee, total_seats, available_seats, is_popular, description`

**Create/Edit:** Modal with `FormData`. **Delete:** `confirm()` dialog then DELETE request.

---

### 3.6 Reviews

**Tab ID:** `reviews`  
Model: `PlatformReview` in `apps/content/models.py`  
Views: `core_admin/apps/content/views.py`

#### List View

| Endpoint | Method | URL | View | File:Line |
|---|---|---|---|---|
| List | GET | `/dashboard/admin/api/reviews/` | `admin_reviews_list_api` | `content/views.py:82` |

**Table columns:** Name + Email | Star Rating | Comment (truncated) | Date | Status (Visible/Hidden) | Actions

**Fields returned:** `id, name, email, rating, comment, is_approved, created_at`

#### Create / Edit

Not in admin panel — submitted publicly via POST `/api/reviews/submit/`.

#### Delete

- **Confirmation:** `confirm()` dialog
- **Endpoint:** POST `/dashboard/admin/api/reviews/<review_id>/delete/` → `admin_review_delete_api` (`content/views.py:119`)

#### Status Toggle (Approve / Hide)

- **Endpoint:** POST `/dashboard/admin/api/reviews/<review_id>/toggle/` → `admin_review_toggle_api` (`content/views.py:102`)
- **Effect:** Flips `review.is_approved` boolean
- **Response:** `{"success": true, "is_approved": true}`

---

### 3.7 Achievements

**Tab ID:** `achievements`  
Model: `Achievement` in `apps/content/models.py`  
Views: `core_admin/apps/content/views.py`

#### List View

- **Rendering:** Card grid (`#achievements-grid-admin`) — NOT a table
- **Endpoint:** GET `/dashboard/admin/api/achievements/` → `admin_achievements_list_api` (`content/views.py:146`)

**Fields returned:** `id, title, category, category_display, description, photo_url, video_url, date, is_active, created_at`

**Categories:** `milestone`, `meeting`, `review`, `video`

#### Create / Edit — Modal

- **Modal:** `#achievement-modal`
- **Create endpoint:** POST `/dashboard/admin/api/achievements/create/` → `admin_achievement_create_api` (`content/views.py:168`)
- **Edit endpoint:** POST `/dashboard/admin/api/achievements/<pk>/` → `admin_achievement_detail_api` (`content/views.py:194`)
- **Submission:** `FormData` (multipart), supports `photo` file upload

#### Delete

- **Confirmation:** `confirm()` dialog
- **Endpoint:** DELETE `/dashboard/admin/api/achievements/<pk>/` → `admin_achievement_detail_api` (`content/views.py:194`)

#### Toggle Active Status

Controlled via Edit modal's `is_active` select dropdown — no dedicated toggle endpoint.

---

### 3.8 Custom Inquiries

**Tab ID:** `custom-inquiries`  
Model: `CustomPackageInquiry` in `apps/packages/models.py`

#### List View

| Endpoint | Method | URL | View | File:Line |
|---|---|---|---|---|
| List | GET | `/dashboard/admin/api/custom-inquiries/` | `admin_custom_inquiries_list_api` | `accounts/views.py:3287` |

**Table columns:** Name + Email + Phone | Package Type (Hajj/Umrah) | Days | Makkah Distance | Madinah Distance | Airline | Notes | Status (Contacted/Pending) | Actions

**Fields returned:** `id, name, email, phone, package_type, days, makkah_distance, madinah_distance, airline, additional_notes, is_contacted, created_at`

#### Status Toggle (Mark Contacted / Mark Pending)

- **Endpoint:** POST `/dashboard/admin/api/custom-inquiries/<pk>/contact/` → `admin_custom_inquiry_contact_api` (`accounts/views.py:3314`)
- **Effect:** Flips `inquiry.is_contacted` boolean
- **Response:** `{"success": true, "is_contacted": true}`

#### Create / Delete

Not available in admin panel.

---

### 3.9 Agent Ledger

**Location:** Separate full-page view (accessed via "View Data" button on Manage Accounts tab)  
**URL:** `/dashboard/admin/agents/<agent_id>/view/`  
**Template:** `core_admin/templates/dashboard/admin/agent_detail.html`

#### API Endpoints

| Action | Method | URL | View | File:Line |
|---|---|---|---|---|
| Get Ledger | GET | `/dashboard/admin/api/agents/<agent_id>/ledger/` | `admin_agent_ledger_api` | `accounts/views.py:2478` |
| Create Entry | POST | `/dashboard/admin/api/agents/<agent_id>/ledger/add/` | `admin_agent_ledger_create_api` | `accounts/views.py:2525` |
| Delete Entry | POST | `/dashboard/admin/api/ledger/entries/<entry_id>/delete/` | `admin_agent_ledger_delete_api` | `accounts/views.py:2570` |

> ⚠️ **URL Inconsistency:** Two URL patterns exist for ledger delete:
> - `urls.py:75`: `/dashboard/admin/api/ledger/entries/<int:entry_id>/delete/`
> - `urls.py:146`: `/dashboard/admin/api/ledger/<int:entry_id>/delete/`
> Both map to the same view. The JS tries primary URL, falls back to secondary.

**Ledger GET Response:**
```json
{
  "agent": {"id", "username", "company_name", "email"},
  "entries": [
    {"id", "entry_type", "category", "amount", "description", "reference", "running_balance", "created_at"}
  ],
  "summary": {"total_credit", "total_debit", "balance"}
}
```

**Create Entry Request (JSON body):**
```json
{
  "entry_type": "credit",
  "category": "commission",
  "amount": "50000.00",
  "description": "Commission for June 2026",
  "reference": "BK-00123"
}
```

**AgentLedger model fields:** `agent (FK), entry_type (credit/debit), category (commission/payment/refund/adjustment/penalty/advance/other), amount, description, reference, created_by (FK), created_at`

---

### 3.10 Clients

**Source:** `User.objects.filter(role='customer')`

#### List View

| Endpoint | Method | URL | View | File:Line |
|---|---|---|---|---|
| List | GET | `/dashboard/admin/api/clients/` | `admin_clients_list_api` | `accounts/views.py:2433` |

**Fields returned:** `id, username, first_name, last_name, email, phone, address, is_email_verified, is_active, date_joined`

#### Toggle Active Status (Block / Unblock)

- **Endpoint:** POST `/dashboard/admin/api/clients/<client_id>/toggle/` → `admin_client_toggle_api` (`accounts/views.py:2459`)
- **Effect:** Flips `client.is_active` boolean
- **Response:** `{"success": true, "is_active": false}`

---

### 3.11 Blogs

**SEPARATE PAGE** — Not part of the SPA. Standalone template.  
**URL:** `/dashboard/admin/blogs/`  
**Template:** `core_admin/templates/dashboard/admin/blogs_list.html`  
**View:** `admin_blogs_page_view` at `core_admin/apps/blog/admin_views.py:22`  
**Extends:** `{% extends 'base.html' %}` (includes public navbar/footer)

#### List API

| Endpoint | Method | URL | View | File:Line |
|---|---|---|---|---|
| List (paginated) | GET | `/dashboard/admin/api/blogs/` | `admin_blogs_list_api` | `blog/admin_views.py:32` |

**Query params:** `q` (search), `category`, `status` (draft/published/all), `page`  
**Pagination:** 20 per page via Django `Paginator`

**Fields returned:** `id, title, slug, category_id, category_name, category_color, author_name, read_time, views, status, is_featured, cover_url, static_cover, excerpt, created_at, updated_at, published_at`

#### Create

- **Pattern:** Slide-in drawer/panel (not a simple dialog modal)
- **Endpoint:** POST `/dashboard/admin/api/blogs/create/` → `admin_blog_create_api` (`blog/admin_views.py:112`)
- **Rich text editor:** Quill.js v1.3.6 (CDN)
- **Body format:** `multipart/form-data` (supports `cover_image` file upload)
- **Fields:** `title, category_id, author_name, read_time, status, is_featured, static_cover, excerpt, body, cover_image`
- **Side effect:** When status is `published`, dispatches Celery task `trigger_n8n_content_update_webhook` to N8N webhook

#### Edit

- **Get data:** GET `/dashboard/admin/api/blogs/<slug>/` → `admin_blog_detail_api` (`blog/admin_views.py:177`)
- **Save:** POST `/dashboard/admin/api/blogs/<slug>/` → same view

#### Delete

- **Endpoint:** POST or DELETE `/dashboard/admin/api/blogs/<slug>/delete/` → `admin_blog_delete_api` (`blog/admin_views.py:257`)
- **No `confirm()` dialog.** Hard delete immediately.

#### Publish/Draft Toggle

- **Endpoint:** POST `/dashboard/admin/api/blogs/<slug>/toggle-publish/` → `admin_blog_toggle_publish_api` (`blog/admin_views.py:274`)
- **Effect:** Flips status between `draft` and `published`. Sets `published_at` when newly published.

#### Categories

| Action | Method | URL | View | File:Line |
|---|---|---|---|---|
| List | GET | `/dashboard/admin/api/blog-categories/` | `admin_blog_categories_api` | `blog/admin_views.py:314` |
| Create | POST | `/dashboard/admin/api/blog-categories/create/` | `admin_blog_category_create_api` | `blog/admin_views.py:338` |

---

### 3.12 Financial Analytics

**Tab ID:** `analytics`

| Endpoint | Method | URL | View | File:Line |
|---|---|---|---|---|
| Financial Data | GET | `/dashboard/admin/api/analytics/financial/` | `admin_financial_analytics_api` | `accounts/views.py:3741` |
| Export | GET | `/dashboard/admin/api/analytics/export/<fmt>/` | `admin_export_pandas_analytics_api` | `accounts/views.py:3885` |

**Export formats:** `excel`, `csv`  
**Data engine:** NumPy + Pandas  
**Stat cards:** Gross Sales Volume, Confirmed Payments, Pending Receivables, AOV (Average Order Value), per-department breakdowns (Visa, Umrah, Hajj, Flights)

---

### 3.13 System Reports & Exports

**Tab ID:** `reports`

| Export | Method | URL | View | File:Line |
|---|---|---|---|---|
| Visas CSV | GET | `/dashboard/admin/api/reports/export/visas/` | `admin_export_visas_csv_api` | `accounts/views.py:3455` |
| Bookings CSV | GET | `/dashboard/admin/api/reports/export/bookings/` | `admin_export_bookings_csv_api` | `accounts/views.py:3487` |
| Flights CSV | GET | `/dashboard/admin/api/reports/export/flights/` | `admin_export_flights_csv_api` | `accounts/views.py:3521` |
| Agents CSV | GET | `/dashboard/admin/api/reports/export/agents/` | `admin_export_agents_csv_api` | `accounts/views.py:3553` |
| Multi-format | GET | `/dashboard/admin/api/reports/export/<report_type>/<fmt>/` | `admin_export_report_api` | `accounts/views.py:3580` |

**Multi-format formats:** `csv`, `excel` (.xls), `word` (.doc), `pdf` (uses `reports/report_printable.html`)

---

### 3.14 Custom Bills

| Action | Method | URL | View | File:Line |
|---|---|---|---|---|
| List / Create | GET / POST | `/dashboard/admin/api/custom-bills/` | `admin_custom_bills_api` | `accounts/views.py:3966` |
| Delete | POST | `/dashboard/admin/api/custom-bills/<pk>/delete/` | `admin_delete_custom_bill_api` | `accounts/views.py:4012` |
| Export | GET | `/dashboard/admin/api/custom-bills/<pk>/export/<fmt>/` | `admin_export_custom_bill_api` | `accounts/views.py:4021` |

**Model** (`accounts/models.py:102`): `bill_number, title, department (umrah/hajj/visa/ticket/general), bill_type (income/expense), vendor_client_name, amount, is_paid, description`

**Export formats:** `pdf`, `word`/`doc`, `excel`/`xls`/`xlsx`, `csv`

**Create body format:** JSON (`Content-Type: application/json`) — this is the **only admin endpoint using JSON body**.

---

## 4. Frontend Pattern

### 4.1 Base Layout

**Main Admin SPA (`overview.html`):**
- Does **NOT** extend `base.html`
- Standalone self-contained HTML file with its own `<aside>` sidebar
- Loads Tailwind CSS via CDN (`https://cdn.tailwindcss.com`)
- Loads FontAwesome via CDN

**Blog Admin Page (`blogs_list.html`):**
- **Extends** `{% extends 'base.html' %}`
- Uses compiled Tailwind from `{% static 'css/tailwind.css' %}`
- Includes public navbar/footer from `base.html`

**Agent Detail Page (`agent_detail.html`):**
- Standalone page with same design pattern as `overview.html`

### 4.2 AJAX / Fetch Pattern

All API calls use native `fetch()` with `async/await`. No jQuery, Axios, or third-party HTTP library.

**Standard GET fetch (exact copy from `overview.html:2877`):**
```javascript
const res = await fetch("/dashboard/admin/api/packages/");
const data = await res.json();
// Then DOM manipulation
data.packages.forEach(p => {
    const row = document.createElement("tr");
    row.innerHTML = `...`;
    tbody.appendChild(row);
});
```

**Standard mutating POST with FormData (exact copy from `overview.html:2670`):**
```javascript
const formData = new FormData(document.getElementById("package-form"));
const url = id ? `/dashboard/admin/api/packages/${id}/` : `/dashboard/admin/api/packages/`;

const response = await fetch(url, {
    method: "POST",
    body: formData,
    headers: {
        "X-CSRFToken": "{{ csrf_token }}"
    }
});
if (response.ok) {
    closePackageModal();
    syncData();
} else {
    alert("Failed to save package. Please check all fields and try again.");
}
```

**URL-encoded POST for status changes (exact copy from `overview.html:2718`):**
```javascript
const response = await fetch(`/dashboard/admin/api/bookings/${id}/`, {
    method: "POST",
    body: new URLSearchParams({'status': status}),
    headers: {
        "X-CSRFToken": "{{ csrf_token }}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
});
if (response.ok) syncData();
```

**CSRF token:** Always passed as `X-CSRFToken` header from Django template tag `{{ csrf_token }}`.

### 4.3 Table / List Rendering

**Pattern:** Server-side renders the shell HTML structure, then **client-side JS DOM manipulation** for all data. No server-side context data for tables — all from AJAX.

**Main orchestrator — `syncData()` (overview.html:2857):**
```javascript
async function syncData() {
    const loader = document.getElementById("tab-loader");
    loader.classList.remove("hidden");
    try {
        // Always fetches overview stats first
        const statsResp = await fetch("/dashboard/admin/api/overview-stats/");
        const statsData = await statsResp.json();
        // Update stat cards...
        // Conditionally load current tab
        if (currentTab === "packages") { ... }
        else if (currentTab === "bookings") { ... }
        // etc.
    } finally {
        loader.classList.add("hidden");
    }
}
```

`syncData()` is called:
1. On initial `DOMContentLoaded`
2. After every create, edit, delete, or status change

### 4.4 CSS Framework / Classes Pattern

**Framework:** Tailwind CSS (CDN in `overview.html`, compiled in `base.html` pages)

| Element | Classes |
|---|---|
| Table rows | `hover:bg-white/[0.01] transition-all border-b border-white/5` |
| Action button (primary/green) | `px-2 py-1 bg-emerald-600 hover:bg-emerald-700 text-white text-[10px] font-bold rounded transition-all` |
| Action button (danger/red) | `px-2 py-1 bg-rose-600 hover:bg-rose-700 text-white text-[10px] font-bold rounded transition-all` |
| Action button (warning/amber) | `px-2 py-1 bg-amber-600 hover:bg-amber-700 text-white text-[10px] font-bold rounded transition-all` |
| Cards / Panels | `bg-slate-900 border border-white/5 rounded-2xl shadow-lg` |
| Status badge (approved) | `px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20` |
| Status badge (pending) | `px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20` |
| Status badge (rejected) | `px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20` |
| Form inputs | `bg-slate-950 border border-white/10 text-xs font-bold text-white rounded-xl px-3 py-2.5 focus:outline-none focus:border-brand-orange` |
| Brand color | `text-brand-orange` / `bg-brand-orange` (hex `#EA580C`) |
| Font | `Plus Jakarta Sans` (CDN) |

---

## 5. Common Reusable Components

### 5.1 Confirmation Dialogs

**Pattern:** Native browser `confirm()` — NOT a custom modal.
```javascript
if (!confirm("Are you sure you want to delete this package?")) return;
```
Used for: Package delete, Review delete, Achievement delete.

### 5.2 Modals

Modals are inline HTML divs toggled with `hidden` class. Each section has its own modal:

| Modal ID | Section | Purpose |
|---|---|---|
| `#inspect-modal` | Agent Docs | View uploaded documents (photo, ID cards) |
| `#package-modal` | Packages | Create / Edit package |
| `#flight-modal` | Flights | Enter price quote for flight request |
| `#visa-package-modal` | Visas | Create / Edit visa package |
| `#flight-ticket-modal` | Flight Tickets | Create / Edit ticket offer |
| `#achievement-modal` | Achievements | Create / Edit achievement |
| `#ledger-panel` | Agent Ledger | Full-screen side panel for ledger entries |

**Modal open/close pattern:**
```javascript
function openPackageModal(id = null) {
    document.getElementById("package-modal").classList.remove("hidden");
    if (id) { /* populate form fields from cache */ }
}
function closePackageModal() {
    document.getElementById("package-modal").classList.add("hidden");
    document.getElementById("package-form").reset();
}
```
Backdrop div has `onclick="closeXModal()"` to close on outside click.

### 5.3 Pagination Component

No reusable pagination component. Only the Blog admin page uses Django `Paginator`. All other SPA tabs load entire dataset at once.

### 5.4 File Upload Pattern

Native HTML `<input type="file">` submitted via `FormData`. Backend saves to `settings.MEDIA_ROOT/<subdir>/`.

```html
<input type="file" name="photo" accept="image/*" 
    class="w-full text-xs text-slate-400 bg-slate-950 border border-white/10 rounded-xl px-3 py-2 focus:outline-none">
```

### 5.5 Global Loading Indicator

One `#tab-loader` div shown/hidden during `syncData()`:
```javascript
loader.classList.remove("hidden"); // show before fetch
// ... after all fetches ...
loader.classList.add("hidden");    // hide
```

### 5.6 `escapeHTML()` Utility

All user-generated content in `innerHTML` is sanitized:
```javascript
function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
        tag => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[tag] || tag)
    );
}
```

---

## 6. Sidebar / Navigation Structure

### File Location

The sidebar is **hardcoded inline HTML** in `core_admin/templates/dashboard/admin/overview.html` starting at line 152. There is no separate include file for the admin sidebar.

### Current Menu Items (exact order, from overview.html:174-228)

```html
<nav>
    <button onclick="switchTab('overview')">           Overview              </button>
    <button onclick="switchTab('analytics')">          Financial Analytics   </button>
    <button onclick="switchTab('packages')">           Packages              </button>
    <button onclick="switchTab('bookings')">           Bookings              </button>
    <button onclick="switchTab('visas')">              Visas                 </button>
    <button onclick="switchTab('flights')">            Flights               </button>
    <button onclick="switchTab('manage-accounts')">    Manage Accounts       </button>
    <button onclick="switchTab('pending-accounts')">   Pending Accounts      </button>
    <button onclick="switchTab('reviews')">            Manage Reviews        </button>
    <button onclick="switchTab('achievements')">       Achievements          </button>
    <button onclick="switchTab('custom-inquiries')">   Custom Inquiries      </button>
    <a href="{% url 'admin_blogs_page' %}">            Manage Blog Articles  </a> <!-- navigates away! -->
    <button onclick="switchTab('reports')">            System Reports        </button>
</nav>
```

### How `switchTab()` Works

```javascript
let currentTab = 'overview';

function switchTab(tabName) {
    // 1. Hide all .tab-pane divs
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.add('hidden'));
    // 2. Show target tab div (id="tab-content-{tabName}")
    document.getElementById(`tab-content-${tabName}`).classList.remove('hidden');
    // 3. Update active button styling (id="tab-btn-{tabName}")
    document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.remove('bg-brand-orange', 'text-white');
        b.classList.add('text-slate-400');
    });
    document.getElementById(`tab-btn-${tabName}`).classList.add('bg-brand-orange', 'text-white');
    // 4. Update workspace header title
    document.getElementById('workspace-title').textContent = tabTitles[tabName];
    // 5. Store and sync data
    currentTab = tabName;
    syncData();
}
```

**Naming conventions:**
- Tab content div: `id="tab-content-{tabName}"` (e.g., `tab-content-packages`)
- Tab button: `id="tab-btn-{tabName}"` (e.g., `tab-btn-packages`)

### How to Add a New Sidebar Item (Airline Ticketing example)

**Step 1 — Add button in `<nav>` (after line 228):**
```html
<button onclick="switchTab('airline-ticketing')" id="tab-btn-airline-ticketing"
    class="tab-btn flex items-center space-x-2.5 px-3.5 py-2 rounded-xl text-xs md:text-sm font-bold transition-all text-slate-400 hover:text-white hover:bg-white/5 shrink-0">
    <i class="fa-solid fa-ticket w-4"></i>
    <span>Airline Ticketing</span>
</button>
```

**Step 2 — Add content div inside `<div class="flex-grow overflow-y-auto">`:**
```html
<div id="tab-content-airline-ticketing" class="tab-pane hidden space-y-8">
    <!-- table header, tbody#airline-ticketing-tbody, etc. -->
</div>
```

**Step 3 — Add title in `tabTitles` JS object.**

**Step 4 — Add `else if (currentTab === "airline-ticketing") { ... }` in `syncData()`.**

**Step 5 — Add backend view + URL.**

---

## 7. Naming Conventions

### 7.1 URL Pattern

```
/dashboard/admin/api/<resource>/                          → list + create (GET + POST)
/dashboard/admin/api/<resource>/<pk>/                     → detail + edit + delete
/dashboard/admin/api/<resource>/<pk>/<action>/            → specific action (POST)
/dashboard/admin/<resource>/                              → page render (separate pages only)
```

**Examples:**
- `/dashboard/admin/api/packages/` — list/create
- `/dashboard/admin/api/packages/<pk>/` — edit/delete
- `/dashboard/admin/api/agents/<agent_id>/approve/` — specific action
- `/dashboard/admin/api/reports/export/<report_type>/<fmt>/` — multi-param

### 7.2 Template File Naming

```
dashboard/admin/overview.html          → main SPA (all tabs)
dashboard/admin/blogs_list.html        → separate blog management page
dashboard/admin/agent_detail.html      → separate agent detail page
```
Convention: `<resource>_list.html` for lists, `<resource>_detail.html` for detail pages.

### 7.3 View Function Naming

```python
admin_<resource>s_api(request)                # list + create (GET + POST)
admin_<resource>_detail_api(request, pk)      # edit + delete
admin_<action>_<resource>(request, id)        # specific action (e.g., admin_approve_agent)
admin_<resource>_<action>_api(request, id)    # specific action (e.g., admin_review_toggle_api)
admin_<resource>_page_view(request)           # separate page render
```

### 7.4 Django URL Name

```python
name='admin_<resource>_api'           # list endpoints
name='admin_<resource>_detail_api'    # detail endpoints
name='admin_<action>_<resource>'      # action endpoints (e.g., admin_approve_agent)
name='admin_<resource>_page'          # page views (e.g., admin_blogs_page)
```

---

## 8. Gaps / Inconsistencies

### 8.1 Duplicate View Functions in `accounts/views.py`

Several view functions are defined **twice**. Django uses the **last defined** version:

| Function | First Definition | Second Definition (active) |
|---|---|---|
| `admin_dashboard_api` | line 487 | line 2336 |
| `admin_approve_agent` | line 543 | line 2369 |
| `admin_reject_agent` | line 555 | line 2386 |
| `admin_suspend_agent` | line 1202 | line 2402 |
| `admin_toggle_agent_verification_badge` | line 2131 | line 2418 |
| `admin_flight_tickets_api` | line 1002 | line 3075 |
| `admin_flight_ticket_detail_api` | line 1102 | line 3134 |

The second versions use `_is_super_admin` + `@login_required` + `@never_cache` instead of `@user_passes_test(is_admin)`.

**For new sections:** Use `@user_passes_test(is_admin)` pattern — do NOT introduce a third pattern.

### 8.2 Two Permission Patterns Coexist

- **Pattern A (standard):** `@user_passes_test(is_admin)` — used by most views
- **Pattern B (newer duplicates):** `@login_required` + `@never_cache` + inline `_is_super_admin` check

**New sections must use Pattern A.**

### 8.3 Blog Section Is a Separate Page (Architectural Inconsistency)

All sections are SPA tabs in `overview.html`. Blog is the **only one** that navigates to a separate URL (`/dashboard/admin/blogs/`) and extends `base.html` with the public navbar/footer.

**New sections should be SPA tabs in `overview.html`**, not separate pages.

### 8.4 Two URL Patterns for Ledger Delete

Both `urls.py:75` and `urls.py:146` point to the same delete view with different URL formats. The JS tries primary, then falls back to secondary. Redundant.

### 8.5 Inconsistent Delete Confirmation

- Most deletes: `confirm()` dialog before deletion
- Blog delete (`admin_blog_delete_api`): **No `confirm()` observed** — hard deletes immediately

**New sections should use `confirm()` for all delete operations.**

### 8.6 Custom Bills Uses JSON Body (Not FormData)

`admin_custom_bills_api` create accepts `application/json`. All other admin create endpoints use `multipart/form-data` or `application/x-www-form-urlencoded`.

**New sections should use FormData.**

### 8.7 No Client-Side Pagination in SPA Tabs

All SPA tabs load the entire dataset in one fetch. Only the Blog page has server-side pagination. For sections that could have many records (e.g., airline tickets), consider pagination from the start.

### 8.8 `is_admin()` Redefined in 3 Separate Files

No shared utility module exists. Each app/file that needs admin check has its own copy:
- `apps/accounts/views.py:477`
- `apps/content/views.py:78`
- `apps/blog/admin_views.py:16`

When adding a new section in a new file, define `is_admin` locally following the same pattern.

---

## Quick Reference: Adding Airline Ticketing Section

### Backend

**In `core_admin/apps/accounts/views.py` (or a new app's views.py):**
```python
# Permission function (if in new file — copy this exactly)
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == 'super_admin')

# List + Create
@csrf_exempt
@user_passes_test(is_admin)
def admin_airline_tickets_api(request):
    if request.method == 'GET':
        tickets = AirlineTicket.objects.all().order_by('-created_at')
        # serialize and return JsonResponse({'tickets': data})
    elif request.method == 'POST':
        # create from request.POST + request.FILES
        return JsonResponse({'success': True, 'ticket_id': ticket.id})

# Detail + Edit + Delete
@csrf_exempt
@user_passes_test(is_admin)
def admin_airline_ticket_detail_api(request, pk):
    ticket = get_object_or_404(AirlineTicket, pk=pk)
    if request.method == 'POST':
        # update fields from request.POST
        ticket.save()
        return JsonResponse({'success': True})
    elif request.method == 'DELETE':
        ticket.delete()
        return JsonResponse({'success': True})
```

### URLs in `core_admin/config/urls.py`

```python
path('dashboard/admin/api/airline-tickets/', accounts_views.admin_airline_tickets_api, name='admin_airline_tickets_api'),
path('dashboard/admin/api/airline-tickets/<int:pk>/', accounts_views.admin_airline_ticket_detail_api, name='admin_airline_ticket_detail_api'),
```

### Frontend in `overview.html`

1. Add sidebar button inside `<nav>` (follow existing button class pattern)
2. Add `<div id="tab-content-airline-ticketing" class="tab-pane hidden space-y-8">` inside workspace div
3. Add `'airline-ticketing': 'Airline Ticketing'` to `tabTitles` JS object
4. Add `else if (currentTab === "airline-ticketing") { ... }` branch in `syncData()`
5. Use `FormData` for create/edit, `new URLSearchParams` for status-only changes
6. Use `confirm()` for delete confirmation
7. Follow existing table row class: `hover:bg-white/[0.01] transition-all border-b border-white/5`
8. Create modal following `#package-modal` pattern (inline HTML div with `hidden` class)

---

*Documentation generated: 2026-07-22*  
*Scanned files:*  
- `core_admin/config/urls.py` (178 lines)
- `core_admin/apps/accounts/views.py` (4124 lines)
- `core_admin/apps/content/views.py` (220 lines)
- `core_admin/apps/blog/admin_views.py` (375 lines)
- `core_admin/apps/accounts/models.py` (131 lines)
- `core_admin/templates/dashboard/admin/overview.html` (4172 lines)
- `core_admin/templates/dashboard/admin/blogs_list.html` (654 lines)
- `core_admin/templates/base.html` (48 lines)

