import json
from pathlib import Path
from openapi_agent import OpenAPISpecAgent, build_reference_marketplace_spec


def test_build_and_lint_reference_spec():
    spec, yaml_text, report = build_reference_marketplace_spec()
    assert report["valid"] is True
    assert report["error_count"] == 0
    assert report["warning_count"] == 0
    assert report["paths_count"] == 5
    assert report["operations_count"] == 6
    assert 'openapi: "3.0.3"' in yaml_text
    assert "HttpError400:" in yaml_text
    assert "HttpError429:" in yaml_text
    assert len(yaml_text.splitlines()) >= 350


def test_analyze_python_routes():
    sample_code = '''
from fastapi import FastAPI
app = FastAPI()

@app.get("/users/{user_id}")
def get_user_profile(user_id: str):
    """Fetch a user profile by ID."""
    return {"id": user_id}

@app.post("/users")
def create_user():
    """Create a new user account."""
    return {"ok": True}
'''
    agent = OpenAPISpecAgent(openapi_version="3.1.0")
    endpoints = agent.analyze_python_routes(sample_code)
    assert len(endpoints) == 2
    assert endpoints[0].operation_id == "get_user_profile"
    assert endpoints[0].parameters[0].name == "user_id"
    spec = agent.build_spec_dict(endpoints)
    lint = agent.lint_spec(spec)
    assert lint["valid"] is True
    assert lint["openapi_version"] == "3.1.0"
