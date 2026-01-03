"""
Null Spike Detector
Detects when null percentage in columns increases beyond threshold
"""

from typing import Dict, List, Optional
from datetime import datetime


class NullSpikeDetector:
    """
    Detects anomalous increases in null values.
    
    Triggers when:
    - Null percentage increases >20% from baseline
    - Absolute null rate exceeds 30%
    - Critical columns become mostly null (>50%)
    """
    
    def __init__(self, spike_threshold: float = 0.20, absolute_threshold: float = 0.30):
        """
        Args:
            spike_threshold: Relative increase threshold (default 20%)
            absolute_threshold: Absolute null rate threshold (default 30%)
        """
        self.spike_threshold = spike_threshold
        self.absolute_threshold = absolute_threshold
    
    def detect(
        self, 
        current_stats: Dict[str, Dict], 
        baseline_stats: Optional[Dict[str, Dict]] = None
    ) -> List[Dict]:
        """
        Detect null value spikes.
        
        Args:
            current_stats: Current column statistics
                Format: {
                    'column_name': {
                        'total_rows': int,
                        'null_count': int,
                        'null_percentage': float
                    }
                }
            baseline_stats: Historical baseline (optional)
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        for column_name, stats in current_stats.items():
            current_null_pct = stats.get('null_percentage', 0.0)
            
            # Check absolute threshold
            if current_null_pct > self.absolute_threshold:
                anomalies.append({
                    'type': 'null_spike_absolute',
                    'column': column_name,
                    'severity': self._classify_severity(current_null_pct),
                    'description': f'Column "{column_name}" has {current_null_pct*100:.1f}% null values',
                    'current_null_percentage': current_null_pct,
                    'threshold': self.absolute_threshold,
                    'detected_at': datetime.utcnow().isoformat()
                })
            
            # Check relative spike (if baseline available)
            if baseline_stats and column_name in baseline_stats:
                baseline_null_pct = baseline_stats[column_name].get('null_percentage', 0.0)
                
                # Calculate relative increase
                if baseline_null_pct > 0:
                    relative_increase = (current_null_pct - baseline_null_pct) / baseline_null_pct
                else:
                    # Baseline was 0% nulls, any nulls is significant
                    relative_increase = current_null_pct if current_null_pct > 0.05 else 0
                
                if relative_increase > self.spike_threshold:
                    anomalies.append({
                        'type': 'null_spike_relative',
                        'column': column_name,
                        'severity': self._classify_severity_relative(relative_increase),
                        'description': f'Column "{column_name}" null rate increased from {baseline_null_pct*100:.1f}% to {current_null_pct*100:.1f}%',
                        'baseline_null_percentage': baseline_null_pct,
                        'current_null_percentage': current_null_pct,
                        'relative_increase': relative_increase,
                        'detected_at': datetime.utcnow().isoformat()
                    })
        
        return anomalies
    
    def _classify_severity(self, null_percentage: float) -> str:
        """Classify severity based on absolute null percentage"""
        if null_percentage > 0.70:
            return 'critical'  # >70% nulls
        elif null_percentage > 0.50:
            return 'high'      # 50-70% nulls
        elif null_percentage > 0.30:
            return 'medium'    # 30-50% nulls
        else:
            return 'low'       # <30% nulls
    
    def _classify_severity_relative(self, relative_increase: float) -> str:
        """Classify severity based on relative increase"""
        if relative_increase > 2.0:
            return 'critical'  # >200% increase (e.g., 10% → 30%)
        elif relative_increase > 1.0:
            return 'high'      # 100-200% increase
        elif relative_increase > 0.5:
            return 'medium'    # 50-100% increase
        else:
            return 'low'       # 20-50% increase
    
    def calculate_column_stats(self, column_data: List) -> Dict:
        """
        Calculate null statistics for a column.
        
        Args:
            column_data: List of column values (None = null)
        
        Returns:
            Dict with null statistics
        """
        total_rows = len(column_data)
        null_count = sum(1 for val in column_data if val is None)
        null_percentage = null_count / total_rows if total_rows > 0 else 0.0
        
        return {
            'total_rows': total_rows,
            'null_count': null_count,
            'null_percentage': null_percentage
        }


# Example usage and testing
if __name__ == '__main__':
    detector = NullSpikeDetector()
    
    # Test case 1: Absolute threshold violation
    current = {
        'email': {
            'total_rows': 1000,
            'null_count': 400,
            'null_percentage': 0.40  # 40% nulls
        }
    }
    
    anomalies = detector.detect(current)
    print(f"Test 1 - Absolute threshold: {len(anomalies)} anomalies detected")
    if anomalies:
        print(f"  → {anomalies[0]['description']}")
    
    # Test case 2: Relative spike
    baseline = {
        'email': {
            'total_rows': 1000,
            'null_count': 50,
            'null_percentage': 0.05  # 5% nulls
        }
    }
    
    current = {
        'email': {
            'total_rows': 1000,
            'null_count': 300,
            'null_percentage': 0.30  # 30% nulls (6x increase!)
        }
    }
    
    anomalies = detector.detect(current, baseline)
    print(f"\nTest 2 - Relative spike: {len(anomalies)} anomalies detected")
    for a in anomalies:
        print(f"  → {a['type']}: {a['description']} (severity: {a['severity']})")