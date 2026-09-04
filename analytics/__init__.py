"""
Week27 Analytics Package - LLM Evaluation Tool
Author: Mingtao
Version: 1.0

This package provides core analytics functionality for LLM evaluation:
- Schema definitions and validation (schema.py)
- Metrics calculations (metrics.py)
- Benchmark runner (benchmark_runner.py)
- Error analyzer (error_analyzer.py)

Following the coding style guide:
- Single Source of Truth: All schemas defined in schema.py
- Real Instrumentation: Actual validation logic, not just print statements
- Data Integrity: Schema validation, duplicate detection, bounds checking
"""

from analytics.schema import (
    SupportTicketSchema,
    InvoiceSchema,
    BenchmarkCase,
    ModelOutputRecord,
    EvaluationResult,
    RegressionCase,
    FailureCategory,
    SeverityLevel,
    DifficultyLevel,
    validate_support_ticket,
    validate_invoice,
    SUPPORT_TICKET_REQUIRED_FIELDS,
    INVOICE_REQUIRED_FIELDS,
    VALID_ISSUE_TYPES,
    VALID_PRIORITIES,
)

from analytics.metrics import (
    calculate_accuracy,
    calculate_precision,
    calculate_recall,
    calculate_f1_score,
    calculate_all_metrics,
    calculate_per_class_metrics,
    calculate_macro_metrics,
    calculate_exact_match,
    calculate_schema_validity_rate,
    calculate_field_accuracy,
    calculate_guardrail_metric,
    verify_metrics_example,
)

from analytics.benchmark_runner import (
    BenchmarkRunner,
    create_baseline_benchmark,
)

from analytics.error_analyzer import (
    ErrorAnalyzer,
    create_regression_suite,
)

__version__ = "1.0"
__author__ = "Mingtao"

__all__ = [
    # Schemas
    'SupportTicketSchema',
    'InvoiceSchema',
    'BenchmarkCase',
    'ModelOutputRecord',
    'EvaluationResult',
    'RegressionCase',
    
    # Enums
    'FailureCategory',
    'SeverityLevel',
    'DifficultyLevel',
    
    # Validators
    'validate_support_ticket',
    'validate_invoice',
    
    # Constants
    'SUPPORT_TICKET_REQUIRED_FIELDS',
    'INVOICE_REQUIRED_FIELDS',
    'VALID_ISSUE_TYPES',
    'VALID_PRIORITIES',
    
    # Metrics
    'calculate_accuracy',
    'calculate_precision',
    'calculate_recall',
    'calculate_f1_score',
    'calculate_all_metrics',
    'calculate_per_class_metrics',
    'calculate_macro_metrics',
    'calculate_exact_match',
    'calculate_schema_validity_rate',
    'calculate_field_accuracy',
    'calculate_guardrail_metric',
    'verify_metrics_example',
    
    # Benchmark
    'BenchmarkRunner',
    'create_baseline_benchmark',
    
    # Error Analysis
    'ErrorAnalyzer',
    'create_regression_suite',
]
