# InvoiceFlow — Flask + SQLite Invoice Manager

A full-stack invoice management web app built with Python Flask and SQLite.

## Features
- User authentication (register / login)
- Create, edit, delete invoices with line items
- Client management
- Invoice preview + print to PDF
- Reports & analytics dashboard
- Per-user settings (business info, currency, tax, etc.)

---

## Run Locally

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
python app.py
```

### 3. Open in browser
```
http://localhost:5000
```

---

## Deploy to Railway (Free — Recommended)

Railway is the easiest way to host Flask apps for free with a real URL.

### Steps:
1. Push this folder to a GitHub repo
2. Go to https://railway.app → New Project → Deploy from GitHub
3. Select your repo
4. Railway auto-detects Flask and deploys it
5. Go to Settings → Add a custom domain or use the generated `.railway.app` URL
6. Set environment variable: `SECRET_KEY=your-random-secret-key-here`

Done! Your app is live at `https://yourapp.railway.app`

---

## Deploy to Render (Also Free)

1. Push to GitHub
2. Go to https://render.com → New Web Service → Connect your repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Add env var: `SECRET_KEY=your-random-secret-key`
6. Deploy

---

## Project Structure

```
invoiceflow/
├── app.py              # Flask app + all routes + SQLAlchemy models
├── requirements.txt    # Python dependencies
├── Procfile            # For Railway/Render deployment
├── README.md
└── templates/
    ├── login.html      # Login & Register page
    └── app.html        # Main application (dashboard, invoices, clients, reports)
```

---

## Tech Stack
- **Backend**: Python Flask
- **Database**: SQLite (via Flask-SQLAlchemy)
- **Auth**: werkzeug password hashing + Flask sessions
- **Frontend**: Vanilla JS + CSS (no frameworks needed)
- **PDF Export**: Browser print dialog (Ctrl+P → Save as PDF)

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Flask session secret (change in production!) |

---

## Portfolio Notes

This project demonstrates:
- RESTful API design with Flask
- SQLite database with SQLAlchemy ORM
- User authentication with password hashing
- Multi-user data isolation
- Full CRUD operations
- Clean frontend without frameworks
