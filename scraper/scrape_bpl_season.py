"""
scraper/scrape_bpl_season.py
Scrape BPL match results (numeric only) season by season.
Usage:  python -m scraper.scrape_bpl_season --season 2025
        python -m scraper.scrape_bpl_season --all
"""

import argparse
import sys
from .utils import fetch, safe_int, safe_float, parse_overs
from api.database import execute_db, query_one

# ESPNcricinfo BPL series IDs (update as new seasons are added)
BPL_SERIES_IDS = {
    2012: 534641, 2013: 586757, 2015: 793290, 2016: 965667,
    2017: 1089609, 2019: 1153237, 2022: 1298134, 2023: 1352021,
    2024: 1405230, 2025: 1450000,  # update 2025 ID when confirmed
}


def scrape_season(year: int):
    series_id = BPL_SERIES_IDS.get(year)
    if not series_id:
        print(f"[scraper] No series ID for season {year}")
        return

    url = f"https://www.espncricinfo.com/series/{series_id}/match-schedule-fixtures-and-results"
    soup = fetch(url)
    if not soup:
        print(f"[scraper] Failed to fetch season {year}")
        return

    match_links = soup.select("a[href*='/full-scorecard']")
    print(f"[scraper] Found {len(match_links)} match links for {year}")

    inserted = 0
    for link in match_links:
        href = link.get("href", "")
        # Extract numeric match ID from URL
        parts = [p for p in href.split("/") if p.isdigit()]
        if not parts:
            continue
        match_id = int(parts[-1])

        if query_one("SELECT 1 FROM matches WHERE match_id=?", (match_id,)):
            continue  # already scraped

        score_url = f"https://www.espncricinfo.com{href}"
        score_soup = fetch(score_url)
        if not score_soup:
            continue

        _parse_and_store_scorecard(match_id, year, score_soup)
        inserted += 1

    print(f"[scraper] Season {year}: {inserted} new matches stored.")


def _parse_and_store_scorecard(match_id: int, season: int, soup):
    """Extract only numeric fields from a scorecard page."""
    try:
        # Match date
        date_el = soup.select_one(".match-info-link-LIVE, [class*='date']")
        date_str = date_el.get_text(strip=True)[:10] if date_el else None

        # Venue
        venue_el = soup.select_one(".info-icon + span, [class*='ground']")
        venue = venue_el.get_text(strip=True)[:100] if venue_el else None

        # Innings totals (numeric only)
        innings = soup.select(".scorecard-section")
        if len(innings) < 2:
            return

        def parse_innings(inn_el):
            total_el = inn_el.select_one(".total-score, [class*='score']")
            if not total_el:
                return 0, 0, 0.0
            txt = total_el.get_text(strip=True)
            # e.g. "182/6 (20 ov)"
            parts = txt.split()
            score_part = parts[0] if parts else "0/0"
            runs, wkts = (safe_int(x) for x in (score_part + "/10").split("/")[:2])
            overs = 0.0
            for part in parts:
                if "ov" in part.lower():
                    overs = parse_overs(part.replace("ov", "").replace("(", "").strip())
                    break
            return runs, wkts, overs

        r1, w1, o1 = parse_innings(innings[0])
        r2, w2, o2 = parse_innings(innings[1])

        execute_db(
            """INSERT OR IGNORE INTO matches
               (match_id, season, date, venue,
                team1_runs, team1_wickets, team1_overs,
                team2_runs, team2_wickets, team2_overs)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (match_id, season, date_str, venue,
             r1, w1, o1, r2, w2, o2),
        )
    except Exception as e:
        print(f"[scraper] Error parsing match {match_id}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, help="Single season year e.g. 2025")
    parser.add_argument("--all",    action="store_true", help="Scrape all seasons")
    args = parser.parse_args()

    if args.all:
        for yr in sorted(BPL_SERIES_IDS.keys()):
            scrape_season(yr)
    elif args.season:
        scrape_season(args.season)
    else:
        parser.print_help()
