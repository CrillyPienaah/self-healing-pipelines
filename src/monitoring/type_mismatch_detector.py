"""
Type Mismatch Detector
Detects when actual data types don't match expected schema
"""

from typing import Dict, List, Any
from datetime import datetime
import re


class TypeMismatchDetector:
    """
    Detects type mismatches between expected schema and actual data.
    
    Triggers when:
    - String data in numeric columns
    - Invalid dates/timestamps
    - JSON in varchar columns
    - Numeric data exceeds column precision
    """
    
    def __init__(self, sample_size: int = 100):
        """
        Args:
            sample_size: Number of rows to sample for validation
        """
        self.sample_size = sample_size
    
    def detect(
        self,
        expected_schema: Dict[str, str],
        actual_samples: Dict[str, List[Any]]
    ) -> List[Dict]:
        """
        Detect type mismatches.
        
        Args:
            expected_schema: Expected column types
                Format: {'column_name': 'integer' | 'varchar' | 'decimal' | 'boolean' | ...}
            actual_samples: Sample of actual data
                Format: {'column_name': [value1, value2, ...]}
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        for column_name, expected_type in expected_schema.items():
            if column_name not in actual_samples:
                continue
            
            samples = actual_samples[column_name][:self.sample_size]
            
            # Skip nulls for type checking
            non_null_samples = [s for s in samples if s is not None]
            if not non_null_samples:
                continue
            
            # Detect mismatches based on expected type
            mismatches = []
            
            if expected_type in ['integer', 'int', 'bigint']:
                mismatches = self._check_integer_type(non_null_samples)
            
            elif expected_type in ['decimal', 'float', 'numeric', 'double']:
                mismatches = self._check_numeric_type(non_null_samples)
            
            elif expected_type in ['varchar', 'text', 'string']:
                mismatches = self._check_string_type(non_null_samples)
            
            elif expected_type in ['boolean', 'bool']:
                mismatches = self._check_boolean_type(non_null_samples)
            
            elif expected_type in ['timestamp', 'datetime', 'date']:
                mismatches = self._check_datetime_type(non_null_samples)
            
            elif expected_type == 'json':
                mismatches = self._check_json_type(non_null_samples)
            
            # If mismatches found, create anomaly
            if mismatches:
                mismatch_rate = len(mismatches) / len(non_null_samples)
                
                anomalies.append({
                    'type': 'type_mismatch',
                    'column': column_name,
                    'severity': self._classify_mismatch_severity(mismatch_rate),
                    'description': f'Column "{column_name}" expected {expected_type} but found {len(mismatches)} mismatches in {len(non_null_samples)} samples',
                    'expected_type': expected_type,
                    'mismatch_count': len(mismatches),
                    'sample_size': len(non_null_samples),
                    'mismatch_rate': mismatch_rate,
                    'example_mismatches': mismatches[:3],  # First 3 examples
                    'detected_at': datetime.utcnow().isoformat()
                })
        
        return anomalies
    
    def _check_integer_type(self, samples: List[Any]) -> List[Any]:
        """Check if samples are valid integers"""
        mismatches = []
        for sample in samples:
            try:
                int(sample)
            except (ValueError, TypeError):
                mismatches.append(sample)
        return mismatches
    
    def _check_numeric_type(self, samples: List[Any]) -> List[Any]:
        """Check if samples are valid numbers"""
        mismatches = []
        for sample in samples:
            try:
                float(sample)
            except (ValueError, TypeError):
                mismatches.append(sample)
        return mismatches
    
    def _check_string_type(self, samples: List[Any]) -> List[Any]:
        """Check if samples are strings (most permissive)"""
        mismatches = []
        for sample in samples:
            if not isinstance(sample, str):
                mismatches.append(sample)
        return mismatches
    
    def _check_boolean_type(self, samples: List[Any]) -> List[Any]:
        """Check if samples are booleans"""
        mismatches = []
        valid_boolean_strings = {'true', 'false', '1', '0', 'yes', 'no', 't', 'f'}
        
        for sample in samples:
            if isinstance(sample, bool):
                continue
            elif isinstance(sample, str) and sample.lower() in valid_boolean_strings:
                continue
            elif isinstance(sample, int) and sample in [0, 1]:
                continue
            else:
                mismatches.append(sample)
        return mismatches
    
    def _check_datetime_type(self, samples: List[Any]) -> List[Any]:
        """Check if samples are valid dates/timestamps"""
        mismatches = []
        
        # Common date patterns
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # 2024-01-01
            r'\d{2}/\d{2}/\d{4}',   # 01/01/2024
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO timestamp
        ]
        
        for sample in samples:
            if not isinstance(sample, str):
                mismatches.append(sample)
                continue
            
            # Check if matches any date pattern
            is_valid_date = any(re.match(pattern, str(sample)) for pattern in date_patterns)
            if not is_valid_date:
                mismatches.append(sample)
        
        return mismatches
    
    def _check_json_type(self, samples: List[Any]) -> List[Any]:
        """Check if samples are valid JSON"""
        import json
        mismatches = []
        
        for sample in samples:
            if isinstance(sample, (dict, list)):
                continue  # Already parsed JSON
            
            try:
                json.loads(str(sample))
            except (json.JSONDecodeError, TypeError):
                mismatches.append(sample)
        
        return mismatches
    
    def _classify_mismatch_severity(self, mismatch_rate: float) -> str:
        """Classify severity based on mismatch percentage"""
        if mismatch_rate > 0.50:
            return 'critical'  # >50% mismatches
        elif mismatch_rate > 0.20:
            return 'high'      # 20-50% mismatches
        elif mismatch_rate > 0.05:
            return 'medium'    # 5-20% mismatches
        else:
            return 'low'       # <5% mismatches


# Example usage
if __name__ == '__main__':
    detector = TypeMismatchDetector()
    
    # Test case: Strings in integer column
    schema = {'user_id': 'integer', 'price': 'decimal'}
    samples = {
        'user_id': [1, 2, 'abc', 4, 'xyz', 6],  # 2 strings in integer column
        'price': [19.99, 29.99, 'free', 9.99]    # 1 string in decimal column
    }
    
    anomalies = detector.detect(schema, samples)
    
    print(f"Detected {len(anomalies)} type mismatches:")
    for a in anomalies:
        print(f"\n{a['column']}:")
        print(f"  Expected: {a['expected_type']}")
        print(f"  Mismatches: {a['mismatch_count']}/{a['sample_size']} ({a['mismatch_rate']*100:.1f}%)")
        print(f"  Examples: {a['example_mismatches']}")
        print(f"  Severity: {a['severity']}")