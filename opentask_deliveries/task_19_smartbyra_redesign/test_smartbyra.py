from pathlib import Path


def test_smartbyra_redesign_meets_all_criteria():
    html = (Path(__file__).resolve().parent / "smartbyra_redesign.html").read_text(encoding="utf-8")
    assert html.count("<svg") >= 2
    assert "Smartbyrå" in html or "smartbyrå" in html
    assert "799 kr/mnd + mva" in html
    assert "Få gratis forslag" in html
    assert "Designrasjonale" in html
