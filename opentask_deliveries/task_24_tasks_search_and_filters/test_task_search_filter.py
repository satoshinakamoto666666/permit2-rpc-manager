import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from task_search_filter import TaskFilterState, filter_and_sort_tasks


def test_task_search_filter_and_url_persistence():
    tasks = [
        {"id": "1", "title": "Python CSV Parser", "description": "Parse CSV", "skillsTags": ["python"], "budgetText": "100 USDC", "status": "open", "createdAt": "2026-11-09"},
        {"id": "2", "title": "OpenAPI Agent", "description": "Write YAML", "skillsTags": ["openapi", "python"], "budgetText": "500 USDC", "status": "open", "createdAt": "2026-11-10"},
        {"id": "3", "title": "Closed Task", "description": "Old", "skillsTags": ["python"], "budgetText": "10 USDC", "status": "closed", "createdAt": "2026-11-01"},
    ]
    state = TaskFilterState.from_query_string("?q=openapi&skill=python&status=open&sort=newest")
    res = filter_and_sort_tasks(tasks, state)
    assert res["count"] == 1
    assert res["tasks"][0]["id"] == "2"
    assert "q=openapi" in res["url_query"]
