# WhatsApp Business Automation SaaS - Deployment Guide

This comprehensive guide covers deploying your WhatsApp Business Automation SaaS to production.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Development Setup](#development-setup)
4. [Production Deployment](#production-deployment)
5. [Environment Variables](#environment-variables)
6. [Docker Deployment](#docker-deployment)
7. [Cloud Deployment](#cloud-deployment)
8. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Architecture Overview

### System Components
```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
│                     http://localhost:3000                        │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                    HTTPS / WSS
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                       Backend (Django)                           │
│                     http://localhost:8000                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │   REST API   │ │   Billing   │ │   Webhooks  │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
└─────────────────────────────┬───────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│    MySQL      │   │  Redis/Cache  │   │   Celery      │
│  (Database)   │   │  (Cache/Rate  │   │  (Background  │
│               │   │   Limiting)   │   │   Tasks)      │
└───────────────┘   └───────────────┘   └───────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Chrome Extension (MV3)                        │
│                  https://web.whatsapp.com/*                      │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack
- **Frontend**: Next.js 14, Tailwind CSS, TypeScript
- **Backend**: Django 5.0, Django REST Framework
- **Database**: MySQL 8.0
- **Cache**: Redis
- **Task Queue**: Celery + Redis
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Payments**: Stripe, PayPal
- **Deployment**: Docker, AWS/DigitalOcean

---

## Prerequisites

### Required Services
1. **MySQL 8.0+** - Primary database
2. **Redis 7.0+** - Cache and message broker
3. **Stripe Account** - Payment processing
4. **WhatsApp Business API** - Message sending (optional)

### System Requirements
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (for containerized deployment)

---

## Development Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd whatsapp-business-automation
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 3. Configure Environment Variables (.env)
```env
# Django
DJANGO_SECRET_KEY=your-secret-key-change-in-production
DJANGO_DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
MYSQL_DATABASE=whatsapp_automation
MYSQL_USER=your_db_user
MYSQL_PASSWORD=your_db_password
MYSQL_HOST=localhost
MYSQL_PORT=3306

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-jwt-secret-key

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# Frontend URL
FRONTEND_URL=http://localhost:3000

# Sentry (optional)
SENTRY_DSN=
```

### 4. Database Setup
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load initial data (plans)
python manage.py loaddata initial_plans
```

### 5. Start Backend Services

**Terminal 1 - Django Server:**
```bash
cd backend
python manage.py runserver
```

**Terminal 2 - Celery Worker:**
```bash
cd backend
celery -A whatsapp_api worker -l info -c 2
```

**Terminal 3 - Celery Beat (scheduler):**
```bash
cd backend
celery -A whatsapp_api beat -l info
```

### 6. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Start development server
npm run dev
```

### 7. Chrome Extension Setup

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select the `extension/` folder

---

## Production Deployment

### Option 1: Docker Deployment (Recommended)

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  # Frontend
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=https://api.yourdomain.com
    depends_on:
      - backend

  # Backend
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DJANGO_DEBUG=False
      - ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
      - MYSQL_HOST=db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  # Database
  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=whatsapp_automation
      - MYSQL_USER=user
      - MYSQL_PASSWORD=password
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"

  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Celery Worker
  celery:
    build: ./backend
    command: celery -A whatsapp_api worker -l info -c 2
    environment:
      - MYSQL_HOST=db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - backend
      - db
      - redis

  # Celery Beat
  celery-beat:
    build: ./backend
    command: celery -A whatsapp_api beat -l info
    environment:
      - MYSQL_HOST=db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - backend
      - db
      - redis

volumes:
  mysql_data:
  redis_data:
```

Deploy:
```bash
docker-compose up -d --build
```

### Option 2: Manual Deployment

#### Backend (Gunicorn + Nginx)
```bash
# Install production dependencies
pip install gunicorn whitenoise

# Collect static files
python manage.py collectstatic --noinput

# Run with Gunicorn
gunicorn whatsapp_api.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 120
```

#### Nginx Configuration
```nginx
upstream backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /static/ {
        alias /path/to/static/;
    }
}
```

---

## Cloud Deployment

### AWS (Elastic Beanstalk)

1. Create `Dockerrun.aws.json`:
```json
{
  "AWSEBDockerrunVersion": "2",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-registry/backend:latest",
      "environment": [...]
    }
  ]
}
```

2. Create RDS MySQL instance
3. Create ElastiCache Redis
4. Configure Load Balancer
5. Set up CloudWatch for logging

### DigitalOcean

1. Create Droplet (Ubuntu 22.04)
2. Install Docker:
```bash
curl -fsSL https://get.docker.com | sh
```
3. Deploy with docker-compose
4. Set up Managed MySQL
5. Configure Cloud Firewall

### Vercel (Frontend Only)

```bash
cd frontend
vercel --prod
```

---

## Monitoring & Maintenance

### Sentry Integration
Already configured in settings.py. Add DSN to environment:
```env
SENTRY_DSN=https://...@sentry.io/...
```

### Health Checks
```bash
# Backend health
curl https://api.yourdomain.com/health/

# Database check
curl https://api.yourdomain.com/health/db/
```

### Log Management
```bash
# View Celery logs
docker logs -f celery

# View Django logs
tail -f /var/log/django.log
```

### Backups
```bash
# MySQL backup
mysqldump -u user -p whatsapp_automation > backup_$(date +%Y%m%d).sql

# Automated backup (cron)
0 2 * * * mysqldump -u user -p whatsapp_automation > /backups/backup_$(date +\%Y\%m\%d).sql
```

### SSL/HTTPS (Let's Encrypt)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

---

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check MySQL is running
   - Verify credentials in .env
   - Ensure database exists

2. **Redis Connection Error**
   - Check Redis is running
   - Verify REDIS_URL in .env
   - Check firewall rules

3. **Celery Tasks Not Running**
   - Verify Celery worker is started
   - Check broker connection
   - Review task logs

4. **Stripe Webhooks Failing**
   - Verify webhook secret
   - Check endpoint URL is accessible
   - Review Stripe dashboard logs

---

## Security Checklist

- [ ] Change all secret keys
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable audit logging
- [ ] Configure backups
- [ ] Set up monitoring
- [ ] Review user permissions
- [ ] Secure database credentials
- [ ] Enable firewall rules

---

## License

MIT License - See LICENSE file for details
