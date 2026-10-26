import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
from analytics.benchmark_runner import BenchmarkRunner


BENCHMARK_PATH = ROOT / "benchmark_data" / "baseline_30cases.jsonl"
RESULTS_PATH = ROOT / "results"


def classify_baseline(prompt: str) -> str:
    text = prompt.lower()
    if any(word in text for word in ("bill", "payment", "invoice", "refund", "subscription")):
        return "Billing"
    if any(word in text for word in ("account", "login", "password", "username", "authentication")):
        return "Account"
    if any(word in text for word in ("app", "error", "loading", "crash", "feature", "technical")):
        return "Technical"
    return "Other"


def classify_explicit_rules(prompt: str) -> str:
    text = prompt.lower()
    if any(word in text for word in ("login", "password", "username", "authentication", "账户")):
        return "Account"
    if any(word in text for word in ("bill", "payment", "invoice", "refund", "subscription", "factura")):
        return "Billing"
    if any(word in text for word in ("app", "error", "loading", "crash", "feature", "404", "export")):
        return "Technical"
    return "Other"


def make_model(classifier):
    def model_fn(prompt: str) -> dict:
        label = classifier(prompt)
        return {"raw_output": label, "parsed_output": {"label": label}}

    return model_fn


def main() -> None:
    RESULTS_PATH.mkdir(parents=True, exist_ok=True)
    runner = BenchmarkRunner(str(BENCHMARK_PATH), str(RESULTS_PATH))
    runner.load_jsonl()
    runner.run_model("variant_a", make_model(classify_baseline), resume=False)
    runner.run_model("variant_b", make_model(classify_explicit_rules), resume=False)
    runner.export_report(str(RESULTS_PATH / "comparison_report.json"))

    report = json.loads((RESULTS_PATH / "comparison_report.json").read_text(encoding="utf-8"))
    for variant, result in report["model_results"].items():
        print(
            f"{variant}: accuracy={result['accuracy']:.3f}, "
            f"macro_f1={result['f1_score']:.3f}"
        )
    print(f"Report: {RESULTS_PATH / 'comparison_report.json'}")


if __name__ == "__main__":
    main()
