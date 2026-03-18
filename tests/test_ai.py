from ai.predictions import _safe_div, _player_fantasy_score, compare_players

def test_safe_div():       assert _safe_div(10, 4) == 2.5
def test_safe_div_zero():  assert _safe_div(10, 0) == 0.0

def test_fantasy_score():
    p = {"runs":500,"centuries":2,"fifties":4,"sixes":20,"fours":60,
         "wickets":0,"five_wickets":0,"catches":5,"stumpings":0,"run_outs":0,
         "economy":0.0,"strike_rate":140.0}
    assert _player_fantasy_score(p) > 0

def test_compare_players():
    p1 = {"player_id":1,"name":"Shakib","role":"All-Rounder","matches_played":100,
          "runs":3000,"batting_avg":30.0,"strike_rate":120.0,"centuries":2,"fifties":20,
          "sixes":100,"wickets":80,"economy":6.5,"bowling_avg":20.0,"catches":50,
          "stumpings":0,"run_outs":5,"fantasy_price":9.5,"five_wickets":1}
    p2 = {"player_id":2,"name":"Tamim","role":"Batsman","matches_played":100,
          "runs":3500,"batting_avg":35.0,"strike_rate":118.0,"centuries":3,"fifties":25,
          "sixes":80,"wickets":0,"economy":0.0,"bowling_avg":0.0,"catches":30,
          "stumpings":0,"run_outs":4,"fantasy_price":8.5,"five_wickets":0}
    result = compare_players(p1, p2)
    assert "fantasy_recommendation" in result
    assert result["player1"]["name"] == "Shakib"
