"""
database/migrate.py - BPL Stats DB
Run: python -m database.migrate
"""
import sqlite3, os, hashlib
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
        (1,2012,"2012-02-09","2012-03-09",6,28),
        (2,2013,"2013-01-10","2013-02-08",6,28),
        (3,2015,"2015-11-22","2015-12-18",6,28),
        (4,2016,"2016-11-04","2016-12-09",6,28),
        (5,2017,"2017-11-02","2017-12-12",7,28),
        (6,2019,"2019-01-05","2019-02-08",7,28),
        (7,2022,"2022-01-21","2022-02-18",6,34),
        (8,2023,"2023-01-06","2023-02-16",6,34),
        (9,2024,"2024-01-06","2024-02-09",6,34),
        (10,2025,"2025-01-30","2025-02-27",6,34),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO seasons(season_id,year,start_date,end_date,num_teams,num_matches) VALUES(?,?,?,?,?,?)",
        seasons)
    conn.commit()
    print(f"[migrate] Seeded {len(seasons)} seasons.")

def seed_teams(conn):
    teams = [
        (1,"Fortune Barishal","FB","Barishal","[2012,2013,2015,2016,2017,2019,2022,2023,2024,2025]"),
        (2,"Comilla Victorians","CV","Comilla","[2012,2013,2015,2016,2017,2019,2022,2023,2024,2025]"),
        (3,"Rangpur Riders","RR","Rangpur","[2012,2013,2015,2016,2017,2019,2022,2023,2024,2025]"),
        (4,"Dhaka Capitals","DC","Dhaka","[2022,2023,2024,2025]"),
        (5,"Sylhet Strikers","SS","Sylhet","[2012,2013,2015,2016,2017,2019,2022,2023,2024,2025]"),
        (6,"Chittagong Kings","CK","Chittagong","[2012,2013,2015,2016,2017,2019,2022,2023,2024,2025]"),
        (7,"Khulna Tigers","KT","Khulna","[2012,2013,2015,2016,2017,2019,2022,2023,2024]"),
        (8,"Rajshahi Royals","RR2","Rajshahi","[2012,2013,2015,2016,2017,2019]"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO teams(team_id,name,abbreviation,home_city,seasons_active) VALUES(?,?,?,?,?)",
        teams)
    conn.commit()
    print(f"[migrate] Seeded {len(teams)} teams.")

def seed_players(conn):
    players = [
        (1,"Shakib Al Hasan","BD","All-Rounder","LHB","SLA",0),
        (2,"Mustafizur Rahman","BD","Bowler","LHB","LFM",0),
        (3,"Liton Das","BD","Wicket-Keeper","RHB","None",0),
        (4,"Tamim Iqbal","BD","Batsman","LHB","None",0),
        (5,"Mehidy Hasan Miraz","BD","All-Rounder","RHB","OB",0),
        (6,"Towhid Hridoy","BD","Batsman","RHB","OB",0),
        (7,"Nurul Hasan","BD","Wicket-Keeper","RHB","None",0),
        (8,"Shoriful Islam","BD","Bowler","LHB","LFM",0),
        (9,"Mohammad Naim","BD","Batsman","LHB","None",0),
        (10,"Taskin Ahmed","BD","Bowler","RHB","RFM",0),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO players(player_id,name,nationality,role,batting_style,bowling_style,is_overseas) VALUES(?,?,?,?,?,?,?)",
        players)
    conn.commit()
    print(f"[migrate] Seeded {len(players)} players.")

def seed_superadmin(conn):
    pw = hashlib.sha256("admin123".encode()).hexdigest()
    conn.execute(
        "INSERT OR IGNORE INTO users(username,email,password,role,api_key) VALUES(?,?,?,?,?)",
        ("superadmin","admin@bijoyfantasy.com",pw,"superadmin","SUPERADMIN_KEY_CHANGE_ME"))
    conn.commit()
    print("[migrate] Superadmin created. CHANGE PASSWORD IMMEDIATELY.")

def run():
    print(f"[migrate] Target DB: {DB_PATH}")
    conn = get_conn()
    apply_schema(conn)
    seed_seasons(conn)
    seed_teams(conn)
    seed_players(conn)
    seed_superadmin(conn)
    conn.close()
    print("[migrate] Done.")

if __name__ == "__main__":
    run()
