import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from creator_provenance import backfill_task_provenance, resolve_creator_provenance


def test_creator_provenance_and_backfill():
    # OpenClaw posting via API token under a human account must resolve as "Created by agent"
    prov = resolve_creator_provenance({"auth_type": "api_token", "profile_kind": "human"})
    assert prov["creatorKind"] == "agent"
    assert prov["displayLabel"] == "Created by agent"

    human_prov = resolve_creator_provenance({"auth_type": "session", "profile_kind": "human"})
    assert human_prov["displayLabel"] == "Created by human"

    migrated = backfill_task_provenance(
        [
            {"id": "t1", "owner": {"kind": "human"}, "createdVia": "openclaw"},
            {"id": "t2", "owner": {"kind": "human"}, "createdVia": "browser"},
        ]
    )
    assert migrated[0]["displayLabel"] == "Created by agent"
    assert migrated[1]["displayLabel"] == "Created by human"
