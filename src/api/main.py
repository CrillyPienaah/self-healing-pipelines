from fastapi import FastAPI, HTTPException
from typing import List, Optional
from datetime import datetime
import hashlib
import json

app = FastAPI(
    title='Self-Healing Pipelines API',
    version='0.1.0',
    description='AI-native platform for autonomous data pipeline remediation'
)

# In-memory storage (will replace with database later)
pipelines_db = {}
snapshots_db = {}
anomalies_db = {}
next_pipeline_id = 1
next_snapshot_id = 1
next_anomaly_id = 1


@app.get('/')
async def root():
    return {
        'message': 'Self-Healing Pipeline Platform API',
        'status': 'ok',
        'version': '0.1.0'
    }


@app.get('/health')
async def health_check():
    return {'status': 'healthy', 'version': '0.1.0'}


@app.post('/api/v1/pipelines')
async def create_pipeline(
    name: str,
    description: Optional[str] = None,
    source_type: str = 'dbt'
):
    '''Register a new pipeline for monitoring'''
    global next_pipeline_id
    
    # Check if pipeline already exists
    for pid, pipeline in pipelines_db.items():
        if pipeline['name'] == name:
            raise HTTPException(status_code=400, detail='Pipeline already exists')
    
    pipeline_id = next_pipeline_id
    pipeline = {
        'id': pipeline_id,
        'name': name,
        'description': description,
        'source_type': source_type,
        'created_at': datetime.utcnow().isoformat()
    }
    
    pipelines_db[pipeline_id] = pipeline
    snapshots_db[pipeline_id] = []
    anomalies_db[pipeline_id] = []
    next_pipeline_id += 1
    
    return pipeline


@app.get('/api/v1/pipelines')
async def list_pipelines():
    '''List all registered pipelines'''
    return {
        'pipelines': list(pipelines_db.values()),
        'count': len(pipelines_db)
    }


@app.post('/api/v1/pipelines/{pipeline_id}/snapshots')
async def record_snapshot(
    pipeline_id: int,
    columns: List[dict],
    row_count: Optional[int] = None
):
    '''Record a schema snapshot for drift detection'''
    global next_snapshot_id, next_anomaly_id
    
    # Verify pipeline exists
    if pipeline_id not in pipelines_db:
        raise HTTPException(status_code=404, detail='Pipeline not found')
    
    # Calculate schema hash
    schema_str = json.dumps(columns, sort_keys=True)
    schema_hash = hashlib.sha256(schema_str.encode()).hexdigest()
    
    # Check for schema drift
    drift_detected = False
    snapshots = snapshots_db[pipeline_id]
    
    if snapshots:
        latest_snapshot = snapshots[-1]
        if latest_snapshot['schema_hash'] != schema_hash:
            drift_detected = True
            
            # Create anomaly record
            anomaly = {
                'id': next_anomaly_id,
                'pipeline_id': pipeline_id,
                'type': 'schema_drift',
                'severity': 'medium',
                'description': f'Schema changed from {len(latest_snapshot["columns"])} to {len(columns)} columns',
                'detected_at': datetime.utcnow().isoformat(),
                'resolved': None,
                'details': {
                    'old_columns': latest_snapshot['columns'],
                    'new_columns': columns
                }
            }
            anomalies_db[pipeline_id].append(anomaly)
            next_anomaly_id += 1
    
    # Save snapshot
    snapshot = {
        'id': next_snapshot_id,
        'pipeline_id': pipeline_id,
        'schema_hash': schema_hash,
        'columns': columns,
        'row_count': row_count,
        'snapshot_time': datetime.utcnow().isoformat()
    }
    snapshots_db[pipeline_id].append(snapshot)
    next_snapshot_id += 1
    
    return {
        'snapshot_id': snapshot['id'],
        'schema_hash': schema_hash,
        'drift_detected': drift_detected,
        'snapshot_time': snapshot['snapshot_time']
    }


@app.get('/api/v1/pipelines/{pipeline_id}/anomalies')
async def get_anomalies(
    pipeline_id: int,
    unresolved_only: bool = True
):
    '''Get anomalies for a pipeline'''
    if pipeline_id not in pipelines_db:
        raise HTTPException(status_code=404, detail='Pipeline not found')
    
    anomalies = anomalies_db[pipeline_id]
    
    if unresolved_only:
        anomalies = [a for a in anomalies if a['resolved'] is None]
    
    return {
        'anomalies': anomalies,
        'count': len(anomalies)
    }


@app.get('/api/v1/pipelines/{pipeline_id}/snapshots')
async def get_snapshots(pipeline_id: int, limit: int = 10):
    '''Get recent snapshots for a pipeline'''
    if pipeline_id not in pipelines_db:
        raise HTTPException(status_code=404, detail='Pipeline not found')
    
    snapshots = snapshots_db[pipeline_id][-limit:]
    
    return {
        'snapshots': snapshots,
        'count': len(snapshots)
    }
