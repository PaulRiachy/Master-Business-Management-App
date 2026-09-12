# Master Business Management — Submission MVP

A small internal business-management application covering the complete project lifecycle:

**RFQ → Quoted → Ordered → Shipping → Closed**

The MVP includes the required workflow, financial controls, role-based access, activity timeline, dashboard attention rules, and a database-grounded AI assistant.

## Stack

- Frontend: Next.js 15 + React 19 + TypeScript
- Backend: Python 3.12 + FastAPI
- Database: PostgreSQL 17 + SQLAlchemy
- Authentication: JWT
- AI: OpenAI-compatible API
- Local database: Docker Compose
- Bonus: lightweight AI chat widget

## Versions to use

- **Python 3.12.x**
- **Node.js 20 LTS (20.x)**
- **Docker Desktop** with Docker Compose

Do not use Python 3.14 for this submission environment.

## New setup from scratch

Follow these steps on a fresh checkout. No migration or upgrade steps are required.

### 1. Start PostgreSQL

From the repository root:

```bash
docker compose up -d postgres
```

The included Compose file creates the PostgreSQL database expected by the backend.

### 2. Set up the backend

#### Windows PowerShell

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python seed.py
uvicorn app.main:app --reload --port 8000
```

#### macOS / Linux

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
python seed.py
uvicorn app.main:app --reload --port 8000
```

The seed script waits for PostgreSQL to become available before creating tables and demo data.

### 3. Configure AI

Open `backend/.env` and set your provider configuration:

```env
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-5.6-luna
```

The non-AI application works without an API key. AI features require a valid provider key.

The integration uses the standard OpenAI Python client, so another OpenAI-compatible provider can be used by changing only `OPENAI_BASE_URL` and `OPENAI_MODEL`.

Note: openrouter/free was used in the testing of this project, no open AI api was available at time of testing. 
Additionally, if it says api key not found, rerun and should work fine. (docker compose down -v, docker compose up -d postgres, python seed.py)

### 4. Verify the backend

Open:

- `http://localhost:8000/health`
- `http://localhost:8000/docs`

The health endpoint should return HTTP 200:

```json
{"status":"ok","database":"ok"}
```

### 5. Set up the frontend

Open a second terminal:

```bash
cd frontend
npm install
```

Create `.env.local` from `.env.local.example`.

#### Windows PowerShell

```powershell
Copy-Item .env.local.example .env.local
```

#### macOS / Linux

```bash
cp .env.local.example .env.local
```

The file should contain:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

Start the frontend:

```bash
npm run dev
```

Open `http://localhost:3000`.

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Admin | `admin@example.com` | `admin123` |
| Sales | `sales@example.com` | `sales123` |
| Procurement | `procurement@example.com` | `proc123` |

## Verification procedure

### Backend checks

From `backend` with the virtual environment active:

```bash
pytest -q
python -m compileall -q app seed.py
```

Expected test result:

```text
19 passed
```

### Frontend build check

From `frontend`:

```bash
npm run build
```

### Manual application check

1. Log in as **Admin**.
2. Confirm the Dashboard loads without errors.
3. Open **Projects** and confirm the four seeded projects are visible.
4. Open **Northstar Store Rollout** and move `Quoted → Ordered`.
5. Open **Acme Spare Parts** and confirm `Shipping` status and shipment hold.
6. Try to close it without an override reason; the backend must reject it.
7. Enter an Admin override reason and close it.
8. Confirm the override is recorded in the Activity Timeline.
9. Return to Dashboard and confirm the counts update.
10. Use the **Ask My Business** chat with: `Show me projects for Acme Trading with margins below 20%.`
11. Ask a follow-up question in the same chat.
12. Generate a **Daily Brief**.
13. Generate a **Follow-up Email** for a project.
14. Edit the draft and use **Edit & Confirm**.
15. Confirm the approved AI draft appears in the Activity Timeline.
16. Toggle Light/Dark mode and refresh the page.
17. Log in as **Sales** and confirm supplier costs and profit/margin are hidden.
18. Log in as **Procurement** and confirm customer revenue/balance and profit/margin are hidden.
19. As **Sales**, ask AI for supplier costs, expenses, profit, or margin; it must refuse the restricted request.
20. As **Procurement**, ask AI for customer revenue, customer balance, profit, or margin; it must refuse the restricted request.
21. Generate a Daily Brief as Sales and Procurement and verify it contains only information allowed for that role.

## Required demo walkthrough

The assignment allows a video **or** a bulleted demo. Use the following walkthrough in the submission:

- **Create RFQ:** create a new project from the Projects page.
- **Quote:** move the project from `RFQ` to `Quoted`.
- **Order:** move it from `Quoted` to `Ordered`.
- **Ship:** move it from `Ordered` to `Shipping`.
- **Financial Control:** show estimated vs actual financials and the calculated margin.
- **Shipment Hold:** show that a shipping project with an outstanding customer balance cannot be closed normally.
- **Admin Override:** enter a reason and show the override in the Activity Timeline.
- **Dashboard Attention:** show overdue work, missing next actions, low-margin Admin alerts, and shipment holds.
- **Role-Based Access:** show different financial visibility for Admin, Sales, and Procurement.
- **Ask My Business:** ask a database-grounded question about projects or margins.
- **Daily Brief:** generate the current attention summary.
- **AI Follow-Up:** generate a customer follow-up draft for a project.
- **Human Approval:** edit the AI draft and explicitly confirm it before it is recorded.
- **API Documentation:** open `/docs` to demonstrate the REST API.
- **AI Chat Bonus:** ask multiple questions in the dashboard chat widget.

## Architecture

```text
master-business-management-app/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth_routes.py
│   │   │   ├── master_data_routes.py
│   │   │   ├── project_routes.py
│   │   │   ├── dashboard_routes.py
│   │   │   ├── ai_routes.py
│   │   │   └── routes.py
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   │       ├── ai_service.py
│   │       └── project_service.py
│   ├── seed.py
│   ├── tests.py
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── components/
│   └── lib/
├── docker-compose.yml
└── README.md
```

The API is intentionally split by responsibility while preserving one `/api` entry point. Business rules remain in services; route modules handle HTTP concerns; SQLAlchemy models represent the relational data.

## Core business rules

### Workflow

The backend enforces the only valid forward sequence:

```text
RFQ → Quoted → Ordered → Shipping → Closed
```

Skipping states or moving backward is rejected.

### Financial control

```text
Estimated Total Cost = Estimated Supplier Cost + Estimated Expenses
Actual Total Cost    = Actual Supplier Cost + Actual Expenses
Actual Profit        = Actual Revenue - Actual Total Cost
Actual Margin        = Actual Profit / Actual Revenue × 100
```

### Shipment hold

When a project is in `Shipping` and `Customer Balance Due > 0`:

- closing is blocked;
- the project is flagged on the dashboard;
- only an Admin can override the hold;
- the Admin must provide a reason;
- the Admin name, timestamp, and reason are recorded in the Activity Timeline.

### Permissions

| Capability | Admin | Sales | Procurement |
|---|:---:|:---:|:---:|
| Customers | ✓ | ✓ | ✓ |
| Suppliers | ✓ | — | ✓ |
| Customer revenue | ✓ | ✓ | — |
| Supplier costs | ✓ | — | ✓ |
| Profit / margin | ✓ | — | — |
| Low-margin alerts | ✓ | — | — |
| Project status | ✓ | ✓ | ✓ |
| Shipment-hold override | ✓ | — | — |

Restricted financial fields are omitted from role-filtered API responses and AI context.

## Ask My Business AI

The AI retrieves current project data from PostgreSQL and applies role-based filtering before the model is called. Closed projects are excluded from current business-query context.

Supported capabilities:

1. Daily Brief
2. Natural-language business questions
3. Project-specific follow-up email drafts
4. Human approval before an AI draft becomes an activity
5. Dashboard AI chat widget

The AI is instructed to use the supplied business context only, never invent business facts, use the current date for due-date interpretation, and avoid Markdown tables in favor of concise headings and bullets.

## API routes

- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/customers`
- `POST /api/customers`
- `GET /api/suppliers`
- `POST /api/suppliers`
- `GET /api/users`
- `GET /api/projects`
- `POST /api/projects`
- `PUT /api/projects/{project_id}`
- `GET /api/projects/{project_id}`
- `POST /api/projects/{project_id}/activities`
- `POST /api/projects/{project_id}/transition`
- `PATCH /api/projects/{project_id}/financials`
- `GET /api/dashboard`
- `POST /api/ai/ask`
- `POST /api/ai/daily-brief`
- `POST /api/ai/draft-followup/{project_id}`
- `POST /api/ai/confirm-draft/{project_id}`

## Final Notes
- AI was used in the development of this project for adjustments, code reviews, and bug fixes.
- Prioritized simplicity and functionality over adding too many features.
- Only AI Widget was implemented from bonus section.