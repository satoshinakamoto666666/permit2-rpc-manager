from fomc_probability_model import compute_fomc_september_probabilities


def test_fomc_model_contains_required_criteria():
    res = compute_fomc_september_probabilities()
    assert "thesis_论点" in res
    assert "evidence_依据" in res
    assert "probabilities_百分比" in res
    probs = res["probabilities_百分比"]
    assert probs["total_pct"] == 100.0
    assert 0.0 < probs["加息25个基点_hike_25bps_pct"] < 15.0
    assert probs["降息25个基点_cut_25bps_pct"] > probs["加息25个基点_hike_25bps_pct"]
