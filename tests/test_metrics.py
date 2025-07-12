import pytest
from prometheus_client.parser import text_string_to_metric_families

@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    # Hit a regular endpoint to generate metrics
    resp = await client.get("/neos")
    assert resp.status_code == 200

    metrics_resp = await client.get("/metrics")
    assert metrics_resp.status_code == 200
    body = metrics_resp.text
    assert "http_requests_total" in body
    assert "http_request_latency_seconds" in body

    found_count = False
    found_latency = False
    for family in text_string_to_metric_families(body):
        if family.name == "http_requests":
            for sample in family.samples:
                if sample.name == "http_requests_total":
                    assert sample.value > 0
                    found_count = True
        if family.name == "http_request_latency_seconds":
            for sample in family.samples:
                if sample.name.endswith("_count"):
                    assert sample.value > 0
                    found_latency = True
    assert found_count and found_latency
