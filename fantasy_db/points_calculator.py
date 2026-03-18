"""
fantasy_db/points_calculator.py
Fantasy points calculation engine.
Called after each match completes to compute GW points for all teams.
Run: python -m fantasy_db.points_calculator --gw 17
"""

import argparse
from api.database import query_db, query_one, execute_db


# ── Scoring constants (mirrors scoring_rules table) ──────────
SCORING = {
    "run":          1.0,
    "four":         1.0,
    "six":          2.0,
    "fifty":        10.0,
    "century":      25.0,
    "duck":        -5.0,
    "sr_140":       6.0,    # strike rate >= 140 (min 10 balls)
    "sr_120":       4.0,
    "sr_100":       2.0,
    "wicket":       20.0,
    "maiden":       4.0,
    "three_wkt":    8.0,
    "five_wkt":     20.0,
    "econ_5":       6.0,    # economy <= 5.0 (min 2 overs)
    "econ_6":       4.0,
    "econ_7":       2.0,
    "econ_9":      -2.0,
    "econ_10":     -4.0,
    "catch":        8.0,
    "stumping":     12.0,
    "runout":       8.0,
    "captain_mult": 2.0,
    "vc_mult":      1.5,
    "transfer_ded": -4.0,
}


def calc_player_pts(perf: dict) -> float:
    """Compute raw fantasy points for one player's match performance."""
    pts = 0.0

    # Batting
    pts += perf.get("runs_scored", 0)     * SCORING["run"]
    pts += perf.get("fours", 0)            * SCORING["four"]
    pts += perf.get("sixes", 0)            * SCORING["six"]
    if perf.get("is_fifty"):    pts += SCORING["fifty"]
    if perf.get("is_century"):  pts += SCORING["century"]
    if perf.get("is_duck"):     pts += SCORING["duck"]

    bf = perf.get("balls_faced", 0)
    sr = perf.get("strike_rate", 0.0)
    if bf >= 10:
        if sr >= 140: pts += SCORING["sr_140"]
        elif sr >= 120: pts += SCORING["sr_120"]
        elif sr >= 100: pts += SCORING["sr_100"]

    # Bowling
    pts += perf.get("wickets_taken", 0) * SCORING["wicket"]
    pts += perf.get("maidens", 0)        * SCORING["maiden"]
    if perf.get("is_three_wickets"): pts += SCORING["three_wkt"]
    if perf.get("is_five_wickets"):  pts += SCORING["five_wkt"]

    ov = perf.get("overs_bowled", 0.0)
    ec = perf.get("economy_rate", 0.0)
    if ov >= 2:
        if   ec <= 5.0:  pts += SCORING["econ_5"]
        elif ec <= 6.0:  pts += SCORING["econ_6"]
        elif ec <= 7.0:  pts += SCORING["econ_7"]
        elif ec >= 10.0: pts += SCORING["econ_10"]
        elif ec >= 9.0:  pts += SCORING["econ_9"]

    # Fielding
    pts += perf.get("catches_taken", 0) * SCORING["catch"]
    pts += perf.get("stumpings", 0)      * SCORING["stumping"]
    pts += perf.get("run_outs", 0)       * SCORING["runout"]

    return round(pts, 2)


def process_gameweek(gw_id: int) -> dict:
    """
    For a completed GW:
    1. Compute raw fantasy points per player per match
    2. Apply captain/vc multipliers per fantasy team
    3. Apply transfer deductions
    4. Write gw_team_points and gw_player_points
    5. Update overall fantasy_team totals
    """
    gw = query_one("SELECT * FROM gameweeks WHERE gw_id=?", (gw_id,))
    if not gw:
        return {"error": f"Gameweek {gw_id} not found"}

    # Get all matches in this GW
    matches = query_db("SELECT match_id FROM bpl_matches WHERE gameweek_id=?", (gw_id,))
    match_ids = [m["match_id"] for m in matches]
    if not match_ids:
        return {"error": "No matches in this gameweek"}

    # Update raw fantasy pts in player_performances for these matches
    perfs = query_db(
        f"SELECT * FROM player_performances WHERE match_id IN ({','.join('?'*len(match_ids))})",
        tuple(match_ids)
    )
    for pf in perfs:
        raw = calc_player_pts(pf)
        execute_db(
            "UPDATE player_performances SET total_fantasy_pts=? WHERE perf_id=?",
            (raw, pf["perf_id"])
        )

    # Build a lookup: player_id -> total pts this GW
    player_gw_pts = {}
    for pf in perfs:
        pid = pf["player_id"]
        player_gw_pts[pid] = player_gw_pts.get(pid, 0.0) + calc_player_pts(pf)

    # Get all fantasy teams for this season
    teams = query_db("SELECT * FROM fantasy_teams WHERE season_id=?", (gw["season_id"],))
    summary = []

    for ft in teams:
        squad = query_db(
            "SELECT * FROM fantasy_squad WHERE ft_id=? AND is_playing_xi=1",
            (ft["ft_id"],)
        )
        # Transfer deduction
        extra_transfers = query_db(
            "SELECT COUNT(*) n FROM transfers WHERE ft_id=? AND gw_id=? AND is_free=0",
            (ft["ft_id"], gw_id)
        )
        transfer_ded = (extra_transfers[0]["n"] if extra_transfers else 0) * abs(SCORING["transfer_ded"])

        bat_pts = bowl_pts = field_pts = bonus_pts = cap_bonus = 0.0

        for sp in squad:
            pid  = sp["player_id"]
            base = player_gw_pts.get(pid, 0.0)
            mult = SCORING["captain_mult"] if sp["is_captain"] else (SCORING["vc_mult"] if sp["is_vice_captain"] else 1.0)
            final = round(base * mult, 2)

            if sp["is_captain"]: cap_bonus += base  # extra points from captain
            bonus_pts += round(base * (mult - 1.0), 2)

            # Write gw_player_points
            execute_db(
                """INSERT OR REPLACE INTO gw_player_points
                   (ft_id,gw_id,player_id,is_captain,is_vice_captain,is_playing_xi,
                    base_pts,multiplier,final_pts)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (ft["ft_id"], gw_id, pid,
                 sp["is_captain"], sp["is_vice_captain"], 1,
                 base, mult, final)
            )
            bat_pts  += base * 0.5  # approximate split
            bowl_pts += base * 0.3
            field_pts+= base * 0.2

        total = round(bat_pts + bowl_pts + field_pts + bonus_pts - transfer_ded, 2)

        execute_db(
            """INSERT OR REPLACE INTO gw_team_points
               (ft_id,gw_id,batting_pts,bowling_pts,fielding_pts,bonus_pts,
                captain_bonus,transfer_deduction,total_pts)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (ft["ft_id"], gw_id,
             round(bat_pts,2), round(bowl_pts,2), round(field_pts,2),
             round(bonus_pts,2), round(cap_bonus,2), transfer_ded, total)
        )
        summary.append({"team": ft["team_name"], "total_pts": total})

    # Mark GW as finished
    execute_db("UPDATE gameweeks SET is_finished=1 WHERE gw_id=?", (gw_id,))

    # Compute GW ranks
    ranked = sorted(summary, key=lambda x: x["total_pts"], reverse=True)
    for i, r in enumerate(ranked, 1):
        execute_db(
            """UPDATE gw_team_points SET gw_rank=?
               WHERE gw_id=? AND ft_id=(
                 SELECT ft_id FROM fantasy_teams WHERE team_name=?)""",
            (i, gw_id, r["team"])
        )

    print(f"[points] GW{gw_id} processed — {len(teams)} teams, {len(perfs)} performances")
    return {"gw_id": gw_id, "teams_processed": len(teams), "top_score": ranked[0] if ranked else None}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gw", type=int, required=True, help="Gameweek ID to process")
    args = parser.parse_args()
    result = process_gameweek(args.gw)
    print(result)
