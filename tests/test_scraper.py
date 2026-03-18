from scraper.utils import safe_int, safe_float, parse_overs

def test_safe_int_normal():   assert safe_int("42") == 42
def test_safe_int_comma():    assert safe_int("1,234") == 1234
def test_safe_int_slash():    assert safe_int("4/18") == 4
def test_safe_int_invalid():  assert safe_int("DNB") == 0
def test_safe_float_normal(): assert safe_float("7.25") == 7.25
def test_safe_float_invalid():assert safe_float("-") == 0.0
def test_parse_overs():       assert abs(parse_overs("18.4") - 18.667) < 0.01
