"""Offline tests: simulated responses are written only under pytest temporary folders."""

import json
from pathlib import Path
from unittest.mock import MagicMock
from urllib.error import HTTPError

import pytest

from examples.llm_client import ModelClient, parse_response
from examples.run_llm_variants import (
    BASELINE_INSTRUCTIONS, STRUCTURED_INSTRUCTIONS, load_cases, run_experiment
)

def dataset(tmp_path):
    path = tmp_path / "benchmark.jsonl"
    cases = [{"id": f"case_{i:02}", "input_prompt": f"Ticket {i}", "expected_output": {"label": "Billing"},
              "task_type": "classification", "difficulty": "normal", "slice_category": "billing"}
             for i in range(30)]
    path.write_text("".join(json.dumps(case) + "\n" for case in cases), encoding="utf-8")
    return path, cases

class FakeClient:
    model = "fixed-test-model"
    base_url = "https://example.invalid/v1"
    temperature = 0
    max_tokens = 64

    def __init__(self, failures=8):
        self.failures = failures
        self.calls = []

    def call(self, instructions, prompt):
        self.calls.append((instructions, prompt))
        index = int(prompt.split()[-1])
        label = "Other" if instructions == BASELINE_INSTRUCTIONS and index < self.failures else "Billing"
        text = label if instructions == BASELINE_INSTRUCTIONS else json.dumps({"label": label})
        return {"raw_output": text, "parsed_output": parse_response(text), "token_count": 3,
                "usage": {"total_tokens": 3}, "latency_ms": 12.5, "response_model": self.model,
                "response_id": str(len(self.calls)), "finish_reason": "stop",
                "request": {"model": self.model, "temperature": self.temperature, "max_tokens": self.max_tokens,
                            "messages": [{"role": "user", "content": instructions + "\n" + prompt}]}}

@pytest.mark.parametrize("content,expected", [
    ("Billing", {"label": "Billing"}), ('{"label":"Technical"}', {"label": "Technical"}),
    ("Here is Billing", None), ('["Billing"]', None), ("not JSON", None)])
def test_shared_parser(content, expected):
    assert parse_response(content) == expected

def test_real_adapter_preserves_output_usage_and_request(monkeypatch):
    response = MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps({
        "model": "fixed-model", "id": "request-1", "usage": {"total_tokens": 7},
        "choices": [{"message": {"content": "Billing"}, "finish_reason": "stop"}]}).encode()
    transport = MagicMock(return_value=response)
    monkeypatch.setattr("examples.llm_client.urlopen", transport)
    client = ModelClient("test-secret", "fixed-model", "https://example.invalid/v1", delay=0)
    result = client.call(BASELINE_INSTRUCTIONS, "My bill is wrong")
    assert result["raw_output"] == "Billing" and result["token_count"] == 7
    payload = json.loads(transport.call_args.args[0].data)
    assert payload["temperature"] == 0 and payload["max_tokens"] == 64
    assert "expected_output" not in json.dumps(payload)
    assert "test-secret" not in json.dumps(result)

@pytest.mark.parametrize("model", ["default", "fast", "pro", "auto"])
def test_random_routing_alias_rejected(model):
    with pytest.raises(ValueError, match="fixed"):
        ModelClient("secret", model, "https://example.invalid/v1")

def test_api_error_does_not_leak_body_or_key(monkeypatch):
    def failed(*args, **kwargs):
        raise HTTPError("https://example.invalid", 401, "test-secret", None, None)
    monkeypatch.setattr("examples.llm_client.urlopen", failed)
    with pytest.raises(RuntimeError) as error:
        ModelClient("test-secret", "fixed", "https://example.invalid/v1").call("Classify", "ticket")
    assert str(error.value) == "LLM request failed: HTTP 401"

def test_full_workflow_freezes_and_reruns_same_eight(tmp_path):
    path, cases = dataset(tmp_path)
    client = FakeClient()
    status = run_experiment(client, path, tmp_path)
    assert status["status"] == "complete"
    assert len(client.calls) == 76  # 30 + 30 + 8 before + 8 after; no cached regression calls.
    frozen = json.loads((tmp_path / "regression/regression_8cases.json").read_text())
    assert len(frozen) == 8
    for case in frozen:
        original = next(row for row in cases if row["id"] == case["original_case_id"])
        assert case["input_prompt"] == original["input_prompt"]
        assert case["expected_output"] == original["expected_output"]
        assert case["previous_prediction"] == {"label": "Other"}
    before_prompts = [prompt for _, prompt in client.calls[60:68]]
    after_prompts = [prompt for _, prompt in client.calls[68:76]]
    assert before_prompts == after_prompts == [case["input_prompt"] for case in frozen]
    comparison = json.loads((tmp_path / "regression/regression_comparison.json").read_text())
    assert comparison["before_correct"] == 0 and comparison["after_correct"] == 8
    assert (comparison["improved"], comparison["unchanged"], comparison["regressed"]) == (8, 0, 0)
    report = json.loads((tmp_path / "results/llm_comparison_report.json").read_text())
    for name in ("llm_variant_a", "llm_variant_b"):
        records = [json.loads(line) for line in (tmp_path / f"results/{name}_results.jsonl").read_text().splitlines()]
        assert len(records) == 30
        assert all(record["latency_ms"] == 12.5 for record in records)
        metrics = report["model_results"][name]
        assert metrics["total_cases"] == 30 and metrics["precision"] is not None
        assert metrics["difficulty_results"] and metrics["category_results"]
        assert report["token_usage"][name]["reported_total_tokens"] == 90
    assert len((tmp_path / "results/llm_requests.jsonl").read_text().splitlines()) == 76

def test_fewer_than_eight_failures_is_not_fabricated(tmp_path):
    path, _ = dataset(tmp_path)
    status = run_experiment(FakeClient(failures=2), path, tmp_path)
    assert status["status"] == "regression_incomplete"
    assert status["baseline_failures"] == 2
    assert not (tmp_path / "regression/regression_8cases.json").exists()
    assert not (tmp_path / "regression/regression_comparison.json").exists()

def test_existing_experiment_not_overwritten(tmp_path):
    path, _ = dataset(tmp_path)
    folder = tmp_path / "results"
    folder.mkdir()
    saved = folder / "llm_variant_a_results.jsonl"
    saved.write_text("keep original")
    client = FakeClient()
    with pytest.raises(ValueError, match="already exist"):
        run_experiment(client, path, tmp_path)
    assert saved.read_text() == "keep original" and not client.calls

def test_model_change_aborts_comparison(tmp_path):
    path, _ = dataset(tmp_path)
    client = FakeClient()
    original = client.call
    def changing(instructions, prompt):
        result = original(instructions, prompt)
        if len(client.calls) > 1:
            result["response_model"] = "another-model"
        return result
    client.call = changing
    with pytest.raises(RuntimeError, match="changed"):
        run_experiment(client, path, tmp_path)
    status = json.loads((tmp_path / "results/llm_run_status.json").read_text())
    assert status["status"] == "failed"
    assert not (tmp_path / "results/llm_comparison_report.json").exists()

def test_wrong_case_count_stops_before_model_call(tmp_path):
    path, _ = dataset(tmp_path)
    path.write_text("\n".join(path.read_text().splitlines()[:29]))
    with pytest.raises(ValueError, match="exactly 30"):
        load_cases(path)

def test_api_failure_stops_without_thirty_fake_error_records(tmp_path):
    path, _ = dataset(tmp_path)
    client = FakeClient()
    client.call = MagicMock(side_effect=RuntimeError("HTTP 403"))
    with pytest.raises(RuntimeError):
        run_experiment(client, path, tmp_path)
    client.call.assert_called_once()
    assert not (tmp_path / "results/llm_variant_a_results.jsonl").exists()
