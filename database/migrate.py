"""
database/migrate.py
Run: python -m database.migrate
Creates the DB, applies schema, seeds data.
FIXED: All INSERT statements match the actual bpl_schema.sql column structure.
"""

import sqlite3
import hashlib
import os
from pathlib import Path

ROOT    = Path(__file__).parent.parent
SCHEMA  = Path(__file__).parent / "bpl_schema.sql"
DB_PATH = os.getenv("DATABASE_PATH", str(ROOT / "bpl.db"))


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def apply_schema(conn):
    conn.executescript(SCHEMA.read_text())
    conn.commit()
    print("[migrate] Schema applied.")


def seed_seasons(conn):
    seasons = [
        (1, 2012, "2012-02-09", "2012-03-09", 6, 28),
        (2, 2013, "2013-01-10", "2013-02-08", 6, 28),
        (3, 2015, "2015-11-22", "2015-12-18", 6, 28),
        (4, 2016, "2016-11-04", "2016-12-09", 6, 28),
        (5, 2017, "2017-11-02", "2017-12-12", 7, 28),
        (6, 2019, "2019-01-05", "2019-02-08", 7, 28),
        (7, 2022, "2022-01-21", "2022-02-18", 6, 34),
        (8, 2023, "2023-01-06", "2023-02-16", 6, 34),
        (9, 2024, "2024-01-06", "2024-02-09", 6, 34),
        (10,2025, "2025-01-30", "2025-02-27", 6, 34),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO seasons(season_id,year,start_date,end_date,num_teams,num_matches) VALUES(?,?,?,?,?,?)",
        seasons
    )
    conn.commit()
    print(f"[migrate] Seeded {len(seasons)} seasons.")


def seed_teams(conn):
    # Schema: team_id, name, abbreviation, home_city, seasons_active (others default 0)
    teams = [
        (1, "Fortune Barishal",   "FB",  "Barishal",   "[2012,2013,2014,2015,2016,2017,2019,2022,2023,2024,2025]"),
        (2, "Comilla Victorians", "CV",  "Comilla",    "[2012,2013,2014,2015,2016,2017,2019,2022,2023,2024,2025]"),
        (3, "Rangpur Riders",     "RR",  "Rangpur",    "[2012,2013,2014,2015,2016,2017,2019,2022,2023,2024,2025]"),
        (4, "Dhaka Capitals",     "DC",  "Dhaka",      "[2022,2023,2024,2025]"),
        (5, "Sylhet Strikers",    "SS",  "Sylhet",     "[2012,2013,2014,2015,2016,2017,2019,2022,2023,2024,2025]"),
        (6, "Chittagong Kings",   "CK",  "Chittagong", "[2012,2013,2014,2015,2016,2017,2019,2022,2023,2024,2025]"),
        (7, "Khulna Tigers",      "KT",  "Khulna",     "[2012,2013,2014,2015,2016,2017,2019,2022,2023,2024]"),
        (8, "Rajshahi Royals",    "RR2", "Rajshahi",   "[2012,2013,2014,2015,2016,2017,2019]"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO teams(team_id,name,abbreviation,home_city,seasons_active) VALUES(?,?,?,?,?)",
        teams
    )
    conn.commit()
    print(f"[migrate] Seeded {len(teams)} teams.")


def seed_players(conn):
    # Schema: player_id, name, nationality, role, batting_style, bowling_style, is_overseas
    players = [
        (1,  "Shakib Al Hasan",    "BD", "All-Rounder",   "LHB", "SLA",  0),
        (2,  "Mustafizur Rahman",  "BD", "Bowler",         "LHB", "LFM",  0),
        (3,  "Liton Das",          "BD", "Wicket-Keeper",  "RHB", "None", 0),
        (4,  "Tamim Iqbal",        "BD", "Batsman",        "LHB", "None", 0),
        (5,  "Mehidy Hasan Miraz", "BD", "All-Rounder",    "RHB", "OB",   0),
        (6,  "Towhid Hridoy",      "BD", "Batsman",        "RHB", "OB",   0),
        (7,  "Nurul Hasan",        "BD", "Wicket-Keeper",  "RHB", "None", 0),
        (8,  "Shoriful Islam",     "BD", "Bowler",         "LHB", "LFM",  0),
        (9,  "Mohammad Naim",      "BD", "Batsman",        "LHB", "None", 0),
        (10, "Taskin Ahmed",       "BD", "Bowler",         "RHB", "RFM",  0),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO players(player_id,name,nationality,role,batting_style,bowling_style,is_overseas) VALUES(?,?,?,?,?,?,?)",
        players
    )
    conn.commit()
    print(f"[migrate] Seeded {len(players)} players.")


def seed_player_career_stats(conn):
    # Schema: player_id, matches, innings_bat, runs, balls_faced, highest_score,
    #         not_outs, fours, sixes, fifties, centuries, batting_avg, strike_rate,
    #         innings_bowl, overs_bowled, balls_bowled, runs_conceded, wickets,
    #         best_bowling, bowling_avg, economy, bowling_sr,
    #         four_wickets, five_wickets, catches, stumpings, run_outs
    stats = [
        (1,  160,148,3380,2870,95, 15,310,195,24,2, 28.6,117.8, 95,520.3,3122,3240,108,"7/36",30.0,6.23,28.9, 0,7, 88,0,12),
        (2,  120,45, 280, 310,22,  8, 18,  8, 0,0,  8.7, 90.3,120,380.2,2281,2180,145,"6/43",15.0,5.74,15.8, 0,4, 32,0, 8),
        (3,  118,112,2840,2420,112,14,290,142,18,1, 29.2,117.4,  0,  0.0,   0,   0,  0,"0/0",  0.0,0.0,  0.0, 0,0, 72,18, 5),
        (4,  130,128,3810,3220,141,10,420,168,28,3, 32.1,118.3,  0,  0.0,   0,   0,  0,"0/0",  0.0,0.0,  0.0, 0,0, 48, 0, 4),
        (5,  105,88, 1380,1320,64, 20,112, 58, 6,0, 20.3,104.5, 78,295.4,1772,2140, 88,"4/28",24.3,7.23,20.1, 0,0, 52, 0, 8),
        (6,   88,82, 2120,1880,98,  9,198, 95,14,0, 28.8,112.8, 12, 12.0,  72,  88,  3,"2/14",29.3,7.33,24.0, 0,0, 35, 0, 6),
        (7,   98,90, 2280,2040,88,  8,195,118,12,0, 28.9,111.8,  0,  0.0,   0,   0,  0,"0/0",  0.0,0.0,  0.0, 0,0, 64,22, 3),
        (8,   78,32,  198, 252,18,  8, 14,  8, 0,0,  8.1, 78.6, 60,240.1,1441,1640, 92,"4/18",17.8,6.83,15.7, 0,0, 22, 0, 4),
        (9,   92,88, 2340,2080,108, 9,228,102,16,1, 29.5,112.5,  0,  0.0,   0,   0,  0,"0/0",  0.0,0.0,  0.0, 0,0, 28, 0, 3),
        (10,  95,28,  148, 198,14,  5, 10,  6, 0,0,  6.2, 74.7, 80,320.3,1922,2340,118,"5/28",19.8,7.31,16.3, 0,1, 24, 0, 6),
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO player_career_stats(
            player_id,matches,innings_bat,runs,balls_faced,highest_score,
            not_outs,fours,sixes,fifties,centuries,batting_avg,strike_rate,
            innings_bowl,overs_bowled,balls_bowled,runs_conceded,wickets,
            best_bowling,bowling_avg,economy,bowling_sr,
            four_wickets,five_wickets,catches,stumpings,run_outs)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        stats
    )
    conn.commit()
    print(f"[migrate] Seeded {len(stats)} player career stats.")


def seed_player_season_stats(conn):
    # Link players to teams for 2025 season (season_id=10)
    # Schema: player_id, season_id, team_id, matches, runs, balls_faced, fours, sixes,
    #         fifties, centuries, batting_avg, strike_rate, wickets, overs_bowled,
    #         runs_conceded, economy, bowling_avg, catches, stumpings
    pss = [
        (1, 10,1, 12, 450,380,45,22, 3,0,42.5,118.4,15,48.0,298,6.21,19.9, 8,0),
        (2, 10,4, 10,  12, 18, 1, 0, 0,0, 6.0, 66.7,28,40.0,245,6.13,8.8,  4,0),
        (3, 10,2, 11, 288,245,28,12, 2,0,32.0,117.6, 0, 0.0,  0,0.0, 0.0, 14,5),
        (4, 10,4, 10, 310,262,38,12, 2,0,38.8,118.3, 0, 0.0,  0,0.0, 0.0,  4,0),
        (5, 10,1, 11, 195,185,22, 8, 1,0,22.8,105.4,18,44.0,312,7.09,17.3, 6,0),
        (6, 10,2, 10, 280,248,28,10, 2,0,35.0,112.9, 0, 0.0,  0,0.0, 0.0,  4,0),
        (7, 10,3, 11, 220,198,21, 9, 1,0,27.5,111.1, 0, 0.0,  0,0.0, 0.0, 12,4),
        (8, 10,2, 10,  18, 22, 1, 0, 0,0, 6.0, 81.8,22,38.0,268,7.05,12.2, 3,0),
        (9, 10,3, 11, 265,232,24,10, 2,0,33.1,114.2, 0, 0.0,  0,0.0, 0.0,  3,0),
        (10,10,1, 10,  14, 19, 1, 0, 0,0, 7.0, 73.7,20,38.0,284,7.47,14.2, 2,0),
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO player_season_stats(
            player_id,season_id,team_id,matches,runs,balls_faced,fours,sixes,
            fifties,centuries,batting_avg,strike_rate,wickets,overs_bowled,
            runs_conceded,economy,bowling_avg,catches,stumpings)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        pss
    )
    conn.commit()
    print(f"[migrate] Seeded {len(pss)} player season stats.")


def seed_superadmin(conn):
    pw = hashlib.sha256("admin123".encode()).hexdigest()
    conn.execute(
        "INSERT OR IGNORE INTO users(username,email,password,role,api_key) VALUES(?,?,?,?,?)",
        ("superadmin","admin@bijoyfantasy.com", pw,"superadmin","SUPERADMIN_KEY_CHANGE_ME")
    )
    conn.commit()
    print("[migrate] Superadmin created. CHANGE PASSWORD IMMEDIATELY.")


def run():
    print(f"[migrate] Target DB: {DB_PATH}")
    conn = get_conn()
    apply_schema(conn)
    seed_seasons(conn)
    seed_teams(conn)
    seed_players(conn)
    seed_player_career_stats(conn)
    seed_player_season_stats(conn)
    seed_superadmin(conn)
    conn.close()
    print("[migrate] Done. BPL API database ready.")


if __name__ == "__main__":
    run()
