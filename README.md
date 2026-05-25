# Support CRM System

A full-stack customer support ticketing CRM built with FastAPI, SQLite, and a responsive HTML/CSS/JavaScript frontend.

## Deployed Application

Live URL: https://web-production-0c2f8.up.railway.app/

## Features

- Create support tickets with customer name, email, issue title, and description.
- Auto-generate ticket IDs such as `TKT-001` with timestamps.
- View a clean ticket list with ID, customer, title, status, and date.
- Search across ticket ID, customer name, email, subject, and description.
- Filter tickets by `Open`, `In Progress`, and `Closed`.
- View ticket details, update status, and add internal notes.

## Tech Stack

- Backend: Python, FastAPI
- Database: SQLite with SQLAlchemy
- Frontend: HTML, CSS, vanilla JavaScript
- Deployment target: Railway

## Local Setup

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:

   ```bash
   uvicorn app.main:app --reload
   ```

4. Open the app:

   ```text
   http://127.0.0.1:8000
   ```

The SQLite database is created automatically as `support_crm.db`.

## API Endpoints

### Create Ticket

`POST /api/tickets`

```json
{
  "customer_name": "Jane Customer",
  "customer_email": "jane@example.com",
  "subject": "Order not delivered",
  "description": "The order has not arrived yet."
}
```

### List Tickets

`GET /api/tickets?status=Open&search=jane`

### Get Ticket Details

`GET /api/tickets/TKT-001`

### Update Ticket

`PUT /api/tickets/TKT-001`

```json
{
  "status": "In Progress",
  "notes": "Contacted courier and shared update with customer."
}
```

## Railway Deployment

1. Push this project to a GitHub repository.
2. Create a new Railway project from the GitHub repo.
3. Railway will install `requirements.txt` and use the start command from `railway.json`.
4. Optional environment variable:

   ```text
   DATABASE_URL=sqlite:///./support_crm.db
   ```

5. Deploy and use the public Railway URL as the submitted deployed application.

## Repository Checklist

- `README.md` with setup and deployment instructions
- `.env.example`
- `.gitignore`
- FastAPI backend in `app/`
- Frontend static files in `app/static/`
- Railway deployment configuration
