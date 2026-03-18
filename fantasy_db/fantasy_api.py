"""
fantasy_db/fantasy_api.py
Complete FastAPI router for all fantasy dashboard endpoints.
Mount this in api/main.py: app.include_router(fantasy_router, prefix="/fantasy")
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Reuse the existing DB helpers from the BPL API
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.database import query_db, query_one, execute_db
from api.auth import get_current_user
from api.dependencies import paid_required, admin_required, superadmin_required

router = APIRouter(tags=["Fantasy"])


# ── Pydantic Models ───────────────────────────────────────────

class CreateTeamRequest(BaseModel):
    season_id: int = 1
    team_name: str = "My XI"

class AddPlayerRequest(BaseModel):
    ft_id: int
    player_id: int
    is_playing_xi: int = 1
    is_captain: int = 0
    is_vice_captain: int = 0

class SetCaptainRequest(BaseModel):
    ft_id: int
    player_id: int
    is_captain: bool = True   # False = set as vice-captain

class TransferRequest(BaseModel):
    ft_id: int
    gw_id: int
    player_out_id: int
    player_in_id: int


# ══════════════════════════════════════════════════════════════
# DASHBOARD — ADMIN OVERVIEW
# ══════════════════════════════════════════════════════════════

@router.get("/admin/overview")
def admin_overview(current_user=admin_required):
    """Full admin dashboard metrics for the investor demo."""
    total_users  = query_one("SELECT COUNT(*) n FROM users")["n"]
    paid_users   = query_one("SELECT COUNT(*) n FROM users WHERE role='paid'")["n"]
    free_users   = total_users - paid_users
    total_teams  = query_one("SELECT COUNT(*) n FROM fantasy_teams")["n"]
    active_subs  = query_one("SELECT COUNT(*) n FROM subscriptions WHERE status='completed'")["n"]
    revenue      = query_one("SELECT COALESCE(SUM(amount_bdt),0) t FROM subscriptions WHERE status='completed'")["t"]
    total_players= query_one("SELECT COUNT(*) n FROM bpl_players")["n"]
    total_matches= query_one("SELECT COUNT(*) n FROM bpl_matches")["n"]
    active_gw    = query_one("SELECT * FROM gameweeks WHERE is_active=1 ORDER BY gw_number DESC LIMIT 1")
    return {
        "users":       {"total": total_users, "paid": paid_users, "free": free_users},
        "fantasy":     {"teams": total_teams},
        "revenue":     {"total_bdt": round(revenue,2), "active_subscriptions": active_subs},
        "data":        {"players": total_players, "matches": total_matches},
        "active_gameweek": active_gw,
    }


@router.get("/admin/users")
def admin_users(skip: int = 0, limit: int = 50, current_user=admin_required):
    return query_db(
        "SELECT user_id,username,email,phone,role,is_active,created_at FROM users LIMIT ? OFFSET ?",
        (limit, skip)
    )


@router.get("/admin/subscriptions")
def admin_subscriptions(status: str = None, current_user=admin_required):
    if status:
        return query_db(
            """SELECT s.*,u.username,u.email FROM subscriptions s
               JOIN users u ON s.user_id=u.user_id WHERE s.status=? ORDER BY s.created_at DESC""",
            (status,)
        )
    return query_db(
        "SELECT s.*,u.username,u.email FROM subscriptions s JOIN users u ON s.user_id=u.user_id ORDER BY s.created_at DESC"
    )


# ══════════════════════════════════════════════════════════════
# GAMEWEEKS
# ══════════════════════════════════════════════════════════════

@router.get("/gameweeks")
def list_gameweeks(season_id: int = 1):
    return query_db(
        "SELECT * FROM gameweeks WHERE season_id=? ORDER BY gw_number",
        (season_id,)
    )


@router.get("/gameweeks/active")
def active_gameweek(season_id: int = 1):
    gw = query_one("SELECT * FROM gameweeks WHERE season_id=? AND is_active=1", (season_id,))
    if not gw:
        raise HTTPException(status_code=404, detail="No active gameweek")
    matches = query_db(
        """SELECT m.*,t1.name as team1_name,t2.name as team2_name,tw.name as winner_name
           FROM bpl_matches m
           JOIN bpl_teams t1 ON m.team1_id=t1.team_id
           JOIN bpl_teams t2 ON m.team2_id=t2.team_id
           LEFT JOIN bpl_teams tw ON m.winner_id=tw.team_id
           WHERE m.gameweek_id=?""",
        (gw["gw_id"],)
    )
    return {"gameweek": gw, "matches": matches}


# ══════════════════════════════════════════════════════════════
# PLAYERS — FANTASY SELECTION
# ══════════════════════════════════════════════════════════════

@router.get("/players")
def fantasy_players(
    role:       str = Query(None),
    team_id:    int = Query(None),
    min_price:  float = Query(None),
    max_price:  float = Query(None),
    available_only: bool = True,
    skip: int = 0, limit: int = 100
):
    """All players available for fantasy selection with price and stats."""
    clauses, params = ["1=1"], []
    if available_only:
        clauses.append("p.is_available=1"); 
    if role:
        clauses.append("p.role=?"); params.append(role)
    if team_id:
        clauses.append("pts.team_id=?"); params.append(team_id)
    if min_price is not None:
        clauses.append("p.base_price>=?"); params.append(min_price)
    if max_price is not None:
        clauses.append("p.base_price<=?"); params.append(max_price)
    where = " AND ".join(clauses)
    rows = query_db(
        f"""SELECT p.player_id, p.name, p.role, p.nationality,
                   p.batting_style, p.bowling_style,
                   p.total_matches, p.total_runs, p.total_wickets,
                   p.batting_avg, p.strike_rate, p.economy_rate,
                   p.centuries, p.fifties, p.fours, p.sixes,
                   p.catches, p.stumpings, p.base_price, p.is_available,
                   t.name as team_name, t.abbreviation as team_abbr,
                   COALESCE(ph.ownership_pct,0) as ownership_pct
            FROM bpl_players p
            LEFT JOIN player_team_season pts ON p.player_id=pts.player_id AND pts.season_id=1
            LEFT JOIN bpl_teams t ON pts.team_id=t.team_id
            LEFT JOIN (SELECT player_id, ownership_pct FROM player_price_history
                       ORDER BY recorded_at DESC LIMIT 1) ph ON p.player_id=ph.player_id
            WHERE {where}
            ORDER BY p.total_runs DESC LIMIT ? OFFSET ?""",
        tuple(params) + (limit, skip)
    )
    return {"count": len(rows), "players": rows}


@router.get("/players/{player_id}/gw-history")
def player_gw_history(player_id: int, season_id: int = 1):
    """Per-gameweek fantasy points history for a player."""
    rows = query_db(
        """SELECT gw.gw_number, gw.name as gw_name,
                  pf.runs_scored, pf.wickets_taken, pf.catches_taken,
                  pf.stumpings, pf.total_fantasy_pts, m.date, m.venue,
                  t.abbreviation as opponent
           FROM player_performances pf
           JOIN bpl_matches m ON pf.match_id=m.match_id
           JOIN gameweeks gw ON m.gameweek_id=gw.gw_id
           JOIN bpl_teams t ON (CASE WHEN m.team1_id=pf.team_id THEN m.team2_id ELSE m.team1_id END)=t.team_id
           WHERE pf.player_id=? AND gw.season_id=?
           ORDER BY gw.gw_number""",
        (player_id, season_id)
    )
    return {"player_id": player_id, "gw_history": rows}


# ══════════════════════════════════════════════════════════════
# FANTASY TEAMS — CRUD
# ══════════════════════════════════════════════════════════════

@router.get("/my-team")
def get_my_team(season_id: int = 1, current_user: dict = Depends(get_current_user)):
    ft = query_one(
        "SELECT * FROM fantasy_teams WHERE user_id=? AND season_id=?",
        (current_user["user_id"], season_id)
    )
    if not ft:
        raise HTTPException(status_code=404, detail="No fantasy team found. Create one first.")
    squad = query_db(
        """SELECT fs.*, p.name, p.role, p.nationality,
                  p.base_price, p.total_runs, p.total_wickets,
                  p.batting_avg, p.strike_rate, p.economy_rate,
                  t.abbreviation as team_abbr
           FROM fantasy_squad fs
           JOIN bpl_players p ON fs.player_id=p.player_id
           LEFT JOIN player_team_season pts ON p.player_id=pts.player_id AND pts.season_id=?
           LEFT JOIN bpl_teams t ON pts.team_id=t.team_id
           WHERE fs.ft_id=?
           ORDER BY fs.is_playing_xi DESC, fs.position_order""",
        (season_id, ft["ft_id"])
    )
    gw_pts = query_db(
        "SELECT * FROM gw_team_points WHERE ft_id=? ORDER BY gw_id DESC LIMIT 5",
        (ft["ft_id"],)
    )
    return {"team": ft, "squad": squad, "recent_gw_points": gw_pts}


@router.post("/my-team/create")
def create_team(req: CreateTeamRequest, current_user: dict = Depends(get_current_user)):
    existing = query_one(
        "SELECT ft_id FROM fantasy_teams WHERE user_id=? AND season_id=?",
        (current_user["user_id"], req.season_id)
    )
    if existing:
        raise HTTPException(status_code=400, detail="You already have a team this season.")
    ft_id = execute_db(
        "INSERT INTO fantasy_teams(user_id,season_id,team_name) VALUES(?,?,?)",
        (current_user["user_id"], req.season_id, req.team_name)
    )
    return {"message": "Team created", "ft_id": ft_id}


@router.post("/my-team/add-player")
def add_player(req: AddPlayerRequest, current_user: dict = Depends(get_current_user)):
    # Validate ownership
    ft = query_one("SELECT * FROM fantasy_teams WHERE ft_id=? AND user_id=?",
                   (req.ft_id, current_user["user_id"]))
    if not ft:
        raise HTTPException(status_code=403, detail="Not your team.")

    # Squad size check
    count = query_one("SELECT COUNT(*) n FROM fantasy_squad WHERE ft_id=?", (req.ft_id,))["n"]
    rules = query_one("SELECT * FROM team_rules WHERE season_id=?", (ft["season_id"],))
    if count >= (rules["squad_size"] if rules else 15):
        raise HTTPException(status_code=400, detail="Squad full (15/15).")

    # Budget check
    player = query_one("SELECT * FROM bpl_players WHERE player_id=?", (req.player_id,))
    if not player:
        raise HTTPException(status_code=404, detail="Player not found.")
    if ft["budget_remaining"] < player["base_price"]:
        raise HTTPException(status_code=400, detail=f"Insufficient budget. Need £{player['base_price']}m.")

    execute_db(
        """INSERT OR IGNORE INTO fantasy_squad
           (ft_id,player_id,purchase_price,is_playing_xi,is_captain,is_vice_captain,position_order)
           VALUES(?,?,?,?,?,?,?)""",
        (req.ft_id, req.player_id, player["base_price"],
         req.is_playing_xi, req.is_captain, req.is_vice_captain, count+1)
    )
    execute_db(
        "UPDATE fantasy_teams SET budget_remaining=budget_remaining-?, updated_at=CURRENT_TIMESTAMP WHERE ft_id=?",
        (player["base_price"], req.ft_id)
    )
    return {"message": f"{player['name']} added to squad.", "budget_remaining": ft["budget_remaining"] - player["base_price"]}


@router.post("/my-team/set-captain")
def set_captain(req: SetCaptainRequest, current_user: dict = Depends(get_current_user)):
    ft = query_one("SELECT ft_id FROM fantasy_teams WHERE ft_id=? AND user_id=?",
                   (req.ft_id, current_user["user_id"]))
    if not ft:
        raise HTTPException(status_code=403, detail="Not your team.")
    if req.is_captain:
        execute_db("UPDATE fantasy_squad SET is_captain=0 WHERE ft_id=?", (req.ft_id,))
        execute_db("UPDATE fantasy_squad SET is_captain=1 WHERE ft_id=? AND player_id=?",
                   (req.ft_id, req.player_id))
        return {"message": "Captain set."}
    else:
        execute_db("UPDATE fantasy_squad SET is_vice_captain=0 WHERE ft_id=?", (req.ft_id,))
        execute_db("UPDATE fantasy_squad SET is_vice_captain=1 WHERE ft_id=? AND player_id=?",
                   (req.ft_id, req.player_id))
        return {"message": "Vice-captain set."}


@router.post("/my-team/transfer")
def make_transfer(req: TransferRequest, current_user: dict = Depends(get_current_user)):
    ft = query_one("SELECT * FROM fantasy_teams WHERE ft_id=? AND user_id=?",
                   (req.ft_id, current_user["user_id"]))
    if not ft:
        raise HTTPException(status_code=403, detail="Not your team.")

    rules = query_one("SELECT * FROM team_rules WHERE season_id=?", (ft["season_id"],)) or {}
    free_transfers = rules.get("free_transfers", 1)
    transfer_deduct = rules.get("transfer_deduct", 4.0)

    # Count transfers already made this GW
    gw_transfers = query_one(
        "SELECT COUNT(*) n FROM transfers WHERE ft_id=? AND gw_id=?",
        (req.ft_id, req.gw_id)
    )["n"]
    is_free = gw_transfers < free_transfers
    deduction = 0.0 if is_free else transfer_deduct

    player_out = query_one("SELECT * FROM bpl_players WHERE player_id=?", (req.player_out_id,))
    player_in  = query_one("SELECT * FROM bpl_players WHERE player_id=?", (req.player_in_id,))
    if not player_out or not player_in:
        raise HTTPException(status_code=404, detail="Player not found.")

    # Budget check
    budget_change = player_out["base_price"] - player_in["base_price"]
    new_budget = ft["budget_remaining"] + budget_change
    if new_budget < 0:
        raise HTTPException(status_code=400, detail="Insufficient budget for this transfer.")

    execute_db(
        "DELETE FROM fantasy_squad WHERE ft_id=? AND player_id=?",
        (req.ft_id, req.player_out_id)
    )
    execute_db(
        "INSERT INTO fantasy_squad(ft_id,player_id,purchase_price) VALUES(?,?,?)",
        (req.ft_id, req.player_in_id, player_in["base_price"])
    )
    execute_db(
        """INSERT INTO transfers
           (ft_id,gw_id,player_out_id,player_in_id,sell_price,buy_price,is_free,deduction_pts)
           VALUES(?,?,?,?,?,?,?,?)""",
        (req.ft_id, req.gw_id, req.player_out_id, req.player_in_id,
         player_out["base_price"], player_in["base_price"], 1 if is_free else 0, deduction)
    )
    execute_db(
        "UPDATE fantasy_teams SET budget_remaining=?, transfers_made=transfers_made+1 WHERE ft_id=?",
        (new_budget, req.ft_id)
    )
    return {
        "message": f"Transfer: {player_out['name']} → {player_in['name']}",
        "is_free": is_free,
        "deduction": deduction,
        "new_budget": round(new_budget, 2)
    }


# ══════════════════════════════════════════════════════════════
# LEADERBOARDS
# ══════════════════════════════════════════════════════════════

@router.get("/leaderboard/overall")
def overall_leaderboard(season_id: int = 1, skip: int = 0, limit: int = 50):
    return query_db(
        """SELECT ft.ft_id, ft.team_name, ft.total_points, ft.overall_rank,
                  u.username
           FROM fantasy_teams ft
           JOIN users u ON ft.user_id=u.user_id
           WHERE ft.season_id=?
           ORDER BY ft.total_points DESC LIMIT ? OFFSET ?""",
        (season_id, limit, skip)
    )


@router.get("/leaderboard/gw/{gw_id}")
def gw_leaderboard(gw_id: int, skip: int = 0, limit: int = 50):
    return query_db(
        """SELECT gtp.ft_id, gtp.total_pts, gtp.gw_rank,
                  ft.team_name, u.username,
                  gtp.batting_pts, gtp.bowling_pts, gtp.fielding_pts,
                  gtp.captain_bonus, gtp.transfer_deduction
           FROM gw_team_points gtp
           JOIN fantasy_teams ft ON gtp.ft_id=ft.ft_id
           JOIN users u ON ft.user_id=u.user_id
           WHERE gtp.gw_id=?
           ORDER BY gtp.total_pts DESC LIMIT ? OFFSET ?""",
        (gw_id, limit, skip)
    )


@router.get("/leaderboard/players/{gw_id}")
def gw_player_leaderboard(gw_id: int, limit: int = 20):
    return query_db(
        """SELECT pf.player_id, p.name, p.role,
                  t.abbreviation as team,
                  pf.runs_scored, pf.wickets_taken, pf.catches_taken,
                  pf.stumpings, pf.total_fantasy_pts
           FROM player_performances pf
           JOIN bpl_players p ON pf.player_id=p.player_id
           JOIN bpl_teams t ON pf.team_id=t.team_id
           JOIN bpl_matches m ON pf.match_id=m.match_id
           WHERE m.gameweek_id=?
           ORDER BY pf.total_fantasy_pts DESC LIMIT ?""",
        (gw_id, limit)
    )


# ══════════════════════════════════════════════════════════════
# SCORING RULES
# ══════════════════════════════════════════════════════════════

@router.get("/scoring-rules")
def get_scoring_rules(season_id: int = 1):
    return query_db(
        "SELECT * FROM scoring_rules WHERE season_id=? AND is_active=1 ORDER BY category,points DESC",
        (season_id,)
    )


@router.get("/team-rules")
def get_team_rules(season_id: int = 1):
    return query_one("SELECT * FROM team_rules WHERE season_id=?", (season_id,))


# ══════════════════════════════════════════════════════════════
# CONTESTS
# ══════════════════════════════════════════════════════════════

@router.get("/contests")
def list_contests(season_id: int = 1, contest_type: str = None):
    if contest_type:
        return query_db(
            "SELECT * FROM contests WHERE season_id=? AND contest_type=? AND is_active=1",
            (season_id, contest_type)
        )
    return query_db(
        "SELECT * FROM contests WHERE season_id=? AND is_active=1 ORDER BY entry_fee_bdt",
        (season_id,)
    )


@router.post("/contests/{contest_id}/join")
def join_contest(contest_id: int, ft_id: int, current_user: dict = Depends(get_current_user)):
    contest = query_one("SELECT * FROM contests WHERE contest_id=?", (contest_id,))
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found.")
    if contest["current_teams"] >= contest["max_teams"]:
        raise HTTPException(status_code=400, detail="Contest is full.")

    execute_db(
        "INSERT OR IGNORE INTO contest_entries(contest_id,ft_id,user_id) VALUES(?,?,?)",
        (contest_id, ft_id, current_user["user_id"])
    )
    execute_db(
        "UPDATE contests SET current_teams=current_teams+1 WHERE contest_id=?",
        (contest_id,)
    )
    return {"message": "Joined contest successfully."}


# ══════════════════════════════════════════════════════════════
# AI PREMIUM FEATURES (paid only)
# ══════════════════════════════════════════════════════════════

@router.get("/premium/predictions/{gw_id}")
def gw_predictions(gw_id: int, current_user=paid_required):
    preds = query_db(
        """SELECT ap.*,
                  t.name as predicted_winner_name,
                  ps.name as top_scorer_name,
                  pw.name as top_wicket_name,
                  m.date, m.venue,
                  t1.abbreviation as team1, t2.abbreviation as team2
           FROM ai_predictions ap
           JOIN bpl_matches m ON ap.match_id=m.match_id
           JOIN bpl_teams t  ON ap.predicted_winner_id=t.team_id
           JOIN bpl_teams t1 ON m.team1_id=t1.team_id
           JOIN bpl_teams t2 ON m.team2_id=t2.team_id
           LEFT JOIN bpl_players ps ON ap.pred_top_scorer_id=ps.player_id
           LEFT JOIN bpl_players pw ON ap.pred_top_wicket_taker_id=pw.player_id
           WHERE ap.gw_id=?""",
        (gw_id,)
    )
    return {"gw_id": gw_id, "predictions": preds}


@router.get("/premium/differentials/{gw_id}")
def gw_differentials(gw_id: int, max_ownership: float = 15.0, current_user=paid_required):
    """AI differential picks — high upside, low ownership players."""
    return query_db(
        """SELECT dp.*, p.name, p.role, p.base_price,
                  t.abbreviation as team
           FROM ai_differential_picks dp
           JOIN bpl_players p ON dp.player_id=p.player_id
           LEFT JOIN player_team_season pts ON p.player_id=pts.player_id AND pts.season_id=1
           LEFT JOIN bpl_teams t ON pts.team_id=t.team_id
           WHERE dp.gw_id=? AND dp.ownership_pct <= ?
           ORDER BY dp.value_score DESC LIMIT 10""",
        (gw_id, max_ownership)
    )


@router.get("/premium/player-compare")
def compare_players(
    player1_id: int = Query(...),
    player2_id: int = Query(...),
    current_user=paid_required
):
    """Head-to-head numeric comparison for fantasy selection."""
    def get_full(pid):
        p = query_one("SELECT * FROM bpl_players WHERE player_id=?", (pid,))
        if not p:
            raise HTTPException(status_code=404, detail=f"Player {pid} not found.")
        last5 = query_db(
            """SELECT pf.runs_scored,pf.wickets_taken,pf.total_fantasy_pts,m.date
               FROM player_performances pf JOIN bpl_matches m ON pf.match_id=m.match_id
               WHERE pf.player_id=? ORDER BY m.date DESC LIMIT 5""",
            (pid,)
        )
        fantasy_score = (p["total_runs"]*1 + p["centuries"]*25 + p["fifties"]*10
                         + p["sixes"]*2 + p["total_wickets"]*20 + p["catches"]*8)
        value = round(fantasy_score / p["base_price"], 2) if p["base_price"] else 0
        return {**dict(p), "last_5_matches": last5, "fantasy_score": fantasy_score, "value_score": value}

    p1 = get_full(player1_id)
    p2 = get_full(player2_id)
    better = p1["name"] if p1["fantasy_score"] >= p2["fantasy_score"] else p2["name"]
    val_pick = p1["name"] if p1["value_score"] >= p2["value_score"] else p2["name"]
    return {
        "player1": p1, "player2": p2,
        "recommendation": better, "value_pick": val_pick
    }


# ══════════════════════════════════════════════════════════════
# NOTIFICATIONS
# ══════════════════════════════════════════════════════════════

@router.get("/notifications")
def my_notifications(current_user: dict = Depends(get_current_user)):
    notifs = query_db(
        "SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 20",
        (current_user["user_id"],)
    )
    execute_db(
        "UPDATE notifications SET is_read=1 WHERE user_id=? AND is_read=0",
        (current_user["user_id"],)
    )
    return notifs
