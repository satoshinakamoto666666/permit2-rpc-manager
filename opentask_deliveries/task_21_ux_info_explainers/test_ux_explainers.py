import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ux_explainers import EXPLAINER_CATALOG, render_accessible_explainer


def test_ux_explainers_cover_all_five_concepts():
    assert set(EXPLAINER_CATALOG.keys()) == {
        "bid",
        "contract",
        "deliverable_url",
        "off_platform_payment",
        "api_token_scopes",
    }
    html_snippet = render_accessible_explainer("deliverable_url")
    assert 'role="tooltip"' in html_snippet
    assert 'tabindex="0"' in html_snippet
