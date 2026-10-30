# Week27 LLM Evaluation Tool

> **Author**: Mingtao  
> **Version**: 1.0  
> **Based on**: Week27 Learning Plan & Theory Assignment

A professional LLM evaluation toolkit implementing schema validation, metrics calculation, benchmark running, and error analysis following engineering best practices.

---

## 📁 Project Structure

```text
week27/
├── analytics/              # Core analytics logic (Single Source of Truth)
│   ├── __init__.py
│   ├── schema.py           # ⭐ Schema definitions & validators
│   ├── metrics.py          # ⭐ Metrics calculations (TP/FP/FN/TN, F1, etc.)
│   ├── benchmark_runner.py # ⭐ Benchmark harness
│   └── error_analyzer.py   # ⭐ Error categorization & analysis
├── tests/                  # Automated test suite
│   ├── test_all.py         # 42 evaluator tests
│   └── test_llm_experiment.py # 17 offline experiment tests
├── benchmark_data/         # Benchmark datasets
│   └── baseline_30cases.jsonl
├── examples/
│   ├── compare_variants.py # Reproducible rule-based comparison
│   ├── llm_client.py       # HTTP model adapter
│   └── run_llm_variants.py # Real LLM comparison and regression workflow
├── results/               # Existing rule-based results; LLM files are created by a live run
├── planning/               # Original planning documents
└── README.md               # This file
```

---

## 🎯 Features

### 1. Schema Validation (Part 2: Structured Output)

**Single Source of Truth**: All schemas defined in `analytics/schema.py`

```python
from analytics.schema import validate_support_ticket, validate_invoice

# Support Ticket Validation
ticket = {
    "customer_name": "John Doe",
    "issue_type": "Billing",  # Must be: Billing/Technical/Account/Other
    "priority": "High",       # Must be: Low/Medium/High/Critical
    "summary": "Charged twice",
    "requires_human_review": False
}
is_valid, errors = validate_support_ticket(ticket)

# Invoice Validation with Cross-field Checks
invoice = {
    "supplier": "Acme Corp",
    "invoice_number": "INV-001",
    "date": "2024-01-15",
    "currency": "USD",
    "subtotal": 100.0,
    "tax": 10.0,
    "total": 110.0  # Auto-validated: must equal subtotal + tax
}
is_valid, errors = validate_invoice(invoice)
```

**Validation Types**:
- ✅ Required field checking
- ✅ Type validation (string, number, boolean)
- ✅ Enum value validation
- ✅ Bounds checking (no negative amounts)
- ✅ Cross-field consistency (total = subtotal + tax)

---

### 2. Metrics Library (Part 4: Metrics)

**Hand-verifiable calculations** with zero-division safety:

```python
from analytics.metrics import calculate_all_metrics, verify_metrics_example

# Example from Part 4, Question 2: TP=36, FP=9, FN=4, TN=51
result = calculate_all_metrics(tp=36, fp=9, fn=4, tn=51)
# Returns:
# {
#   "accuracy": 0.87,    # (36+51)/100
#   "precision": 0.80,   # 36/(36+9)
#   "recall": 0.90,      # 36/(36+4)
#   "f1_score": 0.847... # 2*(0.8*0.9)/(0.8+0.9)
# }

# Verify against hand calculations
verification = verify_metrics_example()
assert verification["accuracy_match"]  # True
assert verification["precision_match"] # True
assert verification["recall_match"]    # True
```

**Available Metrics**:

- Accuracy, Precision, Recall, F1 Score
- Per-class metrics for multi-class classification
- Macro-averaged metrics (better for imbalanced datasets)
- Exact match for string outputs
- Schema validity rate
- Field-level accuracy
- Guardrail metrics for safety-critical failures

---

### 3. Benchmark Runner (Part 4 & 5: Benchmark Design)

**Repeatable evaluation harness** with resume capability:

```python
from analytics.benchmark_runner import BenchmarkRunner, create_baseline_benchmark

# Create baseline benchmark (30 cases, 5 difficulty slices)
benchmark_path = create_baseline_benchmark("./benchmark_data/baseline.jsonl")

# Initialize runner
runner = BenchmarkRunner(benchmark_path, output_dir="./results")
runner.load_jsonl()

# Run model evaluation (with automatic resumption)
def mock_model_fn(prompt):
    return {"raw_output": "Classification result", "parsed_output": {"label": "Billing"}}

records = runner.run_model("mock_model_v1", mock_model_fn)

# Generate report
report_path = runner.export_report()
```

**Benchmark Features**:

- ✅ JSONL/CSV format support
- ✅ Malformed input handling (skip & continue)
- ✅ Resume after interruption
- ✅ Raw output preservation for audit
- ✅ Separate difficulty and category analysis
- ✅ Fair model comparison (same dataset, same prompt, same rules)

---

### 4. Error Analyzer (Part 6: Error Analysis)

**Convert scores into engineering work**:

```python
from analytics.error_analyzer import ErrorAnalyzer, create_regression_suite

# Analyze failures
analyzer = ErrorAnalyzer("./results", benchmark_cases=runner.cases)
analyzer.load_results()
analysis = analyzer.analyze_failures()

# Print summary
analyzer.print_summary()

# Export detailed report
report_path = analyzer.export_report()

# Create a regression suite after collecting at least 8 verified failures
regression_path = create_regression_suite(analysis["all_failures"], "./regression_suite.json")
```

**Failure Categories**:

- `invalid_json` - Parse failures
- `missing_field` - Required fields absent
- `wrong_type` - Type mismatches
- `invalid_enum` - Values outside allowed set
- `invented_value` - Hallucinated data
- `cross_field_inconsistency` - Logical conflicts
- `prompt_injection` - A tagged attack case where output matches the attacker's requested output

**Severity Levels**:

- `critical` - Prompt injection, invented facts
- `high` - Data corruption risk
- `medium` - Missing fields
- `low` - Formatting issues

---

## 🔒 Security & Integrity (Part 7)

### Protected Against:

1. **Prompt Injection**: Detection heuristics in error analyzer
2. **Ground Truth Leakage**: Separation of `input_prompt` and `expected_output`
3. **Selective Reporting**: All metrics exported, not just favorable ones
4. **Benchmark Poisoning**: Version control for datasets and evaluation code

### Trust Boundaries:

```text
Dataset → Benchmark Runner → Model → Evaluator → Report
   ↑            ↑              ↑         ↑          ↑
Untrusted   Controlled    Untrusted  Secret    Audited
Data        Variables     Output     Logic     Output
```

---

## ✅ Test Coverage (59 Tests)

All tests correspond to actual `if/raise` logic in code:

| Category | Tests | Coverage |
|----------|-------|----------|
| Schema Validation | 6 | Malformed and extra-field detection |
| Invoice Validation | 5 | Cross-field and extra-field validation |
| Metrics | 9 | Hand-verifiable calculations |
| Guardrail Metrics | 3 | Safety thresholds |
| Benchmark Runner | 6 | Ground-truth comparison, metrics, slices |
| Error Analyzer | 5 | Categorization, regression suites and before/after comparison |
| Security | 4 | Explicit attack-case handling |
| Edge Cases | 4 | Empty data, extreme values |
| LLM Experiment | 17 | Adapter, fixed settings, real-call workflow, frozen regression, failed runs and provenance |

Run tests:
```bash
python -m pytest -q
```

---

## 📋 Course Requirements Mapping

| Requirement | Implementation | File |
|-------------|----------------|------|
| Schema Validator | `validate_support_ticket()`, `validate_invoice()` | `schema.py` |
| Metric Library | `calculate_all_metrics()`, precision/recall/F1 | `metrics.py` |
| Benchmark Runner | `BenchmarkRunner` class with resume | `benchmark_runner.py` |
| Error Analyzer | `ErrorAnalyzer` with categorization | `error_analyzer.py` |
| Regression Suite | `create_regression_suite()` | `error_analyzer.py` |
| 30+ Benchmark Cases | `create_baseline_benchmark()` | `benchmark_runner.py` |
| 8+ Regression Cases | Requires 8 verified failures with original inputs and expected outputs | `error_analyzer.py` |
| Security Analysis | Injection detection, ground truth protection | All files |

---

## 🚀 Quick Start

```python
# 1. Import everything from single source
from analytics import (
    validate_support_ticket,
    calculate_all_metrics,
    BenchmarkRunner,
    ErrorAnalyzer,
    create_baseline_benchmark
)

# 2. Create benchmark
benchmark_path = create_baseline_benchmark("./my_benchmark.jsonl")

# 3. Run evaluation
runner = BenchmarkRunner(benchmark_path)
runner.load_jsonl()
# ... run models ...

# 4. Analyze results
analyzer = ErrorAnalyzer("./results", runner.cases)
analyzer.analyze_failures()
analyzer.print_summary()
```

---

## Evaluation Target

Support-ticket classification: predict one of `Billing`, `Technical`, `Account`, or `Other` from the input ticket.

## Dataset

`benchmark_data/baseline_30cases.jsonl` contains 30 labeled cases. Difficulty (`easy`, `normal`, `edge`, `ambiguous`, `adversarial`), issue slices, and the four classification labels are reported separately.

## Metrics

Classification reports exact-label accuracy and macro precision, recall, and F1, including per-class metrics. Schema validity and semantic correctness are reported independently. Extraction semantics compare each expected field value after schema validation.

## Benchmark Protocol

Run both deterministic local reference configurations on the same checked-in dataset:

```bash
python -m examples.compare_variants
```

The runner writes `variant_a_results.jsonl`, `variant_b_results.jsonl`, and `comparison_report.json` under `results/`. These are rule-based harness examples, not external or production LLM evaluations.

## Results

The generated `results/comparison_report.json` reports:

| Local reference configuration | Cases | Accuracy | Macro F1 |
|---|---:|---:|---:|
| `variant_a` | 30 | 0.633 | 0.633 |
| `variant_b` | 30 | 0.733 | 0.739 |

These are measured rule-based harness results, not evidence about an LLM.

## Error Analysis

Failure reports preserve the original benchmark input and expected output. Regression suites are generated only when at least eight verified failures contain both values; the same frozen cases can be evaluated before and after a controlled change with `compare_regression_runs()`.

## Real LLM Experiment

The real runner is ready and tested offline. A live LLM run has **not** been completed in this
revision. The existing `variant_a` and `variant_b` results remain rule-based examples.
No simulated test responses are saved as real experiment results.

Use one fixed model ID and the same endpoint for both variants:

```powershell
python -m examples.run_llm_variants --base-url https://api.llm7.io/v1 --model FIXED_MODEL_ID --api-key-env llm7_api
```

Set the credential in that environment variable before running. Credentials are not written
to result files. Another OpenAI-compatible endpoint can be supplied with `--base-url` and
`--api-key-env`. Routing aliases such as `default`, `fast` and `pro` are rejected.

- Variant A: baseline classification prompt.
- Variant B: explicit label definitions, ticket-data boundary and JSON instructions.
- Fixed controls: the same 30 cases, model, temperature 0, max tokens 64, parser and evaluator.
- Only the prompt changes. Neither expected outputs nor case labels are sent to the model.

The runner first calls Variant A on all 30 cases, freezes eight verified failures if available,
then calls Variant B on the same 30 cases. It makes 16 additional calls to run both prompts
against the same frozen eight inputs. Regression results are freshly generated, not replayed.
Selection uses baseline failure severity, before examining Variant B results.

The live run creates:

```text
results/
├── llm_variant_a_results.jsonl
├── llm_variant_b_results.jsonl
├── llm_comparison_report.json
├── llm_requests.jsonl
└── llm_run_status.json
regression/
├── regression_8cases.json
├── before_results.json
├── after_results.json
└── regression_comparison.json
```

The comparison includes accuracy, macro precision/recall/F1, schema validity, difficulty and
category slices, measured HTTP latency and provider token usage when available. The request
audit preserves prompts, raw responses, response IDs, model IDs and usage. Dataset/evaluator
hashes and settings are recorded for reproducibility. Every response model ID must match;
the service's hidden backend revisions cannot be independently verified.

The regression file preserves original user inputs, expected labels, previous predictions,
failure categories and severity. The report lists before/after correctness and all improved,
unchanged and regressed IDs, plus a recommendation.

If there are fewer than eight baseline failures, the runner reports `regression_incomplete`
and exits with code 2. It does not manufacture failures or substitute the rule-based outputs.
API errors stop the experiment and mark the run failed. Existing experiment files are never
silently overwritten; use `--output-root PATH` for a separate run. Offline tests simulate API
responses only inside temporary test folders and do not prove live model performance.

## Security

Adversarial benchmark cases explicitly declare the attacker's requested output. Prompt-injection failures are counted only when the model returns that tagged output, not from incidental words such as “ignore” or “pass”.

## Limitations

The checked-in comparison uses simple deterministic keyword rules and does not call an LLM. Results depend on the small 30-case dataset. Regression suites cannot be claimed until at least eight real, verified failures have been collected.

## Recommendation

Use this implementation to validate evaluator behavior, then run two real model/configuration variants and review their error analysis before making a model-quality recommendation.

## 📝 Pre-Commit Checklist

Before committing:

- [ ] **Schema Consistency**: All schemas in `schema.py`, imported everywhere
- [ ] **Real Instrumentation**: Actual validation logic, not print statements
- [ ] **Logic Validation**: Funnel checks sequence, A/B checks boundaries
- [ ] **Security**: Duplicate detection, bounds checking, tagged injection cases
- [ ] **Test Coverage**: Every "PASS" backed by assert in `test_all.py`
- [ ] **Documentation**: README matches implementation

---

## 📚 References

- Week27 Learning Plan: `planning/Week27_Learning_Plan.docx`
- Theory Assignment: `planning/Week27_Theory_Assignment.docx`

---

> "Perfect is the enemy of good, but **inconsistency** is the enemy of engineering."
> — Mingtao's Engineering Law
