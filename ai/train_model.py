"""
ai/train_model.py
Train a scikit-learn Random Forest model on BPL numeric match data.
Run: python -m ai.train_model
Saves model to ai/bpl_model.pkl
"""

import pickle
import numpy as np
from pathlib import Path

try:
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

from ..api.database import query_db

MODEL_PATH = Path(__file__).parent / "bpl_model.pkl"


def build_features(match_rows: list[dict]) -> tuple:
    """
    Convert match records into numeric feature matrix.
    Features: team win rates, avg NRR, avg runs, avg wickets per game.
    Label: 1 if team1 won, 0 if team2 won.
    """
    X, y = [], []
    for m in match_rows:
        if not m.get("winner_id"):
            continue
        t1 = m["team1_id"]
        t2 = m["team2_id"]
        # Aggregate stats up to this match (avoid leakage: only prior seasons)
        def team_stats(tid, before_season):
            r = query_db(
                """SELECT AVG(CAST(wins AS FLOAT)/(wins+losses+0.001)) as wr,
                          AVG(net_run_rate) as nrr,
                          AVG(CAST(runs_scored AS FLOAT)/NULLIF(matches_played,0)) as rpo
                   FROM team_season_stats
                   WHERE team_id=? AND season < ?""",
                (tid, before_season),
            )
            row = r[0] if r else {}
            return [
                row.get("wr") or 0.5,
                row.get("nrr") or 0.0,
                row.get("rpo") or 140.0,
            ]

        season = m.get("season", 9999)
        f1 = team_stats(t1, season)
        f2 = team_stats(t2, season)
        X.append(f1 + f2)
        y.append(1 if m["winner_id"] == t1 else 0)

    return np.array(X), np.array(y)


def train():
    if not ML_AVAILABLE:
        print("[train] scikit-learn not installed. Run: pip install scikit-learn pandas")
        return

    matches = query_db("SELECT * FROM matches WHERE winner_id IS NOT NULL ORDER BY date")
    if len(matches) < 20:
        print(f"[train] Only {len(matches)} completed matches found. Need at least 20 to train.")
        return

    X, y = build_features(matches)
    if len(X) < 10:
        print("[train] Not enough feature rows after filtering.")
        return

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    clf = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42)
    clf.fit(X_train_s, y_train)

    acc = accuracy_score(y_test, clf.predict(X_test_s))
    print(f"[train] Accuracy: {acc:.3f} on {len(X_test)} test matches")

    with open(MODEL_PATH, "wb") as f:
        pickle.dump({"model": clf, "scaler": scaler, "accuracy": acc}, f)
    print(f"[train] Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    train()
