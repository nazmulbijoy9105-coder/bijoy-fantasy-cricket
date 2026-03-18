-- ============================================================
-- BPL API Project — Database Schema
-- Numeric stats only. No copyrighted text/commentary.
-- Governance: GDPR-aligned, role-based access at API layer.
-- ============================================================
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- USERS & AUTH
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    UNIQUE NOT NULL,
    email       TEXT    UNIQUE NOT NULL,
    password    TEXT    NOT NULL,
    role        TEXT    NOT NULL DEFAULT 'free',
    api_key     TEXT    UNIQUE,
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- SUBSCRIPTIONS
CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           INTEGER NOT NULL,
    plan              TEXT    NOT NULL DEFAULT 'monthly',
    payment_gateway   TEXT    NOT NULL,
    payment_reference TEXT    UNIQUE NOT NULL,
    status            TEXT    NOT NULL DEFAULT 'pending',
    amount_bdt        REAL    NOT NULL,
    start_date        DATE,
    expiry_date       DATE,
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- SEASONS
CREATE TABLE IF NOT EXISTS seasons (
    season_id   INTEGER PRIMARY KEY,
    year        INTEGER NOT NULL UNIQUE,
    start_date  DATE,
    end_date    DATE,
    num_teams   INTEGER,
    num_matches INTEGER
);

-- TEAMS
CREATE TABLE IF NOT EXISTS teams (
    team_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    abbreviation    TEXT    NOT NULL,
    home_city       TEXT,
    seasons_active  TEXT,
    total_matches   INTEGER DEFAULT 0,
    total_wins      INTEGER DEFAULT 0,
    total_losses    INTEGER DEFAULT 0,
    titles_won      INTEGER DEFAULT 0
);

-- PLAYERS
CREATE TABLE IF NOT EXISTS players (
    player_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    nationality     TEXT,
    role            TEXT,
    batting_style   TEXT,
    bowling_style   TEXT,
    dob             DATE,
    is_overseas     INTEGER DEFAULT 0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- PLAYER CAREER STATS
CREATE TABLE IF NOT EXISTS player_career_stats (
    stat_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id       INTEGER NOT NULL UNIQUE,
    matches         INTEGER DEFAULT 0,
    innings_bat     INTEGER DEFAULT 0,
    runs            INTEGER DEFAULT 0,
    balls_faced     INTEGER DEFAULT 0,
    highest_score   INTEGER DEFAULT 0,
    not_outs        INTEGER DEFAULT 0,
    fours           INTEGER DEFAULT 0,
    sixes           INTEGER DEFAULT 0,
    fifties         INTEGER DEFAULT 0,
    centuries       INTEGER DEFAULT 0,
    batting_avg     REAL    DEFAULT 0.0,
    strike_rate     REAL    DEFAULT 0.0,
    innings_bowl    INTEGER DEFAULT 0,
    overs_bowled    REAL    DEFAULT 0.0,
    balls_bowled    INTEGER DEFAULT 0,
    runs_conceded   INTEGER DEFAULT 0,
    wickets         INTEGER DEFAULT 0,
    best_bowling    TEXT,
    bowling_avg     REAL    DEFAULT 0.0,
    economy         REAL    DEFAULT 0.0,
    bowling_sr      REAL    DEFAULT 0.0,
    four_wickets    INTEGER DEFAULT 0,
    five_wickets    INTEGER DEFAULT 0,
    catches         INTEGER DEFAULT 0,
    stumpings       INTEGER DEFAULT 0,
    run_outs        INTEGER DEFAULT 0,
    FOREIGN KEY(player_id) REFERENCES players(player_id) ON DELETE CASCADE
);

-- PLAYER SEASON STATS
CREATE TABLE IF NOT EXISTS player_season_stats (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id       INTEGER NOT NULL,
    season_id       INTEGER NOT NULL,
    team_id         INTEGER NOT NULL,
    matches         INTEGER DEFAULT 0,
    runs            INTEGER DEFAULT 0,
    balls_faced     INTEGER DEFAULT 0,
    fours           INTEGER DEFAULT 0,
    sixes           INTEGER DEFAULT 0,
    fifties         INTEGER DEFAULT 0,
    centuries       INTEGER DEFAULT 0,
    batting_avg     REAL    DEFAULT 0.0,
    strike_rate     REAL    DEFAULT 0.0,
    wickets         INTEGER DEFAULT 0,
    overs_bowled    REAL    DEFAULT 0.0,
    runs_conceded   INTEGER DEFAULT 0,
    economy         REAL    DEFAULT 0.0,
    bowling_avg     REAL    DEFAULT 0.0,
    catches         INTEGER DEFAULT 0,
    stumpings       INTEGER DEFAULT 0,
    UNIQUE(player_id, season_id),
    FOREIGN KEY(player_id) REFERENCES players(player_id),
    FOREIGN KEY(season_id) REFERENCES seasons(season_id),
    FOREIGN KEY(team_id)   REFERENCES teams(team_id)
);

-- MATCHES
CREATE TABLE IF NOT EXISTS matches (
    match_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    season_id       INTEGER NOT NULL,
    match_number    INTEGER,
    match_type      TEXT DEFAULT 'league',
    date            DATE,
    venue           TEXT,
    city            TEXT,
    team1_id        INTEGER NOT NULL,
    team2_id        INTEGER NOT NULL,
    toss_winner_id  INTEGER,
    toss_decision   TEXT,
    winner_id       INTEGER,
    win_margin      INTEGER,
    win_by          TEXT,
    dl_applied      INTEGER DEFAULT 0,
    no_result       INTEGER DEFAULT 0,
    team1_score     INTEGER,
    team1_wickets   INTEGER,
    team1_overs     REAL,
    team2_score     INTEGER,
    team2_wickets   INTEGER,
    team2_overs     REAL,
    FOREIGN KEY(season_id)      REFERENCES seasons(season_id),
    FOREIGN KEY(team1_id)       REFERENCES teams(team_id),
    FOREIGN KEY(team2_id)       REFERENCES teams(team_id),
    FOREIGN KEY(winner_id)      REFERENCES teams(team_id)
);

-- INNINGS
CREATE TABLE IF NOT EXISTS innings (
    innings_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id        INTEGER NOT NULL,
    innings_number  INTEGER NOT NULL,
    batting_team_id INTEGER NOT NULL,
    bowling_team_id INTEGER NOT NULL,
    total_runs      INTEGER DEFAULT 0,
    total_wickets   INTEGER DEFAULT 0,
    total_overs     REAL    DEFAULT 0.0,
    total_balls     INTEGER DEFAULT 0,
    extras          INTEGER DEFAULT 0,
    wides           INTEGER DEFAULT 0,
    no_balls        INTEGER DEFAULT 0,
    byes            INTEGER DEFAULT 0,
    leg_byes        INTEGER DEFAULT 0,
    FOREIGN KEY(match_id) REFERENCES matches(match_id)
);

-- BATTING PERFORMANCES
CREATE TABLE IF NOT EXISTS batting_performances (
    perf_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    innings_id      INTEGER NOT NULL,
    match_id        INTEGER NOT NULL,
    player_id       INTEGER NOT NULL,
    batting_order   INTEGER,
    runs            INTEGER DEFAULT 0,
    balls           INTEGER DEFAULT 0,
    fours           INTEGER DEFAULT 0,
    sixes           INTEGER DEFAULT 0,
    strike_rate     REAL    DEFAULT 0.0,
    is_not_out      INTEGER DEFAULT 0,
    dismissal_type  TEXT,
    FOREIGN KEY(innings_id) REFERENCES innings(innings_id),
    FOREIGN KEY(match_id)   REFERENCES matches(match_id),
    FOREIGN KEY(player_id)  REFERENCES players(player_id)
);

-- BOWLING PERFORMANCES
CREATE TABLE IF NOT EXISTS bowling_performances (
    perf_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    innings_id      INTEGER NOT NULL,
    match_id        INTEGER NOT NULL,
    player_id       INTEGER NOT NULL,
    overs           REAL    DEFAULT 0.0,
    balls_bowled    INTEGER DEFAULT 0,
    runs_conceded   INTEGER DEFAULT 0,
    wickets         INTEGER DEFAULT 0,
    maidens         INTEGER DEFAULT 0,
    wides           INTEGER DEFAULT 0,
    no_balls        INTEGER DEFAULT 0,
    economy         REAL    DEFAULT 0.0,
    FOREIGN KEY(innings_id) REFERENCES innings(innings_id),
    FOREIGN KEY(match_id)   REFERENCES matches(match_id),
    FOREIGN KEY(player_id)  REFERENCES players(player_id)
);

-- AI PREDICTIONS (premium)
CREATE TABLE IF NOT EXISTS ai_predictions (
    pred_id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id                 INTEGER,
    model_version            TEXT,
    predicted_winner_id      INTEGER,
    win_probability          REAL,
    predicted_top_scorer_id  INTEGER,
    predicted_top_wicket_id  INTEGER,
    expected_score_team1     INTEGER,
    expected_score_team2     INTEGER,
    confidence               REAL,
    features_json            TEXT,
    created_at               DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(match_id) REFERENCES matches(match_id)
);

-- INDEXES
CREATE INDEX IF NOT EXISTS idx_player_season ON player_season_stats(player_id, season_id);
CREATE INDEX IF NOT EXISTS idx_batting_match  ON batting_performances(match_id);
CREATE INDEX IF NOT EXISTS idx_bowling_match  ON bowling_performances(match_id);
CREATE INDEX IF NOT EXISTS idx_matches_season ON matches(season_id);
CREATE INDEX IF NOT EXISTS idx_sub_user       ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_sub_status     ON subscriptions(status);
