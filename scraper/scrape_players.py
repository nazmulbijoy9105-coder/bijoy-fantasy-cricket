"""
scraper/scrape_players.py
Scrape BPL player NUMERIC stats from ESPNcricinfo.
Governance: Only numeric stats are stored (runs, wkts, avg, SR, econ).
No biography, no images, no commentary.
"""

import sys
from .utils import fetch, safe_int, safe_float, parse_overs
from api.database import execute_db, query_db

CRICINFO_BPL_BATTING = "https://stats.espncricinfo.com/ci/engine/records/batting/most_runs_career.html?id=117;type=trophy"
CRICINFO_BPL_BOWLING = "https://stats.espncricinfo.com/ci/engine/records/bowling/most_wickets_career.html?id=117;type=trophy"


def scrape_batting_stats():
    """Scrape career batting leaderboard — numeric stats only."""
    soup = fetch(CRICINFO_BPL_BATTING)
    if not soup:
        print("[players] Could not reach batting stats page.")
        return

    rows = soup.select("table.engineTable tr.data1, table.engineTable tr.data2")
    count = 0
    for row in rows:
        cols = [td.get_text(strip=True) for td in row.select("td")]
        if len(cols) < 10:
            continue
        # cols: rank, player, span, mat, inns, no, runs, hs, avg, bf, sr, 100, 50, 0, 4s, 6s
        name       = cols[1].split("(")[0].strip()
        matches    = safe_int(cols[3])
        innings    = safe_int(cols[4])
        not_outs   = safe_int(cols[5])
        runs       = safe_int(cols[6])
        highest    = safe_int(cols[7].replace("*", ""))
        bat_avg    = safe_float(cols[8])
        balls      = safe_int(cols[9])
        sr         = safe_float(cols[10])
        centuries  = safe_int(cols[11])
        fifties    = safe_int(cols[12])
        fours      = safe_int(cols[14]) if len(cols) > 14 else 0
        sixes      = safe_int(cols[15]) if len(cols) > 15 else 0

        execute_db(
            """INSERT INTO players
               (name, matches_played, innings_batted, not_outs, runs, balls_faced,
                highest_score, batting_avg, strike_rate, centuries, fifties, fours, sixes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(name) DO UPDATE SET
                 matches_played=excluded.matches_played,
                 runs=excluded.runs, batting_avg=excluded.batting_avg,
                 strike_rate=excluded.strike_rate, centuries=excluded.centuries,
                 fifties=excluded.fifties, fours=excluded.fours, sixes=excluded.sixes""",
            (name, matches, innings, not_outs, runs, balls,
             highest, bat_avg, sr, centuries, fifties, fours, sixes),
        )
        count += 1

    print(f"[players] Upserted {count} batting records.")


def scrape_bowling_stats():
    """Scrape career bowling leaderboard — numeric stats only."""
    soup = fetch(CRICINFO_BPL_BOWLING)
    if not soup:
        print("[players] Could not reach bowling stats page.")
        return

    rows = soup.select("table.engineTable tr.data1, table.engineTable tr.data2")
    count = 0
    for row in rows:
        cols = [td.get_text(strip=True) for td in row.select("td")]
        if len(cols) < 9:
            continue
        name    = cols[1].split("(")[0].strip()
        wickets = safe_int(cols[6])
        runs_c  = safe_int(cols[8])
        econ    = safe_float(cols[9]) if len(cols) > 9 else 0.0
        b_avg   = safe_float(cols[10]) if len(cols) > 10 else 0.0
        best    = cols[11] if len(cols) > 11 else "0/0"
        five_w  = safe_int(cols[12]) if len(cols) > 12 else 0

        execute_db(
            """UPDATE players SET
               wickets=?, runs_conceded=?, economy=?, bowling_avg=?, best_bowling=?, five_wickets=?
               WHERE name=?""",
            (wickets, runs_c, econ, b_avg, best, five_w, name),
        )
        count += 1

    print(f"[players] Updated {count} bowling records.")


if __name__ == "__main__":
    scrape_batting_stats()
    scrape_bowling_stats()
