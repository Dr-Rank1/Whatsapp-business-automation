# Quick Start Guide - Get Live in 10 Minutes

## Prerequisites
- Docker & Docker Compose installed
- M-Pesa developer account (https://developer.safaricom.co.ke)

---

## Step 1: Configure Environment

```bash
cd backend
cp .env.example .env
```

Edit `.env` with your settings:
```env
DJANGO_SECRET_KEY=any-random-key-here
ALLOWED_HOSTS=localhost,yourdomain.com
MYSQL_DATABASE=whatsapp_automation
MYSQL_USER=whatsapp_user
MYSQL_PASSWORD=password123
MYSQL_HOST=db
REDIS_URL=redis://redis:6379/0
MPESA_ENVIRONMENT=sandbox
MPESA_CONSUMER_KEY=your_key
MPESA_CONSUMER_SECRET=your_secret
MPESA_BUSINESS_SHORT_CODE=123456
MPESA_PASSKEY=your_passkey
MPESA_CALLBACK_URL=http://localhost:8000/api/v1/billing/mpesa/callback/
FRONTEND_URL=http://localhost:3000
```

---

## Step 2: Deploy

```bash
# From project root
docker-compose up -d --build
```

---

## Step 3: Setup Database

```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py load_initial_data
docker-compose exec backend python manage.py createsuperuser
```

---

## Step 4: Access

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Admin Panel | http://localhost:8000/admin/ |

---

## Step 5: Load Chrome Extension

1. Open Chrome → Extensions → Enable Developer Mode
2. Click "Load unpacked"
3. Select `extension/` folder

---

## Done! 🎉

Your SaaS is running at http://localhost:3000

## For Production

1. Buy a domain
2. Update `.env` with your domain
3. Set `DJANGO_DEBUG=False`
4. Change `MPESA_ENVIRONMENT=production`
5. Set up SSL with Let's Encrypt
