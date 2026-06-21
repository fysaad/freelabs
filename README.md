# BRACU Free Room Finder 🏫

A live web application that shows which classrooms and labs are free at BRAC University,
based on the Summer 2026 class schedule.

---

## Project Structure

```
├── app.py              ← Flask backend + API
├── index.html          ← Frontend (single-page, Tailwind CSS)
├── schedule.json       ← Parsed schedule data (4,568 entries, 177 rooms)
├── parse_schedule.py   ← PDF parser (run once to regenerate schedule.json)
├── requirements.txt    ← Python dependencies
├── Procfile            ← For Render / Railway deployment
├── .gitignore
└── README.md
```

---

## Run Locally

### 1. Clone / download the project

```bash
git clone https://github.com/YOUR_USERNAME/bracu-free-rooms.git
cd bracu-free-rooms
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. (Optional) Re-parse the PDF

Only needed if you have an updated schedule PDF:

```bash
python parse_schedule.py Class_Schedule_Summer_2026.pdf
```

This overwrites `schedule.json`.

### 5. Start the server

```bash
python app.py
```

Open http://localhost:5000 in your browser.

---

## API Reference

All endpoints return JSON.

| Endpoint | Params | Description |
|---|---|---|
| `GET /api/free-rooms` | `day`, `start`, `end` | Free rooms in a time window |
| `GET /api/room-schedule` | `day`, `room` | Full day schedule for one room |
| `GET /api/all-rooms` | — | List of all room codes |
| `GET /api/stats` | — | Entry counts per day |

**Example:**
```
GET /api/free-rooms?day=MONDAY&start=02:00 PM&end=03:20 PM
```

---

## Deploy to Render (Free Tier) — Step by Step

### Step 1 — Push to GitHub

```bash
# Initialize git (if not already)
git init
git add .
git commit -m "Initial commit — BRACU Free Room Finder"

# Create a repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/bracu-free-rooms.git
git branch -M main
git push -u origin main
```

### Step 2 — Create a Render account

Go to https://render.com and sign up (free, no credit card needed).

### Step 3 — Create a new Web Service

1. Click **New → Web Service**
2. Connect your GitHub account and select your repo
3. Fill in the settings:

| Setting | Value |
|---|---|
| **Name** | `bracu-free-rooms` (or anything you like) |
| **Region** | Singapore (closest to BD) |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2` |
| **Instance Type** | Free |

4. Click **Create Web Service**

Render will build and deploy automatically. Your app will be live at:
`https://bracu-free-rooms.onrender.com` (or your chosen name).

> **Note:** Free Render instances spin down after 15 minutes of inactivity.
> The first request after a sleep takes ~30 seconds. This is normal.
> Upgrade to Starter ($7/mo) to keep it always-on.

---

## Deploy to Railway — Alternative

1. Go to https://railway.app and sign up
2. Click **New Project → Deploy from GitHub repo**
3. Select your repo
4. Railway auto-detects Python and reads the `Procfile`
5. Set environment variable: `PORT=8080` (Railway sets this automatically)
6. Deploy — you get a live URL immediately

Railway gives $5 of free credit per month, enough for ~500 hours.

---

## Update the Schedule (Next Semester)

1. Get the new PDF from BRACU
2. Run: `python parse_schedule.py new_schedule.pdf`
3. Commit and push `schedule.json`
4. Render / Railway will redeploy automatically

---

## Tech Stack

- **Backend:** Python 3.11, Flask 3.0, Gunicorn
- **PDF Parsing:** pdfplumber
- **Frontend:** Vanilla JS, Tailwind CSS (CDN)
- **Data:** 4,568 schedule entries, 177 rooms, Summer 2026
