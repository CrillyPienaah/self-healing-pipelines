"""
Row Count Anomaly Detector
Detects sudden changes in data volume
"""

from typing import Dict, List, Optional
from datetime import datetime
import statistics


class RowCountDetector:
    """
    Detects anomalous changes in row counts.
    
    Triggers when:
    - Row count drops >50% from baseline
    - Row count spikes >200% from baseline  
    - Row count deviates >3 standard deviations from historical average
    """
    
    def __init__(
        self, 
        drop_threshold: float = 0.50,
        spike_threshold: float = 2.00,
        stddev_threshold: float = 3.0
    ):
        """
        Args:
            drop_threshold: Relative drop threshold (default 50%)
            spike_threshold: Relative spike threshold (default 200%)
            stddev_threshold: Standard deviation threshold (default 3 sigma)
        """
        self.drop_threshold = drop_threshold
        self.spike_threshold = spike_threshold
        self.stddev_threshold = stddev_threshold
    
    def detect(
        self,
        current_count: int,
        baseline_count: Optional[int] = None,
        historical_counts: Optional[List[int]] = None
    ) -> List[Dict]:
        """
        Detect row count anomalies.
        
        Args:
            current_count: Current number of rows
            baseline_count: Expected row count (e.g., yesterday's count)
            historical_counts: List of past counts for statistical analysis
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Method 1: Compare to baseline (if available)
        if baseline_count and baseline_count > 0:
            relative_change = (current_count - baseline_count) / baseline_count
            
            # Detect drops
            if relative_change < -self.drop_threshold:
                anomalies.append({
                    'type': 'row_count_drop',
                    'severity': self._classify_drop_severity(relative_change),
                    'description': f'Row count dropped {abs(relative_change)*100:.1f}% from {baseline_count} to {current_count}',
                    'baseline_count': baseline_count,
                    'current_count': current_count,
                    'relative_change': relative_change,
                    'detected_at': datetime.utcnow().isoformat()
                })
            
            # Detect spikes
            elif relative_change > self.spike_threshold:
                anomalies.append({
                    'type': 'row_count_spike',
                    'severity': self._classify_spike_severity(relative_change),
                    'description': f'Row count spiked {relative_change*100:.1f}% from {baseline_count} to {current_count}',
                    'baseline_count': baseline_count,
                    'current_count': current_count,
                    'relative_change': relative_change,
                    'detected_at': datetime.utcnow().isoformat()
                })
        
        # Method 2: Statistical analysis (if historical data available)
        if historical_counts and len(historical_counts) >= 7:  # At least 1 week of data
            mean_count = statistics.mean(historical_counts)
            stddev_count = statistics.stdev(historical_counts) if len(historical_counts) > 1 else 0
            
            if stddev_count > 0:
                z_score = abs(current_count - mean_count) / stddev_count
                
                if z_score > self.stddev_threshold:
                    anomalies.append({
                        'type': 'row_count_outlier',
                        'severity': self._classify_outlier_severity(z_score),
                        'description': f'Row count {current_count} is {z_score:.1f} standard deviations from mean {mean_count:.0f}',
                        'current_count': current_count,
                        'historical_mean': mean_count,
                        'historical_stddev': stddev_count,
                        'z_score': z_score,
                        'detected_at': datetime.utcnow().isoformat()
                    })
        
        return anomalies
    
    def _classify_drop_severity(self, relative_change: float) -> str:
        """Classify severity of row count drops"""
        drop_magnitude = abs(relative_change)
        
        if drop_magnitude > 0.95:
            return 'critical'  # >95% drop (near-empty table!)
        elif drop_magnitude > 0.80:
            return 'high'      # 80-95% drop
        elif drop_magnitude > 0.60:
            return 'medium'    # 60-80% drop
        else:
            return 'low'       # 50-60% drop
    
    def _classify_spike_severity(self, relative_change: float) -> str:
        """Classify severity of row count spikes"""
        if relative_change > 10.0:
            return 'critical'  # >1000% spike (10x increase!)
        elif relative_change > 5.0:
            return 'high'      # 500-1000% spike
        elif relative_change > 3.0:
            return 'medium'    # 300-500% spike
        else:
            return 'low'       # 200-300% spike
    
    def _classify_outlier_severity(self, z_score: float) -> str:
        """Classify severity based on statistical outlier magnitude"""
        if z_score > 5.0:
            return 'critical'  # >5 sigma
        elif z_score > 4.0:
            return 'high'      # 4-5 sigma
        elif z_score > 3.0:
            return 'medium'    # 3-4 sigma (our threshold)
        else:
            return 'low'


# Example usage and testing
if __name__ == '__main__':
    detector = RowCountDetector()
    
    # Test case 1: Sudden drop
    print("Test 1 - Row count drop:")
    anomalies = detector.detect(current_count=500, baseline_count=10000)
    if anomalies:
        print(f"  ✓ Detected: {anomalies[0]['description']}")
        print(f"  Severity: {anomalies[0]['severity']}")
    
    # Test case 2: Sudden spike
    print("\nTest 2 - Row count spike:")
    anomalies = detector.detect(current_count=25000, baseline_count=5000)
    if anomalies:
        print(f"  ✓ Detected: {anomalies[0]['description']}")
        print(f"  Severity: {anomalies[0]['severity']}")
    
    # Test case 3: Statistical outlier
    print("\nTest 3 - Statistical outlier:")
    historical = [10000, 10200, 9800, 10100, 9900, 10300, 10000]  # Stable around 10k
    anomalies = detector.detect(
        current_count=500,  # Sudden drop to 500
        historical_counts=historical
    )
    if anomalies:
        print(f"  ✓ Detected: {anomalies[0]['description']}")
        print(f"  Z-score: {anomalies[0]['z_score']:.2f}")
        print(f"  Severity: {anomalies[0]['severity']}")