# 🏥 MedAssist - Smart Doctor Appointment System

<div align="center">

![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18.2-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Mistral AI](https://img.shields.io/badge/Mistral_AI-LLM-FF7000?style=for-the-badge)
![MCP](https://img.shields.io/badge/MCP-Protocol-6366F1?style=for-the-badge)

**An AI-powered healthcare appointment system with natural language booking, multi-turn conversations, and smart doctor reporting.**

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [API Reference](#-api-reference) • [Deployment](#-deployment)

</div>

---

## 🎯 Overview

MedAssist is a full-stack healthcare appointment system that leverages **Model Context Protocol (MCP)** to create an agentic AI assistant. Patients can book appointments using natural language, while doctors receive intelligent summary reports via Slack, email, or in-app notifications.

### 🔥 Key Highlights

- **Agentic AI** - LLM dynamically selects and chains tools to fulfill requests
- **Multi-turn Conversations** - Maintains context across conversation turns
- **Real Integrations** - Google Calendar, Slack, SendGrid
- **Role-based Access** - Patient and Doctor dashboards
- **Production Ready** - Docker, async architecture, proper auth

---

## 📸 Screenshots

### Patient Booking Flow
![Patient Dashboard](./screenshots/patient-dashboard.png)
*Natural language booking with AI assistant - "Book with Dr. Ahuja tomorrow at 10 AM"*

![Booking Success](./screenshots/booking-success.png)
*Multi-turn conversation showing context memory and MCP tools in action*

### Doctor Dashboard
![Doctor Dashboard](./screenshots/doctor-dashboard.png)
*Doctor's schedule and statistics overview with AI assistant*

![Slack Report](./screenshots/doctor-slack-report.png)
*Automated report delivery to Slack notification channel*

---

## ✨ Features

### For Patients
| Feature | Description |
|---------|-------------|
| 🗣️ **Natural Language Booking** | "Book with Dr. Ahuja tomorrow at 10 AM" |
| 📅 **Calendar Integration** | Appointments sync to Google Calendar |
| 📧 **Email Confirmations** | Automatic confirmation emails |
| 🔄 **Context Memory** | AI remembers previous messages |

### For Doctors
| Feature | Description |
|---------|-------------|
| 📊 **Smart Reports** | "How many patients visited yesterday?" |
| 📱 **Slack Notifications** | Daily summaries sent to Slack |
| 📈 **Statistics Dashboard** | Patient visits, symptoms breakdown |
| 🗓️ **Schedule Management** | View and manage appointments |

### MCP Tools Available
```
check_doctor_availability  → Check when a doctor is free
schedule_appointment       → Book an appointment
get_patient_statistics     → Get visit stats and reports
send_doctor_report         → Send reports via Slack/Email
reschedule_appointment     → Auto-reschedule appointments
cancel_appointment         → Cancel with notifications
get_all_doctors            → List available doctors
```

---

## 🛠️ Tech Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│  React 18 • TypeScript • Vite • Axios • Lucide Icons            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                  │
│  FastAPI • SQLAlchemy • Pydantic • JWT Auth • AsyncIO           │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   PostgreSQL    │ │   Mistral AI    │ │   MCP Server    │
│   (Database)    │ │   (LLM)         │ │   (Tools)       │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Google Calendar │ │     Slack       │ │    SendGrid     │
│   (Scheduling)  │ │ (Notifications) │ │    (Email)      │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## � Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 16+ (or Docker)
- Mistral AI API Key

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/medassist.git
cd medassist
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### 3. Database Setup

```bash
# Using Docker (recommended)
docker run -d \
  --name medassist-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=medassist \
  -p 5432:5432 \
  postgres:16-alpine
```

### 4. Frontend Setup

```bash
cd frontend
npm install
```

### 5. Run the Application

```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

**Access the app at:** http://localhost:5173

---

## ⚙️ Environment Variables

Create `backend/.env` with:

```env
# Required
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/medassist
MISTRAL_API_KEY=your_mistral_api_key
SECRET_KEY=your-super-secret-key-change-in-production

# Optional - External Services
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_FILE=token.json
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx
SENDGRID_API_KEY=your_sendgrid_key

# Development
DEBUG=true
CORS_ORIGINS=["http://localhost:5173"]
```

---

## 🏗️ Architecture

```mermaid
flowchart TB
    subgraph Frontend["🖥️ Frontend (React)"]
        UI[Chat Interface]
        Dashboard[Dashboards]
    end

    subgraph Backend["⚙️ Backend (FastAPI)"]
        API[REST API]
        Agent[AI Agent]
        MCP[MCP Tools]
    end

    subgraph External["🔌 External Services"]
        LLM[Mistral AI]
        Calendar[Google Calendar]
        Slack[Slack]
        Email[SendGrid]
    end

    subgraph Database["🗄️ PostgreSQL"]
        Users[(Users)]
        Appointments[(Appointments)]
        Conversations[(Conversations)]
    end

    UI --> API
    API --> Agent
    Agent <--> LLM
    Agent --> MCP
    MCP --> Database
    MCP --> Calendar
    MCP --> Slack
    MCP --> Email
```

---

## � API Reference

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register new user |
| `/api/auth/login` | POST | Login and get JWT token |
| `/api/auth/me` | GET | Get current user info |

### Chat (AI Agent)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat/message` | POST | Send message to AI |
| `/api/chat/history` | GET | Get conversation history |
| `/api/chat/prompts` | GET | Get prompt history |

### Appointments

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/appointments` | GET | List appointments |
| `/api/appointments` | POST | Create appointment |
| `/api/appointments/{id}` | PUT | Update appointment |
| `/api/appointments/{id}` | DELETE | Cancel appointment |

### Doctors

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/doctors` | GET | List all doctors |
| `/api/doctors/{id}/availability` | GET | Get available slots |
| `/api/doctors/{id}/stats` | GET | Get doctor statistics |

**Full API docs at:** http://localhost:8000/docs

---

## 🐳 Deployment

### Using Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: medassist
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/medassist
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

```bash
docker-compose up -d
```

### Render Deployment

1. **Backend**: Deploy as Web Service with `uvicorn app.main:app`
2. **Frontend**: Deploy as Static Site with `npm run build`
3. **Database**: Use Render PostgreSQL

---

## 🧪 Testing

### Sample Prompts

**Patient Booking:**
```
"I want to book with Dr. Ahuja tomorrow morning"
"Book the 10 AM slot"
"What doctors are available?"
```

**Doctor Reports:**
```
"How many patients visited yesterday?"
"Send a daily report to Slack"
"How many patients had fever this week?"
```

### Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Patient | patient@example.com | patient123 |
| Doctor | dr.ahuja@clinic.com | doctor123 |
| Doctor | dr.sharma@clinic.com | doctor123 |
| Doctor | dr.patel@clinic.com | doctor123 |

---

## 📁 Project Structure

```
medassist/
├── backend/
│   ├── app/
│   │   ├── routers/      # API endpoints
│   │   ├── services/     # Calendar, Email, Notifications
│   │   ├── agent.py      # AI Agent with Mistral
│   │   ├── mcp_server.py # MCP Tools implementation
│   │   ├── models.py     # SQLAlchemy models
│   │   └── schemas.py    # Pydantic schemas
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Dashboard pages
│   │   ├── context/      # Auth context
│   │   └── api/          # API client
│   ├── package.json
│   └── Dockerfile
│
└── README.md
```

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Google OAuth blocked | Add email as test user in Google Cloud Console |
| Database connection error | Ensure PostgreSQL is running and credentials match |
| CORS errors | Check `CORS_ORIGINS` in `.env` matches frontend URL |
| AI not responding | Verify `MISTRAL_API_KEY` is set correctly |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## � License

This project is part of the **Dobbe AI Full-Stack Developer Intern Assignment**.

---

<div align="center">

**Built with ❤️ using FastAPI, React, and Mistral AI**

[⬆ Back to Top](#-medassist---smart-doctor-appointment-system)

</div>
