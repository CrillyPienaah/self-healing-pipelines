from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import hashlib
import json

# Import anomaly detectors
from src.monitoring.null_spike_detector import NullSpikeDetector
from src.monitoring.row_count_detector import RowCountDetector
from src.monitoring.type_mismatch_detector import TypeMismatchDetector

# Initialize detectors
null_detector = NullSpikeDetector()
row_count_detector = RowCountDetector()
type_detector = TypeMismatchDetector()

# Import fix generator
try:
    from src.agents.fix_generator import FixGenerator
    fix_generator = FixGenerator()
    print('✓ Fix Generator initialized successfully')
except Exception as e:
    print(f'⚠ Fix Generator initialization failed: {e}')
    fix_generator = None

# Import multi-agent orchestrator
try:
    from src.agents.orchestrator import AgentOrchestrator
    orchestrator = AgentOrchestrator()
    print('✓ Multi-Agent Orchestrator initialized successfully')
except Exception as e:
    print(f'⚠ Multi-Agent Orchestrator initialization failed: {e}')
    orchestrator = None

app = FastAPI(
    title='Self-Healing Pipelines API',
    version='0.5.0',
    description='AI-native platform for autonomous data pipeline remediation'
)

# Enable CORS for React dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:5173',
        'http://localhost:3000',
    ],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
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


class ColumnStats(BaseModel):
    total_rows: int
    null_count: int
    null_percentage: float


class QualitySnapshotRequest(BaseModel):
    columns: List[ColumnInfo]
    row_count: int
    column_stats: Optional[Dict[str, ColumnStats]] = None
    sample_data: Optional[Dict[str, List[Any]]] = None


@app.get('/')
async def root():
    return {
        'message': 'Self-Healing Pipeline Platform API',
        'status': 'ok',
        'version': '0.5.0',
        'features': {
            'schema_drift_detection': True,
            'null_spike_detection': True,
            'row_count_detection': True,
            'type_mismatch_detection': True,
            'llm_fix_generation': fix_generator is not None,
            'multi_agent_analysis': orchestrator is not None
        }
    }


@app.get('/health')
async def health_check():
    return {
        'status': 'healthy',
        'version': '0.5.0',
        'llm_available': fix_generator is not None,
        'multi_agent_available': orchestrator is not None,
        'detectors_count': 4
    }


@app.post('/api/v1/pipelines')
async def create_pipeline(
    name: str,
    description: Optional[str] = None,
    source_type: str = 'dbt'
):
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
    return {
        'pipelines': list(pipelines_db.values()),
        'count': len(pipelines_db)
    }


@app.post('/api/v1/pipelines/{pipeline_id}/snapshots')
async def record_snapshot(
    pipeline_id: int,
    snapshot: SnapshotRequest
):
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


@app.post('/api/v1/pipelines/{pipeline_id}/snapshots/quality')
async def record_quality_snapshot(
    pipeline_id: int,
    snapshot: QualitySnapshotRequest
):
    '''
    Enhanced snapshot with all 4 anomaly types:
    1. Schema drift
    2. Null spikes
    3. Row count anomalies
    4. Type mismatches
    '''
    global next_snapshot_id, next_anomaly_id
    
    if pipeline_id not in pipelines_db:
        raise HTTPException(status_code=404, detail='Pipeline not found')
    
    columns = [col.dict() for col in snapshot.columns]
    detected_anomalies = []
    
    snapshots = snapshots_db[pipeline_id]
    
    # 1. SCHEMA DRIFT
    schema_str = json.dumps(columns, sort_keys=True)
    schema_hash = hashlib.sha256(schema_str.encode()).hexdigest()
    
    if snapshots:
        latest = snapshots[-1]
        
        if latest['schema_hash'] != schema_hash:
            old_count = len(latest['columns'])
            new_count = len(columns)
            
            detected_anomalies.append({
                'id': next_anomaly_id,
                'pipeline_id': pipeline_id,
                'type': 'schema_drift',
                'severity': 'medium',
                'description': f'Schema changed from {old_count} to {new_count} columns',
                'detected_at': datetime.utcnow().isoformat(),
                'resolved': None,
                'details': {
                    'old_columns': latest['columns'],
                    'new_columns': columns
                }
            })
            next_anomaly_id += 1
        
        # 2. NULL SPIKES
        if snapshot.column_stats and latest.get('column_stats'):
            current_stats = {k: v.dict() for k, v in snapshot.column_stats.items()}
            baseline_stats = latest['column_stats']
            
            null_anomalies = null_detector.detect(current_stats, baseline_stats)
            
            for null_anom in null_anomalies:
                detected_anomalies.append({
                    'id': next_anomaly_id,
                    'pipeline_id': pipeline_id,
                    'type': null_anom['type'],
                    'severity': null_anom['severity'],
                    'description': null_anom['description'],
                    'detected_at': datetime.utcnow().isoformat(),
                    'resolved': None,
                    'details': null_anom
                })
                next_anomaly_id += 1
        
        # 3. ROW COUNT ANOMALIES
        if snapshot.row_count and latest.get('row_count'):
            historical = [s['row_count'] for s in snapshots[-7:] if s.get('row_count')]
            
            row_anomalies = row_count_detector.detect(
                current_count=snapshot.row_count,
                baseline_count=latest['row_count'],
                historical_counts=historical if len(historical) >= 3 else None
            )
            
            for row_anom in row_anomalies:
                detected_anomalies.append({
                    'id': next_anomaly_id,
                    'pipeline_id': pipeline_id,
                    'type': row_anom['type'],
                    'severity': row_anom['severity'],
                    'description': row_anom['description'],
                    'detected_at': datetime.utcnow().isoformat(),
                    'resolved': None,
                    'details': row_anom
                })
                next_anomaly_id += 1
        
        # 4. TYPE MISMATCHES
        if snapshot.sample_data:
            expected_schema = {col['name']: col['type'] for col in columns}
            
            type_anomalies = type_detector.detect(expected_schema, snapshot.sample_data)
            
            for type_anom in type_anomalies:
                detected_anomalies.append({
                    'id': next_anomaly_id,
                    'pipeline_id': pipeline_id,
                    'type': 'type_mismatch',
                    'severity': type_anom['severity'],
                    'description': type_anom['description'],
                    'detected_at': datetime.utcnow().isoformat(),
                    'resolved': None,
                    'details': type_anom
                })
                next_anomaly_id += 1
    
    # Store all anomalies
    for anom in detected_anomalies:
        anomalies_db[pipeline_id].append(anom)
    
    # Store snapshot
    snapshot_record = {
        'id': next_snapshot_id,
        'pipeline_id': pipeline_id,
        'schema_hash': schema_hash,
        'columns': columns,
        'row_count': snapshot.row_count,
        'column_stats': {k: v.dict() for k, v in snapshot.column_stats.items()} if snapshot.column_stats else None,
        'snapshot_time': datetime.utcnow().isoformat()
    }
    snapshots_db[pipeline_id].append(snapshot_record)
    next_snapshot_id += 1
    
    return {
        'snapshot_id': snapshot_record['id'],
        'anomalies_detected': len(detected_anomalies),
        'anomaly_types': list(set(a['type'] for a in detected_anomalies)),
        'snapshot_time': snapshot_record['snapshot_time']
    }


@app.get('/api/v1/pipelines/{pipeline_id}/anomalies')
async def get_anomalies(
    pipeline_id: int,
    unresolved_only: bool = True
):
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
    if pipeline_id not in pipelines_db:
        raise HTTPException(status_code=404, detail='Pipeline not found')
    
    snapshots = snapshots_db[pipeline_id][-limit:]
    
    return {
        'snapshots': snapshots,
        'count': len(snapshots)
    }


@app.post('/api/v1/anomalies/{anomaly_id}/propose-fix')
async def propose_fix(anomaly_id: int):
    global next_fix_id
    
    if not fix_generator:
        raise HTTPException(
            status_code=503,
            detail='Fix generation unavailable. OpenAI API key not configured.'
        )
    
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
    
    try:
        fix_proposal = fix_generator.generate_schema_drift_fix(anomaly)
        
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
        raise HTTPException(status_code=500, detail=f'Fix generation failed: {str(e)}')


@app.get('/api/v1/fixes/{fix_id}')
async def get_fix(fix_id: int):
    if fix_id not in fixes_db:
        raise HTTPException(status_code=404, detail='Fix not found')
    return fixes_db[fix_id]


@app.post('/api/v1/fixes/{fix_id}/approve')
async def approve_fix(fix_id: int):
    if fix_id not in fixes_db:
        raise HTTPException(status_code=404, detail='Fix not found')
    
    fix = fixes_db[fix_id]
    fix['status'] = 'approved'
    fix['approved_at'] = datetime.utcnow().isoformat()
    
    return {
        'message': 'Fix approved successfully',
        'fix_id': fix_id,
        'status': 'approved'
    }


@app.post('/api/v1/fixes/{fix_id}/reject')
async def reject_fix(fix_id: int, reason: Optional[str] = None):
    if fix_id not in fixes_db:
        raise HTTPException(status_code=404, detail='Fix not found')
    
    fix = fixes_db[fix_id]
    fix['status'] = 'rejected'
    fix['rejected_at'] = datetime.utcnow().isoformat()
    fix['rejection_reason'] = reason
    
    return {
        'message': 'Fix rejected',
        'fix_id': fix_id,
        'status': 'rejected'
    }


@app.get('/api/v1/anomalies/{anomaly_id}/fixes')
async def get_fixes_for_anomaly(anomaly_id: int):
    fixes = [fix for fix in fixes_db.values() if fix['anomaly_id'] == anomaly_id]
    return {
        'fixes': fixes,
        'count': len(fixes)
    }


@app.post('/api/v1/anomalies/{anomaly_id}/analyze-multi-agent')
async def analyze_with_multi_agent(anomaly_id: int):
    global next_fix_id
    
    if not orchestrator:
        raise HTTPException(
            status_code=503,
            detail='Multi-agent system unavailable. Check configuration.'
        )
    
    anomaly = None
    pipeline_id = None
    for pid in anomalies_db:
        for a in anomalies_db[pid]:
            if a['id'] == anomaly_id:
                anomaly = a
                pipeline_id = pid
                break
        if anomaly:
            break
    
    if not anomaly:
        raise HTTPException(status_code=404, detail='Anomaly not found')
    
    past_fixes = []
    for pid in anomalies_db:
        for past_anomaly in anomalies_db[pid]:
            anomaly_fixes = [f for f in fixes_db.values() if f['anomaly_id'] == past_anomaly['id']]
            if anomaly_fixes:
                past_fixes.append({
                    'anomaly': past_anomaly,
                    'fix': anomaly_fixes[0]
                })
    
    try:
        result = orchestrator.process_anomaly(anomaly, past_fixes)
        
        if result.get('proceed_with_fix') and result.get('proposed_fix'):
            fix_data = result['proposed_fix']
            
            fix_record = {
                'id': next_fix_id,
                'anomaly_id': anomaly_id,
                'proposed_at': datetime.utcnow().isoformat(),
                'fix_type': fix_data['fix_type'],
                'root_cause': fix_data['root_cause'],
                'fix_code': fix_data['fix_code'],
                'rollback_plan': fix_data['rollback_plan'],
                'confidence_score': fix_data['confidence_score'],
                'risks': fix_data['risks'],
                'status': 'pending',
                'applied_at': None,
                'detective_analysis': result.get('detective_analysis'),
                'critic_validation': result.get('critic_validation'),
                'final_recommendation': result.get('final_recommendation'),
                'agent_consensus': result.get('agent_consensus')
            }
            
            fixes_db[next_fix_id] = fix_record
            next_fix_id += 1
            
            result['fix_id'] = fix_record['id']
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Multi-agent analysis failed: {str(e)}'
        )


@app.get('/api/v1/system/agents/status')
async def get_agent_status():
    return {
        'detective_available': orchestrator is not None,
        'fixer_available': fix_generator is not None,
        'critic_available': orchestrator is not None,
        'orchestrator_available': orchestrator is not None,
        'multi_agent_enabled': orchestrator is not None and fix_generator is not None
    }


@app.get('/api/v1/system/detectors/status')
async def get_detector_status():
    return {
        'schema_drift': True,
        'null_spike': null_detector is not None,
        'row_count': row_count_detector is not None,
        'type_mismatch': type_detector is not None,
        'total_detectors': 4,
        'all_operational': all([
            null_detector is not None,
            row_count_detector is not None,
            type_detector is not None
        ])
    }