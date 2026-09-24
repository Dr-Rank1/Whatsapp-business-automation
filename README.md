# WhatsApp Business Automation SaaS

A comprehensive, scalable, and powerful WhatsApp Business automation system explicitly designed for modern enterprises and SMEs. This unified platform integrates a seamless Chrome Extension, an intuitive Next.js Web Dashboard, and a highly resilient Django REST API Backend to orchestrate your entire customer communication pipeline.

## Vision & Architecture

At its core, this project aims to empower businesses with friction-free WhatsApp automation. The architecture is cleanly divided into three distinct, yet deeply interconnected domains:

1. **Backend (Django REST API)**
   The intelligent backbone of the platform. It handles user authentication, contact databases, intricate campaign logic, precise task scheduling (via Celery), comprehensive risk management, and scalable subscription billing. Includes seamless integration with localized payment providers like M-Pesa alongside global Stripe support.

2. **Frontend (Next.js Dashboard)**
   The command center. A responsive, dynamic, and intuitive user interface optimized for performance. It allows businesses to visualize metrics, manage extensive contact lists, structure campaigns, and configure account settings with ease.

3. **Chrome Extension (Manifest V3)**
   The bridge. A lightweight and secure browser extension that injects directly into WhatsApp Web. It guarantees a smooth workflow by bringing template selection, quick message dispatch, and real-time account synchronization directly to your browser tab.

## Technology Stack

- **Frontend Environment**: Next.js 14, React, Tailwind CSS, TypeScript
- **Backend Environment**: Django 5.0, Django REST Framework, Python 3.10+
- **Background Processing**: Celery (for high-volume task scheduling)
- **Database Architecture**: MySQL 8.0
- **Caching & Message Broker**: Redis
- **Payment Gateways**: M-Pesa (Kenya), Stripe (Global)
- **Security & Authentication**: JWT (JSON Web Tokens)
- **Infrastructure & Deployment**: Docker, Docker Compose

## Key Features

### Advanced Core Capabilities
- **Intelligent Contact Management**: Import, segment, update, and rigorously organize contacts to target audiences effectively.
- **Dynamic Message Templates**: Create, store, and utilize highly customizable, reusable message structures to maintain brand consistency.
- **High-Volume Campaign Execution**: Orchestrate and execute bulk messaging campaigns featuring granular progress tracking and delivery metrics.
- **Precision Scheduled Messaging**: Configure time-sensitive automated messages to ensure communication reaches clients at peak engagement hours.
- **Proactive Risk Management**: Built-in rate limiting, throttling, and safety protocols carefully engineered to protect your WhatsApp account from being flagged or banned.

### Business Optimization & Subscription Management
- **Multi-Tier Subscriptions**: Flexible access levels ranging from Free to Agency plans, supporting diverse user requirements and scaling alongside businesses.
- **Frictionless Payment Integration**: Automated checkout and subscription handling through Stripe, with deeply integrated, localized support for M-Pesa.
- **Deep Analytics Dashboard**: Rich data visualizations, comprehensive charts, and actionable insights to monitor success rates, track message logs, and analyze overall engagement.
- **Integrated Referral Program**: Trackable referral links and automated commission management to drive organic platform growth.

## Quick Start Guide

### System Prerequisites

To ensure a smooth setup, verify that your environment meets the following requirements:
- Python 3.10 or higher
- Node.js 18 or higher
- MySQL 8.0 or higher
- Redis (required for Celery workers and caching)
- Docker and Docker Compose (highly recommended for deployment)
- Google Chrome (for the extension)

### Recommended: Running with Docker

Deploying via Docker is the quickest and most reliable method to get the entire stack running.

1. Clone the repository to your local machine.
2. Navigate to the root directory of the project.
3. Configure your environment variables by copying the provided `.env.example` templates in both the `backend` and `frontend` directories.
4. Execute the following commands to build the containers and seed the database:

```bash
docker-compose up -d --build
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py load_initial_data
```

### Alternative: Manual Local Setup

#### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Important: Update the .env file with your actual database credentials

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
*The backend API will be accessible at `http://localhost:8000`, with interactive API documentation available at `http://localhost:8000/api/docs/`.*

#### 2. Frontend Setup

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
npm run dev
```
*The Next.js frontend dashboard will be running at `http://localhost:3000`.*

#### 3. Chrome Extension Installation

1. Launch Google Chrome and navigate to `chrome://extensions/`.
2. Toggle "Developer mode" on (located in the top right corner).
3. Click on the "Load unpacked" button.
4. Select the `extension` folder from the root of this project.
5. The extension icon will now be visible in your browser toolbar, ready for integration with WhatsApp Web.

## Configuration & Security

### Environment Variables
Thoroughly review the `.env.example` files located within the `backend` and `frontend` directories. These files document the complete list of required environment variables. It is critical to ensure that database connections, secret keys, allowed hosts, and payment gateway credentials are set correctly and securely before transitioning to a production environment.

### Security Best Practices
- **Secret Management**: Always rotate and strictly secure your `SECRET_KEY` in production environments.
- **Transport Security**: Enforce HTTPS across all deployed services to encrypt data in transit.
- **Debug Mode**: Explicitly disable debug mode (`DEBUG=False`) when deploying publicly to prevent information leakage.
- **CORS Configuration**: Configure CORS accurately to permit requests only from trusted and verified domains.
- **Database Hardening**: Utilize cryptographically strong passwords for databases and strictly restrict port access via firewalls.

## Author

Designed, developed, and maintained by Ian Gicheha Mbae (Dr-Rank1).

## License

This project is open-sourced software licensed under the MIT License.
