import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from zero_bureaucracy_kpi_framework import CORE_KPI_LIBRARY, ZeroBureaucracyScoringEngine


def test_zero_bureaucracy_kpi_library_and_scoring():
    engine = ZeroBureaucracyScoringEngine()
    assert len(CORE_KPI_LIBRARY) == 12
    dimensions = {k.dimension for k in CORE_KPI_LIBRARY}
    assert dimensions == {"Speed", "Effort", "Automation", "Duplication", "Friction"}

    result = engine.evaluate_client(
        observations={"ZB-SPD-01": 2.0, "ZB-AUT-01": 85.0, "ZB-DUP-01": 0.0},
        custom_targets={"ZB-SPD-01": 3.0},
    )
    assert 0.0 <= result["composite_zero_bureaucracy_index"] <= 100.0
    csv_table = engine.export_excel_ready_csv()
    assert "ZB-SPD-01" in csv_table
    assert len(csv_table.strip().splitlines()) == 13
