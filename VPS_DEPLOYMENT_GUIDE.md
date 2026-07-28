# 🚀 Complete Step-by-Step VPS Deployment Guide
## REI Golden Star Travel & Tours — Production Deployment (GitHub, Docker, Nginx, SSL, Gunicorn)

This document provides a complete, copy-paste ready guide to deploy the **REI Golden Star Travel & Tours** portal on any Linux VPS (Ubuntu 22.04 / 24.04 LTS) such as Hostinger, DigitalOcean, Hetzner, AWS EC2, Linode, or Contabo.

---

## 📋 Table of Contents
1. [Prerequisites & Server Requirements](#1-prerequisites--server-requirements)
2. [Step 1: Push Code to GitHub Repository](#step-1-push-code-to-github-repository)
3. [Step 2: Connect & Setup Linux VPS Server](#step-2-connect--setup-linux-vps-server)
4. [Step 3: Install Docker & Docker Compose on VPS](#step-3-install-docker--docker-compose-on-vps)
5. [Step 4: Clone Repository on VPS](#step-4-clone-repository-on-vps)
6. [Step 5: Configure Production Environment Variables (.env)](#step-5-configure-production-environment-variables-env)
7. [Step 6: Launch Docker Containers (Postgres, Redis, Django, FastAPI)](#step-6-launch-docker-containers-postgres-redis-django-fastapi)
8. [Step 7: Database Migrations & Initial Setup](#step-7-database-migrations--initial-setup)
9. [Step 8: Configure Nginx & Free SSL Certificate (Let's Encrypt / Certbot)](#step-8-configure-nginx--free-ssl-certificate-lets-encrypt--certbot)
10. [Step 9: Daily Maintenance, Backups & Logs](#step-9-daily-maintenance-backups--logs)

---

## 1. Prerequisites & Server Requirements

| Component | Minimum Requirement | Recommended Production |
|---|---|---|
| **OS** | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |
| **CPU** | 2 Cores | 4 Cores |
| **RAM** | 4 GB | 8 GB |
| **SSD Storage** | 40 GB NVMe | 80 GB NVMe |
| **Domain Name** | `yourdomain.com` pointing to VPS IP | `yourdomain.com` & `api.yourdomain.com` |

---

## Step 1: Push Code to GitHub Repository

Run these commands in PowerShell or Terminal inside your local project root (`travel-agecny-main`):

```bash
# 1. Initialize git repository if not already initialized
git init

# 2. Add all project files
git add .

# 3. Commit changes
git commit -m "Production ready commit with B2B/B2C Admin Panel & Airline Ticketing"

# 4. Set main branch name
git branch -M main

# 5. Add remote GitHub repository (replace URL with your own GitHub repo)
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/travel-agency-main.git

# 6. Push code to GitHub
git push -u origin main
```

> ⚠️ **IMPORTANT**: Ensure your `.env` file containing local passwords is listed in `.gitignore` so secret keys are not committed to public repositories.

---

## Step 2: Connect & Setup Linux VPS Server

Open your SSH terminal (e.g. Putty, MobaXterm, or Windows Terminal) and connect to your VPS IP address:

```bash
ssh root@YOUR_VPS_IP
```

### Update VPS Packages & Configure Firewall:
```bash
# Update Ubuntu package lists
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y curl wget git ufw htop unzip software-properties-common

# Configure UFW Firewall rules
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## Step 3: Install Docker & Docker Compose on VPS

Run the official Docker installation script on your VPS:

```bash
# Download and install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose Plugin
sudo apt install -y docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

---

## Step 4: Clone Repository on VPS

Navigate to `/var/www/` and clone your project repository:

```bash
# Navigate to web root
cd /var/www

# Clone repository from GitHub
git clone https://github.com/YOUR_GITHUB_USERNAME/travel-agency-main.git travel-agency

# Enter directory
cd travel-agency
```

---

## Step 5: Configure Production Environment Variables (.env)

Create a production `.env` file inside `/var/www/travel-agency`:

```bash
nano .env
```

Paste the following production configuration (replace domains and secrets with your own):

```env
# ── PRODUCTION ENVIRONMENT SETTINGS ──
DEBUG=False
SECRET_KEY=prod-secret-key-change-this-to-random-64-character-string-2026
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,YOUR_VPS_IP
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# ── DATABASE SETTINGS (Postgres Vector) ──
POSTGRES_DB=golden_star_db
POSTGRES_USER=golden_admin
POSTGRES_PASSWORD=SecureProductionPassword2026!
DATABASE_URL=postgresql://golden_admin:SecureProductionPassword2026!@postgres:5432/golden_star_db

# ── REDIS & CACHE ──
REDIS_URL=redis://redis:6379/0

# ── FASTAPI & JWT ──
JWT_SECRET_KEY=prod-jwt-secret-key-change-this-to-another-random-string
ENCRYPTION_KEY=g-T3J4W1n6o-8RzX_K0aM-Y9sL3v5C7u8X9z0A1B2C3=
```

Press `Ctrl + O` then `Enter` to save, and `Ctrl + X` to exit `nano`.

---

## Step 6: Launch Docker Containers (Postgres, Redis, Django, FastAPI)

Build and launch all containers in background daemon mode:

```bash
# Build and launch Docker services
docker compose up -d --build

# Check running container statuses
docker compose ps
```

You should see 4 active running containers:
1. `gsa_postgres` (PostgreSQL 15 + PGVector)
2. `gsa_redis` (Redis 7)
3. `gsa_django` (Django Gunicorn application server)
4. `gsa_fastapi` (FastAPI high-speed API engine)

---

## Step 7: Database Migrations & Initial Setup

Execute database migrations and static files collection inside the running Django container:

```bash
# 1. Run database migrations
docker compose exec core_admin python core_admin/manage.py migrate

# 2. Collect all CSS, JS, and image static files for Nginx
docker compose exec core_admin python core_admin/manage.py collectstatic --noinput

# 3. Create Super Admin User (Credentials: reigoldenstarmianejaz)
docker compose exec core_admin python core_admin/manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='reigoldenstarmianejaz').exists():
    User.objects.create_superuser('reigoldenstarmianejaz', 'admin@goldenstar.com', 'LYPJED@11709lheISB#6690', role='super_admin', approval_status='approved');
    print('Super Admin Created Successfully!');
else:
    u = User.objects.get(username='reigoldenstarmianejaz');
    u.set_password('LYPJED@11709lheISB#6690');
    u.role = 'super_admin';
    u.is_superuser = True;
    u.save();
    print('Super Admin Credentials Updated!');
"
```

---

## Step 8: Configure Nginx & Free SSL Certificate (Let's Encrypt / Certbot)

Install Nginx and Certbot on your main VPS host:

```bash
# Install Nginx and Certbot
sudo apt install -y nginx certbot python3-certbot-nginx
```

Create a production Nginx configuration for your domain:

```bash
sudo nano /etc/nginx/sites-available/travelagency
```

Paste the following Nginx server block:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 100M;

    # Static files served directly by Nginx for ultra-fast response
    location /static/ {
        alias /var/www/travel-agency/core_admin/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # Media uploads (passports, hotel photos, logos)
    location /media/ {
        alias /var/www/travel-agency/core_admin/media/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # FastAPI endpoints
    location /fastapi/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Main Django Portal & Admin Panel
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site & test Nginx configuration:

```bash
# Symlink config to sites-enabled
sudo ln -s /etc/nginx/sites-available/travelagency /etc/nginx/sites-enabled/

# Test Nginx syntax
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Install Free SSL Certificate:
```bash
# Run Certbot to generate SSL and enable HTTPS redirect automatically
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Certbot will automatically obtain an SSL certificate, configure HTTPS on port 443, and set up automatic 90-day SSL renewals!

---

## Step 9: Daily Maintenance, Backups & Logs

### Viewing Real-Time Logs:
```bash
# View all container logs
docker compose logs -f

# View Django logs specifically
docker compose logs -f core_admin
```

### Automated Database Backup Cron Job:
To auto-backup your PostgreSQL database every night at 2:00 AM, create a cron job:

```bash
crontab -e
```

Add this line at the bottom:

```cron
0 2 * * * docker exec gsa_postgres pg_dump -U golden_admin golden_star_db | gzip > /var/www/travel-agency/backups/db_$(date +\%F).sql.gz
```

---

## 🎯 Verification Checklist

After completing the steps above, visit:
- **Public Portal**: `https://yourdomain.com/`
- **B2B / Super Admin Panel**: `https://yourdomain.com/dashboard/admin/`
  - **Username**: `reigoldenstarmianejaz`
  - **Password**: `LYPJED@11709lheISB#6690`
- **Agent Dashboard**: `https://yourdomain.com/dashboard/agent/`
- **Blogs Studio**: `https://yourdomain.com/dashboard/admin/blogs/`

Your **REI Golden Star Travel & Tours** portal is now 100% LIVE, secure, and production-ready on your VPS! 🚀
