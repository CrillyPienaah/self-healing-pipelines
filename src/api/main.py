from fastapi import FastAPI, HTTPException
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel
import hashlib
import json

# Import fix generator
try:
    from src.agents.fix_generator import FixGenerator
    fix_generator = FixGenerator()
    print(' Fix Generator initialized successfully')
except Exception as e:
    print(f' Fix Generator initialization failed: {e}')
    fix_generator = None

app = FastAPI(
    title='Self-Healing Pipelines API',
    version='0.2.0',
    description='AI-native platform for autonomous data pipeline remediation'
)

# In-memory storage
pipelines_db = {}
snapshots_db = {}
anomalies_db = {}
fixes_db = {}
next_pipeline_id = 1
next_snapshot_id = 1
next_anomaly_id = 1
next_fix_id = 1


# Pydantic models
class ColumnInfo(BaseModel):
    name: str
    type: str


class SnapshotRequest(BaseModel):
    columns: List[ColumnInfo]
    row_count: Optional[int] = None


@app.get('/')
async def root():
    return {
        'message': 'Self-Healing Pipeline Platform API',
        'status': 'ok',
        'version': '0.2.0',
        'features': {
            'schema_drift_detection': True,
            'llm_fix_generation': fix_generator is not None
        }
    }


@app.get('/health')
async def health_check():
    return {
        'status': 'healthy',
        'version': '0.2.0',
        'llm_available': fix_generator is not None
    }


@app.post('/api/v1/pipelines')
async def create_pipeline(
    name: str,
    description: Optional[str] = None,
    source_type: str = 'dbt'
):
    '''Register a new pipeline for monitoring'''
    global next_pipeline_id
    
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
    snapshot: SnapshotRequest
):
    '''Record a schema snapshot for drift detection'''
    global next_snapshot_id, next_anomaly_id
    
    if pipeline_id not in pipelines_db:
        raise HTTPException(status_code=404, detail='Pipeline not found')
    
    columns = [col.dict() for col in snapshot.columns]
    
    schema_str = json.dumps(columns, sort_keys=True)
    schema_hash = hashlib.sha256(schema_str.encode()).hexdigest()
    
    drift_detected = False
    snapshots = snapshots_db[pipeline_id]
    
    if snapshots:
        latest_snapshot = snapshots[-1]
        if latest_snapshot['schema_hash'] != schema_hash:
            drift_detected = True
            
            old_col_count = len(latest_snapshot['columns'])
            new_col_count = len(columns)
            description = f'Schema changed from {old_col_count} to {new_col_count} columns'
            
            anomaly = {
                'id': next_anomaly_id,
                'pipeline_id': pipeline_id,
                'type': 'schema_drift',
                'severity': 'medium',
                'description': description,
                'detected_at': datetime.utcnow().isoformat(),
                'resolved': None,
                'details': {
                    'old_columns': latest_snapshot['columns'],
                    'new_columns': columns
                }
            }
            anomalies_db[pipeline_id].append(anomaly)
            next_anomaly_id += 1
    
    snapshot_record = {
        'id': next_snapshot_id,
        'pipeline_id': pipeline_id,
        'schema_hash': schema_hash,
        'columns': columns,
        'row_count': snapshot.row_count,
        'snapshot_time': datetime.utcnow().isoformat()
    }
    snapshots_db[pipeline_id].append(snapshot_record)
    next_snapshot_id += 1
    
    return {
        'snapshot_id': snapshot_record['id'],
        'schema_hash': schema_hash,
        'drift_detected': drift_detected,
        'snapshot_time': snapshot_record['snapshot_time']
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


# ============= LLM FIX GENERATION ENDPOINTS =============

@app.post('/api/v1/anomalies/{anomaly_id}/propose-fix')
async def propose_fix(anomaly_id: int):
    '''Generate a fix proposal for an anomaly using GPT-4'''
    global next_fix_id
    
    if not fix_generator:
        raise HTTPException(
            status_code=503,
            detail='Fix generation unavailable. OpenAI API key not configured.'
        )
    
    # Find the anomaly
    anomaly = None
    for pipeline_id in anomalies_db:
        for a in anomalies_db[pipeline_id]:
            if a['id'] == anomaly_id:
                anomaly = a
                break
        if anomaly:
            break
    
    if not anomaly:
        raise HTTPException(status_code=404, detail='Anomaly not found')
    
    # Generate fix using GPT-4
    try:
        fix_proposal = fix_generator.generate_schema_drift_fix(anomaly)
        
        # Store fix
        fix_record = {
            'id': next_fix_id,
            'anomaly_id': anomaly_id,
            'proposed_at': datetime.utcnow().isoformat(),
            'fix_type': fix_proposal['fix_type'],
            'root_cause': fix_proposal['root_cause'],
            'fix_code': fix_proposal['fix_code'],
            'rollback_plan': fix_proposal['rollback_plan'],
            'confidence_score': fix_proposal['confidence_score'],
            'risks': fix_proposal['risks'],
            'status': 'pending',
            'applied_at': None
        }
        
        fixes_db[next_fix_id] = fix_record
        next_fix_id += 1
        
        return fix_record
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Fix generation failed: {str(e)}'
        )


@app.get('/api/v1/fixes/{fix_id}')
async def get_fix(fix_id: int):
    '''Get details of a proposed fix'''
    if fix_id not in fixes_db:
        raise HTTPException(status_code=404, detail='Fix not found')
    
    return fixes_db[fix_id]


@app.post('/api/v1/fixes/{fix_id}/approve')
async def approve_fix(fix_id: int):
    '''Approve a proposed fix'''
    if fix_id not in fixes_db:
        raise HTTPException(status_code=404, detail='Fix not found')
    
    fix = fixes_db[fix_id]
    fix['status'] = 'approved'
    fix['approved_at'] = datetime.utcnow().isoformat()
    
    return {
        'message': 'Fix approved successfully',
        'fix_id': fix_id,
        'status': 'approved',
        'next_step': 'Apply fix to production pipeline'
    }


@app.post('/api/v1/fixes/{fix_id}/reject')
async def reject_fix(fix_id: int, reason: Optional[str] = None):
    '''Reject a proposed fix'''
    if fix_id not in fixes_db:
        raise HTTPException(status_code=404, detail='Fix not found')
    
    fix = fixes_db[fix_id]
    fix['status'] = 'rejected'
    fix['rejected_at'] = datetime.utcnow().isoformat()
    fix['rejection_reason'] = reason
    
    return {
        'message': 'Fix rejected',
        'fix_id': fix_id,
        'status': 'rejected',
        'reason': reason
    }


@app.get('/api/v1/anomalies/{anomaly_id}/fixes')
async def get_fixes_for_anomaly(anomaly_id: int):
    '''Get all fix proposals for an anomaly'''
    fixes = [fix for fix in fixes_db.values() if fix['anomaly_id'] == anomaly_id]
    
    return {
        'fixes': fixes,
        'count': len(fixes)
    }
