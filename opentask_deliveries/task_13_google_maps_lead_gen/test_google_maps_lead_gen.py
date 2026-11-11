import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from google_maps_lead_gen import GoogleMapsLeadGenEngine


def test_google_maps_lead_gen_dedup_and_export():
    engine = GoogleMapsLeadGenEngine()
    sample_places = [
        {
            "place_id": "ChIJ_001",
            "name": "Apex Crypto Cafe",
            "formatted_address": "100 Main St, Austin, TX",
            "formatted_phone_number": "+1 (512) 555-0199",
            "website": "https://www.apexcafe.io/menu",
            "rating": 4.8,
            "user_ratings_total": 120,
            "types": ["cafe", "food"],
        },
        {
            "place_id": "ChIJ_001",  # Duplicate
            "name": "Apex Crypto Cafe",
        },
    ]
    leads = engine.process_places_payload(sample_places)
    assert len(leads) == 1
    assert leads[0].domain == "apexcafe.io"
    assert leads[0].lead_score == 100
    assert leads[0].qualification_tier == "A_HOT"
    csv_out = engine.to_csv(leads)
    assert "Apex Crypto Cafe" in csv_out
    json_out = json.loads(engine.to_json(leads))
    assert json_out[0]["place_id"] == "ChIJ_001"
