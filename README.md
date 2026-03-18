# BijoyFantasyCricketBD 🏏

**Bangladesh's first full-stack fantasy cricket platform** — built on BPL (Bangladesh Premier League) 2012–2026 numeric statistics.

> FastAPI · SQLite · AI Predictions · Bcash/Nagad Payments · Role-based Access · Render.com ready

---

## What this is

A commercial-ready fantasy cricket SaaS platform for the Bangladeshi market. Users pick a 15-player squad from real BPL players, earn points based on live match performances, compete in leagues, and subscribe via Bcash or Nagad.

**Not a WordPress site. A real platform.**

| Layer | Technology |
|---|---|
| API | FastAPI + Python 3.11 |
| Database | SQLite (WAL mode) — 26 tables |
| Auth | bcrypt + HS256 JWT + API keys |
| Payments | Bcash + Nagad (Bangladesh MFS) |
| AI | scikit-learn Random Forest |
| Deploy | Render.com (free tier, Singapore) |

---

## Quick start (local)

```bash
git clone https://github.com/YOUR_USERNAME/bijoyfantasy-cricket
cd bijoyfantasy-cricket

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

# Initialise both databases
python -m database.migrate
python -m fantasy_db.migrate

# Start the API
uvicorn api.main:app --reload
```

Open **http://localhost:8000/docs** — full interactive Swagger UI.

---

## Project structure

```
bijoyfantasy-cricket/
│
├── api/                        ← FastAPI backend
│   ├── main.py                 ← App entry, all routers, middleware
│   ├── auth.py                 ← bcrypt + JWT + API key auth
│   ├── database.py             ← SQLite helpers (query_db, execute_db)
│   ├── dependencies.py         ← Role guards (free/paid/admin/superadmin)
│   ├── payment.py              ← Bcash + Nagad payment integration
│   ├── admin_dashboard.py      ← Admin portal routes
│   └── endpoints/
│       ├── teams.py            ← GET /bpl/teams
│       ├── players.py          ← GET /bpl/players
│       ├── matches.py          ← GET /bpl/matches
│       └── premium.py          ← Paid-only AI endpoints
│
├── database/                   ← Core BPL stats database
│   ├── bpl_schema.sql          ← 11-table schema
│   ├── migrate.py              ← Init + seed (run this first)
│   └── seed_data/
│       └── bpl_2012_2026.json  ← Season data 2012–2026
│
├── fantasy_db/                 ← Fantasy platform database
│   ├── fantasy_schema.sql      ← 26-table fantasy schema
│   ├── migrate.py              ← Fantasy init + seed
│   ├── fantasy_api.py          ← 25 fantasy API endpoints
│   └── points_calculator.py    ← GW points engine (run after each match)
│
├── scraper/                    ← BPL data scrapers (ESPNcricinfo)
│   ├── scrape_bpl_season.py    ← Match results by season
│   ├── scrape_players.py       ← Player career stats
│   ├── scrape_teams.py         ← Team data
│   └── utils.py                ← fetch(), safe_int(), safe_float()
│
├── ai/                         ← Prediction engine
│   ├── predictions.py          ← Win probability + player compare
│   └── train_model.py          ← Train sklearn Random Forest
│
├── tests/                      ← Pytest test suite
│   ├── test_api.py             ← 14 endpoint tests
│   ├── test_scraper.py         ← Scraper utility tests
│   └── test_ai.py              ← AI function tests
│
├── frontend/                   ← Self-contained HTML files
│   ├── dashboard.html          ← Full working admin + player picker demo
│   ├── investor.html           ← Investor pitch page
│   └── landing.html            ← Public API landing page
│
├── render.yaml                 ← Render.com deploy config (free tier)
├── config.yaml                 ← App configuration
├── requirements.txt            ← Python dependencies
├── conftest.py                 ← pytest setup
├── pytest.ini                  ← Test config
└── .env.example                ← Environment variable template
```

---

## API endpoints

### Free (no auth)
```
GET  /bpl/teams
GET  /bpl/teams/{id}
GET  /bpl/players
GET  /bpl/players/{id}
GET  /bpl/matches
GET  /bpl/matches/seasons
GET  /bpl/matches/season/{year}/top-scorers
GET  /bpl/matches/season/{year}/top-wicket-takers
GET  /bpl/matches/{id}
```

### Auth
```
POST /auth/register
POST /auth/token
```

### Payments
```
POST /payment/subscribe        ← Bcash or Nagad
POST /payment/confirm          ← Gateway webhook → issues API key
GET  /payment/my-subscription
```

### Premium (paid API key)
```
GET  /bpl/premium/predictions/{match_id}
GET  /bpl/premium/insights/{match_id}
GET  /bpl/premium/player-compare?player1_id=&player2_id=
GET  /bpl/premium/top-performers
```

### Fantasy
```
GET  /fantasy/gameweeks/active
GET  /fantasy/players
GET  /fantasy/my-team
POST /fantasy/my-team/create
POST /fantasy/my-team/add-player
POST /fantasy/my-team/set-captain
POST /fantasy/my-team/transfer
GET  /fantasy/leaderboard/overall
GET  /fantasy/leaderboard/gw/{gw_id}
GET  /fantasy/premium/predictions/{gw_id}
GET  /fantasy/premium/differentials/{gw_id}
```

### Admin (admin/superadmin only)
```
GET  /admin/stats
GET  /admin/users
POST /admin/users/{id}/revoke-key
GET  /admin/subscriptions
GET  /admin/audit-log
```

---

## Deploy to Render (free)

```bash
# 1. Push to GitHub
git init && git add . && git commit -m "BijoyFantasyCricketBD v1.0"
gh repo create bijoyfantasy-cricket --public --push

# 2. Go to render.com → New Web Service → connect your repo
#    render.yaml handles everything automatically

# 3. Your live URL:
#    https://bijoyfantasy-cricket.onrender.com/docs
```

---

## Wire in the fantasy API (2 lines)

In `api/main.py`, add:

```python
from fantasy_db.fantasy_api import router as fantasy_router
app.include_router(fantasy_router, prefix="/fantasy")
```

---

## Populate real data

```bash
# Scrape all BPL seasons (2012–2026)
python -m scraper.scrape_bpl_season --all

# Scrape player career stats
python -m scraper.scrape_players

# Process GW points after a match
python -m fantasy_db.points_calculator --gw 17

# Train the AI model (needs 20+ real matches)
python -m ai.train_model
```

---

## Scoring rules (fantasy points)

| Action | Points |
|---|---|
| Run | +1 |
| Six | +2 |
| Half century | +10 |
| Century | +25 |
| Duck | -5 |
| Wicket | +20 |
| Maiden | +4 |
| 3-wicket haul | +8 bonus |
| 5-wicket haul | +20 bonus |
| Catch | +8 |
| Stumping | +12 |
| Captain | 2× multiplier |
| Vice-captain | 1.5× multiplier |
| Extra transfer | -4 pts |

---

## Run tests

```bash
pytest tests/ -v
```

---

## Default credentials

After running `python -m database.migrate`:

| Username | Password | Role |
|---|---|---|
| superadmin | admin123 | superadmin |
| bpl_admin | admin456 | admin |

**Change both passwords immediately after first deploy.**

---

## Environment variables

Copy `.env.example` to `.env` and fill in:

```bash
SECRET_KEY=your-secret-key-here
DATABASE_PATH=bijoy_fantasy.db
BCASH_API_KEY=your-bcash-key
BCASH_MERCHANT_ID=your-merchant-id
NAGAD_MERCHANT_ID=your-nagad-id
NAGAD_MERCHANT_KEY=your-nagad-key
ALLOWED_ORIGINS=https://yourdomain.com
SUBSCRIPTION_AMOUNT_BDT=500.0
```

---

## Market

- **163 million** cricket fans in Bangladesh
- **0 competitors** building natively for BPL
- **৳500/month** subscription via Bcash + Nagad
- **৳30L/year** ARR at 500 paid users

---

## License

MIT — free to use, extend, and commercialise.

---

*Built for BijoyFantasyCricketBD · Bangladesh Premier League 2012–2026 · Numeric stats only · AI governance compliant*
# BijoyFantasyCricketBD
