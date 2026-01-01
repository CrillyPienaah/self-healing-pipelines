import requests
import json

BASE_URL = 'http://localhost:8000'

def test_complete_workflow():
    # 1. Create pipeline
    response = requests.post(
        f'{BASE_URL}/api/v1/pipelines',
        params={'name': 'test_pipeline', 'description': 'Test', 'source_type': 'dbt'}
    )
    assert response.status_code == 201
    pipeline_id = response.json()['id']
    print(f' Pipeline created: {pipeline_id}')
    
    # 2. First snapshot (3 columns)
    snapshot1 = {
        'columns': [
            {'name': 'order_id', 'type': 'integer'},
            {'name': 'customer_id', 'type': 'integer'},
            {'name': 'total', 'type': 'decimal'}
        ],
        'row_count': 1000
    }
    response = requests.post(f'{BASE_URL}/api/v1/pipelines/{pipeline_id}/snapshots', json=snapshot1)
    assert response.status_code == 200
    assert response.json()['drift_detected'] == False
    print(' First snapshot recorded (no drift)')
    
    # 3. Second snapshot (4 columns - drift!)
    snapshot2 = {
        'columns': [
            {'name': 'order_id', 'type': 'integer'},
            {'name': 'customer_id', 'type': 'integer'},
            {'name': 'total', 'type': 'decimal'},
            {'name': 'order_date', 'type': 'date'}
        ],
        'row_count': 1050
    }
    response = requests.post(f'{BASE_URL}/api/v1/pipelines/{pipeline_id}/snapshots', json=snapshot2)
    assert response.status_code == 200
    assert response.json()['drift_detected'] == True
    print(' Second snapshot recorded (DRIFT DETECTED!)')
    
    # 4. Check anomalies
    response = requests.get(f'{BASE_URL}/api/v1/pipelines/{pipeline_id}/anomalies')
    assert response.status_code == 200
    anomalies = response.json()['anomalies']
    assert len(anomalies) == 1
    assert anomalies[0]['type'] == 'schema_drift'
    assert anomalies[0]['description'] == 'Schema changed from 3 to 4 columns'
    print(' Anomaly detected and recorded correctly')
    
    print('\n ALL TESTS PASSED!')

if __name__ == '__main__':
    test_complete_workflow()
