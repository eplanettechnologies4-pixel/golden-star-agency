# Technical Stack Documentation

This document lists and details all languages, frameworks, databases, and deployment services utilized in the Golden Star Agency multi-tenant travel platform.

---

## 1. Backend Languages & Frameworks

* **Python**
  * **Role:** The core programming language powering the entire backend ecosystem, including application logic, workers, and chatbots.
  * **Environment:** Required both locally and in production.
* **Django**
  * **Role:** Web framework hosting the main administration panel, client portal, user authentications, CMS/Blogs, and central database schema structures.
  * **Environment:** Required both locally and in production.
* **FastAPI**
  * **Role:** High-performance asynchronous API service built to handle heavy client requests, package checkouts, search consoles, and chatbot message retrieval endpoints.
  * **Environment:** Required both locally and in production.
* **Celery**
  * **Role:** Distributed task queue processing background jobs like status notifications, booking checkouts, and transactional emails.
  * **Environment:** Required both locally and in production.

---

## 2. Database & Storage

* **PostgreSQL**
  * **Role:** Primary relational SQL database used to store transactional application data (such as users, bookings, packages, and visa applications).
  * **Environment:** Required both locally and in production (can fall back to SQLite for quick local scaffolding).
* **pgvector**
  * **Role:** PostgreSQL extension allowing store, index, and query operations on vector embeddings to enable semantic searches inside the AI chatbot.
  * **Environment:** Required both locally and in production.
* **Redis**
  * **Role:** In-memory key-value database acting as the Celery task message broker and caching backend.
  * **Environment:** Required both locally and in production.

---

## 3. Automation Tools

* **n8n**
  * **Role:** Workflow automation server orchestrating complex webhooks, customer integrations, and platform scheduling tasks.
  * **Environment:** Required only in production (optional locally to test integrations).

---

## 4. AI/Chatbot Stack

* **LangChain**
  * **Role:** Framework managing the context, prompt templates, history, and LLM chains for the customer AI Chatbot widget.
  * **Environment:** Required both locally and in production.
* **Embeddings**
  * **Role:** Numerical representations of travel inventory and package texts used to determine semantically matching query results.
  * **Environment:** Required both locally and in production.

---

## 5. Frontend

* **Django Templates**
  * **Role:** Server-rendered HTML templates utilizing Tailwind CSS CDN utilities and FontAwesome iconography to present a premium and highly interactive client workspace.
  * **Environment:** Required both locally and in production.
* **Static CSS/JS**
  * **Role:** Custom CSS styling rules (`style.css`), dynamic script helper logs (`booking.js`, `chatbot.js`), and responsive charts powered by matplotlib.
  * **Environment:** Required both locally and in production.

---

## 6. DevOps & Deployment

* **Docker**
  * **Role:** Containerization platform packaging services into self-contained environments to guarantee consistency.
  * **Environment:** Required only in production (optional locally).
* **Docker Compose**
  * **Role:** Tool used to stand up the entire multi-container service stack (Postgres, Redis, Django, FastAPI, worker, n8n) with a single command.
  * **Environment:** Required only in production (optional locally for convenience).
* **Nginx**
  * **Role:** High-performance reverse proxy and web server handling external client connections, SSL termination, and rate-limiting.
  * **Environment:** Required only in production.
* **Systemd**
  * **Role:** Linux service manager used to daemonize, spawn, and monitor background processes on VMs or bare-metal setups.
  * **Environment:** Required only in production.

---

## 7. Testing & Linting

* **Pytest**
  * **Role:** Comprehensive testing suite verifying API performance, package calculations, and database integrations.
  * **Environment:** Required locally for development and CI/CD pipelines (not used in live production instances).
* **Black**
  * **Role:** Automatic code formatting tool enforcing standard python layout.
  * **Environment:** Required locally and in CI/CD pipelines.
* **Ruff**
  * **Role:** High-speed linting tool checking for syntax errors, style compliance, and redundant imports.
  * **Environment:** Required locally and in CI/CD pipelines.

---

## Server Requirements

The following outline details the minimum specs needed to deploy the Golden Star Agency codebase:

* **Operating System:** Ubuntu 22.04 LTS (or equivalent modern Linux distro).
* **RAM:** Minimum 4 GB RAM (8 GB RAM recommended for handling concurrent PostgreSQL queries, n8n, FastAPI workers, and Celery processes).
* **Storage:** Minimum 20 GB SSD storage.
* **Installed Software:**
  * Python 3.10 or higher
  * PostgreSQL 14+ (with the `pgvector` extension compiled/installed)
  * Redis Server 7+
  * Docker & Docker Compose (optional, if using containerized deployment)
  * Nginx HTTP Server
