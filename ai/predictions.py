"""
ai/predictions.py
Statistical prediction engine. Uses historical numeric data only.
"""


def _safe_div(a, b, default=0.0):
    return round(a / b, 3) if b else default


def _player_fantasy_score(p: dict) -> float:
    bat = (p.get("runs", 0) * 1.0
           + p.get("centuries", 0) * 100
           + p.get("fifties", 0) * 50
           + p.get("sixes", 0) * 6
           + p.get("fours", 0) * 1)
    bowl = (p.get("wickets", 0) * 25
            + p.get("five_wickets", 0) * 50)
    field = (p.get("catches", 0) * 10
             + p.get("stumpings", 0) * 15
             + p.get("run_outs", 0) * 10)
    econ_bonus = max(0, (7.0 - p.get("economy", 7.0)) * 5) if p.get("wickets", 0) > 0 else 0
    sr_bonus   = max(0, (p.get("strike_rate", 100) - 100) * 0.2) if p.get("runs", 0) > 0 else 0
    return round(bat + bowl + field + econ_bonus + sr_bonus, 2)


def _team_strength(team_id: int) -> dict:
    from api.database import query_db
    s = (query_db(
        """SELECT SUM(wins) as wins, SUM(losses) as losses,
                  AVG(net_run_rate) as avg_nrr,
                  SUM(runs_scored) as runs, SUM(wickets_taken) as wickets
           FROM team_season_stats WHERE team_id=?""",
        (team_id,),
    ) or [{}])[0]
    wins   = s.get("wins") or 0
    losses = s.get("losses") or 1
    return {
        "win_rate":      round(_safe_div(wins, wins + losses), 3),
        "avg_nrr":       round(s.get("avg_nrr") or 0.0, 3),
        "run_power":     round((s.get("runs") or 0) / max(wins + losses, 1), 1),
        "wicket_power":  round((s.get("wickets") or 0) / max(wins + losses, 1), 2),
    }


def predict_match(match_id: int, match: dict = None) -> dict:
    from api.database import query_db, query_one
    if match is None:
        match = query_one("SELECT * FROM matches WHERE match_id=?", (match_id,))
    if not match:
        return {"error": "Match not found"}

    t1_id = match.get("team1_id") or match.get("team1")
    t2_id = match.get("team2_id") or match.get("team2")
    t1 = _team_strength(t1_id)
    t2 = _team_strength(t2_id)

    s1 = t1["win_rate"] * 0.6 + max(0, t1["avg_nrr"]) * 0.4
    s2 = t2["win_rate"] * 0.6 + max(0, t2["avg_nrr"]) * 0.4
    total = (s1 + s2) or 1
    t1_prob = round(s1 / total, 3)
    t2_prob = round(1 - t1_prob, 3)

    top_scorer = (query_db(
        "SELECT name,player_id,runs,strike_rate,fantasy_price FROM players WHERE team_id IN (?,?) ORDER BY runs DESC LIMIT 1",
        (t1_id, t2_id),
    ) or [{}])[0]
    top_bowler = (query_db(
        "SELECT name,player_id,wickets,economy,fantasy_price FROM players WHERE team_id IN (?,?) AND wickets>0 ORDER BY wickets DESC LIMIT 1",
        (t1_id, t2_id),
    ) or [{}])[0]

    winner_id = t1_id if t1_prob >= 0.5 else t2_id
    winner    = query_one("SELECT name,abbreviation FROM teams WHERE team_id=?", (winner_id,)) or {}

    return {
        "match_id": match_id,
        "team1": {"team_id": t1_id, "win_probability": t1_prob, "strength": t1},
        "team2": {"team_id": t2_id, "win_probability": t2_prob, "strength": t2},
        "predicted_winner": {"team_id": winner_id, "name": winner.get("name"), "confidence": max(t1_prob, t2_prob)},
        "predicted_top_scorer": top_scorer,
        "predicted_top_wicket_taker": top_bowler,
        "model": "statistical_v1",
        "disclaimer": "AI-generated estimate based on historical numeric stats. Not guaranteed.",
    }


def compare_players(p1: dict, p2: dict) -> dict:
    def _m(p):
        return {
            "player_id":    p["player_id"],
            "name":         p["name"],
            "role":         p.get("role"),
            "matches":      p.get("matches_played", 0),
            "runs":         p.get("runs", 0),
            "batting_avg":  round(p.get("batting_avg", 0), 2),
            "strike_rate":  round(p.get("strike_rate", 0), 2),
            "centuries":    p.get("centuries", 0),
            "fifties":      p.get("fifties", 0),
            "sixes":        p.get("sixes", 0),
            "wickets":      p.get("wickets", 0),
            "economy":      round(p.get("economy", 0), 2),
            "bowling_avg":  round(p.get("bowling_avg", 0), 2),
            "catches":      p.get("catches", 0),
            "fantasy_score": _player_fantasy_score(p),
            "fantasy_price": p.get("fantasy_price", 0),
        }
    m1, m2 = _m(p1), _m(p2)
    better     = p1["name"] if m1["fantasy_score"] >= m2["fantasy_score"] else p2["name"]
    val_p1     = _safe_div(m1["fantasy_score"], p1.get("fantasy_price", 1))
    val_p2     = _safe_div(m2["fantasy_score"], p2.get("fantasy_price", 1))
    value_pick = p1["name"] if val_p1 >= val_p2 else p2["name"]
    return {
        "player1": m1,
        "player2": m2,
        "fantasy_recommendation": better,
        "value_pick": value_pick,
        "value_scores": {p1["name"]: round(val_p1, 2), p2["name"]: round(val_p2, 2)},
    }


def top_performers_prediction(season: int = None, top_n: int = 10) -> dict:
    from api.database import query_db
    if season:
        players = query_db(
            "SELECT p.*, t.abbreviation as team_abbr FROM players p JOIN teams t ON p.team_id=t.team_id WHERE p.seasons_played LIKE ?",
            (f"%{season}%",),
        )
    else:
        players = query_db(
            "SELECT p.*, t.abbreviation as team_abbr FROM players p JOIN teams t ON p.team_id=t.team_id"
        )
    ranked = sorted(players, key=_player_fantasy_score, reverse=True)[:top_n]
    return {
        "season": season or "all-time",
        "top_performers": [
            {**p, "predicted_fantasy_score": _player_fantasy_score(p)}
            for p in ranked
        ],
    }
