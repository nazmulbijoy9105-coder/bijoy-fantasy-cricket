"""
database/migrate.py
Run: python -m database.migrate
Creates the DB, applies schema, seeds sample data.
"""

import sqlite3
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCHEMA = ROOT / "database" / "bpl_schema.sql"
SEED = ROOT / "database" / "seed_data" / "bpl_2012_2026.json"
DB_PATH = os.getenv("DATABASE_PATH", str(ROOT / "bpl.db"))


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def apply_schema(conn: sqlite3.Connection) -> None:
    sql = SCHEMA.read_text()
    conn.executescript(sql)
    conn.commit()
    print("[migrate] Schema applied.")


def seed_teams(conn: sqlite3.Connection) -> None:
    teams = [
        (1, "Fortune Barishal",      "FB",  "Barishal",     "Sher-e-Bangla",     "[2012,2013,2014,2015,2016,2017,2019,2022,2023,2024,2025]"),
        (2, "Comilla Victorians",    "CV",  "Comilla",      "Comilla Stadium",   "[2012,2013,2014,2015,2016,2017,2019,2022,2023,2024,2025]"),
        (3, "Rangpur Riders",        "RR",  "Rangpur",      "Shahid Chandu",     "[2012,2013,2014,2015,2016,2017,2019,2022,2023,2024,2025]"),
        (4, "Dhaka Capitals",        "DC",  "Dhaka",        "Sher-e-Bangla",     "[2022,2023,2024,2025]"),
        (5, "Sylhet Strikers",       "SS",  "Sylhet",       "Sylhet Stadium",    "[2012,2013,2014,2015,2016,2017,2019,2022,2023,2024,2025]"),
        (6, "Chittagong Kings",      "CK",  "Chittagong",   "Zahur Ahmed",       "[2012,2013,2014,2015,2016,2017,2019,2022,2023,2024,2025]"),
        (7, "Khulna Tigers",         "KT",  "Khulna",       "Sheikh Abu Naser",  "[2012,2013,2014,2015,2016,2017,2019,2022,2023,2024]"),
        (8, "Rajshahi Royals",       "RR2", "Rajshahi",     "Rajshahi Stadium",  "[2012,2013,2014,2015,2016,2017,2019]"),
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO teams
           (team_id, name, abbreviation, home_city, seasons_active)
           VALUES (?,?,?,?,?)""",
        [(t[0], t[1], t[2], t[3], t[5]) for t in teams]
    )
    conn.commit()
    print(f"[migrate] Seeded {len(teams)} teams.")


def seed_players(conn: sqlite3.Connection) -> None:
    # Numeric stats only — no biographical text
    players = [
        # (player_id, name, role, bat_style, bowl_style, nationality, team_id,
        #  mp, inn_bat, runs, balls, hs, 100s, 50s, 4s, 6s, bat_avg, sr, no,
        #  overs, wkts, runs_c, econ, bowl_avg, bb, 5w, catches, st, ro,
        #  fantasy_price, seasons, form)
        (1,  "Shakib Al Hasan",     "All-Rounder",    "LHB", "SLA",  "BD", 1, 160, 148, 3380, 2870, 95,  2,  24, 310, 195, 28.6, 117.8, 15, 520.3, 108, 3240, 6.23, 30.0, "5/32", 2,  88, 0, 12, 9.5,  "[2012,2013,2014,2015,2016,2017,2019,2022,2023,2024,2025]", "[45,72,18,88,31]"),
        (2,  "Mustafizur Rahman",   "Bowler",         "LHB", "LFM",  "BD", 4, 120, 45,  280,  310,  22,  0,  0,  18,  8,   8.7,  90.3,  8,  380.2, 145, 2180, 5.74, 15.0, "5/22", 4,  32, 0, 8,  8.0,  "[2015,2016,2017,2019,2022,2023,2024,2025]",               "[3/28,2/19,4/22,1/35,3/18]"),
        (3,  "Liton Das",           "Wicket-Keeper",  "RHB", "None", "BD", 2, 118, 112, 2840, 2420, 112, 1,  18, 290, 142, 29.2, 117.4, 14, 0.0,   0,   0,    0.0,  0.0,  "0/0",  0,  72, 18, 5,  7.5,  "[2012,2013,2014,2015,2016,2017,2019,2022,2023,2024,2025]", "[38,0,55,12,44]"),
        (4,  "Tamim Iqbal",         "Batsman",        "LHB", "None", "BD", 4, 130, 128, 3810, 3220, 141, 3,  28, 420, 168, 32.1, 118.3, 10, 0.0,   0,   0,    0.0,  0.0,  "0/0",  0,  48, 0, 4,  8.5,  "[2012,2013,2014,2015,2016,2017,2019,2022,2023,2024]",      "[21,0,68,15,33]"),
        (5,  "Mehidy Hasan Miraz",  "All-Rounder",    "RHB", "OB",   "BD", 1, 105, 88,  1380, 1320, 64,  0,  6,  112, 58,  20.3, 104.5, 20, 295.4, 88,  2140, 7.23, 24.3, "4/28", 0,  52, 0, 8,  7.0,  "[2014,2015,2016,2017,2019,2022,2023,2024,2025]",           "[19,23,0,41,12]"),
        (6,  "Towhid Hridoy",       "Batsman",        "RHB", "OB",   "BD", 2, 88,  82,  2120, 1880, 98,  0,  14, 198, 95,  28.8, 112.8, 9,  12.0,  3,   88,   7.33, 29.3, "2/14", 0,  35, 0, 6,  7.5,  "[2022,2023,2024,2025]",                                    "[16,0,44,28,9]"),
        (7,  "Nurul Hasan",         "Wicket-Keeper",  "RHB", "None", "BD", 3, 98,  90,  2280, 2040, 88,  0,  12, 195, 118, 28.9, 111.8, 8,  0.0,   0,   0,    0.0,  0.0,  "0/0",  0,  64, 22, 3,  7.0,  "[2012,2013,2014,2015,2016,2017,2019,2022,2023,2024,2025]", "[38,12,0,55,21]"),
        (8,  "Shoriful Islam",      "Bowler",         "LHB", "LFM",  "BD", 2, 78,  32,  198,  252,  18,  0,  0,  14,  8,   8.1,  78.6,  8,  240.1, 92,  1640, 6.83, 17.8, "4/18", 0,  22, 0, 4,  6.5,  "[2019,2022,2023,2024,2025]",                               "[2/22,1/18,3/25,0/34,2/19]"),
        (9,  "Mohammad Naim",       "Batsman",        "LHB", "None", "BD", 3, 92,  88,  2340, 2080, 108, 1,  16, 228, 102, 29.5, 112.5, 9,  0.0,   0,   0,    0.0,  0.0,  "0/0",  0,  28, 0, 3,  7.0,  "[2017,2019,2022,2023,2024,2025]",                          "[55,0,34,12,48]"),
        (10, "Taskin Ahmed",        "Bowler",         "RHB", "RFM",  "BD", 1, 95,  28,  148,  198,  14,  0,  0,  10,  6,   6.2,  74.7,  5,  320.3, 118, 2340, 7.31, 19.8, "5/28", 1,  24, 0, 6,  7.5,  "[2013,2014,2015,2016,2017,2019,2022,2023,2024,2025]",      "[2/28,3/22,1/38,4/25,2/19]"),
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO players
           (player_id,name,role,batting_style,bowling_style,nationality,team_id,
            matches_played,innings_batted,runs,balls_faced,highest_score,
            centuries,fifties,fours,sixes,batting_avg,strike_rate,not_outs,
            overs_bowled,wickets,runs_conceded,economy,bowling_avg,best_bowling,
            five_wickets,catches,stumpings,run_outs,
            fantasy_price,seasons_played,recent_form)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        players
    )
    conn.commit()
    print(f"[migrate] Seeded {len(players)} players.")


def seed_seasons(conn: sqlite3.Connection) -> None:
    seasons = [
        (2012, 2, None, 28, 4840, 220),
        (2013, 3, 2,    28, 4920, 235),
        (2015, 2, 1,    28, 5140, 248),
        (2016, 3, 5,    28, 5280, 252),
        (2017, 1, 2,    28, 5410, 261),
        (2019, 2, 3,    28, 5380, 258),
        (2022, 1, 3,    34, 6120, 295),
        (2023, 2, 1,    34, 6340, 308),
        (2024, 3, 2,    34, 6580, 318),
        (2025, 1, 4,    34, 6810, 325),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO seasons(year,champion_id,runner_up_id,total_matches,total_runs,total_wickets) VALUES (?,?,?,?,?,?)",
        seasons
    )
    conn.commit()
    print(f"[migrate] Seeded {len(seasons)} seasons.")


def seed_superadmin(conn: sqlite3.Connection) -> None:
    from passlib.context import CryptContext
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd_ctx.hash("admin123")
    conn.execute(
        "INSERT OR IGNORE INTO users(username,email,password,role,api_key) VALUES (?,?,?,?,?)",
        ("superadmin", "admin@bplapi.com", hashed, "superadmin", "SUPERADMIN_KEY_CHANGE_ME")
    )
    conn.commit()
    print("[migrate] Superadmin user created. CHANGE THE PASSWORD!")


def run():
    print(f"[migrate] Target DB: {DB_PATH}")
    conn = get_conn()
    apply_schema(conn)
    seed_teams(conn)
    seed_players(conn)
    seed_seasons(conn)
    seed_superadmin(conn)
    conn.close()
    print("[migrate] Done.")


if __name__ == "__main__":
    run()
