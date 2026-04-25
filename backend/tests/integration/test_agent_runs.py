from fastapi.testclient import TestClient


def test_create_and_list_runs(client: TestClient) -> None:
    create_response = client.post(
        "/v1/agent-runs",
        json={"agent_name": "research-agent", "input": {"topic": "monorepos"}},
    )
    list_response = client.get("/v1/agent-runs")

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["agent_name"] == "research-agent"

    assert list_response.status_code == 200
    assert any(run["run_id"] == created["run_id"] for run in list_response.json())
