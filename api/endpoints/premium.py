"""
api/endpoints/premium.py
Paid-only endpoints: AI predictions, player comparisons, fantasy insights.
"""

from fastapi import APIRouter, HTTPException, Query
from ..dependencies import paid_required
from ..database import query_db, query_one

router = APIRouter(prefix="/premium", tags=["Premium (Paid)"])


@router.get("/predictions/{match_id}")
def match_predictions(match_id: int, current_user=paid_required):
    """AI win probability + top performer prediction. Requires paid subscription."""
    from ai.predictions import predict_match
    match = query_one("SELECT * FROM matches WHERE match_id=?", (match_id,))
    if not match:
        raise HTTPException(status_code=404, detail="Match not found.")
    cached = query_one(
        "SELECT * FROM premium_insights WHERE match_id=? ORDER BY created_at DESC LIMIT 1",
        (match_id,),
    )
    if cached:
        return {"source": "cached", "insight": cached}
    return {"source": "live", "prediction": predict_match(match_id, match)}


@router.get("/player-compare")
def player_compare(
    player1_id: int = Query(...),
    player2_id: int = Query(...),
    current_user=paid_required,
):
    """Head-to-head numeric comparison of two players."""
    from ai.predictions import compare_players
    p1 = query_one("SELECT * FROM players WHERE player_id=?", (player1_id,))
    p2 = query_one("SELECT * FROM players WHERE player_id=?", (player2_id,))
    if not p1 or not p2:
        raise HTTPException(status_code=404, detail="One or both players not found.")
    return compare_players(p1, p2)


@router.get("/top-performers")
def top_performers(
    season: int = Query(None),
    top_n: int = Query(10, le=50),
    current_user=paid_required,
):
    """AI-ranked top performers by composite fantasy score."""
    from ai.predictions import top_performers_prediction
    return top_performers_prediction(season=season, top_n=top_n)


@router.get("/insights/{match_id}")
def match_insights(match_id: int, current_user=paid_required):
    """Deep numeric match insight: H2H history, venue averages, toss impact."""
    match = query_one("SELECT * FROM matches WHERE match_id=?", (match_id,))
    if not match:
        raise HTTPException(status_code=404, detail="Match not found.")

    h2h = query_db(
        """SELECT season, date,
                  team1_runs, team1_wickets, team1_overs,
                  team2_runs, team2_wickets, team2_overs,
                  win_margin, win_type, winner_id
           FROM matches
           WHERE (team1_id=? AND team2_id=?) OR (team1_id=? AND team2_id=?)
           ORDER BY date DESC LIMIT 10""",
        (match["team1_id"], match["team2_id"], match["team2_id"], match["team1_id"]),
    )
    venue_avg = query_one(
        """SELECT venue,
                  ROUND(AVG(team1_runs),0) as avg_first_innings,
                  ROUND(AVG(team2_runs),0) as avg_second_innings,
                  COUNT(*) as matches_at_venue
           FROM matches WHERE venue=?""",
        (match.get("venue", ""),),
    )
    toss_impact = query_db(
        """SELECT toss_decision, COUNT(*) as matches,
                  SUM(CASE WHEN toss_winner_id=winner_id THEN 1 ELSE 0 END) as toss_winner_wins
           FROM matches WHERE venue=? GROUP BY toss_decision""",
        (match.get("venue", ""),),
    )
    return {
        "match_id": match_id,
        "head_to_head_history": h2h,
        "venue_numeric_stats": venue_avg,
        "toss_impact_stats": toss_impact,
    }
