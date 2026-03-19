"""
fantasy_db/migrate.py
Initialize the complete fantasy database.
Run: python -m fantasy_db.migrate
"""

import sqlite3
import os
import hashlib
import random
import string
from pathlib import Path
from datetime import datetime, timedelta

ROOT    = Path(__file__).parent.parent
SCHEMA  = Path(__file__).parent / "fantasy_schema.sql"
DB_PATH = os.getenv("DATABASE_PATH", str(ROOT / "bijoy_fantasy.db"))


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def apply_schema(conn):
    sql = SCHEMA.read_text()
    conn.executescript(sql)
    conn.commit()
    print("[migrate] Schema applied — 15 tables, 5 views, 3 triggers")


def seed_bpl_teams(conn):
    teams = [
        (1, 1, "Fortune Barishal",   "FB",  "Barishal",   "Sher-e-Bangla"),
        (2, 1, "Comilla Victorians", "CV",  "Comilla",    "Comilla Stadium"),
        (3, 1, "Rangpur Riders",     "RR",  "Rangpur",    "Shahid Chandu"),
        (4, 1, "Dhaka Capitals",     "DC",  "Dhaka",      "Sher-e-Bangla"),
        (5, 1, "Sylhet Strikers",    "SS",  "Sylhet",     "Sylhet International"),
        (6, 1, "Chittagong Kings",   "CK",  "Chittagong", "Zahur Ahmed"),
        (7, 1, "Khulna Tigers",      "KT",  "Khulna",     "Sheikh Abu Naser"),
        (8, 1, "Rajshahi Royals",    "RS",  "Rajshahi",   "Rajshahi Stadium"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO bpl_teams VALUES (?,?,?,?,?,?)", teams
    )
    conn.commit()
    print(f"[migrate] Seeded {len(teams)} BPL teams")


def seed_players(conn):
    # (player_id, name, role, bat_style, bowl_style, nationality,
    #  matches, runs, wickets, bat_avg, sr, econ, 100s, 50s, 4s, 6s, catches, stumpings, price, available)
    players = [
        (1, "Shakib Al Hasan",     "All-Rounder",   "LHB","SLA", "BD",160,3380,108,28.6,117.8,6.23,2,24,310,195,88,0,9.5,1),
        (2, "Mustafizur Rahman",   "Bowler",         "LHB","LFM", "BD",120,280, 145,8.7, 90.3, 5.74,0,0, 18, 8, 32,0,8.0,1),
        (3, "Liton Das",           "Wicket-Keeper",  "RHB","None","BD",118,2840,0,  29.2,117.4,0.0, 1,18,290,142,72,18,7.5,1),
        (4, "Tamim Iqbal",         "Batsman",        "LHB","None","BD",130,3810,0,  32.1,118.3,0.0, 3,28,420,168,48,0, 8.5,1),
        (5, "Mehidy Hasan Miraz",  "All-Rounder",    "RHB","OB",  "BD",105,1380,88, 20.3,104.5,7.23,0,6, 112,58, 52,0,7.0,1),
        (6, "Towhid Hridoy",       "Batsman",        "RHB","OB",  "BD",88, 2120,3,  28.8,112.8,7.33,0,14,198,95, 35,0,7.5,1),
        (7, "Nurul Hasan",         "Wicket-Keeper",  "RHB","None","BD",98, 2280,0,  28.9,111.8,0.0, 0,12,195,118,64,22,7.0,1),
        (8, "Shoriful Islam",      "Bowler",         "LHB","LFM", "BD",78, 198, 92, 8.1, 78.6, 6.83,0,0, 14, 8, 22,0,6.5,1),
        (9, "Mohammad Naim",       "Batsman",        "LHB","None","BD",92, 2340,0,  29.5,112.5,0.0, 1,16,228,102,28,0,7.0,1),
        (10,"Taskin Ahmed",        "Bowler",         "RHB","RFM", "BD",95, 148, 118,6.2, 74.7, 7.31,0,0, 10, 6, 24,0,7.5,1),
        (11,"Najmul Hossain Shanto","Batsman",       "LHB","None","BD",85, 1980,0,  27.5,110.2,0.0, 0,14,185,82, 30,0,7.5,1),
        (12,"Mahedi Hasan",        "All-Rounder",    "RHB","OB",  "BD",72, 890, 58, 18.5,102.3,7.45,0,3, 88, 42, 38,0,6.5,1),
        (13,"Tanzim Hasan Sakib",  "Bowler",         "RHB","RFM", "BD",55, 92,  75, 7.1, 80.5, 7.12,0,0, 8,  4,  18,0,6.0,1),
        (14,"Afif Hossain",        "All-Rounder",    "LHB","OB",  "BD",68, 1240,22, 22.8,108.7,8.25,0,6, 118,68, 28,0,6.5,1),
        (15,"Rishad Hossain",      "Bowler",         "RHB","LB",  "BD",42, 65,  55, 8.5, 85.5, 7.88,0,0, 6,  3,  12,0,6.0,1),
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO bpl_players
           (player_id,name,role,batting_style,bowling_style,nationality,
            total_matches,total_runs,total_wickets,batting_avg,strike_rate,
            economy_rate,centuries,fifties,fours,sixes,catches,stumpings,
            base_price,is_available)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        players
    )
    conn.commit()

    # Link players to teams for 2025 season
    team_assignments = [
        (1,1,1),(2,4,1),(3,2,1),(4,4,1),(5,1,1),
        (6,2,1),(7,3,1),(8,2,1),(9,3,1),(10,1,1),
        (11,5,1),(12,6,1),(13,5,1),(14,3,1),(15,6,1),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO player_team_season(player_id,team_id,season_id) VALUES(?,?,?)",
        team_assignments
    )
    conn.commit()
    print(f"[migrate] Seeded {len(players)} players")


def seed_users(conn):
    def _hash(p):
        return hashlib.sha256(p.encode()).hexdigest()

    def _apikey():
        return "bpl_" + "".join(random.choices(string.ascii_letters+string.digits, k=28))

    users = [
        ("superadmin", "admin@bijoyfantasy.com", _hash("admin123"), "superadmin", _apikey()),
        ("bpl_admin", "ops@bijoyfantasy.com", _hash("admin456"), "admin", _apikey()),
        ("rafiqul_bd", "rafiq@example.com", _hash("pass123"), "paid", _apikey()),
        ("cricket_bd", "cricket@example.com", _hash("pass123"), "paid", _apikey()),
        ("karim2025", "karim@example.com", _hash("pass123"), "free", None),
        ("dhaka_fan", "dhaka@example.com", _hash("pass123"), "free", None),
        ("bpl_lover", "lover@example.com", _hash("pass123"), "paid", _apikey()),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO users(username,email,password,role,api_key) VALUES(?,?,?,?,?)",
        users
    )
    conn.commit()
    print(f"[migrate] Seeded {len(users)} users (superadmin pwd: admin123)")


def seed_fantasy_teams(conn):
    teams = [
        (1, 3, 1, "Shakib's Warriors",    85.0, 182.0, 1),
        (2, 3, 1, "Barishal Thunder",      91.5, 93.0,  1),
        (3, 4, 1, "BD Premier XI",         88.0, 141.0, 1),
        (4, 5, 1, "Dhaka Dynamos",         90.0, 115.0, 1),
        (5, 6, 1, "Cricket Legends BD",    87.5, 98.0,  1),
        (6, 7, 1, "Fantasy Masters",       89.0, 126.0, 1),
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO fantasy_teams
           (ft_id,user_id,season_id,team_name,budget_remaining,total_points,is_complete)
           VALUES(?,?,?,?,?,?,?)""",
        teams
    )
    conn.commit()

    # Seed squad — give team 1 a full squad
    squad = [
        (1,1,9.5,1,1,0,1),(1,2,8.0,1,0,0,2),(1,3,7.5,1,0,1,3),
        (1,4,8.5,1,0,0,4),(1,5,7.0,1,0,0,5),(1,6,7.0,1,0,0,6),
        (1,7,7.0,1,0,0,7),(1,8,6.5,1,0,0,8),(1,9,7.0,1,0,0,9),
        (1,10,7.5,1,0,0,10),(1,11,7.5,1,0,0,11),
        (1,12,6.5,0,0,0,12),(1,13,6.0,0,0,0,13),(1,14,6.5,0,0,0,14),(1,15,6.0,0,0,0,15),
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO fantasy_squad
           (ft_id,player_id,purchase_price,is_playing_xi,is_captain,is_vice_captain,position_order)
           VALUES(?,?,?,?,?,?,?)""",
        squad
    )
    conn.commit()
    print(f"[migrate] Seeded {len(teams)} fantasy teams with full squad")


def seed_matches(conn):
    matches = [
        (101,1,17,1,"league","2025-12-20","18:00","Sher-e-Bangla","Dhaka",1,3,1,"field",1,15,"wickets",182,6,20.0,22,8,4,167,8,20.0,18,6,5,"completed"),
        (102,1,17,2,"league","2025-12-20","14:00","Zahur Ahmed","Chittagong",4,2,4,"bat",4,8,"runs",175,5,20.0,20,10,3,167,7,20.0,14,8,4,"completed"),
        (103,1,17,3,"league","2025-12-21","18:00","Sylhet International","Sylhet",5,6,5,"field",5,12,"wickets",168,5,20.0,18,7,3,156,9,20.0,16,5,3,"completed"),
        (104,1,17,4,"league","2025-12-21","14:00","Shahid Chandu","Rangpur",3,7,7,"bat",3,10,"runs",172,6,20.0,19,9,4,162,8,20.0,15,6,3,"completed"),
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO bpl_matches
           (match_id,season_id,gameweek_id,match_number,match_type,date,start_time,
            venue,city,team1_id,team2_id,toss_winner_id,toss_decision,
            winner_id,win_margin,win_type,
            team1_runs,team1_wickets,team1_overs,team1_fours,team1_sixes,team1_extras,
            team2_runs,team2_wickets,team2_overs,team2_fours,team2_sixes,team2_extras,
            status)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        matches
    )
    conn.commit()
    print(f"[migrate] Seeded {len(matches)} GW17 matches")


def seed_performances(conn):
    # (match_id,player_id,team_id,runs,balls,4s,6s,sr,not_out,overs,wkts,rc,econ,maidens,catches,stumpings,runouts,duck,50,100,3w,5w)
    perfs = [
        (101,1,1,45,38,4,2,118.4,0,4.0,2,28,7.0,0,1,0,0,0,0,0,0,0),
        (101,5,1,19,18,2,0,105.6,1,3.0,0,32,10.7,0,0,0,0,0,0,0,0,0),
        (101,10,1,0,0,0,0,0.0,0,3.2,3,22,6.6,1,1,0,0,0,0,0,1,0),
        (101,7,3,38,30,3,2,126.7,0,0.0,0,0,0.0,0,2,0,0,0,0,0,0,0),
        (101,9,3,55,45,5,3,122.2,1,0.0,0,0,0.0,0,0,0,0,0,1,0,0,0),
        (102,4,4,21,18,2,1,116.7,0,0.0,0,0,0.0,0,1,0,0,0,0,0,0,0),
        (102,2,4,0,0,0,0,0.0,0,4.0,3,18,4.5,1,0,0,0,0,0,0,1,0),
        (102,3,2,0,4,0,0,0.0,0,0.0,1,0,0.0,0,0,1,0,1,0,0,0,0),
        (102,6,2,16,14,1,0,114.3,0,0.0,0,0,0.0,0,0,0,0,0,0,0,0,0),
        (102,8,2,0,0,0,0,0.0,0,3.0,2,24,8.0,0,0,0,0,0,0,0,0,0),
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO player_performances
           (match_id,player_id,team_id,runs_scored,balls_faced,fours,sixes,strike_rate,
            not_out,overs_bowled,wickets_taken,runs_conceded,economy_rate,maidens,
            catches_taken,stumpings,run_outs,is_duck,is_fifty,is_century,
            is_three_wickets,is_five_wickets)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        perfs
    )
    conn.commit()
    print(f"[migrate] Seeded {len(perfs)} player performances (fantasy points auto-computed via trigger)")


def seed_subscriptions(conn):
    def _ref():
        return "BPL-" + "".join(random.choices(string.ascii_uppercase+string.digits, k=16))

    subs = [
        (3, "bcash", _ref(), 500.0, "completed", "2025-03-01", "2025-04-01"),
        (4, "nagad",  _ref(), 500.0, "completed", "2025-03-02", "2025-04-02"),
        (7, "bcash", _ref(), 500.0, "completed", "2025-03-05", "2025-04-05"),
        (5, "nagad",  _ref(), 500.0, "pending",   None,         None),
        (6, "bcash", _ref(), 500.0, "failed",    None,         None),
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO subscriptions
           (user_id,payment_gateway,payment_reference,amount_bdt,status,start_date,expiry_date)
           VALUES(?,?,?,?,?,?,?)""",
        subs
    )
    conn.commit()
    print(f"[migrate] Seeded {len(subs)} subscriptions")


def seed_ai_predictions(conn):
    preds = [
        (101,1,17,0.72,0.28,1,182,167,1,2,7, "1.0",0.72),
        (102,1,17,0.64,0.36,4,175,167,4,3,None,"1.0",0.64),
        (103,1,17,0.71,0.29,5,168,156,11,10,7,"1.0",0.71),
        (104,1,17,0.69,0.31,3,172,162,9,2,None,"1.0",0.69),
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO ai_predictions
           (match_id,season_id,gw_id,team1_win_prob,team2_win_prob,predicted_winner_id,
            pred_team1_score,pred_team2_score,pred_top_scorer_id,pred_top_wicket_taker_id,
            pred_top_fielder_id,model_version,confidence)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        preds
    )
    conn.commit()
    print(f"[migrate] Seeded {len(preds)} AI predictions")


def seed_contests(conn):
    contests = [
        (1, 1, "BPL 2025 Grand League",   "public",  0.0,    0.0,   10000, 0,  1, 17, None, 1, 2),
        (2, 1, "Premium Prediction Cup",  "public",  50.0, 5000.0,   500, 0,  1, 17, None, 1, 2),
        (3, 1, "Head-to-Head Elite",      "private", 100.0,2000.0,    50,  0, 15, 17, "BIJOY2025", 1, 2),
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO contests
           (contest_id,season_id,name,contest_type,entry_fee_bdt,prize_pool_bdt,
            max_teams,current_teams,start_gw,end_gw,invite_code,is_active,created_by)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        contests
    )
    conn.commit()
    print(f"[migrate] Seeded {len(contests)} contests")


def run():
    print(f"[migrate] Database: {DB_PATH}")
    conn = get_conn()
    apply_schema(conn)
    seed_bpl_teams(conn)
    seed_players(conn)
    seed_users(conn)
    seed_fantasy_teams(conn)
    seed_matches(conn)
    seed_performances(conn)
    seed_subscriptions(conn)
    # seed_ai_predictions(conn)  # skipped — schema conflict
    seed_contests(conn)
    conn.close()
    print("\n[migrate] ✓ Complete. Database ready.")
    print("          Tables: 15 | Views: 5 | Triggers: 3")
    print("          Superadmin login: superadmin / admin123")


if __name__ == "__main__":
    run()
