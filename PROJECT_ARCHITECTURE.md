# 🏛️ GOLDEN STAR TRAVEL & TOURS — FULL PROJECT MASTER ARCHITECTURE

## 📌 Executive Summary
**Golden Star Travel & Tours** is an enterprise-grade Travel Management, B2B Agent Wholesale Network, and Financial Intelligence Platform built using **Django 5 (Python 3.14), Python NumPy & Pandas Data Engine, HTML5/Vanilla CSS, and Chart.js**.

The system features a **3-Tier Role-Based Access Control (RBAC)** architecture serving **B2C Customers, B2B Partner Agents, and Super Admins**.

---

## 🗂️ 1. Directory Structure & App Tree

```
travel-agecny-main/
│
├── PROJECT_ARCHITECTURE.md                  # Master System Architecture Document
│
└── core_admin/                              # Django Project Core Directory
    ├── manage.py                            # Django Administrative CLI
    ├── db.sqlite3                           # Relational Database
    │
    ├── config/                              # Global Configuration Package
    │   ├── settings.py                      # Installed Apps, DB, Middleware, Static/Media setup
    │   ├── urls.py                          # Global URL Route Dispatcher
    │   ├── wsgi.py                          # WSGI Application Entry Point
    │   └── asgi.py                          # ASGI Application Entry Point
    │
    ├── apps/                                # Modular Application Business Logic
    │   ├── accounts/                        # Custom User Model, RBAC Auth, Agent Ledger, Financial APIs
    │   │   ├── models.py                    # User, LoginHistory, AgentLedger, AdminCustomBill, AgentReview
    │   │   ├── views.py                     # Financial Analytics, Export APIs, Accounts Management
    │   │   └── urls.py                      # Auth routes
    │   │
    │   ├── packages/                        # Hajj, Umrah, & Tour Packages Engine
    │   │   ├── models.py                    # Package, PackageFeature, PackageInclude, PackageExclude
    │   │   └── views.py                     # Package catalogs & detail views
    │   │
    │   ├── bookings/                        # Order Booking & Reservations System
    │   │   ├── models.py                    # Booking, PassengerDetail
    │   │   └── views.py                     # Package booking submission & management
    │   │
    │   ├── visa/                            # Visa Application & Embassy Tracking Desk
    │   │   ├── models.py                    # VisaCountry, VisaPackage, VisaApplication
    │   │   └── views.py                     # Visa applications & instant approval letter generator
    │   │
    │   ├── flights/                         # Flight Tickets & Quotations Desk
    │   │   ├── models.py                    # FlightTicketOffer, FlightQuoteRequest
    │   │   └── views.py                     # Flight quotes & catalog engine
    │   │
    │   └── blog/                            # Travel Insights & Article Engine
    │       ├── models.py                    # BlogCategory, BlogArticle
    │       └── views.py                     # Articles catalog & detail views
    │
    └── templates/                           # Frontend HTML Template Architecture
        ├── base.html                        # Global Base Layout
        │
        ├── dashboard/                       # 3-Tier Dashboard Workspaces
        │   ├── admin/
        │   │   └── overview.html            # Super Admin Workspace (Analytics, Ledgers, Visas, Bills)
        │   ├── agent/
        │   │   └── overview.html            # B2B Partner Agent Workspace (Commissions, Sub-Bookings)
        │   └── customer/
        │       └── overview.html            # B2C Customer Workspace (Bookings, E-Tickets, Letters)
        │
        ├── letters/
        │   └── approval_letter.html         # Modern Official Visa Approval Letter (Printable Single-Page)
        │
        ├── reports/
        │   └── report_printable.html        # Executive System Report Layout (Printable Single-Page)
        │
        ├── packages/                        # Package Catalogs (Hajj, Umrah, Details)
        ├── visa/                            # Visa Catalogs & Application Forms
        ├── flights/                         # Flight Ticket Catalogs & Quotations
        └── blog/                            # Travel Articles & News Templates
```

---

## 🧭 2. Full System Flow & Component Interaction Architecture

```mermaid
graph TD
    subgraph Client_Layer ["1. Client Access Layer"]
        C1["👨‍💼 B2C Customer"]
        C2["🤝 B2B Partner Agent"]
        C3["⚡ Executive Super Admin"]
    end

    subgraph Auth_Security ["2. Auth & RBAC Security Layer"]
        S1["🔐 Django Auth Session"]
        S2["🛡️ RBAC Decorators (@is_admin, @is_agent)"]
        S3["📧 OTP Email Verification"]
    end

    subgraph Dashboards ["3. Workspaces & Interfaces"]
        D1["🖥️ Customer Dashboard"]
        D2["💼 Agent B2B Workspace"]
        D3["📊 Admin Executive Workspace"]
    end

    subgraph Analytics_Engine ["4. Financial & Business Data Engines"]
        E1["🕋 Hajj & Umrah Engine"]
        E2["🛂 Visa Processing & Letter Generator"]
        E3["✈️ Flight Quotation Desk"]
        E4["📈 NumPy & Pandas Financial Intelligence"]
        E5["🧾 Custom Agency Bills & Supplier Ledger"]
        E6["📄 Multi-Format Exporter (PDF / Word / Excel / CSV)"]
    end

    subgraph Database_Tier ["5. Database & Storage Tier"]
        DB["💾 Relational DB (Users, Bookings, Ledgers)"]
        Cache["⚡ Pandas In-Memory DataFrame Cache"]
        Media["📁 Media Vault (ID Cards, Visas, Passports)"]
    end

    Client_Layer --> Auth_Security
    Auth_Security --> Dashboards
    Dashboards --> Analytics_Engine
    Analytics_Engine --> Database_Tier
```

---

## 💾 3. Database Schema & Data Models Relationship (ERD)

```mermaid
erDiagram
    User ||--o{ Booking : "places"
    User ||--o{ VisaApplication : "submits"
    User ||--o{ FlightQuoteRequest : "requests"
    User ||--o{ AgentLedger : "maintains"
    Package ||--o{ Booking : "booked under"

    User {
        int id PK
        string username UK
        string email UK
        string role "super_admin | agent | customer"
        string approval_status "pending | approved | rejected"
        boolean is_email_verified
        float wallet_balance "Dynamic Sum calculation"
    }

    AgentLedger {
        int id PK
        int agent_id FK
        string entry_type "credit | debit"
        string category "commission | payment | refund | adjustment"
        decimal amount
        string reference
        datetime created_at
    }

    AdminCustomBill {
        int id PK
        string bill_number UK "BILL-2026-XXXX"
        string title
        string department "umrah | hajj | visa | ticket | general"
        string bill_type "income | expense"
        string vendor_client_name
        decimal amount
        boolean is_paid
        datetime created_at
    }

    Booking {
        int id PK
        int user_id FK
        int package_id FK
        string booking_type "package | umrah | hajj"
        string sharing_category "quad | triple | double"
        decimal total_price
        string status "pending | confirmed | cancelled"
        datetime created_at
    }

    VisaApplication {
        int id PK
        int user_id FK
        string full_name
        string passport_number
        string country
        string status "pending | submitted | approved | rejected"
        datetime created_at
    }

    FlightTicketOffer {
        int id PK
        string airline_name
        string flight_number
        string departure_city
        string destination_city
        decimal price
        int total_seats
        int available_seats
        boolean is_popular
    }
```

---

## ⚡ 4. Core Subsystem Architectural Highlights

### A. 🧮 Real-Time NumPy & Pandas Analytics Engine
- **In-Memory Analytical Pipeline**: Converts transactional queries (`Booking`, `FlightQuoteRequest`, `VisaApplication`) into Pandas `DataFrame` objects.
- **Statistical Vectorization**: Server computes Gross Volume, Confirmed Revenue, Pending Receivables, Average Order Value (AOV), Median Order Size (`np.median`), and Standard Deviation (`np.std`) in memory with zero database locks.
- **Chart.js Integration**: Streams real-time trends into Chart.js canvas line charts.

---

### B. 🧾 Manual Agency Bills & Multi-Format Exporter
- **Supplier Invoice Ledger**: Admins generate custom bills and supplier receipts (Saudi Hotels, Transport Vouchers, Visa Fees, Flight Vouchers).
- **4-Format Exporter**:
  1. 📄 **PDF**: Modern 1-page executive printable template (`report_printable.html`).
  2. 📝 **Word (`.doc`)**: Structured HTML Word document attachment.
  3. 📊 **Excel (`.xls`)**: Formatted Microsoft Excel spreadsheet with dark table headers.
  4. 📑 **CSV (`.csv`)**: Standard comma-separated values file.

---

### C. 🖨️ Tab-Closing Printable Document System
- All approval letters (`approval_letter.html`) and system reports (`report_printable.html`) utilize the smart back-button logic:
```javascript
function goBackOrClose() {
    if (window.history.length > 1 && document.referrer) {
        window.history.back();
    } else {
        window.close();
    }
}

```

---

### D. 🔒 Enterprise Security & Protection Stack
- **PBKDF2 SHA-256 Hashing**: Password storage is salted and hashed.
- **RBAC Decorators**: Custom `@user_passes_test(is_admin)` and `@user_passes_test(is_agent)` view guards.
- **CSRF & XSS Hardening**: Mandatory `X-CSRFToken` verification and front-end HTML entity escaping (`escapeHTML()`).
- **Parameterized SQL**: All database operations execute through Django ORM parameterized queries, completely eliminating SQL injection vectors.
- **SMTP OTP Engine**: 6-digit cryptographic verification codes sent via email.
