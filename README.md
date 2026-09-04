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
│   └── test_all.py         # 34 comprehensive tests
├── benchmark_data/         # Benchmark datasets
│   └── baseline_30cases.jsonl
├── docs/                   # Documentation
├── planning/               # Original planning documents
├── CODING_STYLE_GUIDE.md   # Engineering standards
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
- ✅ Per-slice analysis (easy/normal/edge/ambiguous/adversarial)
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

# Create regression suite from critical failures
regression_path = create_regression_suite(analysis["all_failures"], "./regression_suite.json")
```

**Failure Categories**:
- `invalid_json` - Parse failures
- `missing_field` - Required fields absent
- `wrong_type` - Type mismatches
- `invalid_enum` - Values outside allowed set
- `invented_value` - Hallucinated data
- `cross_field_inconsistency` - Logical conflicts
- `prompt_injection` - Security vulnerabilities

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
```
Dataset → Benchmark Runner → Model → Evaluator → Report
   ↑            ↑              ↑         ↑          ↑
Untrusted   Controlled    Untrusted  Secret    Audited
Data        Variables     Output     Logic     Output
```

---

## ✅ Test Coverage (34 Tests)

All tests correspond to actual `if/raise` logic in code:

| Category | Tests | Coverage |
|----------|-------|----------|
| Schema Validation | 5 | Malformed input detection |
| Invoice Validation | 4 | Cross-field consistency |
| Metrics | 9 | Hand-verifiable calculations |
| Guardrail Metrics | 3 | Safety thresholds |
| Benchmark Runner | 4 | Resume, malformed handling |
| Error Analyzer | 3 | Categorization, severity |
| Security | 2 | Injection detection |
| Edge Cases | 4 | Empty data, extreme values |

Run tests:
```bash
python -m pytest tests/test_all.py -v
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
| 8+ Regression Cases | Selects diverse failures by severity | `error_analyzer.py` |
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

## 📝 Pre-Commit Checklist

Following the coding style guide:

- [ ] **Schema Consistency**: All schemas in `schema.py`, imported everywhere
- [ ] **Real Instrumentation**: Actual validation logic, not print statements
- [ ] **Logic Validation**: Funnel checks sequence, A/B checks boundaries
- [ ] **Security**: Duplicate detection, bounds checking, injection detection
- [ ] **Test Coverage**: Every "PASS" backed by assert in `test_all.py`
- [ ] **Documentation**: README matches implementation

---

## 📚 References

- Week27 Learning Plan: `planning/Week27_Learning_Plan.docx`
- Theory Assignment: `planning/Week27_Theory_Assignment.docx`
- Coding Style Guide: `CODING_STYLE_GUIDE.md`

---

> "Perfect is the enemy of good, but **inconsistency** is the enemy of engineering."
> — Mingtao's Engineering Law
