from pathlib import Path


def test_how_it_works_faq_content():
    html = (Path(__file__).resolve().parent / "how_it_works_faq.html").read_text(encoding="utf-8")
    assert "Requester Flow" in html
    assert "Worker &amp; Agent Flow" in html
    assert "verifiable deliverables" in html.lower()
    assert "footer" in html
