# AML Risk Scoring System

A production-grade Anti-Money Laundering (AML) risk scoring engine that processes financial transactions, applies configurable compliance rules, generates alerts, and provides a real-time dashboard for compliance teams.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)
![React](https://img.shields.io/badge/React-18-blue)
![Coverage](https://img.shields.io/badge/Coverage-94%25-brightgreen)
![Tests](https://img.shields.io/badge/Tests-66%20passing-brightgreen)

## Overview

The system evaluates every incoming transaction against 5 configurable AML rules, calculates a weighted risk score, and automatically generates compliance alerts for flagged transactions. Compliance officers can review and action alerts directly from the dashboard.

Transaction → Rule Engine → Risk Score → Alert Generation → Dashboard Review


## Features

- **Rule Engine** — 5 configurable AML rules with weighted scoring
  - High transaction amount detection
  - Velocity checking (burst transactions)
  - Geographic anomaly detection (impossible travel)
  - OFAC/sanctions list screening
  - KYC status verification
- **Risk Scoring** — weighted algorithm producing 0-100 risk scores
- **Alert Workflow** — open → in review → resolved/escalated/false positive
- **Real-time Dashboard** — live stats, transactions, alerts, customer profiles
- **REST API** — full OpenAPI/Swagger documentation
- **94% Test Coverage** — 66 tests (unit + integration + endpoint)
- **Kubernetes Ready** — HPA auto-scaling, health probes, resource limits

## Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| Python 3.11 | Core language |
| FastAPI | REST API framework |
| SQLAlchemy | ORM |
| PostgreSQL | Primary database |
| Redis | Caching and task queue |
| Celery | Background task processing |
| Alembic | Database migrations |
| pytest | Testing framework |

### Frontend
| Technology | Purpose |
|---|---|
| React 18 | UI framework |
| TypeScript | Type safety |
| TanStack Query | Data fetching and caching |
| Tailwind CSS | Styling |
| Vite | Build tool |

### DevOps
| Technology | Purpose |
|---|---|
| Docker | Containerization |
| Kubernetes | Orchestration |
| GitHub Actions | CI/CD pipeline |
| PostgreSQL 15 | Production database |
| Redis 7 | Production cache |

## Architecture

aml-risk-system/
├── backend/
│ ├── app/
│ │ ├── api/v1/endpoints/ # REST endpoints
│ │ ├── core/ # Config, exceptions, logging
│ │ ├── db/models/ # SQLAlchemy models
│ │ ├── schemas/ # Pydantic validation
│ │ └── services/ # Business logic
│ │ ├── rule_engine.py # Core AML rules
│ │ ├── transaction_service.py
│ │ └── alert_service.py
│ └── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── frontend/
│ └── src/
│ ├── pages/ # Dashboard, Customers, Transactions, Alerts
│ ├── services/ # API client
│ └── types/ # TypeScript interfaces
├── k8s/ # Kubernetes manifests
│ ├── backend/ # Deployment, Service, HPA
│ ├── postgres/ # Deployment, Service, PVC
│ └── redis/ # Deployment, Service
└── .github/workflows/ # CI/CD pipeline


## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker Desktop

### Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/vaggelispollatos/aml-risk-system.git
cd aml-risk-system

# Start infrastructure
docker-compose up postgres redis -d

# Start backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Start frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** for the dashboard.  
Open **http://localhost:8000/docs** for the API documentation.

## Running Tests

```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html --cov-fail-under=80
```

Coverage report is generated at `backend/htmlcov/index.html`.

## API Endpoints

### Customers
| Method | Endpoint | Description |
|---|---|---|
| POST | /api/v1/customers | Create customer |
| GET | /api/v1/customers | List customers |
| GET | /api/v1/customers/{id} | Get customer |
| PATCH | /api/v1/customers/{id} | Update customer |

### Transactions
| Method | Endpoint | Description |
|---|---|---|
| POST | /api/v1/transactions | Create and score transaction |
| GET | /api/v1/transactions | List transactions |
| GET | /api/v1/transactions/{id} | Get transaction |

### Alerts
| Method | Endpoint | Description |
|---|---|---|
| GET | /api/v1/alerts | List alerts |
| GET | /api/v1/alerts/{id} | Get alert |
| PATCH | /api/v1/alerts/{id} | Review alert |

## AML Rules

| Rule | Severity | Weight | Description |
|---|---|---|---|
| High Amount | High | 25% | Transaction exceeds $10,000 threshold |
| Velocity Check | Critical | 30% | More than 5 transactions in 60 minutes |
| Geographic Anomaly | High | 20% | Impossible travel between transactions |
| Sanctions Check | Critical | 25% | Customer on OFAC sanctions list |
| KYC Verification | Medium | 10% | Customer KYC not approved |

## Kubernetes Deployment

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Apply secrets and config
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml

# Deploy infrastructure
kubectl apply -f k8s/postgres/
kubectl apply -f k8s/redis/

# Deploy backend
kubectl apply -f k8s/backend/

# Check status
kubectl get pods -n aml-system
```

## CI/CD Pipeline

Every push to `main` or `develop`:
1. Installs dependencies
2. Runs linting (flake8)
3. Runs all tests
4. Enforces 80% minimum coverage
5. Builds Docker image

## License

MIT