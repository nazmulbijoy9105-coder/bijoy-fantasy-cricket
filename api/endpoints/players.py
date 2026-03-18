"""players.py — Free tier: player stats (numeric only)."""
from fastapi import APIRouter, HTTPException, Query
from ..database import query_db

router = APIRouter(prefix="/api/v1/players", tags=["Players"])


@router.get("/")
async def list_players(
    role: str | None = None,
    nationality: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    base  = "SELECT p.*, c.runs, c.wickets, c.batting_avg, c.strike_rate, c.economy FROM players p LEFT JOIN player_career_stats c ON p.player_id=c.player_id"
    where, params = [], []
    if role:
        where.append("p.role=?"); params.append(role)
    if nationality:
        where.append("p.nationality=?"); params.append(nationality)
    sql = base + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY c.runs DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    return query_db(sql, tuple(params))


@router.get("/{player_id}")
async def get_player(player_id: int):
    rows = query_db("""
        SELECT p.*, c.*
        FROM players p
        LEFT JOIN player_career_stats c ON p.player_id=c.player_id
        WHERE p.player_id=?
    """, (player_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Player not found")
    return rows[0]


@router.get("/{player_id}/seasons")
async def player_seasons(player_id: int):
    return query_db("""
        SELECT ps.*, s.year, t.name as team_name
        FROM player_season_stats ps
        JOIN seasons s ON ps.season_id=s.season_id
        JOIN teams t   ON ps.team_id=t.team_id
        WHERE ps.player_id=?
        ORDER BY s.year DESC
    """, (player_id,))


@router.get("/{player_id}/match-log")
async def player_match_log(player_id: int, limit: int = Query(20, le=100)):
    batting = query_db("""
        SELECT bp.*, m.date, m.season_id
        FROM batting_performances bp
        JOIN matches m ON bp.match_id=m.match_id
        WHERE bp.player_id=?
        ORDER BY m.date DESC LIMIT ?
    """, (player_id, limit))
    bowling = query_db("""
        SELECT bwl.*, m.date, m.season_id
        FROM bowling_performances bwl
        JOIN matches m ON bwl.match_id=m.match_id
        WHERE bwl.player_id=?
        ORDER BY m.date DESC LIMIT ?
    """, (player_id, limit))
    return {"batting": batting, "bowling": bowling}


@router.get("/leaderboard/batting")
async def batting_leaderboard(
    season: int | None = None,
    stat: str = Query("runs", enum=["runs","batting_avg","strike_rate","sixes","fours"]),
    limit: int = Query(20, le=100),
):
    if season:
        return query_db(f"""
            SELECT ps.player_id, p.name, p.nationality, ps.{stat}, ps.matches, s.year
            FROM player_season_stats ps
            JOIN players p ON ps.player_id=p.player_id
            JOIN seasons s ON ps.season_id=s.season_id
            WHERE s.year=?
            ORDER BY ps.{stat} DESC LIMIT ?
        """, (season, limit))
    return query_db(f"""
        SELECT c.player_id, p.name, p.nationality, c.{stat}, c.matches
        FROM player_career_stats c
        JOIN players p ON c.player_id=p.player_id
        ORDER BY c.{stat} DESC LIMIT ?
    """, (limit,))


@router.get("/leaderboard/bowling")
async def bowling_leaderboard(
    season: int | None = None,
    stat: str = Query("wickets", enum=["wickets","economy","bowling_avg","bowling_sr"]),
    limit: int = Query(20, le=100),
):
    if season:
        return query_db(f"""
            SELECT ps.player_id, p.name, p.nationality, ps.{stat}, ps.matches, s.year
            FROM player_season_stats ps
            JOIN players p ON ps.player_id=p.player_id
            JOIN seasons s ON ps.season_id=s.season_id
            WHERE s.year=?
            ORDER BY ps.{stat} ASC LIMIT ?
        """, (season, limit))
    return query_db(f"""
        SELECT c.player_id, p.name, p.nationality, c.{stat}, c.matches
        FROM player_career_stats c
        JOIN players p ON c.player_id=p.player_id
        ORDER BY c.{stat} ASC LIMIT ?
    """, (limit,))
