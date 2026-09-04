"""
Week27 Event Schema - Single Source of Truth
Author: Mingtao
Version: 1.0

This module defines all structured output schemas and event types for the LLM Evaluation Tool.
All other modules must import from this file to ensure consistency.
"""

from typing import TypedDict, List, Optional, Literal
from enum import Enum


# =============================================================================
# Part 2: Structured Output Schemas
# =============================================================================

class SupportTicketSchema(TypedDict):
    """Schema for support ticket extraction (Part 2, Question 2)"""
    customer_name: str
    issue_type: Literal["Billing", "Technical", "Account", "Other"]
    priority: Literal["Low", "Medium", "High", "Critical"]
    summary: str
    requires_human_review: bool


# Required fields for validation
SUPPORT_TICKET_REQUIRED_FIELDS = ["customer_name", "issue_type", "priority", "summary", "requires_human_review"]

# Valid enum values
VALID_ISSUE_TYPES = {"Billing", "Technical", "Account", "Other"}
VALID_PRIORITIES = {"Low", "Medium", "High", "Critical"}


# =============================================================================
# Invoice Extraction Schema (Part 2, Task: Invoice Extraction Evaluator)
# =============================================================================

class InvoiceSchema(TypedDict):
    """Schema for invoice extraction"""
    supplier: str
    invoice_number: str
    date: str
    currency: str
    subtotal: float
    tax: float
    total: float


INVOICE_REQUIRED_FIELDS = ["supplier", "invoice_number", "date", "currency", "subtotal", "tax", "total"]


# =============================================================================
# Benchmark Case Schema (Part 4 & 5)
# =============================================================================

class DifficultyLevel(Enum):
    EASY = "easy"
    NORMAL = "normal"
    EDGE = "edge"
    AMBIGUOUS = "ambiguous"
    ADVERSARIAL = "adversarial"


class FailureCategory(Enum):
    """Failure taxonomy for error analysis (Part 6, Question 2)"""
    INVALID_JSON = "invalid_json"
    MISSING_FIELD = "missing_field"
    EXTRA_FIELD = "extra_field"
    WRONG_TYPE = "wrong_type"
    INVALID_ENUM = "invalid_enum"
    WRONG_VALUE = "wrong_value"
    INVENTED_VALUE = "invented_value"
    CROSS_FIELD_INCONSISTENCY = "cross_field_inconsistency"
    PARSE_FAILURE = "parse_failure"
    SCHEMA_VIOLATION = "schema_violation"
    REFUSAL = "refusal"
    PROMPT_INJECTION = "prompt_injection"
    EVALUATOR_ERROR = "evaluator_error"


class SeverityLevel(Enum):
    """Severity levels for error analysis (Part 5, Task: Failure Triage Review)"""
    LOW = "low"           # Formatting issues, minor typos
    MEDIUM = "medium"     # Wrong but recoverable
    HIGH = "high"         # Wrong answer, data corruption risk
    CRITICAL = "critical" # Invented facts, security issues, prompt injection


class BenchmarkCase(TypedDict):
    """Schema for a single benchmark case"""
    id: str
    task_type: str  # "classification", "extraction", "reasoning"
    input_prompt: str
    expected_output: dict  # Ground truth
    difficulty: str  # From DifficultyLevel
    slice_category: str  # For slice-level analysis
    metadata: Optional[dict]


# =============================================================================
# Model Output Record Schema
# =============================================================================

class ModelOutputRecord(TypedDict):
    """Schema for storing model output during evaluation"""
    case_id: str
    model_name: str
    model_version: str
    raw_output: str
    parsed_output: Optional[dict]
    schema_valid: bool
    semantic_valid: bool
    validation_errors: List[str]
    latency_ms: Optional[float]
    token_count: Optional[int]
    timestamp: str


# =============================================================================
# Evaluation Result Schema
# =============================================================================

class EvaluationResult(TypedDict):
    """Schema for evaluation results"""
    model_name: str
    total_cases: int
    schema_pass_rate: float
    semantic_pass_rate: float
    accuracy: Optional[float]
    precision: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]
    avg_latency_ms: Optional[float]
    failure_breakdown: dict  # By FailureCategory
    slice_results: dict  # By slice_category


# =============================================================================
# Regression Test Case Schema
# =============================================================================

class RegressionCase(TypedDict):
    """Schema for regression test cases (Part 5, Implementation 5)"""
    id: str
    original_case_id: str
    description: str
    severity: str  # From SeverityLevel
    failure_category: str  # From FailureCategory
    expected_behavior: str
    is_fixed: bool


# =============================================================================
# Helper Functions for Schema Validation
# =============================================================================

def validate_support_ticket(data: dict) -> tuple[bool, List[str]]:
    """
    Validate a support ticket against the schema.
    Returns (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required fields
    for field in SUPPORT_TICKET_REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return False, errors
    
    # Check types
    if not isinstance(data.get("customer_name"), str):
        errors.append("customer_name must be a string")
    
    if not isinstance(data.get("summary"), str):
        errors.append("summary must be a string")
    
    if not isinstance(data.get("requires_human_review"), bool):
        errors.append("requires_human_review must be a boolean")
    
    # Check enum values
    if data.get("issue_type") not in VALID_ISSUE_TYPES:
        errors.append(f"issue_type must be one of {VALID_ISSUE_TYPES}")
    
    if data.get("priority") not in VALID_PRIORITIES:
        errors.append(f"priority must be one of {VALID_PRIORITIES}")
    
    return len(errors) == 0, errors


def validate_invoice(data: dict) -> tuple[bool, List[str]]:
    """
    Validate an invoice extraction against the schema.
    Returns (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required fields
    for field in INVOICE_REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return False, errors
    
    # Check types
    string_fields = ["supplier", "invoice_number", "date", "currency"]
    for field in string_fields:
        if not isinstance(data.get(field), str):
            errors.append(f"{field} must be a string")
    
    numeric_fields = ["subtotal", "tax", "total"]
    for field in numeric_fields:
        value = data.get(field)
        if not isinstance(value, (int, float)):
            errors.append(f"{field} must be a number")
        elif value < 0:
            errors.append(f"{field} cannot be negative")
    
    # Cross-field validation: total should equal subtotal + tax
    if all(isinstance(data.get(f), (int, float)) for f in numeric_fields):
        expected_total = data["subtotal"] + data["tax"]
        if abs(data["total"] - expected_total) > 0.01:  # Allow small floating point difference
            errors.append(f"total ({data['total']}) does not equal subtotal + tax ({expected_total})")
    
    return len(errors) == 0, errors
