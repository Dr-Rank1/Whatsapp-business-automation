# WhatsApp Business Automation Tool

A comprehensive WhatsApp Business automation system with Chrome Extension, Web Dashboard, and Backend API.

## 📁 Project Structure

```
whatsapp-business-automation/
├── backend/                    # Django REST API
│   ├── whatsapp_api/           # Main Django project
│   │   ├── core/              # User authentication & profiles
│   │   │   ├── models.py      # User, UserProfile models
│   │   │   ├── serializers.py # JWT & user serializers
│   │   │   ├── views.py       # Auth endpoints
│   │   │   └── urls.py        # Auth URL routes
│   │   └── api/               # WhatsApp automation API
│   │       ├── models.py      # Contact, Template, Campaign, etc.
│   │       ├── serializers.py # API serializers
│   │       ├── views.py      # CRUD & business logic
│   │       └── urls.py       # API routes
│   ├── manage.py
│   ├── requirements.txt
│   └── settings.py
│
├── frontend/                   # Next.js Dashboard
│   ├── app/
│   │   ├── auth/              # Login/Register pages
│   │   ├── dashboard/         # Main dashboard
│   │   │   ├── contacts/      # Contacts management
│   │   │   ├── templates/     # Message templates
│   │   │   ├── campaigns/     # Bulk messaging
│   │   │   ├── scheduled/     # Scheduled messages
│   │   │   ├── analytics/     # Stats & charts
│   │   │   └── settings/     # User settings
│   │   ├── components/       # Reusable UI components
│   │   ├── lib/              # API client & utilities
│   │   └── types/            # TypeScript definitions
│   ├── package.json
│   └── tailwind.config.ts
│
└── extension/                  # Chrome Extension (Manifest v3)
    ├── manifest.json
    ├── src/
    │   ├── background/        # Service worker & popup
    │   ├── content/           # Injected into web.whatsapp.com
    │   └── inject/            # CSS styles
    └── icons/                 # Extension icons
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- Chrome Browser

---

### 1. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your database credentials
# MYSQL_DATABASE=whatsapp_automation
# MYSQL_USER=root
# MYSQL_PASSWORD=your_password

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

Backend will run at: **http://localhost:8000**

API Documentation: **http://localhost:8000/api/docs/**

---

### 2. Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local

# Start development server
npm run dev
```

Frontend will run at: **http://localhost:3000**

---

### 3. Chrome Extension Setup

#### Option A: Load from Source

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (top right toggle)
3. Click "Load unpacked"
4. Select the `extension` folder
5. The extension icon will appear in your toolbar

#### Option B: Build and Package

```bash
# In extension folder, create icons first
# (You'll need to add icon files to icons/ folder)

# Then load the extension as above
```

---

## 🔑 Key Features

### User Authentication
- JWT-based authentication
- Register, Login, Logout
- Token refresh
- Password change

### Dashboard
- **Overview**: Real-time stats, upcoming messages
- **Contacts**: Add, edit, delete, block contacts
- **Templates**: Create reusable message templates
- **Campaigns**: Bulk message sending with progress tracking
- **Scheduled**: Time-based message scheduling
- **Analytics**: Charts, success rates, message logs

### Chrome Extension
- Floating action button on WhatsApp Web
- Quick message sending
- Template selection
- Contact management
- Real-time chat detection

---

## 📡 API Endpoints

### Authentication
- `POST /api/v1/auth/register/` - User registration
- `POST /api/v1/auth/login/` - User login
- `POST /api/v1/auth/logout/` - User logout
- `POST /api/v1/auth/token/refresh/` - Refresh JWT
- `GET /api/v1/auth/me/` - Get current user

### Contacts
- `GET /api/v1/contacts/` - List contacts
- `POST /api/v1/contacts/` - Create contact
- `GET /api/v1/contacts/{id}/` - Get contact
- `PATCH /api/v1/contacts/{id}/` - Update contact
- `DELETE /api/v1/contacts/{id}/` - Delete contact

### Templates
- `GET /api/v1/templates/` - List templates
- `POST /api/v1/templates/` - Create template
- `GET /api/v1/templates/{id}/` - Get template
- `PATCH /api/v1/templates/{id}/` - Update template
- `DELETE /api/v1/templates/{id}/` - Delete template

### Campaigns
- `GET /api/v1/campaigns/` - List campaigns
- `POST /api/v1/campaigns/` - Create campaign
- `POST /api/v1/campaigns/{id}/start/` - Start campaign
- `POST /api/v1/campaigns/{id}/pause/` - Pause campaign
- `POST /api/v1/campaigns/{id}/cancel/` - Cancel campaign

### Scheduled Messages
- `GET /api/v1/scheduled/` - List scheduled
- `POST /api/v1/scheduled/` - Create scheduled
- `POST /api/v1/scheduled/{id}/cancel/` - Cancel

### Analytics
- `GET /api/v1/analytics/dashboard/` - Dashboard stats
- `GET /api/v1/analytics/chart/` - Chart data
- `GET /api/v1/messages/` - Message logs
- `POST /api/v1/messages/{id}/retry/` - Retry failed

---

## 🛠️ Environment Variables

### Backend (.env)
```env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

MYSQL_DATABASE=whatsapp_automation
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_HOST=localhost
MYSQL_PORT=3306

CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 📦 Production Deployment

### Backend (Gunicorn + Nginx)
```bash
cd backend
pip install gunicorn whitenoise

# Collect static files
python manage.py collectstatic

# Run with gunicorn
gunicorn whatsapp_api.wsgi:application --bind 0.0.0.0:8000
```

### Frontend (Next.js)
```bash
cd frontend
npm run build
npm start
```

### Database
- Configure MySQL in `settings.py`
- Run migrations before deployment
- Set up regular backups

---

## 🔒 Security Considerations

1. Change `SECRET_KEY` in production
2. Enable HTTPS
3. Set `DEBUG=False` in production
4. Configure CORS properly
5. Use strong database passwords
6. Regular security updates

---

## 📄 License

MIT License - Feel free to use for your projects.

---

## 🤝 Support

For issues and questions:
1. Check API docs at `/api/docs/`
2. Review console logs
3. Check backend logs in `debug.log`
