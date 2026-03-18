-- ============================================================
-- BijoyFantasyCricketBD — Complete Fantasy Database Schema
-- Covers: Users, Fantasy Teams, Contests, Scoring, Gameweeks,
--         Transfers, Leaderboards, Subscriptions, Payments,
--         AI Insights, Admin Audit
-- Governance: Numeric stats only. No copyrighted content.
-- ============================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- ============================================================
-- 1. USERS & AUTH
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    user_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT    UNIQUE NOT NULL,
    email           TEXT    UNIQUE,
    phone           TEXT    UNIQUE,           -- Bangladesh mobile number
    password_hash   TEXT    NOT NULL,
    role            TEXT    NOT NULL DEFAULT 'free',
                                              -- free | paid | admin | superadmin
    api_key         TEXT    UNIQUE,
    is_active       INTEGER NOT NULL DEFAULT 1,
    email_verified  INTEGER NOT NULL DEFAULT 0,
    phone_verified  INTEGER NOT NULL DEFAULT 0,
    preferred_lang  TEXT    DEFAULT 'en',     -- en | bn
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login      DATETIME,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_users_api_key  ON users(api_key);
CREATE INDEX IF NOT EXISTS idx_users_role     ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_email    ON users(email);

-- ============================================================
-- 2. BPL CORE DATA (stats source — numeric only)
-- ============================================================
CREATE TABLE IF NOT EXISTS bpl_seasons (
    season_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    year            INTEGER UNIQUE NOT NULL,
    name            TEXT,                     -- e.g. "BPL 2025"
    start_date      DATE,
    end_date        DATE,
    total_teams     INTEGER DEFAULT 0,
    total_matches   INTEGER DEFAULT 0,
    champion_id     INTEGER,                  -- FK -> bpl_teams
    status          TEXT    DEFAULT 'upcoming' -- upcoming|active|completed
);

CREATE TABLE IF NOT EXISTS bpl_teams (
    team_id         INTEGER PRIMARY KEY,
    season_id       INTEGER NOT NULL,
    name            TEXT    NOT NULL,
    abbreviation    TEXT    NOT NULL,
    city            TEXT,
    home_ground     TEXT,
    FOREIGN KEY(season_id) REFERENCES bpl_seasons(season_id)
);
CREATE INDEX IF NOT EXISTS idx_bplteams_season ON bpl_teams(season_id);

CREATE TABLE IF NOT EXISTS bpl_players (
    player_id       INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL,
    role            TEXT,                     -- Batsman|Bowler|All-Rounder|Wicket-Keeper
    batting_style   TEXT,                     -- RHB|LHB
    bowling_style   TEXT,                     -- RAO|LAO|RFM|LFM|OB|LB|SLA|SLC|None
    nationality     TEXT,
    -- Career numeric stats
    total_matches   INTEGER DEFAULT 0,
    total_runs      INTEGER DEFAULT 0,
    total_wickets   INTEGER DEFAULT 0,
    batting_avg     REAL    DEFAULT 0.0,
    strike_rate     REAL    DEFAULT 0.0,
    economy_rate    REAL    DEFAULT 0.0,
    centuries       INTEGER DEFAULT 0,
    fifties         INTEGER DEFAULT 0,
    fours           INTEGER DEFAULT 0,
    sixes           INTEGER DEFAULT 0,
    catches         INTEGER DEFAULT 0,
    stumpings       INTEGER DEFAULT 0,
    -- Fantasy config
    base_price      REAL    DEFAULT 8.0,      -- in fantasy £m
    is_available    INTEGER DEFAULT 1,        -- 1=available, 0=injured/unavailable
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Player's team assignment per season
CREATE TABLE IF NOT EXISTS player_team_season (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id   INTEGER NOT NULL,
    team_id     INTEGER NOT NULL,
    season_id   INTEGER NOT NULL,
    UNIQUE(player_id, season_id),
    FOREIGN KEY(player_id) REFERENCES bpl_players(player_id),
    FOREIGN KEY(team_id)   REFERENCES bpl_teams(team_id),
    FOREIGN KEY(season_id) REFERENCES bpl_seasons(season_id)
);

CREATE TABLE IF NOT EXISTS bpl_matches (
    match_id        INTEGER PRIMARY KEY,
    season_id       INTEGER NOT NULL,
    gameweek_id     INTEGER,                  -- FK -> gameweeks
    match_number    INTEGER,
    match_type      TEXT    DEFAULT 'league', -- league|quarter|semi|final
    date            DATE,
    start_time      TIME,
    venue           TEXT,
    city            TEXT,
    team1_id        INTEGER,
    team2_id        INTEGER,
    toss_winner_id  INTEGER,
    toss_decision   TEXT,                     -- bat|field
    winner_id       INTEGER,
    win_margin      INTEGER,
    win_type        TEXT,                     -- runs|wickets|tie|no_result
    -- Innings numeric totals
    team1_runs      INTEGER DEFAULT 0,
    team1_wickets   INTEGER DEFAULT 0,
    team1_overs     REAL    DEFAULT 0.0,
    team1_fours     INTEGER DEFAULT 0,
    team1_sixes     INTEGER DEFAULT 0,
    team1_extras    INTEGER DEFAULT 0,
    team2_runs      INTEGER DEFAULT 0,
    team2_wickets   INTEGER DEFAULT 0,
    team2_overs     REAL    DEFAULT 0.0,
    team2_fours     INTEGER DEFAULT 0,
    team2_sixes     INTEGER DEFAULT 0,
    team2_extras    INTEGER DEFAULT 0,
    status          TEXT    DEFAULT 'scheduled', -- scheduled|live|completed|abandoned
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(season_id)      REFERENCES bpl_seasons(season_id),
    FOREIGN KEY(team1_id)       REFERENCES bpl_teams(team_id),
    FOREIGN KEY(team2_id)       REFERENCES bpl_teams(team_id),
    FOREIGN KEY(winner_id)      REFERENCES bpl_teams(team_id)
);
CREATE INDEX IF NOT EXISTS idx_matches_season   ON bpl_matches(season_id);
CREATE INDEX IF NOT EXISTS idx_matches_date     ON bpl_matches(date);
CREATE INDEX IF NOT EXISTS idx_matches_gw       ON bpl_matches(gameweek_id);

-- Per-match per-player numeric performance
CREATE TABLE IF NOT EXISTS player_performances (
    perf_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id        INTEGER NOT NULL,
    player_id       INTEGER NOT NULL,
    team_id         INTEGER NOT NULL,
    -- Batting
    runs_scored     INTEGER DEFAULT 0,
    balls_faced     INTEGER DEFAULT 0,
    fours           INTEGER DEFAULT 0,
    sixes           INTEGER DEFAULT 0,
    strike_rate     REAL    DEFAULT 0.0,
    not_out         INTEGER DEFAULT 0,        -- 1=not out
    -- Bowling
    overs_bowled    REAL    DEFAULT 0.0,
    wickets_taken   INTEGER DEFAULT 0,
    runs_conceded   INTEGER DEFAULT 0,
    economy_rate    REAL    DEFAULT 0.0,
    maidens         INTEGER DEFAULT 0,
    -- Fielding
    catches_taken   INTEGER DEFAULT 0,
    stumpings       INTEGER DEFAULT 0,
    run_outs        INTEGER DEFAULT 0,
    -- Batting milestones (computed flags)
    is_duck         INTEGER DEFAULT 0,
    is_fifty        INTEGER DEFAULT 0,
    is_century      INTEGER DEFAULT 0,
    -- Bowling milestones
    is_three_wickets INTEGER DEFAULT 0,
    is_five_wickets  INTEGER DEFAULT 0,
    -- Fantasy points (computed by trigger/API)
    raw_fantasy_pts REAL    DEFAULT 0.0,
    bonus_pts       REAL    DEFAULT 0.0,
    total_fantasy_pts REAL  DEFAULT 0.0,
    UNIQUE(match_id, player_id),
    FOREIGN KEY(match_id)   REFERENCES bpl_matches(match_id),
    FOREIGN KEY(player_id)  REFERENCES bpl_players(player_id),
    FOREIGN KEY(team_id)    REFERENCES bpl_teams(team_id)
);
CREATE INDEX IF NOT EXISTS idx_perf_match  ON player_performances(match_id);
CREATE INDEX IF NOT EXISTS idx_perf_player ON player_performances(player_id);

-- ============================================================
-- 3. FANTASY CONFIGURATION
-- ============================================================

-- Gameweeks (one per round of BPL fixtures)
CREATE TABLE IF NOT EXISTS gameweeks (
    gw_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    season_id       INTEGER NOT NULL,
    gw_number       INTEGER NOT NULL,
    name            TEXT,                     -- e.g. "Gameweek 17"
    deadline        DATETIME NOT NULL,        -- transfer deadline
    start_date      DATE,
    end_date        DATE,
    is_active       INTEGER DEFAULT 0,
    is_finished     INTEGER DEFAULT 0,
    avg_score       REAL    DEFAULT 0.0,      -- updated after GW completes
    highest_score   REAL    DEFAULT 0.0,
    most_captained_id INTEGER,               -- FK -> bpl_players
    most_transferred_in_id INTEGER,
    UNIQUE(season_id, gw_number),
    FOREIGN KEY(season_id) REFERENCES bpl_seasons(season_id)
);

-- Scoring rules (fully configurable by admin)
CREATE TABLE IF NOT EXISTS scoring_rules (
    rule_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    season_id       INTEGER NOT NULL,
    rule_key        TEXT    NOT NULL,
    description     TEXT    NOT NULL,
    points          REAL    NOT NULL,
    category        TEXT,                     -- batting|bowling|fielding|bonus
    is_active       INTEGER DEFAULT 1,
    UNIQUE(season_id, rule_key),
    FOREIGN KEY(season_id) REFERENCES bpl_seasons(season_id)
);

-- Team composition rules
CREATE TABLE IF NOT EXISTS team_rules (
    rule_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    season_id       INTEGER NOT NULL,
    squad_size      INTEGER DEFAULT 15,
    playing_xi      INTEGER DEFAULT 11,
    max_per_team    INTEGER DEFAULT 5,        -- max players from one BPL team
    min_batsmen     INTEGER DEFAULT 3,
    max_batsmen     INTEGER DEFAULT 6,
    min_bowlers     INTEGER DEFAULT 3,
    max_bowlers     INTEGER DEFAULT 6,
    min_all_rounders INTEGER DEFAULT 1,
    max_all_rounders INTEGER DEFAULT 4,
    min_keepers     INTEGER DEFAULT 1,
    max_keepers     INTEGER DEFAULT 2,
    total_budget    REAL    DEFAULT 100.0,    -- in £m fantasy currency
    captain_mult    REAL    DEFAULT 2.0,      -- captain gets 2x points
    vice_capt_mult  REAL    DEFAULT 1.5,      -- vice-captain gets 1.5x
    free_transfers  INTEGER DEFAULT 1,        -- free transfers per GW
    transfer_deduct REAL    DEFAULT 4.0,      -- pts deducted per extra transfer
    UNIQUE(season_id),
    FOREIGN KEY(season_id) REFERENCES bpl_seasons(season_id)
);

-- ============================================================
-- 4. FANTASY TEAMS (user squads)
-- ============================================================
CREATE TABLE IF NOT EXISTS fantasy_teams (
    ft_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    season_id       INTEGER NOT NULL,
    team_name       TEXT    NOT NULL DEFAULT 'My XI',
    budget_remaining REAL   DEFAULT 100.0,
    total_points    REAL    DEFAULT 0.0,
    overall_rank    INTEGER,
    last_gw_points  REAL    DEFAULT 0.0,
    last_gw_rank    INTEGER,
    transfers_made  INTEGER DEFAULT 0,
    is_complete     INTEGER DEFAULT 0,        -- 1 = submitted valid 15-man squad
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, season_id),
    FOREIGN KEY(user_id)   REFERENCES users(user_id),
    FOREIGN KEY(season_id) REFERENCES bpl_seasons(season_id)
);
CREATE INDEX IF NOT EXISTS idx_ft_user   ON fantasy_teams(user_id);
CREATE INDEX IF NOT EXISTS idx_ft_season ON fantasy_teams(season_id);

-- Players in a fantasy team squad (15 players)
CREATE TABLE IF NOT EXISTS fantasy_squad (
    squad_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ft_id           INTEGER NOT NULL,
    player_id       INTEGER NOT NULL,
    purchase_price  REAL    NOT NULL,         -- price at time of purchase
    is_playing_xi   INTEGER DEFAULT 0,        -- 1 = in starting 11, 0 = sub
    is_captain      INTEGER DEFAULT 0,
    is_vice_captain INTEGER DEFAULT 0,
    position_order  INTEGER DEFAULT 0,        -- 1-11 for XI, 12-15 for subs
    added_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ft_id, player_id),
    FOREIGN KEY(ft_id)     REFERENCES fantasy_teams(ft_id),
    FOREIGN KEY(player_id) REFERENCES bpl_players(player_id),
    -- Ensure only 1 captain and 1 vice captain per team
    CHECK(NOT (is_captain=1 AND is_vice_captain=1))
);
CREATE INDEX IF NOT EXISTS idx_squad_ft     ON fantasy_squad(ft_id);
CREATE INDEX IF NOT EXISTS idx_squad_player ON fantasy_squad(player_id);

-- ============================================================
-- 5. GAMEWEEK POINTS (per user team per GW)
-- ============================================================
CREATE TABLE IF NOT EXISTS gw_team_points (
    gtp_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ft_id           INTEGER NOT NULL,
    gw_id           INTEGER NOT NULL,
    -- Points breakdown
    batting_pts     REAL    DEFAULT 0.0,
    bowling_pts     REAL    DEFAULT 0.0,
    fielding_pts    REAL    DEFAULT 0.0,
    bonus_pts       REAL    DEFAULT 0.0,
    captain_bonus   REAL    DEFAULT 0.0,
    transfer_deduction REAL DEFAULT 0.0,
    total_pts       REAL    DEFAULT 0.0,
    gw_rank         INTEGER,
    calculated_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ft_id, gw_id),
    FOREIGN KEY(ft_id) REFERENCES fantasy_teams(ft_id),
    FOREIGN KEY(gw_id) REFERENCES gameweeks(gw_id)
);
CREATE INDEX IF NOT EXISTS idx_gwpts_ft ON gw_team_points(ft_id);
CREATE INDEX IF NOT EXISTS idx_gwpts_gw ON gw_team_points(gw_id);

-- Per-player points within a GW for a fantasy team
CREATE TABLE IF NOT EXISTS gw_player_points (
    gpp_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ft_id           INTEGER NOT NULL,
    gw_id           INTEGER NOT NULL,
    player_id       INTEGER NOT NULL,
    match_id        INTEGER,
    is_captain      INTEGER DEFAULT 0,
    is_vice_captain INTEGER DEFAULT 0,
    is_playing_xi   INTEGER DEFAULT 0,
    base_pts        REAL    DEFAULT 0.0,
    multiplier      REAL    DEFAULT 1.0,      -- 2x captain, 1.5x vc, 1x else
    final_pts       REAL    DEFAULT 0.0,      -- base_pts * multiplier
    UNIQUE(ft_id, gw_id, player_id),
    FOREIGN KEY(ft_id)     REFERENCES fantasy_teams(ft_id),
    FOREIGN KEY(gw_id)     REFERENCES gameweeks(gw_id),
    FOREIGN KEY(player_id) REFERENCES bpl_players(player_id),
    FOREIGN KEY(match_id)  REFERENCES bpl_matches(match_id)
);

-- ============================================================
-- 6. TRANSFERS
-- ============================================================
CREATE TABLE IF NOT EXISTS transfers (
    transfer_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    ft_id           INTEGER NOT NULL,
    gw_id           INTEGER NOT NULL,
    player_out_id   INTEGER NOT NULL,
    player_in_id    INTEGER NOT NULL,
    sell_price      REAL    NOT NULL,         -- price sold at
    buy_price       REAL    NOT NULL,         -- price bought at
    is_free         INTEGER DEFAULT 1,        -- 1=free transfer, 0=paid (deduction applies)
    deduction_pts   REAL    DEFAULT 0.0,
    transferred_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(ft_id)         REFERENCES fantasy_teams(ft_id),
    FOREIGN KEY(gw_id)         REFERENCES gameweeks(gw_id),
    FOREIGN KEY(player_out_id) REFERENCES bpl_players(player_id),
    FOREIGN KEY(player_in_id)  REFERENCES bpl_players(player_id)
);
CREATE INDEX IF NOT EXISTS idx_transfer_ft ON transfers(ft_id);
CREATE INDEX IF NOT EXISTS idx_transfer_gw ON transfers(gw_id);

-- ============================================================
-- 7. CONTESTS & LEAGUES
-- ============================================================
CREATE TABLE IF NOT EXISTS contests (
    contest_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    season_id       INTEGER NOT NULL,
    name            TEXT    NOT NULL,
    contest_type    TEXT    DEFAULT 'public', -- public|private|head2head
    entry_fee_bdt   REAL    DEFAULT 0.0,      -- 0 = free contest
    prize_pool_bdt  REAL    DEFAULT 0.0,
    max_teams       INTEGER DEFAULT 1000,
    current_teams   INTEGER DEFAULT 0,
    start_gw        INTEGER NOT NULL,
    end_gw          INTEGER NOT NULL,
    invite_code     TEXT    UNIQUE,           -- for private contests
    is_active       INTEGER DEFAULT 1,
    created_by      INTEGER,                  -- FK -> users (admin who created)
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(season_id)  REFERENCES bpl_seasons(season_id),
    FOREIGN KEY(created_by) REFERENCES users(user_id)
);

-- Teams enrolled in a contest
CREATE TABLE IF NOT EXISTS contest_entries (
    entry_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    contest_id      INTEGER NOT NULL,
    ft_id           INTEGER NOT NULL,
    user_id         INTEGER NOT NULL,
    entry_rank      INTEGER,
    total_pts       REAL    DEFAULT 0.0,
    prize_won_bdt   REAL    DEFAULT 0.0,
    joined_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(contest_id, ft_id),
    FOREIGN KEY(contest_id) REFERENCES contests(contest_id),
    FOREIGN KEY(ft_id)      REFERENCES fantasy_teams(ft_id),
    FOREIGN KEY(user_id)    REFERENCES users(user_id)
);
CREATE INDEX IF NOT EXISTS idx_entries_contest ON contest_entries(contest_id);
CREATE INDEX IF NOT EXISTS idx_entries_user    ON contest_entries(user_id);

-- Prize distribution rules per contest
CREATE TABLE IF NOT EXISTS contest_prizes (
    prize_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    contest_id      INTEGER NOT NULL,
    rank_from       INTEGER NOT NULL,
    rank_to         INTEGER NOT NULL,
    prize_bdt       REAL    NOT NULL,
    FOREIGN KEY(contest_id) REFERENCES contests(contest_id)
);

-- ============================================================
-- 8. PLAYER PRICE HISTORY (for value tracking)
-- ============================================================
CREATE TABLE IF NOT EXISTS player_price_history (
    ph_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id       INTEGER NOT NULL,
    season_id       INTEGER NOT NULL,
    gw_id           INTEGER NOT NULL,
    price           REAL    NOT NULL,
    price_change    REAL    DEFAULT 0.0,      -- +/- from previous GW
    ownership_pct   REAL    DEFAULT 0.0,      -- % of teams owning this player
    recorded_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(player_id) REFERENCES bpl_players(player_id),
    FOREIGN KEY(gw_id)     REFERENCES gameweeks(gw_id)
);
CREATE INDEX IF NOT EXISTS idx_ph_player ON player_price_history(player_id);
CREATE INDEX IF NOT EXISTS idx_ph_gw     ON player_price_history(gw_id);

-- ============================================================
-- 9. SUBSCRIPTIONS & PAYMENTS (Bcash / Nagad)
-- ============================================================
CREATE TABLE IF NOT EXISTS subscriptions (
    sub_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    payment_gateway TEXT    NOT NULL,         -- bcash|nagad
    payment_reference TEXT  UNIQUE NOT NULL,
    amount_bdt      REAL    NOT NULL DEFAULT 500.0,
    status          TEXT    DEFAULT 'pending',-- pending|completed|failed|expired|refunded
    start_date      DATE,
    expiry_date     DATE,
    gateway_txn_id  TEXT,                     -- gateway's own transaction ID
    gateway_response TEXT,                    -- raw JSON response from gateway
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);
CREATE INDEX IF NOT EXISTS idx_subs_user   ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subs_ref    ON subscriptions(payment_reference);
CREATE INDEX IF NOT EXISTS idx_subs_status ON subscriptions(status);

-- Contest entry payments
CREATE TABLE IF NOT EXISTS contest_payments (
    cp_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id        INTEGER NOT NULL,
    user_id         INTEGER NOT NULL,
    amount_bdt      REAL    NOT NULL,
    gateway         TEXT    NOT NULL,
    reference       TEXT    UNIQUE NOT NULL,
    status          TEXT    DEFAULT 'pending',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(entry_id) REFERENCES contest_entries(entry_id),
    FOREIGN KEY(user_id)  REFERENCES users(user_id)
);

-- ============================================================
-- 10. AI PREMIUM INSIGHTS
-- ============================================================
CREATE TABLE IF NOT EXISTS ai_predictions (
    pred_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id        INTEGER NOT NULL,
    season_id       INTEGER NOT NULL,
    gw_id           INTEGER,
    -- Predictions (numeric only)
    team1_win_prob      REAL DEFAULT 0.0,     -- 0.0 to 1.0
    team2_win_prob      REAL DEFAULT 0.0,
    predicted_winner_id INTEGER,
    pred_team1_score    INTEGER DEFAULT 0,
    pred_team2_score    INTEGER DEFAULT 0,
    pred_top_scorer_id  INTEGER,
    pred_top_wicket_taker_id INTEGER,
    pred_top_fielder_id INTEGER,
    -- Model metadata
    model_version   TEXT    DEFAULT '1.0',
    confidence      REAL    DEFAULT 0.0,
    features_used   TEXT,                     -- JSON: feature names used
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(match_id)               REFERENCES bpl_matches(match_id),
    FOREIGN KEY(season_id)              REFERENCES bpl_seasons(season_id),
    FOREIGN KEY(predicted_winner_id)    REFERENCES bpl_teams(team_id),
    FOREIGN KEY(pred_top_scorer_id)     REFERENCES bpl_players(player_id),
    FOREIGN KEY(pred_top_wicket_taker_id) REFERENCES bpl_players(player_id)
);

-- AI-generated player differential picks (premium)
CREATE TABLE IF NOT EXISTS ai_differential_picks (
    pick_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    gw_id           INTEGER NOT NULL,
    player_id       INTEGER NOT NULL,
    ownership_pct   REAL    DEFAULT 0.0,      -- low ownership = differential
    predicted_pts   REAL    DEFAULT 0.0,
    value_score     REAL    DEFAULT 0.0,      -- predicted_pts / price
    reason_code     TEXT,                     -- e.g. "FORM|FIXTURE|PRICE"
    confidence      REAL    DEFAULT 0.0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(gw_id)     REFERENCES gameweeks(gw_id),
    FOREIGN KEY(player_id) REFERENCES bpl_players(player_id)
);

-- ============================================================
-- 11. ADMIN & AUDIT
-- ============================================================
CREATE TABLE IF NOT EXISTS admin_log (
    log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_user_id   INTEGER NOT NULL,
    action          TEXT    NOT NULL,
    target_table    TEXT,
    target_id       INTEGER,
    old_value       TEXT,                     -- JSON snapshot
    new_value       TEXT,                     -- JSON snapshot
    ip_address      TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(admin_user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS api_request_log (
    req_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER,
    endpoint        TEXT    NOT NULL,
    method          TEXT    NOT NULL,
    status_code     INTEGER,
    response_ms     INTEGER,
    ip_address      TEXT,
    user_agent      TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_api_log_user ON api_request_log(user_id);
CREATE INDEX IF NOT EXISTS idx_api_log_time ON api_request_log(created_at);

-- ============================================================
-- 12. NOTIFICATIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS notifications (
    notif_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    type            TEXT    NOT NULL,         -- deadline|points|transfer|payment|system
    title           TEXT    NOT NULL,
    body            TEXT,
    is_read         INTEGER DEFAULT 0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);
CREATE INDEX IF NOT EXISTS idx_notif_user ON notifications(user_id);

-- ============================================================
-- 13. VIEWS (convenience queries)
-- ============================================================

-- Fantasy team overview with user info
CREATE VIEW IF NOT EXISTS v_fantasy_team_overview AS
SELECT
    ft.ft_id,
    ft.team_name,
    ft.total_points,
    ft.last_gw_points,
    ft.overall_rank,
    ft.budget_remaining,
    ft.is_complete,
    u.username,
    u.email,
    u.role,
    s.year AS season_year
FROM fantasy_teams ft
JOIN users         u ON ft.user_id   = u.user_id
JOIN bpl_seasons   s ON ft.season_id = s.season_id;

-- Current GW leaderboard
CREATE VIEW IF NOT EXISTS v_gw_leaderboard AS
SELECT
    gtp.gw_id,
    gtp.ft_id,
    gtp.total_pts,
    gtp.gw_rank,
    ft.team_name,
    u.username,
    gw.gw_number,
    gw.name AS gw_name
FROM gw_team_points gtp
JOIN fantasy_teams  ft  ON gtp.ft_id  = ft.ft_id
JOIN users          u   ON ft.user_id = u.user_id
JOIN gameweeks      gw  ON gtp.gw_id  = gw.gw_id;

-- Player ownership and value across active season
CREATE VIEW IF NOT EXISTS v_player_value AS
SELECT
    p.player_id,
    p.name,
    p.role,
    p.base_price,
    p.is_available,
    COUNT(fs.squad_id)                          AS times_owned,
    ROUND(COUNT(fs.squad_id)*100.0 /
          NULLIF((SELECT COUNT(*) FROM fantasy_teams),0),2) AS ownership_pct,
    SUM(CASE WHEN fs.is_captain=1 THEN 1 ELSE 0 END) AS captain_count
FROM bpl_players    p
LEFT JOIN fantasy_squad fs ON p.player_id = fs.player_id
GROUP BY p.player_id;

-- Active subscriptions
CREATE VIEW IF NOT EXISTS v_active_subscriptions AS
SELECT
    s.sub_id,
    s.payment_gateway,
    s.amount_bdt,
    s.status,
    s.start_date,
    s.expiry_date,
    u.username,
    u.email,
    u.phone
FROM subscriptions s
JOIN users u ON s.user_id = u.user_id
WHERE s.status = 'completed'
  AND (s.expiry_date IS NULL OR s.expiry_date >= DATE('now'));

-- ============================================================
-- 14. TRIGGERS
-- ============================================================

-- Auto-compute fantasy points when performance is inserted/updated
CREATE TRIGGER IF NOT EXISTS trg_compute_fantasy_pts
AFTER INSERT ON player_performances
BEGIN
    UPDATE player_performances
    SET total_fantasy_pts = (
        -- Batting points
        (NEW.runs_scored * 1)
        + (NEW.fours     * 1)
        + (NEW.sixes     * 2)
        + (CASE WHEN NEW.is_fifty    =1 THEN 10 ELSE 0 END)
        + (CASE WHEN NEW.is_century  =1 THEN 25 ELSE 0 END)
        + (CASE WHEN NEW.is_duck     =1 THEN -5 ELSE 0 END)
        -- SR bonus (min 10 balls faced)
        + (CASE WHEN NEW.balls_faced >= 10 AND NEW.strike_rate >= 140 THEN 6
                WHEN NEW.balls_faced >= 10 AND NEW.strike_rate >= 120 THEN 4
                WHEN NEW.balls_faced >= 10 AND NEW.strike_rate >= 100 THEN 2
                ELSE 0 END)
        -- Bowling points
        + (NEW.wickets_taken * 20)
        + (NEW.maidens       * 4)
        + (CASE WHEN NEW.is_three_wickets=1 THEN 8  ELSE 0 END)
        + (CASE WHEN NEW.is_five_wickets =1 THEN 20 ELSE 0 END)
        -- Economy bonus (min 2 overs)
        + (CASE WHEN NEW.overs_bowled >= 2 AND NEW.economy_rate <= 5.0  THEN 6
                WHEN NEW.overs_bowled >= 2 AND NEW.economy_rate <= 6.0  THEN 4
                WHEN NEW.overs_bowled >= 2 AND NEW.economy_rate <= 7.0  THEN 2
                WHEN NEW.overs_bowled >= 2 AND NEW.economy_rate >= 10.0 THEN -4
                WHEN NEW.overs_bowled >= 2 AND NEW.economy_rate >= 9.0  THEN -2
                ELSE 0 END)
        -- Fielding points
        + (NEW.catches_taken * 8)
        + (NEW.stumpings     * 12)
        + (NEW.run_outs      * 8)
    )
    WHERE perf_id = NEW.perf_id;
END;

-- Update fantasy_teams total_points when GW points added
CREATE TRIGGER IF NOT EXISTS trg_update_team_total_pts
AFTER INSERT ON gw_team_points
BEGIN
    UPDATE fantasy_teams
    SET total_points    = total_points + NEW.total_pts,
        last_gw_points  = NEW.total_pts,
        updated_at      = CURRENT_TIMESTAMP
    WHERE ft_id = NEW.ft_id;
END;

-- Auto-notify user on subscription confirmation
CREATE TRIGGER IF NOT EXISTS trg_subscription_confirmed
AFTER UPDATE OF status ON subscriptions
WHEN NEW.status = 'completed' AND OLD.status != 'completed'
BEGIN
    INSERT INTO notifications(user_id, type, title, body)
    VALUES(
        NEW.user_id,
        'payment',
        'Subscription Activated',
        'Your premium subscription is active until ' || NEW.expiry_date || '. API key issued.'
    );
END;

-- ============================================================
-- 15. SEED: SCORING RULES (BPL Fantasy Standard)
-- ============================================================
INSERT OR IGNORE INTO bpl_seasons(year,name,status) VALUES(2025,'BPL 2025','active');

INSERT OR IGNORE INTO scoring_rules(season_id,rule_key,description,points,category) VALUES
-- BATTING
(1,'bat_run',       'Run scored',                   1.0,  'batting'),
(1,'bat_four',      'Boundary (4)',                 1.0,  'batting'),
(1,'bat_six',       'Six',                          2.0,  'batting'),
(1,'bat_50',        'Half century (50+ runs)',      10.0, 'batting'),
(1,'bat_100',       'Century (100+ runs)',          25.0, 'batting'),
(1,'bat_duck',      'Duck (0 runs, dismissed)',    -5.0,  'batting'),
(1,'bat_sr_140',    'Strike rate ≥ 140 (10+ balls)',6.0,  'batting'),
(1,'bat_sr_120',    'Strike rate ≥ 120 (10+ balls)',4.0,  'batting'),
(1,'bat_sr_100',    'Strike rate ≥ 100 (10+ balls)',2.0,  'batting'),
-- BOWLING
(1,'bowl_wicket',   'Wicket taken',                20.0, 'bowling'),
(1,'bowl_maiden',   'Maiden over',                  4.0, 'bowling'),
(1,'bowl_3w',       '3 wickets in an innings',      8.0, 'bowling'),
(1,'bowl_5w',       '5 wickets in an innings',     20.0, 'bowling'),
(1,'bowl_econ_5',   'Economy ≤ 5.0 (2+ overs)',     6.0, 'bowling'),
(1,'bowl_econ_6',   'Economy ≤ 6.0 (2+ overs)',     4.0, 'bowling'),
(1,'bowl_econ_7',   'Economy ≤ 7.0 (2+ overs)',     2.0, 'bowling'),
(1,'bowl_econ_9',   'Economy ≥ 9.0 (2+ overs)',    -2.0, 'bowling'),
(1,'bowl_econ_10',  'Economy ≥ 10.0 (2+ overs)',   -4.0, 'bowling'),
-- FIELDING
(1,'field_catch',   'Catch',                        8.0, 'fielding'),
(1,'field_stumping','Stumping (WK only)',           12.0, 'fielding'),
(1,'field_runout',  'Run out (direct)',              8.0, 'fielding'),
-- BONUS
(1,'bonus_captain', 'Captain multiplier',           2.0, 'bonus'),
(1,'bonus_vc',      'Vice-captain multiplier',      1.5, 'bonus'),
(1,'bonus_transfer','Extra transfer deduction',    -4.0, 'bonus');

-- SEED: Default team rules
INSERT OR IGNORE INTO team_rules(season_id) VALUES(1);

-- SEED: Gameweeks 1-17
INSERT OR IGNORE INTO gameweeks(season_id,gw_number,name,deadline,is_active,is_finished) VALUES
(1,1,'Gameweek 1','2025-01-03 17:00:00',0,1),(1,2,'Gameweek 2','2025-01-07 17:00:00',0,1),
(1,3,'Gameweek 3','2025-01-10 17:00:00',0,1),(1,4,'Gameweek 4','2025-01-14 17:00:00',0,1),
(1,5,'Gameweek 5','2025-01-17 17:00:00',0,1),(1,6,'Gameweek 6','2025-01-21 17:00:00',0,1),
(1,7,'Gameweek 7','2025-01-24 17:00:00',0,1),(1,8,'Gameweek 8','2025-01-28 17:00:00',0,1),
(1,9,'Gameweek 9','2025-01-31 17:00:00',0,1),(1,10,'Gameweek 10','2025-02-04 17:00:00',0,1),
(1,11,'Gameweek 11','2025-02-07 17:00:00',0,1),(1,12,'Gameweek 12','2025-02-11 17:00:00',0,1),
(1,13,'Gameweek 13','2025-02-14 17:00:00',0,1),(1,14,'Gameweek 14','2025-02-18 17:00:00',0,1),
(1,15,'Gameweek 15','2025-02-21 17:00:00',0,1),(1,16,'Gameweek 16','2025-02-25 17:00:00',0,1),
(1,17,'Gameweek 17','2025-12-20 17:00:00',1,0);
