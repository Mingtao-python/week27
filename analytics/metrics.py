"""
Week27 Metrics Library - Part 4
Author: Mingtao
Version: 1.0

Implements core evaluation metrics without relying solely on ready-made functions.
All calculations include zero-division safety and hand-verification support.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ConfusionMatrix:
    """Confusion matrix for binary or multi-class classification"""
    tp: int  # True Positives
    fp: int  # False Positives
    fn: int  # False Negatives
    tn: int  # True Negatives


def calculate_accuracy(tp: int, fp: int, fn: int, tn: int) -> float:
    """
    Calculate accuracy: (TP + TN) / (TP + FP + FN + TN)
    
    Part 4, Question 2: Show working for hand calculation.
    Warning: Can be misleading on imbalanced datasets (Part 4, Question 3).
    """
    total = tp + fp + fn + tn
    if total == 0:
        raise ValueError("Total samples cannot be zero")
    return (tp + tn) / total


def calculate_precision(tp: int, fp: int) -> float:
    """
    Calculate precision: TP / (TP + FP)
    
    Precision answers: "Of all positive predictions, how many were correct?"
    High precision = few false positives.
    """
    denominator = tp + fp
    if denominator == 0:
        return 0.0  # No positive predictions, precision undefined but return 0 for safety
    return tp / denominator


def calculate_recall(tp: int, fn: int) -> float:
    """
    Calculate recall (sensitivity): TP / (TP + FN)
    
    Recall answers: "Of all actual positives, how many did we find?"
    High recall = few false negatives.
    """
    denominator = tp + fn
    if denominator == 0:
        return 0.0  # No actual positives, recall undefined but return 0 for safety
    return tp / denominator


def calculate_f1_score(precision: float, recall: float) -> float:
    """
    Calculate F1 score: harmonic mean of precision and recall
    
    F1 = 2 * (precision * recall) / (precision + recall)
    
    The harmonic mean penalizes extreme values more than arithmetic mean.
    A model with precision=1.0 and recall=0.0 would have F1=0.0.
    """
    if precision + recall == 0:
        return 0.0  # Avoid division by zero
    return 2 * (precision * recall) / (precision + recall)


def calculate_all_metrics(tp: int, fp: int, fn: int, tn: int) -> Dict[str, float]:
    """
    Calculate all confusion matrix metrics at once.
    
    Part 4, Question 2 example:
    Given: TP=36, FP=9, FN=4, TN=51
    
    Expected results:
    - Accuracy = (36+51)/(36+9+4+51) = 87/100 = 0.87
    - Precision = 36/(36+9) = 36/45 = 0.80
    - Recall = 36/(36+4) = 36/40 = 0.90
    - F1 = 2*(0.80*0.90)/(0.80+0.90) = 1.44/1.70 = 0.847...
    """
    accuracy = calculate_accuracy(tp, fp, fn, tn)
    precision = calculate_precision(tp, fp)
    recall = calculate_recall(tp, fn)
    f1 = calculate_f1_score(precision, recall)
    
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "confusion_matrix": {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn
        }
    }


def calculate_per_class_metrics(
    predictions: List[str],
    ground_truth: List[str],
    class_label: str
) -> Dict[str, float]:
    """
    Calculate precision, recall, F1 for a specific class in multi-class classification.
    
    Converts multi-class to binary: class_label vs all others.
    """
    if len(predictions) != len(ground_truth):
        raise ValueError("Predictions and ground_truth must have same length")
    
    tp = sum(1 for p, g in zip(predictions, ground_truth) if p == class_label and g == class_label)
    fp = sum(1 for p, g in zip(predictions, ground_truth) if p == class_label and g != class_label)
    fn = sum(1 for p, g in zip(predictions, ground_truth) if p != class_label and g == class_label)
    tn = sum(1 for p, g in zip(predictions, ground_truth) if p != class_label and g != class_label)
    
    precision = calculate_precision(tp, fp)
    recall = calculate_recall(tp, fn)
    f1 = calculate_f1_score(precision, recall)
    
    return {
        "class": class_label,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "support": tp + fn  # Number of actual instances of this class
    }


def calculate_macro_metrics(
    predictions: List[str],
    ground_truth: List[str],
    classes: List[str]
) -> Dict[str, float]:
    """
    Calculate macro-averaged precision, recall, F1 across all classes.
    
    Macro averaging treats all classes equally regardless of size.
    This is better than accuracy for imbalanced datasets.
    """
    per_class_results = []
    for cls in classes:
        metrics = calculate_per_class_metrics(predictions, ground_truth, cls)
        per_class_results.append(metrics)
    
    n_classes = len(classes)
    if n_classes == 0:
        return {"macro_precision": 0.0, "macro_recall": 0.0, "macro_f1": 0.0}
    
    macro_precision = sum(r["precision"] for r in per_class_results) / n_classes
    macro_recall = sum(r["recall"] for r in per_class_results) / n_classes
    macro_f1 = sum(r["f1_score"] for r in per_class_results) / n_classes
    
    return {
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": macro_f1,
        "per_class": per_class_results
    }


def calculate_exact_match(predicted: str, expected: str, case_sensitive: bool = True) -> bool:
    """
    Calculate exact match for string outputs.
    
    Used for tasks where the output must match exactly (e.g., classification labels).
    """
    if not case_sensitive:
        predicted = predicted.lower()
        expected = expected.lower()
    return predicted.strip() == expected.strip()


def calculate_schema_validity_rate(validation_results: List[bool]) -> float:
    """
    Calculate the rate of schema-valid outputs.
    
    Part 2: Distinguish structural correctness from semantic correctness.
    """
    if not validation_results:
        return 0.0
    return sum(validation_results) / len(validation_results)


def calculate_field_accuracy(
    predicted_values: List,
    expected_values: List,
    field_name: str
) -> Dict[str, float]:
    """
    Calculate field-level accuracy for structured extraction.
    
    Returns both count and rate of correct values.
    This separates value correctness from schema validity.
    """
    if len(predicted_values) != len(expected_values):
        raise ValueError("predicted_values and expected_values must have same length")
    
    correct = sum(1 for p, e in zip(predicted_values, expected_values) if p == e)
    total = len(predicted_values)
    
    return {
        "field": field_name,
        "correct_count": correct,
        "total_count": total,
        "accuracy": correct / total if total > 0 else 0.0
    }


def calculate_guardrail_metric(
    outputs: List[Dict],
    guardrail_check,
    failure_threshold: float = 0.05
) -> Dict[str, float]:
    """
    Calculate a guardrail metric for safety-critical failures.
    
    Part 4, Question 5: A guardrail metric sets a maximum acceptable failure rate
    for critical errors (e.g., invented facts, prompt injection success).
    
    Args:
        outputs: List of model outputs
        guardrail_check: Function that returns True if output passes guardrail
        failure_threshold: Maximum acceptable failure rate (default 5%)
    
    Returns:
        Dictionary with failure_rate and pass_status
    """
    if not outputs:
        return {"failure_rate": 0.0, "pass_status": True, "threshold": failure_threshold}
    
    failures = sum(1 for o in outputs if not guardrail_check(o))
    failure_rate = failures / len(outputs)
    
    return {
        "failure_rate": failure_rate,
        "failure_count": failures,
        "total_count": len(outputs),
        "threshold": failure_threshold,
        "pass_status": failure_rate <= failure_threshold
    }


# =============================================================================
# Verification Examples (for testing and documentation)
# =============================================================================

def verify_metrics_example() -> Dict:
    """
    Verify metric calculations with the example from Part 4, Question 2.
    
    Given: TP=36, FP=9, FN=4, TN=51
    
    Hand calculation:
    - Accuracy = 87/100 = 0.87
    - Precision = 36/45 = 0.80
    - Recall = 36/40 = 0.90
    - F1 = 2*(0.80*0.90)/(0.80+0.90) = 1.44/1.70 ≈ 0.847
    """
    tp, fp, fn, tn = 36, 9, 4, 51
    
    results = calculate_all_metrics(tp, fp, fn, tn)
    
    # Verify with hand calculations
    expected = {
        "accuracy": 0.87,
        "precision": 0.80,
        "recall": 0.90,
    }
    
    verification = {
        "calculated": results,
        "expected": expected,
        "accuracy_match": abs(results["accuracy"] - expected["accuracy"]) < 0.001,
        "precision_match": abs(results["precision"] - expected["precision"]) < 0.001,
        "recall_match": abs(results["recall"] - expected["recall"]) < 0.001,
    }
    
    return verification
