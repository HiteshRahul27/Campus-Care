# 🏥 School Health Screening System

Luna-palette dashboard with JWT auth, real users, and persistent Supabase storage.
**Backend on Render · Frontend on Vercel · Database on Supabase**

---

## What you get

- 🔐 Real JWT login — bcrypt-hashed passwords, 8-hour tokens
- 👥 Multi-user — create/delete health worker accounts from the app
- 👩‍🎓 Students — add, edit, delete with combined health data form
- 📊 Dashboard — live stats, averages, recent entries
- ⬇️ CSV export — one click download
- 🎨 Flashy Luna blue UI — glowing cards, animated sidebar

---

## Folder structure

```
flashy_app/
├── backend/
│   ├── main.py            ← FastAPI app (single file, all routes)
│   ├── requirements.txt
│   └── .env.example       ← copy to .env for local dev
├── frontend/
│   ├── index.html         ← Login page
│   ├── app.html           ← Full SPA (dashboard + students + users)
│   └── vercel.json
├── schema.sql             ← Run once in Supabase
├── render.yaml            ← One-click Render deploy config
└── README.md
```

---

## Step 1 — Supabase (Database)

1. Go to **https://supabase.com** → **New Project**
   - Give it a name (e.g. `school-health`)
   - Set a strong database password — **save it somewhere**
   - Pick the region closest to you
   - Wait ~1 minute for it to provision

2. Go to **SQL Editor** → **New Query**
   - Paste the entire contents of `schema.sql`
   - Click **Run** (green button)
   - You should see "Success. No rows returned"

3. Go to **Settings → Database**
   - Scroll to **Connection string → URI**
   - Copy the string — it looks like:
     ```
     postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxx.supabase.co:5432/postgres
     ```
   - Replace `[YOUR-PASSWORD]` with the password you set in step 1
   - **Save this — you'll need it for Render**

---

## Step 2 — GitHub (Required for Render + Vercel)

Push this project to a GitHub repo:

```bash
cd flashy_app
git init
git add .
git commit -m "initial commit"
# Create a repo on github.com first, then:
git remote add origin https://github.com/YOUR_USERNAME/school-health.git
git push -u origin main
```

---

## Step 3 — Render (Backend)

1. Go to **https://render.com** → **New → Web Service**
2. Connect your GitHub repo
3. Set these fields:
   | Field | Value |
   |-------|-------|
   | **Root Directory** | `backend` |
   | **Runtime** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
   | **Instance Type** | Free |

4. Under **Environment Variables**, click **Add Environment Variable** and add:

   | Key | Value |
   |-----|-------|
   | `DATABASE_URL` | your Supabase connection string from Step 1 |
   | `SECRET_KEY` | any long random string, e.g. `h7k2m9p3x5q8w1n4r6j0e` |

5. Click **Create Web Service**
   - First deploy takes ~3 minutes
   - Your backend URL will be: `https://school-health-api.onrender.com` (or similar)
   - **Copy this URL — you'll need it for the frontend**

6. Test it: open `https://your-backend.onrender.com/docs` in browser — you should see Swagger UI

> ⚠️ **Free tier sleeps after 15 min inactivity.** First request after sleep takes ~30 seconds. That's normal.

---

## Step 4 — Update frontend with your backend URL

Open `frontend/index.html` and `frontend/app.html`, find this line near the top of the `<script>` tag in each file:

```js
const API = localStorage.getItem("api_url") || "https://your-backend.onrender.com";
```

Replace `https://your-backend.onrender.com` with your actual Render URL from Step 3.

Then commit and push:
```bash
git add .
git commit -m "set backend url"
git push
```

---

## Step 5 — Vercel (Frontend)

1. Go to **https://vercel.com** → **Add New → Project**
2. Import your GitHub repo
3. Set:
   | Field | Value |
   |-------|-------|
   | **Root Directory** | `frontend` |
   | **Framework Preset** | `Other` |
   | **Build Command** | *(leave blank)* |
   | **Output Directory** | `.` |

4. Click **Deploy**
   - Takes ~30 seconds
   - Your app URL: `https://school-health-xxx.vercel.app`

5. Open the URL → you're on the login page

---

## Step 6 — First Login

Default credentials (auto-created on first backend startup):

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `admin123` |

**Change this immediately** — go to Users tab → Add a new account → then you can delete the default admin if needed (you can't delete yourself, so create a new admin first).

---

## Local Development (optional)

```bash
# Backend
cd backend
cp .env.example .env
# Edit .env — paste your Supabase DATABASE_URL and a SECRET_KEY
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend — just open index.html in browser
# or serve with:
cd frontend
python -m http.server 5500
# open http://localhost:5500
```

For local dev, the frontend will use `http://localhost:8000` — update the `API` const in both HTML files.

---

## API endpoints (all protected by JWT except login)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Get JWT token |
| GET | `/auth/me` | Current user info |
| GET/POST | `/users/` | List / create users |
| DELETE | `/users/{id}` | Delete user |
| GET/POST | `/students/` | List / create students |
| PUT/DELETE | `/students/{id}` | Update / delete student |
| GET/POST | `/health-records/` | List / create records |
| PUT/DELETE | `/health-records/{id}` | Update / delete record |
| GET | `/export/csv` | Download CSV |

Full interactive docs at: `https://your-backend.onrender.com/docs`

---

## Troubleshooting

**CORS error in browser**
→ Make sure your Render backend is running. Check Render logs.

**"detail: Invalid credentials" on login**
→ Backend started but DB tables weren't created. Check Render logs for SQLAlchemy errors. Usually means `DATABASE_URL` is wrong.

**Frontend shows blank / can't reach API**
→ The `API` const in `index.html` and `app.html` still has the placeholder URL. Update it with your actual Render URL.

**Render deploy fails**
→ Make sure Root Directory is set to `backend`, not the repo root.

**Supabase connection refused**
→ In Supabase → Settings → Database → make sure you're using the **URI** format (starts with `postgresql://`), not the individual fields.
