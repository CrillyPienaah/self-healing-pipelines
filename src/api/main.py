from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import hashlib
import json
import csv
import io

# Database imports
from src.db.database import get_db, engine
from src.db import models, crud

# Import anomaly detectors
from src.monitoring.null_spike_detector import NullSpikeDetector
from src.monitoring.row_count_detector import RowCountDetector
from src.monitoring.type_mismatch_detector import TypeMismatchDetector

# Initialize detectors
null_detector = NullSpikeDetector()
row_count_detector = RowCountDetector()
type_detector = TypeMismatchDetector()

# Import AI agents
try:
    from src.agents.fix_generator import FixGenerator
    fix_generator = FixGenerator()
    print('✓ Fix Generator initialized successfully')
except Exception as e:
    print(f'⚠ Fix Generator initialization failed: {e}')
    fix_generator = None

try:
    from src.agents.orchestrator import AgentOrchestrator
    orchestrator = AgentOrchestrator()
    print('✓ Multi-Agent Orchestrator initialized successfully')
except Exception as e:
    print(f'⚠ Multi-Agent Orchestrator initialization failed: {e}')
    orchestrator = None

# Create tables on startup
try:
    if engine:
        models.Base.metadata.create_all(bind=engine)
        print('✓ Database tables initialized')
except Exception as e:
    print(f'⚠ Database table creation failed: {e}')

app = FastAPI(
    title='Self-Healing Pipelines API',
    version='0.6.0',
    description='AI-native platform for autonomous data pipeline remediation'
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://localhost:3000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

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

# Helper
def model_to_dict(obj):
    if obj is None:
        return None
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


# ============= CORE ENDPOINTS =============

@app.get('/')
async def root():
    return {
        'message': 'Self-Healing Pipeline Platform API',
        'status': 'ok',
        'version': '0.6.0',
        'persistence': 'postgresql',
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
        'version': '0.6.0',
        'database': 'postgresql',
        'llm_available': fix_generator is not None,
        'multi_agent_available': orchestrator is not None,
        'detectors_count': 4
    }


# ============= PIPELINE MANAGEMENT =============

@app.post('/api/v1/pipelines')
async def create_pipeline_endpoint(
    name: str,
    description: Optional[str] = None,
    source_type: str = 'dbt',
    db: Session = Depends(get_db)
):
    existing = crud.get_pipeline_by_name(db, name)
    if existing:
        raise HTTPException(status_code=400, detail='Pipeline already exists')
    
    pipeline = crud.create_pipeline(db, name, description, source_type)
    crud.create_audit_log(db, 'create_pipeline', 'pipeline', pipeline.id, {'name': name})
    
    return model_to_dict(pipeline)

@app.get('/api/v1/pipelines')
async def list_pipelines(db: Session = Depends(get_db)):
    pipelines = crud.get_all_pipelines(db)
    return {'pipelines': [model_to_dict(p) for p in pipelines], 'count': len(pipelines)}


# ============= SNAPSHOT & DETECTION =============

@app.post('/api/v1/pipelines/{pipeline_id}/snapshots')
async def record_snapshot(pipeline_id: int, snapshot: SnapshotRequest, db: Session = Depends(get_db)):
    pipeline = crud.get_pipeline(db, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail='Pipeline not found')
    
    columns = [col.dict() for col in snapshot.columns]
    schema_str = json.dumps(columns, sort_keys=True)
    schema_hash = hashlib.sha256(schema_str.encode()).hexdigest()
    
    drift_detected = False
    latest = crud.get_latest_snapshot(db, pipeline_id)
    
    if latest and latest.schema_hash != schema_hash:
        drift_detected = True
        old_count = len(latest.columns)
        new_count = len(columns)
        crud.create_anomaly(db, pipeline_id, 'schema_drift', 'medium',
            f'Schema changed from {old_count} to {new_count} columns',
            {'old_columns': latest.columns, 'new_columns': columns})
    
    snapshot_record = crud.create_snapshot(db, pipeline_id, schema_hash, columns, snapshot.row_count)
    
    return {
        'snapshot_id': snapshot_record.id,
        'schema_hash': schema_hash,
        'drift_detected': drift_detected,
        'snapshot_time': snapshot_record.snapshot_time.isoformat()
    }

@app.post('/api/v1/pipelines/{pipeline_id}/snapshots/quality')
async def record_quality_snapshot(pipeline_id: int, snapshot: QualitySnapshotRequest, db: Session = Depends(get_db)):
    pipeline = crud.get_pipeline(db, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail='Pipeline not found')
    
    columns = [col.dict() for col in snapshot.columns]
    detected_anomalies = []
    
    schema_str = json.dumps(columns, sort_keys=True)
    schema_hash = hashlib.sha256(schema_str.encode()).hexdigest()
    latest = crud.get_latest_snapshot(db, pipeline_id)
    
    if latest:
        # Schema drift
        if latest.schema_hash != schema_hash:
            anom = crud.create_anomaly(db, pipeline_id, 'schema_drift', 'medium',
                f'Schema changed from {len(latest.columns)} to {len(columns)} columns',
                {'old_columns': latest.columns, 'new_columns': columns})
            detected_anomalies.append(anom.type)
        
        # Null spikes
        if snapshot.column_stats and latest.column_stats:
            current_stats = {k: v.dict() for k, v in snapshot.column_stats.items()}
            null_anomalies = null_detector.detect(current_stats, latest.column_stats)
            for null_anom in null_anomalies:
                anom = crud.create_anomaly(db, pipeline_id, null_anom['type'], 
                    null_anom['severity'], null_anom['description'], null_anom)
                detected_anomalies.append(anom.type)
        
        # Row count
        if snapshot.row_count and latest.row_count:
            snapshots_list = crud.get_snapshots(db, pipeline_id, 7)
            historical = [s.row_count for s in snapshots_list if s.row_count]
            row_anomalies = row_count_detector.detect(snapshot.row_count, latest.row_count,
                historical if len(historical) >= 3 else None)
            for row_anom in row_anomalies:
                anom = crud.create_anomaly(db, pipeline_id, row_anom['type'],
                    row_anom['severity'], row_anom['description'], row_anom)
                detected_anomalies.append(anom.type)
        
        # Type mismatches
        if snapshot.sample_data:
            expected_schema = {col['name']: col['type'] for col in columns}
            type_anomalies = type_detector.detect(expected_schema, snapshot.sample_data)
            for type_anom in type_anomalies:
                anom = crud.create_anomaly(db, pipeline_id, 'type_mismatch',
                    type_anom['severity'], type_anom['description'], type_anom)
                detected_anomalies.append(anom.type)
    
    snapshot_record = crud.create_snapshot(db, pipeline_id, schema_hash, columns, snapshot.row_count,
        {k: v.dict() for k, v in snapshot.column_stats.items()} if snapshot.column_stats else None)
    
    return {
        'snapshot_id': snapshot_record.id,
        'anomalies_detected': len(detected_anomalies),
        'anomaly_types': list(set(detected_anomalies)),
        'snapshot_time': snapshot_record.snapshot_time.isoformat()
    }

@app.get('/api/v1/pipelines/{pipeline_id}/snapshots')
async def get_snapshots_endpoint(pipeline_id: int, limit: int = 10, db: Session = Depends(get_db)):
    pipeline = crud.get_pipeline(db, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail='Pipeline not found')
    snapshots = crud.get_snapshots(db, pipeline_id, limit)
    return {'snapshots': [model_to_dict(s) for s in snapshots], 'count': len(snapshots)}


# ============= ANOMALY MANAGEMENT =============

@app.get('/api/v1/pipelines/{pipeline_id}/anomalies')
async def get_anomalies_endpoint(pipeline_id: int, unresolved_only: bool = True, db: Session = Depends(get_db)):
    pipeline = crud.get_pipeline(db, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail='Pipeline not found')
    anomalies = crud.get_anomalies(db, pipeline_id, unresolved_only)
    return {'anomalies': [model_to_dict(a) for a in anomalies], 'count': len(anomalies)}


# ============= FIX GENERATION =============

@app.post('/api/v1/anomalies/{anomaly_id}/propose-fix')
async def propose_fix(anomaly_id: int, db: Session = Depends(get_db)):
    if not fix_generator:
        raise HTTPException(status_code=503, detail='Fix generation unavailable')
    
    anomaly = crud.get_anomaly(db, anomaly_id)
    if not anomaly:
        raise HTTPException(status_code=404, detail='Anomaly not found')
    
    try:
        anomaly_dict = model_to_dict(anomaly)
        fix_proposal = fix_generator.generate_schema_drift_fix(anomaly_dict)
        
        fix_record = crud.create_fix(db, anomaly_id, fix_proposal['fix_type'],
            fix_proposal['root_cause'], fix_proposal['fix_code'], fix_proposal['rollback_plan'],
            fix_proposal['confidence_score'], fix_proposal['risks'])
        
        crud.create_audit_log(db, 'propose_fix', 'fix', fix_record.id,
            {'anomaly_id': anomaly_id, 'confidence': fix_proposal['confidence_score']},
            'gpt-4', fix_proposal['confidence_score'] / 100.0)
        
        return model_to_dict(fix_record)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Fix generation failed: {str(e)}')

@app.get('/api/v1/fixes/{fix_id}')
async def get_fix_endpoint(fix_id: int, db: Session = Depends(get_db)):
    fix = crud.get_fix(db, fix_id)
    if not fix:
        raise HTTPException(status_code=404, detail='Fix not found')
    return model_to_dict(fix)

@app.post('/api/v1/fixes/{fix_id}/approve')
async def approve_fix_endpoint(fix_id: int, db: Session = Depends(get_db)):
    fix = crud.approve_fix(db, fix_id)
    if not fix:
        raise HTTPException(status_code=404, detail='Fix not found')
    crud.create_audit_log(db, 'approve_fix', 'fix', fix_id, {'status': 'approved'})
    return {'message': 'Fix approved successfully', 'fix_id': fix_id, 'status': 'approved'}

@app.post('/api/v1/fixes/{fix_id}/reject')
async def reject_fix_endpoint(fix_id: int, reason: Optional[str] = None, db: Session = Depends(get_db)):
    fix = crud.reject_fix(db, fix_id, reason)
    if not fix:
        raise HTTPException(status_code=404, detail='Fix not found')
    crud.create_audit_log(db, 'reject_fix', 'fix', fix_id, {'status': 'rejected', 'reason': reason})
    return {'message': 'Fix rejected', 'fix_id': fix_id, 'status': 'rejected'}

@app.get('/api/v1/anomalies/{anomaly_id}/fixes')
async def get_fixes_for_anomaly_endpoint(anomaly_id: int, db: Session = Depends(get_db)):
    fixes = crud.get_fixes_for_anomaly(db, anomaly_id)
    return {'fixes': [model_to_dict(f) for f in fixes], 'count': len(fixes)}


# ============= MULTI-AGENT ANALYSIS =============

@app.post('/api/v1/anomalies/{anomaly_id}/analyze-multi-agent')
async def analyze_with_multi_agent(anomaly_id: int, db: Session = Depends(get_db)):
    if not orchestrator:
        raise HTTPException(status_code=503, detail='Multi-agent system unavailable')
    
    anomaly = crud.get_anomaly(db, anomaly_id)
    if not anomaly:
        raise HTTPException(status_code=404, detail='Anomaly not found')
    
    all_anomalies = db.query(models.Anomaly).all()
    past_fixes = []
    for past_anom in all_anomalies:
        fixes = crud.get_fixes_for_anomaly(db, past_anom.id)
        if fixes:
            past_fixes.append({'anomaly': model_to_dict(past_anom), 'fix': model_to_dict(fixes[0])})
    
    try:
        anomaly_dict = model_to_dict(anomaly)
        result = orchestrator.process_anomaly(anomaly_dict, past_fixes)
        
        if result.get('proceed_with_fix') and result.get('proposed_fix'):
            fix_data = result['proposed_fix']
            fix_record = crud.create_fix(db, anomaly_id, fix_data['fix_type'],
                fix_data['root_cause'], fix_data['fix_code'], fix_data['rollback_plan'],
                fix_data['confidence_score'], fix_data['risks'],
                result.get('detective_analysis'), result.get('critic_validation'),
                result.get('final_recommendation'), result.get('agent_consensus'))
            
            crud.create_audit_log(db, 'multi_agent_analysis', 'fix', fix_record.id,
                {'anomaly_id': anomaly_id}, 'gpt-4-multi-agent', fix_data['confidence_score'] / 100.0)
            result['fix_id'] = fix_record.id
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Multi-agent analysis failed: {str(e)}')


# ============= SYSTEM STATUS =============

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
        'all_operational': all([null_detector, row_count_detector, type_detector])
    }


# ============= RESEARCH ENDPOINTS =============

@app.get('/api/v1/research/statistics')
async def get_research_statistics(db: Session = Depends(get_db)):
    all_anomalies = db.query(models.Anomaly).all()
    all_fixes = db.query(models.Fix).filter(models.Fix.detective_analysis != None).all()
    
    anomaly_types = {}
    severity_dist = {}
    for anom in all_anomalies:
        anomaly_types[anom.type] = anomaly_types.get(anom.type, 0) + 1
        severity_dist[anom.severity] = severity_dist.get(anom.severity, 0) + 1
    
    total_multi_agent = len(all_fixes)
    full_consensus = sum(1 for f in all_fixes if f.agent_consensus and f.agent_consensus.get('all_agents_agree'))
    
    confidences = [f.confidence_score for f in all_fixes if f.confidence_score]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    
    safety_scores = [f.critic_validation.get('safety_score', 0) for f in all_fixes 
        if f.critic_validation and isinstance(f.critic_validation, dict)]
    avg_safety = sum(safety_scores) / len(safety_scores) if safety_scores else 0
    
    urgency_dist = {}
    for f in all_fixes:
        if f.detective_analysis and isinstance(f.detective_analysis, dict):
            urgency = f.detective_analysis.get('urgency', 'unknown')
            urgency_dist[urgency] = urgency_dist.get(urgency, 0) + 1
    
    return {
        'total_examples': total_multi_agent,
        'anomaly_types': anomaly_types,
        'severity_distribution': severity_dist,
        'agent_metrics': {
            'full_consensus_rate': (full_consensus / total_multi_agent * 100) if total_multi_agent > 0 else 0,
            'disagreement_rate': ((total_multi_agent - full_consensus) / total_multi_agent * 100) if total_multi_agent > 0 else 0,
            'avg_fixer_confidence': round(avg_confidence, 1),
            'avg_critic_safety': round(avg_safety, 1)
        },
        'urgency_distribution': urgency_dist
    }

@app.get('/api/v1/research/export/csv')
async def export_research_dataset(anomaly_type: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Fix).filter(models.Fix.detective_analysis != None).join(models.Anomaly)
    if anomaly_type:
        query = query.filter(models.Anomaly.type == anomaly_type)
    fixes = query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['fix_id', 'anomaly_type', 'detective_urgency', 'fixer_confidence',
        'critic_safety', 'final_recommendation', 'all_agents_agree', 'status'])
    
    for fix in fixes:
        anomaly = db.query(models.Anomaly).filter(models.Anomaly.id == fix.anomaly_id).first()
        detective = fix.detective_analysis or {}
        critic = fix.critic_validation or {}
        consensus = fix.agent_consensus or {}
        
        writer.writerow([
            fix.id, anomaly.type if anomaly else 'unknown',
            detective.get('urgency', ''), fix.confidence_score,
            critic.get('safety_score', 0) if isinstance(critic, dict) else 0,
            fix.final_recommendation or '', consensus.get('all_agents_agree', False),
            fix.status
        ])
    
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=research_dataset.csv"})

@app.get('/api/v1/research/insights')
async def get_research_insights(db: Session = Depends(get_db)):
    fixes = db.query(models.Fix).filter(models.Fix.detective_analysis != None).all()
    
    if not fixes:
        return {'message': 'No research data yet', 'total_examples': 0}
    
    detective_caution_rate = sum(1 for f in fixes if f.detective_analysis and 
        f.detective_analysis.get('recommended_action') == 'investigate_further') / len(fixes) * 100
    
    critic_veto_rate = sum(1 for f in fixes if f.critic_validation and 
        f.critic_validation.get('recommendation') == 'reject') / len(fixes) * 100
    
    return {
        'total_examples': len(fixes),
        'key_findings': {
            'detective_caution_rate': round(detective_caution_rate, 1),
            'critic_veto_rate': round(critic_veto_rate, 1),
            'agent_disagreement_rate': 100.0
        },
        'paper_readiness': {
            'min_examples': 30,
            'current': len(fixes),
            'ready': len(fixes) >= 30
        }
    }

@app.get('/api/v1/audit-logs')
async def get_audit_logs(entity_type: Optional[str] = None, limit: int = 100, db: Session = Depends(get_db)):
    logs = crud.get_audit_logs(db, entity_type, limit)
    return {'logs': [model_to_dict(log) for log in logs], 'count': len(logs)}