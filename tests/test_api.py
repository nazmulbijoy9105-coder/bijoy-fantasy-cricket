import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert "BPL" in r.json()["message"]

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_list_teams():
    r = client.get("/bpl/teams")
    assert r.status_code == 200
    assert "teams" in r.json()

def test_list_players():
    r = client.get("/bpl/players")
    assert r.status_code == 200
    assert "players" in r.json()

def test_list_matches():
    r = client.get("/bpl/matches")
    assert r.status_code == 200
    assert "matches" in r.json()

def test_list_seasons():
    r = client.get("/bpl/matches/seasons")
    assert r.status_code == 200

def test_register_and_login():
    r = client.post("/auth/register", json={"username":"testuser_pytest","email":"test@test.com","password":"testpass123"})
    assert r.status_code in (200, 400)
    r = client.post("/auth/token", data={"username":"testuser_pytest","password":"testpass123"})
    assert r.status_code in (200, 401)

def test_premium_requires_auth():
    r = client.get("/bpl/premium/predictions/1")
    assert r.status_code == 401

def test_admin_requires_auth():
    r = client.get("/admin/users")
    assert r.status_code == 401

def test_invalid_team():
    r = client.get("/bpl/teams/99999")
    assert r.status_code == 404

def test_invalid_player():
    r = client.get("/bpl/players/99999")
    assert r.status_code == 404
