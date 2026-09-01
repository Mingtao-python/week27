"""
Week27 Error Analyzer - Part 6
Author: Mingtao
Version: 1.0

Implements error analysis functionality:
- Assign failure categories and severity
- Aggregate by category/slice
- Show top failure patterns
- Export concise error reports
"""

import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
from collections import defaultdict

from analytics.schema import FailureCategory, SeverityLevel, ModelOutputRecord, BenchmarkCase
from analytics.metrics import calculate_all_metrics


class ErrorAnalyzer:
    """
    Analyze model failures to identify patterns and root causes.
    
    Part 6: Error Analysis
    - Convert scores into engineering work
    - Distinguish frequency vs severity
    - Identify slice-level concentrations
    - Generate actionable hypotheses
    """
    
    def __init__(self, results_path: str, benchmark_cases: Optional[List[BenchmarkCase]] = None):
        self.results_path = Path(results_path)
        self.benchmark_cases = benchmark_cases or []
        self.case_map = {c['id']: c for c in self.benchmark_cases}
        
        self.records: List[ModelOutputRecord] = []
        self.failures: List[Dict[str, Any]] = []
        self.analysis_results: Dict[str, Any] = {}
    
    def load_results(self, model_name: Optional[str] = None) -> List[ModelOutputRecord]:
        """Load model output results from JSONL file."""
        records = []
        
        if model_name:
            files_to_check = [self.results_path / f"{model_name}_results.jsonl"]
        else:
            files_to_check = list(self.results_path.glob("*_results.jsonl"))
        
        for file_path in files_to_check:
            if not file_path.exists():
                continue
            
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        records.append(record)
                    except json.JSONDecodeError:
                        continue
        
        self.records = records
        return records
    
    def classify_failure(self, record: ModelOutputRecord) -> Optional[Dict[str, Any]]:
        """
        Classify a single failure case.
        
        Returns failure dict with category, severity, and analysis.
        """
        if record.get('schema_valid', True) and record.get('semantic_valid', True):
            return None  # Not a failure
        
        errors = record.get('validation_errors', [])
        raw_output = record.get('raw_output', '')
        case_id = record.get('case_id', 'unknown')
        
        # Determine failure category
        category = FailureCategory.SCHEMA_VIOLATION
        subcategory = None
        
        for error in errors:
            error_lower = error.lower()
            
            if 'missing' in error_lower and 'field' in error_lower:
                category = FailureCategory.MISSING_FIELD
                subcategory = 'required_field'
            elif 'invalid json' in error_lower or 'parse' in error_lower:
                category = FailureCategory.PARSE_FAILURE
            elif 'must be a' in error_lower or 'type' in error_lower:
                category = FailureCategory.WRONG_TYPE
            elif 'one of' in error_lower or 'valid values' in error_lower:
                category = FailureCategory.INVALID_ENUM
            elif 'cannot be negative' in error_lower or 'range' in error_lower:
                category = FailureCategory.CROSS_FIELD_INCONSISTENCY
            elif 'does not equal' in error_lower or 'mismatch' in error_lower:
                category = FailureCategory.CROSS_FIELD_INCONSISTENCY
            elif 'ignore' in raw_output.lower() or 'pass' in raw_output.lower():
                category = FailureCategory.PROMPT_INJECTION
                subcategory = 'injection_attempt'
            elif 'error:' in raw_output.lower() or 'exception' in raw_output.lower():
                category = FailureCategory.PARSE_FAILURE
                subcategory = 'runtime_error'
        
        # Determine severity
        severity = SeverityLevel.MEDIUM
        
        if category == FailureCategory.PROMPT_INJECTION:
            severity = SeverityLevel.CRITICAL
        elif category == FailureCategory.INVENTED_VALUE:
            severity = SeverityLevel.HIGH
        elif category == FailureCategory.CROSS_FIELD_INCONSISTENCY:
            severity = SeverityLevel.HIGH
        elif category == FailureCategory.MISSING_FIELD:
            severity = SeverityLevel.MEDIUM
        elif category == FailureCategory.WRONG_TYPE:
            severity = SeverityLevel.LOW
        elif category == FailureCategory.INVALID_ENUM:
            severity = SeverityLevel.LOW
        
        # Get case context
        case_info = self.case_map.get(case_id, {})
        
        return {
            'case_id': case_id,
            'model_name': record.get('model_name', 'unknown'),
            'failure_category': category.value,
            'failure_subcategory': subcategory,
            'severity': severity.value,
            'errors': errors,
            'raw_output_preview': raw_output[:200] if len(raw_output) > 200 else raw_output,
            'expected_output': case_info.get('expected_output'),
            'difficulty': case_info.get('difficulty', 'unknown'),
            'slice_category': case_info.get('slice_category', 'unknown'),
            'timestamp': record.get('timestamp', datetime.now().isoformat())
        }
    
    def analyze_failures(self) -> Dict[str, Any]:
        """
        Perform comprehensive failure analysis.
        
        Returns:
            Dictionary with:
            - failure_counts_by_category
            - failure_counts_by_severity
            - slice_analysis
            - top_failure_patterns
            - recommendations
        """
        if not self.records:
            self.load_results()
        
        # Classify all failures
        self.failures = []
        for record in self.records:
            failure = self.classify_failure(record)
            if failure:
                self.failures.append(failure)
        
        total_records = len(self.records)
        total_failures = len(self.failures)
        failure_rate = total_failures / total_records if total_records > 0 else 0
        
        # Aggregate by category
        category_counts = defaultdict(int)
        for f in self.failures:
            category_counts[f['failure_category']] += 1
        
        # Aggregate by severity
        severity_counts = defaultdict(int)
        for f in self.failures:
            severity_counts[f['severity']] += 1
        
        # Slice-level analysis
        slice_failures = defaultdict(lambda: {'total': 0, 'failures': 0})
        for record in self.records:
            case_id = record.get('case_id', '')
            case_info = self.case_map.get(case_id, {})
            slice_cat = case_info.get('slice_category', 'unknown')
            slice_failures[slice_cat]['total'] += 1
            
            if not record.get('schema_valid', True) or not record.get('semantic_valid', True):
                slice_failures[slice_cat]['failures'] += 1
        
        slice_analysis = {}
        for slice_cat, counts in slice_failures.items():
            failure_rate = counts['failures'] / counts['total'] if counts['total'] > 0 else 0
            slice_analysis[slice_cat] = {
                'total_cases': counts['total'],
                'failure_count': counts['failures'],
                'failure_rate': failure_rate
            }
        
        # Identify top failure patterns
        pattern_groups = defaultdict(list)
        for f in self.failures:
            key = f"{f['failure_category']}:{f.get('failure_subcategory', 'general')}"
            pattern_groups[key].append(f)
        
        top_patterns = sorted(
            [(k, len(v)) for k, v in pattern_groups.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Generate recommendations
        recommendations = []
        
        if category_counts.get(FailureCategory.PARSE_FAILURE.value, 0) > total_failures * 0.3:
            recommendations.append({
                'priority': 'HIGH',
                'issue': 'High parse failure rate',
                'recommendation': 'Improve prompt clarity for output format, add retry logic with format hints'
            })
        
        if category_counts.get(FailureCategory.PROMPT_INJECTION.value, 0) > 0:
            recommendations.append({
                'priority': 'CRITICAL',
                'issue': 'Prompt injection vulnerabilities detected',
                'recommendation': 'Implement input sanitization, separate instructions from user content, add injection detection'
            })
        
        if category_counts.get(FailureCategory.MISSING_FIELD.value, 0) > total_failures * 0.2:
            recommendations.append({
                'priority': 'MEDIUM',
                'issue': 'Frequent missing required fields',
                'recommendation': 'Add explicit field requirements in prompt, implement schema validation with retries'
            })
        
        high_risk_slices = [s for s, data in slice_analysis.items() if data['failure_rate'] > 0.5]
        if high_risk_slices:
            recommendations.append({
                'priority': 'MEDIUM',
                'issue': f'High failure rates in slices: {", ".join(high_risk_slices)}',
                'recommendation': 'Create targeted training data or prompts for these edge cases'
            })
        
        self.analysis_results = {
            'summary': {
                'total_records': total_records,
                'total_failures': total_failures,
                'failure_rate': failure_rate,
                'analysis_timestamp': datetime.now().isoformat()
            },
            'failure_counts_by_category': dict(category_counts),
            'failure_counts_by_severity': dict(severity_counts),
            'slice_analysis': slice_analysis,
            'top_failure_patterns': top_patterns,
            'all_failures': self.failures,
            'recommendations': recommendations
        }
        
        return self.analysis_results
    
    def export_report(self, output_path: Optional[str] = None) -> str:
        """
        Export a concise error analysis report.
        """
        if not self.analysis_results:
            self.analyze_failures()
        
        if output_path is None:
            output_path = Path(self.results_path) / f"error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:
            output_path = Path(output_path)
        
        # Create human-readable summary
        report = {
            'report_type': 'Error Analysis Report',
            'generated_at': datetime.now().isoformat(),
            'executive_summary': {
                'total_cases_analyzed': self.analysis_results['summary']['total_records'],
                'total_failures_found': self.analysis_results['summary']['total_failures'],
                'overall_failure_rate': f"{self.analysis_results['summary']['failure_rate']:.1%}",
                'most_common_failure': max(self.analysis_results['failure_counts_by_category'].items(), key=lambda x: x[1])[0] if self.analysis_results['failure_counts_by_category'] else 'N/A',
                'critical_issues_count': self.analysis_results['failure_counts_by_severity'].get(SeverityLevel.CRITICAL.value, 0)
            },
            'detailed_findings': {
                'by_category': self.analysis_results['failure_counts_by_category'],
                'by_severity': self.analysis_results['failure_counts_by_severity'],
                'by_slice': self.analysis_results['slice_analysis'],
                'top_patterns': self.analysis_results['top_failure_patterns']
            },
            'recommendations': self.analysis_results['recommendations'],
            'sample_failures': self.analysis_results['all_failures'][:10]  # First 10 as examples
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        return str(output_path)
    
    def print_summary(self):
        """Print a human-readable summary to console."""
        if not self.analysis_results:
            self.analyze_failures()
        
        print("\n" + "="*60)
        print("ERROR ANALYSIS SUMMARY")
        print("="*60)
        
        summary = self.analysis_results['summary']
        print(f"\nTotal Cases: {summary['total_records']}")
        print(f"Total Failures: {summary['total_failures']}")
        print(f"Failure Rate: {summary['failure_rate']:.1%}")
        
        print("\n--- Failures by Category ---")
        for cat, count in sorted(self.analysis_results['failure_counts_by_category'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat}: {count}")
        
        print("\n--- Failures by Severity ---")
        for sev, count in sorted(self.analysis_results['failure_counts_by_severity'].items()):
            print(f"  {sev}: {count}")
        
        print("\n--- Slice Analysis ---")
        for slice_cat, data in sorted(self.analysis_results['slice_analysis'].items(), key=lambda x: x[1]['failure_rate'], reverse=True):
            print(f"  {slice_cat}: {data['failure_count']}/{data['total_cases']} ({data['failure_rate']:.1%})")
        
        print("\n--- Top Recommendations ---")
        for i, rec in enumerate(self.analysis_results['recommendations'], 1):
            print(f"  {i}. [{rec['priority']}] {rec['issue']}")
            print(f"     → {rec['recommendation']}")
        
        print("\n" + "="*60)


def create_regression_suite(failures: List[Dict], output_path: str) -> str:
    """
    Create a regression test suite from important failures.
    
    Part 5, Implementation 5: Regression Suite
    Select at least 8 important failures and freeze them as regression cases.
    """
    # Prioritize by severity and category
    priority_order = {
        SeverityLevel.CRITICAL.value: 0,
        SeverityLevel.HIGH.value: 1,
        SeverityLevel.MEDIUM.value: 2,
        SeverityLevel.LOW.value: 3,
    }
    
    # Sort failures by severity
    sorted_failures = sorted(failures, key=lambda f: priority_order.get(f['severity'], 99))
    
    # Select top 8+ diverse failures
    selected = []
    seen_categories = set()
    
    for failure in sorted_failures:
        if len(selected) >= 12:
            break
        
        cat = failure['failure_category']
        # Ensure diversity: prefer new categories
        if cat not in seen_categories or len(selected) < 8:
            selected.append(failure)
            seen_categories.add(cat)
    
    # Create regression cases
    regression_cases = []
    for i, failure in enumerate(selected, 1):
        regression_cases.append({
            'id': f"regression_{i:03d}",
            'original_case_id': failure['case_id'],
            'description': f"Regression test for {failure['failure_category']} in {failure['slice_category']} slice",
            'severity': failure['severity'],
            'failure_category': failure['failure_category'],
            'expected_behavior': f"Model should produce valid output without {failure['failure_category']}",
            'input_prompt': failure.get('raw_output_preview', ''),  # Would need actual prompt in real implementation
            'is_fixed': False
        })
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(regression_cases, f, indent=2)
    
    return str(output_path)
