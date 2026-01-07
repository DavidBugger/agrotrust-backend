# Agrotrust V1 Backend

A hybrid **Django + FastAPI** backend for Agrotrust, designed for ultra-simple farmer UX and NGO/MFI partner management.

---

## 🚀 Quick Start (Step-by-Step)

### 1. Environment Setup
Clone the repository and ensure you have Python 3.9+ installed.

```bash
# Navigate to the project directory
cd agrotrust-backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
# (If requirements.txt is missing, run: pip install django djangorestframework django-environ psycopg2-binary fastapi uvicorn supabase httpx pyjwt)
```

### 2. Configuration
Copy the `.env` template and fill in your details (optional for SQLite dev).

```bash
cp .env.example .env 
```

### 3. Database Initialization
This project uses SQLite for local development by default.

```bash
# Run migrations
python manage.py makemigrations api
python manage.py migrate

# Create an admin user to access the dashboard
python manage.py createsuperuser
```

---

## 🛠 Running the Servers

Agrotrust runs two concurrent servers:

### A. Django Admin (Internal Management)
Used for managing farmers, viewing activities, and configuring trust weights.
```bash
python manage.py runserver 8000
```
- **URL:** [http://localhost:8000/admin/](http://localhost:8000/admin/)

### B. FastAPI (Public API)
Handles the Farmer App, Partner Dashboard, and Trust Scoring logic.
```bash
python fastapi_app/main.py
```
- **URL:** [http://localhost:8001/](http://localhost:8001/)
- **Interactive Documentation:** [http://localhost:8001/docs](http://localhost:8001/docs)

---

## 📖 API Reference (V1 Highlights)

| Category | Endpoint | Method | Purpose |
| :--- | :--- | :--- | :--- |
| **Auth** | `/auth/sync-user` | `POST` | Sync Supabase session with local DB |
| **Farmer** | `/farmers/profile` | `POST/GET` | Manage farmer basic info |
| **Farmer** | `/farmers/home` | `GET` | Home screen status & greeting |
| **Activities** | `/farm-activities` | `POST/GET` | Log and list farm logs |
| **Trust** | `/farmers/trust-level` | `GET` | Visual trust status & tips |
| **Partner** | `/partners/farmers` | `GET` | NGO list view with filters |
| **Partner** | `/partners/export/farmers` | `GET` | CSV data export |

---

## 🔐 Security Note
For development, JWT verification is mocked in `fastapi_app/main.py`. To enable real Supabase JWT verification:
1. Update `.env` with your `SUPABASE_JWT_SECRET`.
2. Uncomment the JWT decoding logic in `fastapi_app/main.py:verify_token()`.

---

## 📁 Project Structure
- `api/`: Django app containing Core Models.
- `core/`: Django project settings.
- `fastapi_app/`: FastAPI application and logic.
- `db.sqlite3`: Local database file.
- `.env`: Environment variables.

---

## 🚀 Hosting on Render (Free Tier)

This project is pre-configured to deploy on **Render** using a Blueprint (`render.yaml`).

### 1. Database Setup (Render Postgres)
Render provides a free PostgreSQL database (expires after 90 days).
1. Go to [Render Dashboard](https://dashboard.render.com/) -> **New** -> **PostgreSQL**.
2. Name it `agrotrust-db`.
3. Select the **Free** plan.
4. Once created, Render will automatically link it to your web service if you use the Blueprint.

### 2. Deployment Steps
1. **Push Code to GitHub**: Ensure your latest changes are pushed.
2. **Setup Blueprint**:
   - Go to **New** -> **Blueprint**.
   - Connect your repository.
   - Render will detect `render.yaml` and prompt you to create the resources.
3. **Environment Variables**:
   - The Blueprint handles `DATABASE_URL` automatically.
   - You **MUST** manually add `SUPABASE_JWT_SECRET` in the Render Dashboard (**Dashboard -> Web Service -> Environment**).
4. **Build & Start**:
   - Render runs `build.sh` (installs deps, runs migrations).
   - The start command is: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker fastapi_app.main:app`.

### 🛡️ Changing to Production Database
To use a permanent database (like Supabase Postgres):
1. Create your database on Supabase.
2. In Render, go to **Environment Settings**.
3. Edit `DATABASE_URL` and paste your Supabase connection string.
