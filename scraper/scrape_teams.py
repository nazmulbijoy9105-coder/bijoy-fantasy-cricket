"""
scraper/scrape_teams.py
Scrape BPL team data and upsert into DB.
Numeric/factual data only: team name, abbreviation, city.
"""

from api.database import execute_db

BPL_TEAMS = [
    (1, "Fortune Barishal",   "FB",  "Barishal",   "Sher-e-Bangla National Stadium", "[2012,2013,2014,2015,2016,2017,2019,2022,2023,2024,2025]"),
    (2, "Comilla Victorians", "CV",  "Comilla",    "Comilla Stadium",                 "[2012,2013,2014,2015,2016,2017,2019,2022,2023,2024,2025]"),
    (3, "Rangpur Riders",     "RR",  "Rangpur",    "Shahid Chandu Stadium",           "[2012,2013,2014,2015,2016,2017,2019,2022,2023,2024,2025]"),
    (4, "Dhaka Capitals",     "DC",  "Dhaka",      "Sher-e-Bangla National Stadium",  "[2022,2023,2024,2025]"),
    (5, "Sylhet Strikers",    "SS",  "Sylhet",     "Sylhet International Stadium",    "[2012,2013,2014,2015,2016,2017,2019,2022,2023,2024,2025]"),
    (6, "Chittagong Kings",   "CK",  "Chittagong", "Zahur Ahmed Chowdhury Stadium",   "[2012,2013,2014,2015,2016,2017,2019,2022,2023,2024,2025]"),
    (7, "Khulna Tigers",      "KT",  "Khulna",     "Sheikh Abu Naser Stadium",        "[2012,2013,2014,2015,2016,2017,2019,2022,2023,2024]"),
    (8, "Rajshahi Royals",    "RR2", "Rajshahi",   "Rajshahi Stadium",                "[2012,2013,2014,2015,2016,2017,2019]"),
]


def upsert_teams():
    for team in BPL_TEAMS:
        execute_db(
            """INSERT OR REPLACE INTO teams
               (team_id, name, abbreviation, city, home_ground, seasons_active)
               VALUES (?,?,?,?,?,?)""",
            team,
        )
    print(f"[teams] Upserted {len(BPL_TEAMS)} teams.")


if __name__ == "__main__":
    upsert_teams()
