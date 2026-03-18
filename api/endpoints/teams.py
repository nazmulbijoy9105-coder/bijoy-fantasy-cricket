"""teams.py — Free tier: team stats & season records."""
from fastapi import APIRouter, HTTPException, Query
from ..database import query_db

router = APIRouter(prefix="/api/v1/teams", tags=["Teams"])


@router.get("/")
async def list_teams():
    return query_db("SELECT * FROM teams ORDER BY total_wins DESC")


@router.get("/{team_id}")
async def get_team(team_id: int):
    rows = query_db("SELECT * FROM teams WHERE team_id=?", (team_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Team not found")
    return rows[0]


@router.get("/{team_id}/season/{year}")
async def team_season_stats(team_id: int, year: int):
    rows = query_db("""
        SELECT m.match_id, m.date, m.venue, m.win_by, m.win_margin,
               m.team1_score, m.team1_wickets, m.team2_score, m.team2_wickets,
               m.winner_id
        FROM matches m
        JOIN seasons s ON m.season_id = s.season_id
        WHERE (m.team1_id=? OR m.team2_id=?) AND s.year=?
        ORDER BY m.date
    """, (team_id, team_id, year))
    wins   = sum(1 for r in rows if r["winner_id"] == team_id)
    losses = sum(1 for r in rows if r["winner_id"] not in (None, team_id) and r["winner_id"] != 0)
    return {
        "team_id": team_id,
        "season":  year,
        "matches_played": len(rows),
        "wins":    wins,
        "losses":  losses,
        "no_results": len(rows) - wins - losses,
        "match_records": rows,
    }


@router.get("/{team_id}/head-to-head/{opponent_id}")
async def head_to_head(team_id: int, opponent_id: int):
    rows = query_db("""
        SELECT m.match_id, m.date, m.winner_id, m.win_margin, m.win_by,
               m.team1_score, m.team2_score
        FROM matches m
        WHERE (m.team1_id=? AND m.team2_id=?)
           OR (m.team1_id=? AND m.team2_id=?)
        ORDER BY m.date
    """, (team_id, opponent_id, opponent_id, team_id))
    t1_wins = sum(1 for r in rows if r["winner_id"] == team_id)
    t2_wins = sum(1 for r in rows if r["winner_id"] == opponent_id)
    return {
        "team_id":      team_id,
        "opponent_id":  opponent_id,
        "total_matches": len(rows),
        "team_wins":    t1_wins,
        "opponent_wins": t2_wins,
        "no_results":   len(rows) - t1_wins - t2_wins,
        "matches":      rows,
    }
