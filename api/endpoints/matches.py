"""matches.py — Free tier: match results & scorecards."""
from fastapi import APIRouter, HTTPException, Query
from ..database import query_db

router = APIRouter(prefix="/api/v1/matches", tags=["Matches"])


@router.get("/")
async def list_matches(
    season: int | None = None,
    team_id: int | None = None,
    match_type: str | None = None,
    limit: int = Query(20, le=100),
    offset: int = 0,
):
    base = """
        SELECT m.*, s.year,
               t1.name as team1_name, t2.name as team2_name,
               w.name as winner_name
        FROM matches m
        JOIN seasons s  ON m.season_id=s.season_id
        JOIN teams t1   ON m.team1_id=t1.team_id
        JOIN teams t2   ON m.team2_id=t2.team_id
        LEFT JOIN teams w ON m.winner_id=w.team_id
    """
    where, params = [], []
    if season:
        where.append("s.year=?"); params.append(season)
    if team_id:
        where.append("(m.team1_id=? OR m.team2_id=?)"); params += [team_id, team_id]
    if match_type:
        where.append("m.match_type=?"); params.append(match_type)
    sql = base + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY m.date DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    return query_db(sql, tuple(params))


@router.get("/{match_id}")
async def get_match(match_id: int):
    rows = query_db("""
        SELECT m.*, s.year,
               t1.name as team1_name, t2.name as team2_name,
               w.name as winner_name
        FROM matches m
        JOIN seasons s ON m.season_id=s.season_id
        JOIN teams t1  ON m.team1_id=t1.team_id
        JOIN teams t2  ON m.team2_id=t2.team_id
        LEFT JOIN teams w ON m.winner_id=w.team_id
        WHERE m.match_id=?
    """, (match_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Match not found")
    match = rows[0]
    innings = query_db("SELECT * FROM innings WHERE match_id=? ORDER BY innings_number", (match_id,))
    batting, bowling = [], []
    for inn in innings:
        batting += query_db("""
            SELECT bp.*, p.name as player_name
            FROM batting_performances bp
            JOIN players p ON bp.player_id=p.player_id
            WHERE bp.innings_id=?
            ORDER BY bp.batting_order
        """, (inn["innings_id"],))
        bowling += query_db("""
            SELECT bwl.*, p.name as player_name
            FROM bowling_performances bwl
            JOIN players p ON bwl.player_id=p.player_id
            WHERE bwl.innings_id=?
            ORDER BY bwl.overs
        """, (inn["innings_id"],))
    return {"match": match, "innings": innings, "batting": batting, "bowling": bowling}


@router.get("/seasons/list")
async def list_seasons():
    return query_db("SELECT * FROM seasons ORDER BY year DESC")


@router.get("/seasons/{year}/summary")
async def season_summary(year: int):
    season = query_db("SELECT * FROM seasons WHERE year=?", (year,))
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    matches  = query_db("SELECT COUNT(*) as n FROM matches m JOIN seasons s ON m.season_id=s.season_id WHERE s.year=?", (year,))[0]["n"]
    top_bat  = query_db("""
        SELECT p.name, ps.runs, ps.batting_avg, ps.strike_rate
        FROM player_season_stats ps
        JOIN players p ON ps.player_id=p.player_id
        JOIN seasons s ON ps.season_id=s.season_id
        WHERE s.year=? ORDER BY ps.runs DESC LIMIT 5
    """, (year,))
    top_bowl = query_db("""
        SELECT p.name, ps.wickets, ps.economy, ps.bowling_avg
        FROM player_season_stats ps
        JOIN players p ON ps.player_id=p.player_id
        JOIN seasons s ON ps.season_id=s.season_id
        WHERE s.year=? ORDER BY ps.wickets DESC LIMIT 5
    """, (year,))
    return {"season": season[0], "total_matches": matches, "top_batsmen": top_bat, "top_bowlers": top_bowl}
