# Golden Star Agency — B2B2C Multi-Tenant Travel Platform
## Complete Technical Documentation

Welcome to the technical documentation for the **Golden Star Agency** multi-tenant travel SaaS platform. This documentation is written for developers to help them understand the system architecture, database models, APIs, background workers, frontend rendering, and integrations of this codebase.

---

## 1. Project Overview

### 1.1 Purpose & Target Market
Golden Star Agency is a multi-tenant SaaS travel platform designed specifically for the Pakistani travel market. It specializes in Hajj, Umrah, family/group packages, visit visa services, automated flight ticketing, and B2B agent-client management. It supports multi-tenant operations, separating travel agencies, their agents, and customers.

### 1.2 Core Implemented Features
- **User Authentication & Authorization**: Fully configured role-based access control with `super_admin`, `agent`, and `customer` roles. Includes non-blocking email verification and OTP validation.
- **Agent Ledger & B2B Wallets**: Financial transaction logging (credits, debits, adjustments) for agent wallets, supporting commission processing and running balance tracking.
- **Flight Catalog & Detail**: Admin interface for publishing flights, partner airlines, and tickets.
- **Visa Application Tracking**: State management of visa requests (`pending`, `submitted`, `approved`, `rejected`) linked to specific countries and passport numbers.
- **AI-Powered Travel Counselor Chatbot**: LangChain integration querying a pgvector travel inventory with a local fallback similarity search using NumPy.
- **Dynamic Charting**: Premium admin and agent dashboards featuring dynamic matplotlib-generated line, pie, and bar charts.
- **CMS & Publishing**: Category-based blogs and platforms reviews (with admin moderation APIs).
- **Automation Pipeline Infrastructure**: Out-of-the-box support for n8n webhook routing and template daemons.

### 1.3 Work-In-Progress (WIP) & Roadmap Features
- **Global Distribution System (GDS) Integration**: Connect mock/sandbox flights endpoints to live systems like Sabre or Amadeus.
- **B2B Wallet Settlement Integrations**: Local gateway integrations (EasyPaisa, JazzCash, HBL) for wallet refills.
- **WhatsApp Notification Service**: Fully automated WhatsApp notification triggers for sending PDF booking vouchers.
- **AI Personalization**: Enhancements to the chatbot allowing semantic user-preference profile matches.
- **Security Encryption**: Implementing application-level Fernet cryptography for passport and identity card details.

---

## 2. High-Level Architecture

### 2.1 Tech Stack
The platform uses a decoupled microservices-based architecture:
- **Backend Framework**: Django `4.2.x` (Core Admin panel, CMS, ledger, agent system, authentication).
- **API Engine**: FastAPI `0.100.x` (High-frequency async endpoints, AI Chatbot).
- **Database**: PostgreSQL `14+` with the `pgvector` extension.
- **Caching & Event Broker**: Redis `7.x` (Celery task queue & FastAPI session cache).
- **Asynchronous Workers**: Celery `5.3.x` (Background jobs).
- **Automation Server**: n8n (External alert triggers & notification workflows).
- **DevOps**: Docker, Docker Compose, Nginx (Reverse proxy), Systemd.

### 2.2 System Architecture Diagram
```mermaid
graph TD
    %% Clients & Entrypoints
    SuperAdmin[Super Admin] -->|Manages CMS / Rates / Agents| DjangoApp[Django Core Admin :8000]
    Agent[Agent Portal] -->|Bookings / Ledger / Profiles| DjangoApp
    Customer[Customer Web Client] -->|Browse Packages / Track Booking| DjangoApp
    Customer -->|Interacts with Counselor Chatbot| FastAPIApp[FastAPI Async Services :8001]

    %% Django Subsystem
    subgraph Django Subsystems [Django Core Apps]
        DjangoApp --> Accounts[apps.accounts]
        DjangoApp --> Bookings[apps.bookings]
        DjangoApp --> Payments[apps.payments]
        DjangoApp --> Visa[apps.visa]
        DjangoApp --> Flights[apps.flights]
        DjangoApp --> Packages[apps.packages]
        DjangoApp --> Content[apps.content]
        DjangoApp --> Blog[apps.blog]
    end

    %% FastAPI Subsystem
    subgraph FastAPI Subsystems [FastAPI Async Services]
        FastAPIApp --> RouterBookings[routers.bookings]
        FastAPIApp --> RouterChatbot[routers.chatbot]
        FastAPIApp --> RouterPackages[routers.packages]
        FastAPIApp --> RouterVisa[routers.visa]
        FastAPIApp --> RouterFlights[routers.flights]
        
        RouterChatbot --> LangChain[LangChain Chat Chain]
        LangChain --> Claude[Anthropic Claude API]
    end

    %% Tasks & Brokers
    DjangoApp -->|Enqueues Tasks| Celery[Celery Task Worker]
    Celery -->|Task Broker / Results Backend| Redis[(Redis Broker :6379)]
    FastAPIApp -->|Session Cache| Redis

    %% Shared Storage
    Accounts --> DB[(PostgreSQL + pgvector :5432)]
    Bookings --> DB
    Payments --> DB
    RouterBookings --> DB
    LangChain -->|pgvector Query / Cosine Search| DB
    
    %% Integrations
    DjangoApp -->|Webhook Triggers| n8n[n8n Automation Engine :5678]
    n8n -->|Sends SMS / Alerts| WhatsApp[WhatsApp Business API]
```

### 2.3 Run Commands & Port Mapping
| Service | Cwd | Run Command | Default Port |
| :--- | :--- | :--- | :--- |
| **Django Core** | `/core_admin` | `python manage.py runserver 127.0.0.1:8000` | `8000` |
| **FastAPI Async** | `/` | `uvicorn fast_api.main:app --port 8001 --reload` | `8001` |
| **Celery Worker** | `/core_admin` | `celery -A config worker --loglevel=info` | N/A |
| **Redis Server** | Local Machine | `redis-server` | `6379` |
| **PostgreSQL** | Local Machine | PostgreSQL Database Engine | `5432` |
| **n8n Engine** | Local Machine | `n8n start` (or Docker-run) | `5678` |

---

## 3. Database Schema

All database tables are owned and migrated by **Django ORM** (`core_admin/`). FastAPI shares access by pointing to the same Postgres instance and querying the migrated tables (e.g., `packages_package` is mapped to FastAPI SQLAlchemy models).

### 3.1 Entity-Relationship (ER) Diagram
```mermaid
erDiagram
    User ||--o{ LoginHistory : "has log history"
    User ||--o{ AgentReview : "receives reviews"
    User ||--o{ AgentLedger : "has ledger entries"
    User ||--o{ AgentLedger : "creates ledger entry"
    User ||--o{ Booking : "makes booking"
    User ||--o{ VisaApplication : "submits application"
    User ||--o{ FlightQuoteRequest : "submits flight request"
    
    Package ||--o{ Booking : "has bookings"
    
    Flight ||--|{ FlightTicket : "has tickets"
    
    BlogCategory ||--o{ BlogPost : "categorizes"
```

### 3.2 App-by-App Database Model Definitions

#### 3.2.1 `apps.accounts`
Responsible for authentication, permissions, profile settings, partner registrations, ratings, and financial ledgers for agents.
- **User Model (`User`)**
  - Inherits from `AbstractUser`.
  - `role`: `CharField(max_length=20, default='customer')`. Choices: `[('super_admin', 'Super Admin'), ('agent', 'Agent'), ('customer', 'Customer')]`.
  - `phone`: `CharField(max_length=20, null=True, blank=True)`.
  - `address`: `CharField(max_length=255, null=True, blank=True)`.
  - `is_verified_partner`: `BooleanField(default=False)`.
  - `is_email_verified`: `BooleanField(default=False)`.
  - `email_verification_code`: `CharField(max_length=6, null=True, blank=True)`.
  - `otp_created_at`: `DateTimeField(null=True, blank=True)`.
  - `company_name`: `CharField(max_length=100, null=True, blank=True)`.
  - `id_card_front`: `ImageField(upload_to='id_cards/', null=True, blank=True)`.
  - `id_card_back`: `ImageField(upload_to='id_cards/', null=True, blank=True)`.
  - `profile_photo`: `ImageField(upload_to='profiles/', null=True, blank=True)`.
  - `cover_photo`: `ImageField(upload_to='covers/', null=True, blank=True)`.
  - `about`: `TextField(null=True, blank=True)`.
  - `rating`: `FloatField(default=5.0)`.
  - `approval_status`: `CharField(max_length=20, default='pending')`. Choices: `[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('suspended', 'Suspended')]`.

- **LoginHistory Model (`LoginHistory`)**
  - `user`: `ForeignKey(User, on_delete=CASCADE, related_name='login_history')`.
  - `ip_address`: `GenericIPAddressField(null=True, blank=True)`.
  - `user_agent`: `TextField(null=True, blank=True)`.
  - `timestamp`: `DateTimeField(auto_now_add=True)`.

- **AgentReview Model (`AgentReview`)**
  - `agent`: `ForeignKey(User, on_delete=CASCADE, related_name='reviews_received')`.
  - `author_name`: `CharField(max_length=100)`.
  - `rating`: `IntegerField(default=5)`.
  - `comment`: `TextField()`.
  - `created_at`: `DateTimeField(auto_now_add=True)`.

- **AgentLedger Model (`AgentLedger`)**
  - `agent`: `ForeignKey(User, on_delete=CASCADE, related_name='ledger_entries', limit_choices_to={'role': 'agent'})`.
  - `entry_type`: `CharField(max_length=10)`. Choices: `[('credit', 'Credit'), ('debit', 'Debit')]`.
  - `category`: `CharField(max_length=20, default='commission')`. Choices: `[('commission', 'Commission Earned'), ('payment', 'Payment Received'), ('refund', 'Refund Issued'), ('adjustment', 'Manual Adjustment'), ('penalty', 'Penalty / Deduction'), ('advance', 'Advance Payment'), ('other', 'Other')]`.
  - `amount`: `DecimalField(max_digits=12, decimal_places=2)`.
  - `description`: `TextField(blank=True)`.
  - `reference`: `CharField(max_length=100, blank=True)`.
  - `created_by`: `ForeignKey(User, on_delete=SET_NULL, null=True, blank=True, related_name='ledger_created')`.
  - `created_at`: `DateTimeField(auto_now_add=True)`.
  - Meta: `ordering = ['-created_at']`.

#### 3.2.2 `apps.packages`
Defines packages offered (Hajj, Umrah, Tour packages).
- **Package Model (`Package`)**
  - `title`: `CharField(max_length=200)`.
  - `description`: `TextField()`.
  - `price`: `DecimalField(max_digits=10, decimal_places=2)`.
  - `category`: `CharField(max_length=50)`.
  - `duration_days`: `IntegerField()`.
  - `embedding`: `JSONField(null=True, blank=True)`. (Stores 384-dimensional semantic embedding generated via sentence-transformers).
  - `created_at`: `DateTimeField(auto_now_add=True)`.
  - `updated_at`: `DateTimeField(auto_now=True)`.

#### 3.2.3 `apps.bookings`
Manages purchases and orders.
- **Booking Model (`Booking`)**
  - `user`: `ForeignKey(User, on_delete=CASCADE, related_name='bookings')`.
  - `package`: `ForeignKey(Package, on_delete=SET_NULL, null=True, blank=True, related_name='bookings')`.
  - `booking_type`: `CharField(max_length=20, default='package')`. Choices: `[('package', 'Package Booking'), ('custom', 'Custom Booking')]`.
  - `status`: `CharField(max_length=20, default='pending')`. Choices: `[('pending', 'Pending Approval'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')]`.
  - `total_price`: `DecimalField(max_digits=10, decimal_places=2)`.
  - `created_at`: `DateTimeField(auto_now_add=True)`.
  - `updated_at`: `DateTimeField(auto_now=True)`.

#### 3.2.4 `apps.visa`
Handles visa application processing.
- **VisaApplication Model (`VisaApplication`)**
  - `user`: `ForeignKey(User, on_delete=CASCADE, related_name='visa_applications')`.
  - `country`: `CharField(max_length=100)`.
  - `passport_number`: `CharField(max_length=50)`.
  - `status`: `CharField(max_length=20, default='pending')`. Choices: `[('pending', 'Pending'), ('submitted', 'Submitted to Embassy'), ('approved', 'Approved'), ('rejected', 'Rejected')]`.
  - `created_at`: `DateTimeField(auto_now_add=True)`.
  - `updated_at`: `DateTimeField(auto_now=True)`.

#### 3.2.5 `apps.flights`
Ecosystem for cataloging flights and flight quote inquiries.
- **AirlinePartner Model (`AirlinePartner`)**
  - `name`: `CharField(max_length=100)`.
  - `icon_class`: `CharField(max_length=50, default='fa-solid fa-plane')`.
  - `description`: `CharField(max_length=150, default='Official Partner')`.
  - `is_active`: `BooleanField(default=True)`.
  - `created_at`: `DateTimeField(auto_now_add=True)`.

- **Flight Model (`Flight`)**
  - `airline_name`: `CharField(max_length=100)`.
  - `flight_number`: `CharField(max_length=50)`.
  - `departure_city`: `CharField(max_length=100)`.
  - `destination_city`: `CharField(max_length=100)`.
  - `departure_time`: `DateTimeField()`.
  - `arrival_time`: `DateTimeField()`.
  - `image`: `ImageField(upload_to='flights/', null=True, blank=True)`.
  - `static_image_name`: `CharField(max_length=100, null=True, blank=True, default='flights_banner.png')`.
  - `description`: `TextField(null=True, blank=True)`.
  - `is_active`: `BooleanField(default=True)`.
  - `created_at`: `DateTimeField(auto_now_add=True)`.

- **FlightTicket Model (`FlightTicket`)**
  - `flight`: `ForeignKey(Flight, on_delete=CASCADE, related_name='tickets')`.
  - `ticket_class`: `CharField(max_length=20, default='economy')`. Choices: `[('economy', 'Economy Class'), ('business', 'Business Class'), ('first', 'First Class')]`.
  - `price`: `DecimalField(max_digits=10, decimal_places=2)`.
  - `baggage_allowance`: `CharField(max_length=50, default='30 KG')`.
  - `refund_policy`: `CharField(max_length=100, default='Refundable with fee')`.
  - `seats_available`: `PositiveIntegerField(default=10)`.

- **FlightQuoteRequest Model (`FlightQuoteRequest`)**
  - `user`: `ForeignKey(User, on_delete=CASCADE, related_name='flight_requests')`.
  - `departure_city`: `CharField(max_length=100)`.
  - `destination_city`: `CharField(max_length=100)`.
  - `departure_date`: `DateField()`.
  - `return_date`: `DateField(null=True, blank=True)`.
  - `status`: `CharField(max_length=20, default='pending')`. Choices: `[('pending', 'Pending Quote'), ('quoted', 'Quoted'), ('booked', 'Booked'), ('cancelled', 'Cancelled')]`.
  - `price_quote`: `DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)`.
  - `created_at`: `DateTimeField(auto_now_add=True)`.
  - `updated_at`: `DateTimeField(auto_now=True)`.

#### 3.2.6 `apps.content`
Platform review curation and milestone logs.
- **PlatformReview Model (`PlatformReview`)**
  - `name`: `CharField(max_length=100)`.
  - `reviewer_title`: `CharField(max_length=120, null=True, blank=True)`.
  - `email`: `EmailField(null=True, blank=True)`.
  - `rating`: `IntegerField(default=5)`.
  - `comment`: `TextField()`.
  - `photo`: `ImageField(upload_to='reviews/photos/', null=True, blank=True)`.
  - `is_approved`: `BooleanField(default=True)`.
  - `is_featured`: `BooleanField(default=False)`.
  - `created_at`: `DateTimeField(auto_now_add=True)`.
  - Meta: `ordering = ['-is_featured', '-created_at']`.

- **Achievement Model (`Achievement`)**
  - `title`: `CharField(max_length=200)`.
  - `category`: `CharField(max_length=20, default='milestone')`. Choices: `[('review', 'Review'), ('video', 'Video / Media'), ('meeting', 'Meeting / Event'), ('milestone', 'Milestone / Award')]`.
  - `description`: `TextField(null=True, blank=True)`.
  - `photo`: `ImageField(upload_to='achievements/', null=True, blank=True)`.
  - `video_url`: `URLField(null=True, blank=True)`.
  - `date`: `DateField(null=True, blank=True)`.
  - `is_active`: `BooleanField(default=True)`.
  - `created_at`: `DateTimeField(auto_now_add=True)`.
  - Meta: `ordering = ['-date', '-created_at']`.

#### 3.2.7 `apps.blog`
CMS logic for categories and blog publishing.
- **BlogCategory Model (`BlogCategory`)**
  - `name`: `CharField(max_length=80)`.
  - `slug`: `SlugField(unique=True, blank=True)`.
  - `color`: `CharField(max_length=30, default='brand-orange')`.
  - Meta: `ordering = ['name']`.

- **BlogPost Model (`BlogPost`)**
  - `title`: `CharField(max_length=200)`.
  - `slug`: `SlugField(unique=True, blank=True, max_length=220)`.
  - `category`: `ForeignKey(BlogCategory, on_delete=SET_NULL, null=True, blank=True, related_name='posts')`.
  - `cover_image`: `ImageField(upload_to='blog/covers/', null=True, blank=True)`.
  - `static_cover`: `CharField(max_length=120, null=True, blank=True)`.
  - `excerpt`: `TextField(max_length=300, blank=True)`.
  - `body`: `TextField()`.
  - `author_name`: `CharField(max_length=100, default='Golden Star Team')`.
  - `author_avatar`: `CharField(max_length=120, null=True, blank=True)`.
  - `read_time`: `PositiveIntegerField(default=5)`.
  - `is_featured`: `BooleanField(default=False)`.
  - `status`: `CharField(max_length=10, default='draft')`. Choices: `[('draft', 'Draft'), ('published', 'Published')]`.
  - `views`: `PositiveIntegerField(default=0, editable=False)`.
  - `published_at`: `DateTimeField(null=True, blank=True)`.
  - `created_at`: `DateTimeField(auto_now_add=True)`.
  - `updated_at`: `DateTimeField(auto_now=True)`.
  - Meta: `ordering = ['-published_at', '-created_at']`.

#### 3.2.8 Empty/Boilerplate Apps
The following applications are currently scaffolding placeholders with empty models files:
- `apps.companies` (Tenant management B2B shell)
- `apps.customers` (Customer documents & histories shell)
- `apps.payments` (B2B wallet ledger helper module)
- `apps.notifications` (Notification templates & worker triggers)
- `apps.common` (Base Model abstract classes)

### 3.3 Encrypted/Sensitive Fields Status
- **Sensitive data**: Passport Numbers (`VisaApplication.passport_number`), Identity Cards (`User.id_card_front`, `User.id_card_back`), email addresses, and phone numbers are collected on the platform.
- **Encryption Status**: **No application-level encryption is active.** standard plain-text parameters are stored inside Postgres tables. Encryption fields with cryptographic Fernet keys (referenced via `ENCRYPTION_KEY` in `.env.example`) are planned in Phase 3/4.

---

## 4. API Endpoints

### 4.1 Django Core Endpoints (`core_admin/config/urls.py`)
All endpoints are synchronous unless stated otherwise.
- **Public Website & Auth:**
  - `GET /` : Home page view. (No Auth)
  - `GET /about/` : About page template view. (No Auth)
  - `GET /contact/` : Contact page template view. (No Auth)
  - `GET /careers/` : Careers page template view. (No Auth)
  - `GET /privacy-policy/` : Privacy policy template view. (No Auth)
  - `GET /achievements/` : Achievements lists. (No Auth)
  - `GET /packages/hajj/` : Hajj listing placeholder. (No Auth)
  - `GET /packages/umrah/` : Umrah listing placeholder. (No Auth)
  - `GET /packages/<int:pk>/` : Package detail placeholder. (No Auth)
  - `GET /visa/` : Visa countries guide list. (No Auth)
  - `GET /visa/apply/` : Visa application form. (No Auth)
  - `GET /flights/` : Flight listing and tickets detail view. (No Auth)
  - `GET /flights/<int:pk>/` : Specific flight and ticket details. (No Auth)
  - `GET /flights/quote/` : Flight quote request template form. (No Auth)
  - `GET /blogs/` : Categories and published articles listing. (No Auth)
  - `GET /blogs/<slug:slug>/` : Full article presentation and related posts layout. (No Auth)
  - `GET/POST /auth/login/` : Login handler. (No Auth)
  - `GET/POST /auth/signup/` : Registration view for customers and agents. (No Auth)
  - `GET /auth/logout/` : Log out session. (No Auth)
  - `GET/POST /auth/verify-email/<int:user_id>/` : Email validation OTP screen. (No Auth)
  - `GET /auth/resend-otp/<int:user_id>/` : Triggers verification OTP email retry. (No Auth)
  - `GET /auth/pending-approval/` : Approval queue message for agents. (No Auth)
  - `GET/POST /auth/signup/agent/verify/<int:user_id>/` : Step 2 email verification for partner registration. (No Auth)
  - `GET/POST /auth/signup/agent/documents/<int:user_id>/` : Step 3 document upload wizard for partner registration. (No Auth)
  - `GET/POST /auth/forgot-password/` : Request forgot password reset. (No Auth)
  - `GET/POST /auth/forgot-password/verify/` : Password reset OTP verification screen. (No Auth)
  - `GET/POST /auth/forgot-password/reset/<int:user_id>/` : Assign new credentials. (No Auth)

- **User Dashboards (Auth Required):**
  - `GET /dashboard/customer/` : Client historical records and status overview. (Requires `customer` role)
  - `GET /dashboard/agent/` : Agent wallet metrics, bookings log, visa tasks, and flight quotes interface. (Requires `agent` role)
  - `GET /dashboard/admin/` : Super admin dashboard displaying partner lists, reviews moderation, client accounts, and achievement logs. (Requires `super_admin` role)
  - `GET /dashboard/admin/agents/<str:agent_id>/view/` : Detailed profile review for agent validation. (Requires `super_admin`)
  - `GET /dashboard/agent/chart/` : Monthly metrics chart page for agents. (Requires `agent`)
  - `GET /dashboard/agent/profile-settings/` : Edit agent profile. (Requires `agent`)

- **Interactive Dashboard Matplotlib Chart Engine Endpoints (Auth Required):**
  - `GET /dashboard/agent/chart/pie/` : Renders custom donut chart PNG. (Requires `agent`)
  - `GET /dashboard/agent/chart/bar/` : Renders custom grouped bar chart PNG. (Requires `agent`)
  - `GET /dashboard/admin/chart/trend/` : Monthly volumetric trend chart PNG. (Requires `super_admin`)
  - `GET /dashboard/admin/chart/pie/` : Platform activity mix donut chart PNG. (Requires `super_admin`)
  - `GET /dashboard/admin/chart/agents/` : Agent registration mix bar chart PNG. (Requires `super_admin`)

- **REST / AJAX API Endpoints (Auth Required/Admin Restricted):**
  - `GET /dashboard/agent/api/overview-stats/` : Dynamic JSON metrics of counts. (Requires `agent`)
  - `GET /dashboard/agent/api/bookings/` : Returns JSON list of logged bookings under active agent. (Requires `agent`)
  - `GET /dashboard/agent/api/visas/` : Returns JSON list of visa applications. (Requires `agent`)
  - `GET /dashboard/agent/api/flights/` : Returns JSON list of flight quote requests. (Requires `agent`)
  - `GET /dashboard/agent/chart/data/` : JSON dataset of trend counts, pie splits, and bar inputs. (Requires `agent`)
  - `GET /dashboard/admin/api/agents/` : Returns detailed list of registered agent partners. (Requires `super_admin`)
  - `POST /dashboard/admin/api/agents/<str:agent_id>/approve/` : Set agent status to approved (sends approval email). (Requires `super_admin`)
  - `POST /dashboard/admin/api/agents/<str:agent_id>/reject/` : Set agent status to rejected (sends rejection email). (Requires `super_admin`)
  - `POST /dashboard/admin/api/agents/<str:agent_id>/suspend/` : Suspend agent wallet and access. (Requires `super_admin`)
  - `POST /dashboard/admin/api/agents/<str:agent_id>/toggle-badge/` : Toggle partner verification badge. (Requires `super_admin`)
  - `GET /dashboard/admin/api/agents/<str:agent_id>/details/` : Returns validation data of a specific agent. (Requires `super_admin`)
  - `GET /dashboard/admin/api/overview-stats/` : Super Admin statistics (total revenue, agents approval counts, etc.). (Requires `super_admin`)
  - `GET /dashboard/admin/api/packages/` : List catalog packages. (Requires `super_admin`)
  - `GET/POST /dashboard/admin/api/packages/<int:pk>/` : Update package. (Requires `super_admin`)
  - `GET /dashboard/admin/api/visas/` : All global visa applications lists. (Requires `super_admin`)
  - `POST /dashboard/admin/api/visas/<int:pk>/` : Transition status of application. (Requires `super_admin`)
  - `GET /dashboard/admin/api/flights/` : All flight inquiries list. (Requires `super_admin`)
  - `POST /dashboard/admin/api/flights/<int:pk>/` : Transition status of flight quotes. (Requires `super_admin`)
  - `GET /dashboard/admin/api/bookings/` : Retrieve all global bookings. (Requires `super_admin`)
  - `POST /dashboard/admin/api/bookings/<int:pk>/` : Transition booking approval state. (Requires `super_admin`)
  - `GET /dashboard/admin/chart/data/` : Renders administrative metrics data. (Requires `super_admin`)
  - `GET /dashboard/admin/api/reviews/` : Reviews moderation list. (Requires `super_admin`)
  - `POST /dashboard/admin/api/reviews/<int:review_id>/toggle/` : Toggle review approval. (Requires `super_admin`)
  - `DELETE/POST /dashboard/admin/api/reviews/<int:review_id>/delete/` : Delete review from platform. (Requires `super_admin`)
  - `GET /dashboard/admin/api/achievements/` : Retrieve all achievements. (Requires `super_admin`)
  - `POST /dashboard/admin/api/achievements/create/` : Create achievement. (Requires `super_admin`)
  - `POST/DELETE /dashboard/admin/api/achievements/<int:pk>/` : Edit or Delete achievement. (Requires `super_admin`)
  - `GET /dashboard/admin/api/clients/` : Retrieve all customer client users list. (Requires `super_admin`)
  - `POST /dashboard/admin/api/clients/<int:client_id>/toggle/` : Toggle block/unblock customer active status. (Requires `super_admin`)
  - `GET /dashboard/admin/api/agents/<int:agent_id>/ledger/` : Retrieve ledger ledger entries, debit/credit totals, and running balance. (Requires `super_admin`)
  - `POST /dashboard/admin/api/agents/<int:agent_id>/ledger/add/` : Append transaction entry to agent wallet ledger. (Requires `super_admin`)
  - `DELETE/POST /dashboard/admin/api/ledger/<int:entry_id>/delete/` : Remove entry. (Requires `super_admin`)
  - `GET /api/reviews/` : Public reviews fetching list. (No Auth)
  - `POST /api/reviews/submit/` : Submit user review. (No Auth)
  - `GET /api/track/<str:tracking_id>/` : Public order tracker (parses Hajj/Umrah package tracking codes). (No Auth)

#### Example Request/Response: Platform Review Submission API
- **Endpoint**: `/api/reviews/submit/` (POST)
- **Request payload (JSON)**:
  ```json
  {
    "name": "Kamran Khan",
    "email": "kamran@gmail.com",
    "rating": 5,
    "comment": "Outstanding Umrah services! Highly recommended."
  }
  ```
- **Response payload (JSON)**:
  ```json
  {
    "success": true,
    "message": "Review submitted successfully!",
    "review": {
      "id": 4,
      "name": "Kamran Khan",
      "rating": 5,
      "comment": "Outstanding Umrah services! Highly recommended.",
      "created_at": "2026-07-18 10:15"
    }
  }
  ```

---

### 4.2 FastAPI Async Services (`fast_api/`)
All routes share database connections using connection pools. FastAPI is configured with simple JWT security dependencies (`get_current_user`), but endpoints are currently left public (mock responses) for Phase 1 testing.

- **FastAPI Endpoints Matrix**:
  - `GET /` : Health check. Returns online indicators. (No Auth)
  - `GET /packages/` : Package list mockup. (No Auth)
  - `GET /packages/{package_id}` : Specific package detail. (No Auth)
  - `POST /bookings/` : Creates a package booking. (No Auth)
  - `GET /bookings/{booking_id}` : Get status of package order. (No Auth)
  - `POST /payments/pay` : Processes financial payment transactions. (No Auth)
  - `GET /visa/countries` : Lists mock countries and pricing rules. (No Auth)
  - `POST /visa/apply` : Submits visa requests. (No Auth)
  - `POST /flights/quote` : Request flight tickets price quotation. (No Auth)
  - `GET /n8n/sync-data` : Automation server synchronization hook. (No Auth)
  - `POST /chatbot/message` : Processes customer queries via the AI LangChain pipeline. (No Auth)

#### Example Request/Response: FastAPI AI Chatbot Conversation API
- **Endpoint**: `/chatbot/message` (POST)
- **Request Parameters**:
  - `message`: "Do you have any cheap Umrah packages?"
  - `session_id`: "user_xyz_789"
- **Response payload (JSON)**:
  ```json
  {
    "reply": "Assalamu Alaikum! Yes, we have an 'Umrah Special Package' for 15 Days priced at PKR 150,000. It includes hotels and transfers. Would you like to check it out?",
    "session_id": "user_xyz_789"
  }
  ```

---

## 5. Background Jobs (Celery)

### 5.1 Celery Setup
The system initializes Celery inside `core_admin/config/celery.py` and points to the Redis server (`REDIS_URL=redis://127.0.0.1:6379/0`) as the broker and result backend.

### 5.2 Task Definitions (`core_admin/apps/notifications/tasks.py`)
- **`send_notification_email(recipient_email, subject, body)`**
  - **Purpose**: Sends transaction notifications, registration details, or invoices to customers and agent partners asynchronously, avoiding SMTP socket network blocks in views.
  - **Retry Logic**: Defaults to the standard Celery fallback. No custom retry policy is defined in code.
  - **Model updates**: None. It behaves as a notification dispatch service.

### 5.3 Celery Beat Schedule
- **Schedule configuration**: No periodic Celery Beat schedule tasks are configured or active inside `settings.py` or `celery.py` currently. (Marked as: **Not implemented yet**).

---

## 6. External Integrations

### 6.1 GDS Providers (Flights Search)
- **Concrete integration status**: **Not implemented yet.** Flight quotation endpoints return mocked quotes and static partner databases (`AirlinePartner`, `Flight`) populated through seeds. No live connections to Amadeus or Sabre APIs are established.

### 6.2 Payment Gateways
- **Gateway status**: **Not implemented yet.** The payment API (`/payments/pay`) uses static JSON response indicators (`{"status": "success", "transaction_id": "TXN123456"}`). No live endpoints for Stripe, EasyPaisa, or JazzCash are active.

### 6.3 WhatsApp Business API
- **WhatsApp status**: **Not implemented yet.** Social links are populated on templates, but no server code integrates with Twilio or official WhatsApp APIs.

### 6.4 n8n Webhook Broker
- **Location**: n8n routers are configured inside FastAPI (`fast_api/routers/bot_readonly.py`) pointing to `/n8n/sync-data`.
- **Environment variables**: `N8N_WEBHOOK_URL` is declared in `.env.example` but is not active inside the core Django/FastAPI handlers.
- **Workflow configuration**: Located in `automation/workflows/`. Four nodes configurations are pre-defined as placeholders:
  - `chatbot-handler.json`
  - `lead-notification.json`
  - `booking-status-broadcast.json`
  - `content-auto-publish.json`
  These files contain standard initialization nodes ready to be imported into an active n8n GUI dashboard.

---

## 7. AI/ML Components

### 7.1 LangChain & Chatbot Setup (`ai_chatbot/chain.py`)
The system constructs a retrieval chain using LangChain's pipeline integration:
- **LLM Engine**: Anthropic Claude `claude-3-haiku-20240307` model. If no API key (`CLAUDE_API_KEY`) is active, it fails gracefully and outputs a clean mock response.
- **Context Builder**: The conversation binds the system prompt and semantically retrieved packages directly into a ChatPromptTemplate.
- **System Prompt**: Loaded dynamically from `ai_chatbot/prompts/system_prompt.txt`. Falls back to default helper string: `"You are a helpful travel assistant for Golden Star Agency."`

### 7.2 Embeddings Service (`ai_chatbot/embeddings.py`)
Text documents are converted into dense vector arrays.
- **Model**: Local sentence-transformers model `all-MiniLM-L6-v2`. It maps package information to 384-dimensional vector spaces.

### 7.3 Vector Retriever (`ai_chatbot/retriever.py`)
- **pgvector Vector Database Schema**:
  - The `Package` table inside PostgreSQL matches the query using the cosine distance operator `<->`.
  - SQL query executed:
    ```sql
    SELECT id, title, description, price, category, (embedding <-> :vector) AS distance
    FROM packages_package
    ORDER BY distance ASC LIMIT :limit;
    ```
- **Local Cosine Fallback**:
  - If pgvector is not installed on the database backend, the system catches the error, downloads all package records, loads raw embeddings, and computes cosine similarity locally using **NumPy**'s linear algebra package:
    ```python
    similarity = np.dot(query_vector, db_vector) / (norm_q * norm_db)
    ```

---

## 8. Provider Abstraction Layers

- **Abstract layers & Providers (Amadeus / Duffel)**: **Not implemented yet.** There are no active provider abstraction classes or factory functions in this codebase. Flight partner records are queried directly from the local database.

---

## 9. Frontend & Dashboard

### 9.1 Templates Architecture
The frontend uses Django Templates server-side rendering combined with tailwind CSS layouts and interactive elements:
- `/core_admin/templates/`: Core templates folder.
- `base.html`: Main HTML file layout holding script calls.
- `partials/`: Includes global navigation (`navbar.html`) and footer links.
- `dashboard/customer/overview.html`: User portal.
- `dashboard/agent/overview.html`: Travel Agent portal containing wallet, profile setups, and lists.
- `dashboard/admin/overview.html` & `agent_detail.html`: Administrative portals for partner checkouts.

### 9.2 AJAX Polling Workflows
To avoid complete page reloads, the dashboards run asynchronous AJAX loops using the browser's native `fetch` API:
- **Travel Agent Portal (`agent/overview.html`):**
  - **Overview Stats Polling**: Polls `/dashboard/agent/api/overview-stats/` every **4 seconds** (`setInterval(syncData, 4000)`) to update bookings counts, visa logs, and flight requests in real-time.
  - **Charts Polling**: Polls `/dashboard/agent/chart/data/` every **30 seconds** (`setInterval(loadCharts, 30000)`) to refresh the Chart.js visual data canvases (Trend, activity pie, and categories bar graphs).
- **Super Admin Portal (`admin/overview.html`):**
  - **Overview Stats Polling**: Polls `/dashboard/admin/api/overview-stats/` every **4 seconds** (`setInterval(syncData, 4000)`) to update counts.
  - **Charts Polling**: Polls `/dashboard/admin/chart/data/` every **30 seconds** (`setInterval(loadCharts, 30000)`) to update administrative reports.

---

## 10. Environment Variables

All variables are read at runtime using the `python-decouple` config method. Below is the list of variables found in `.env.example`:

| Variable | Purpose | Example Value |
| :--- | :--- | :--- |
| `SECRET_KEY` | Django security key used for cryptographic signing of sessions. | `django-insecure-replace-this-with-a-real-key` |
| `DEBUG` | Enables or disables Django verbose debug output on errors. | `True` |
| `ALLOWED_HOSTS` | Comma-separated domains allowed to connect to the Django server. | `localhost,127.0.0.1` |
| `DATABASE_URL` | Database connection URL in standard Postgres engine format. | `postgresql://postgres:postgres@localhost:5432/golden_star_db` |
| `REDIS_URL` | URL connection endpoint for the Redis Celery broker. | `redis://localhost:6379/0` |
| `ENCRYPTION_KEY` | Cryptography base64 key intended for sensitive fields encryption (WIP). | `your-32-byte-base64-encryption-key-here` |
| `JWT_SECRET_KEY` | Signature key for JWT verification shared between Django and FastAPI. | `your-jwt-signing-key-here` |
| `CLAUDE_API_KEY` | Anthropic Claude API credential token for the travel chatbot. | `your-anthropic-api-key-here` |
| `GROQ_API_KEY` | Groq developer API key for fallback LLM generation. | `your-groq-api-key-here` |
| `N8N_WEBHOOK_URL` | Base url endpoint of the n8n automation webhook server. | `http://localhost:5678/webhook/` |
| `ENVIRONMENT` | Running context environment tag. | `development` |

---

## 11. Setup & Run Instructions

To set up the system locally, follow these steps:

### 11.1 Prerequisites
Ensure you have the following installed:
- **Python 3.10+**
- **PostgreSQL 14+** (with pgvector compiled/enabled)
- **Redis Server**

### 11.2 Installation
1. Clone the project and navigate to the root directory.
2. Initialize and activate a Python virtual environment:
   ```powershell
   # Windows PowerShell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy environment configurations:
   ```bash
   cp .env.example .env
   ```
   *(Ensure to configure `DATABASE_URL` and `REDIS_URL` in `.env` to match your local setup).*

### 11.3 Database Initialization
Compile Django ORM migrations and apply them to Postgres:
```bash
cd core_admin
python manage.py migrate
```

Seed initial CMS content, blogs, reviews, and test accounts:
```bash
python seed_blogs.py
python seed_reviews.py
```

Seed travel agent and dynamic test statistics records (7 bookings, 5 visas, 6 flight quote requests for agent `Danish`):
```bash
cd ..
python scripts/seed_agent_data.py
```

### 11.4 Startup Services
Launch the services in separate terminal windows (remember to activate your `venv` inside each):

1. **Django Core Application (Port 8000)**:
   ```bash
   cd core_admin
   python manage.py runserver 127.0.0.1:8000
   ```
2. **FastAPI Services (Port 8001)**:
   ```bash
   uvicorn fast_api.main:app --host 127.0.0.1 --port 8001 --reload
   ```
3. **Celery Worker**:
   ```bash
   cd core_admin
   celery -A config worker --loglevel=info
   ```

---

## 12. Current Status vs Roadmap

| Feature / Subsystem | Status | Notes |
| :--- | :--- | :--- |
| **Authentication & Profile Setup** | **Completed** | Full multi-threaded verify OTP flow and profile image uploads are active. |
| **Agent Wallet & Ledger Logs** | **Completed** | Ledger creation, deletions, debit/credit math, and running balances are fully active. |
| **Dynamic Matplotlib Charts** | **Completed** | Renders line trend, donut mix, and registration bars as image responses. |
| **AJAX Live Polling** | **Completed** | Non-blocking dashboard updates are active on both Agent and Admin dashboards. |
| **AI LangChain Counselor** | **Completed** | Integrates Claude LLM and pgvector, with a local similarity fallback using NumPy. |
| **Hajj/Umrah Packages catalog** | **In Progress** | Basic models exist; Phase 2 UI integration will connect them to the live booking engines. |
| **GDS Integration** | **Planned** | Mock flights need live links to Sabre or Amadeus API sandboxes. |
| **Payment Gateways** | **Planned** | Integrate local payment portals (JazzCash, EasyPaisa). |
| **WhatsApp Notification Webhook** | **Planned** | Active trigger integration with n8n to send PDF vouchers. |
| **Cryptography Encryption** | **Planned** | Secure passport/CNIC standard database text records using Fernet keys. |
