# WhatsApp Business Automation SaaS

A comprehensive WhatsApp Business automation system tailored for modern enterprises and SMEs, featuring a Chrome Extension, a Next.js Web Dashboard, and a highly scalable Django REST API Backend. This platform provides powerful tools for managing contacts, crafting message templates, executing bulk campaigns, scheduling communications, and analyzing outreach metrics.

## Project Architecture

The repository is structured into three main components:

- **Backend (Django REST API)**: A robust Python backend managing user authentication, contact databases, campaign logic, task scheduling (via Celery), risk management, and subscription billing (including M-Pesa and Stripe integrations).
- **Frontend (Next.js Dashboard)**: A responsive and intuitive user interface for managing operations, analyzing statistics, and handling account settings.
- **Chrome Extension (Manifest V3)**: A seamless browser extension that injects directly into WhatsApp Web, allowing for quick message dispatch, template selection, and account synchronization.

## Technology Stack

- **Frontend**: Next.js 14, React, Tailwind CSS, TypeScript
- **Backend**: Django 5.0, Django REST Framework, Celery
- **Database**: MySQL 8.0
- **Caching & Brokers**: Redis
- **Payments**: M-Pesa (Kenya), Stripe
- **Authentication**: JWT (JSON Web Tokens)
- **Deployment**: Docker, Docker Compose

## Features

### Core Capabilities
- **Contact Management**: Add, update, organize, and segment contacts effectively.
- **Message Templates**: Create and store reusable message structures for rapid communication.
- **Campaign Execution**: Plan and run bulk messaging campaigns with progress tracking and delivery metrics.
- **Scheduled Messaging**: Setup time-based automated messages to reach clients at optimal hours.
- **Risk Management**: Built-in rate limiting and safety protocols to protect your WhatsApp account from being flagged.

### Business & Subscription
- **Multi-tier Subscriptions**: Access levels ranging from Free to Agency plans, supporting diverse user needs.
- **Payment Integration**: Seamless checkout and subscription handling through Stripe and localized support for M-Pesa.
- **Analytics Dashboard**: Comprehensive charts and insights to monitor success rates, message logs, and engagement.
- **Referral Program**: Trackable referral links and commission management.

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- MySQL 8.0 or higher
- Redis (for Celery and caching)
- Docker and Docker Compose (optional but recommended for deployment)
- Google Chrome

### Running with Docker (Recommended)

1. Clone the repository.
2. Navigate to the project root.
3. Configure environment variables by copying `.env.example` files in both the backend and frontend directories.
4. Run the following commands:

```bash
docker-compose up -d --build
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py load_initial_data
```

### Manual Setup

#### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

# Configure your database credentials in the .env file

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
The backend API will be available at http://localhost:8000, and API documentation at http://localhost:8000/api/docs/.

#### Frontend Setup

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
npm run dev
```
The frontend dashboard will be available at http://localhost:3000.

#### Chrome Extension Setup

1. Open Chrome and navigate to `chrome://extensions/`.
2. Enable "Developer mode" in the top right corner.
3. Click "Load unpacked".
4. Select the `extension` folder located in the project root.
5. The extension icon will appear in your browser toolbar, ready to integrate with WhatsApp Web.

## Environment Variables

Refer to the `.env.example` files within the `backend` and `frontend` directories for a complete list of required environment variables. Ensure that database connections, secret keys, allowed hosts, and payment gateway credentials are set securely before running in production.

## Security Considerations

- Always rotate and secure your `SECRET_KEY` in production environments.
- Enforce HTTPS across all services.
- Disable debug mode (`DEBUG=False`) when deploying publicly.
- Configure CORS accurately to only allow trusted domains.
- Utilize strong passwords for databases and restrict port access.

## Author

Developed and maintained by Ian Gicheha Mbae (Dr-Rank1).

## License

This project is licensed under the MIT License.
