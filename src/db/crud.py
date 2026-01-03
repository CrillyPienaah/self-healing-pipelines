"""
CRUD Operations for Database Access
Helper functions for pipeline, anomaly, fix management
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime
from . import models


# ============= PIPELINE OPERATIONS =============

def create_pipeline(db: Session, name: str, description: str = None, source_type: str = 'dbt'):
    """Create a new pipeline"""
    db_pipeline = models.Pipeline(
        name=name,
        description=description,
        source_type=source_type
    )
    db.add(db_pipeline)
    db.commit()
    db.refresh(db_pipeline)
    return db_pipeline


def get_pipeline(db: Session, pipeline_id: int):
    """Get pipeline by ID"""
    return db.query(models.Pipeline).filter(models.Pipeline.id == pipeline_id).first()


def get_pipeline_by_name(db: Session, name: str):
    """Get pipeline by name"""
    return db.query(models.Pipeline).filter(models.Pipeline.name == name).first()


def get_all_pipelines(db: Session):
    """Get all pipelines"""
    return db.query(models.Pipeline).all()


# ============= SNAPSHOT OPERATIONS =============

def create_snapshot(
    db: Session,
    pipeline_id: int,
    schema_hash: str,
    columns: List[Dict],
    row_count: int = None,
    column_stats: Dict = None
):
    """Create a new snapshot"""
    db_snapshot = models.Snapshot(
        pipeline_id=pipeline_id,
        schema_hash=schema_hash,
        columns=columns,
        row_count=row_count,
        column_stats=column_stats
    )
    db.add(db_snapshot)
    db.commit()
    db.refresh(db_snapshot)
    return db_snapshot


def get_latest_snapshot(db: Session, pipeline_id: int):
    """Get most recent snapshot for a pipeline"""
    return db.query(models.Snapshot)\
        .filter(models.Snapshot.pipeline_id == pipeline_id)\
        .order_by(models.Snapshot.snapshot_time.desc())\
        .first()


def get_snapshots(db: Session, pipeline_id: int, limit: int = 10):
    """Get recent snapshots for a pipeline"""
    return db.query(models.Snapshot)\
        .filter(models.Snapshot.pipeline_id == pipeline_id)\
        .order_by(models.Snapshot.snapshot_time.desc())\
        .limit(limit)\
        .all()


# ============= ANOMALY OPERATIONS =============

def create_anomaly(
    db: Session,
    pipeline_id: int,
    anomaly_type: str,
    severity: str,
    description: str,
    details: Dict = None
):
    """Create a new anomaly"""
    db_anomaly = models.Anomaly(
        pipeline_id=pipeline_id,
        type=anomaly_type,
        severity=severity,
        description=description,
        details=details
    )
    db.add(db_anomaly)
    db.commit()
    db.refresh(db_anomaly)
    return db_anomaly


def get_anomaly(db: Session, anomaly_id: int):
    """Get anomaly by ID"""
    return db.query(models.Anomaly).filter(models.Anomaly.id == anomaly_id).first()


def get_anomalies(db: Session, pipeline_id: int, unresolved_only: bool = True):
    """Get anomalies for a pipeline"""
    query = db.query(models.Anomaly).filter(models.Anomaly.pipeline_id == pipeline_id)
    
    if unresolved_only:
        query = query.filter(models.Anomaly.resolved == None)
    
    return query.order_by(models.Anomaly.detected_at.desc()).all()


def resolve_anomaly(db: Session, anomaly_id: int):
    """Mark anomaly as resolved"""
    anomaly = get_anomaly(db, anomaly_id)
    if anomaly:
        anomaly.resolved = datetime.utcnow()
        db.commit()
        db.refresh(anomaly)
    return anomaly


# ============= FIX OPERATIONS =============

def create_fix(
    db: Session,
    anomaly_id: int,
    fix_type: str,
    root_cause: str,
    fix_code: str,
    rollback_plan: str,
    confidence_score: int,
    risks: str,
    detective_analysis: Dict = None,
    critic_validation: Dict = None,
    final_recommendation: str = None,
    agent_consensus: Dict = None
):
    """Create a new fix proposal"""
    db_fix = models.Fix(
        anomaly_id=anomaly_id,
        fix_type=fix_type,
        root_cause=root_cause,
        fix_code=fix_code,
        rollback_plan=rollback_plan,
        confidence_score=confidence_score,
        risks=risks,
        detective_analysis=detective_analysis,
        critic_validation=critic_validation,
        final_recommendation=final_recommendation,
        agent_consensus=agent_consensus
    )
    db.add(db_fix)
    db.commit()
    db.refresh(db_fix)
    return db_fix


def get_fix(db: Session, fix_id: int):
    """Get fix by ID"""
    return db.query(models.Fix).filter(models.Fix.id == fix_id).first()


def get_fixes_for_anomaly(db: Session, anomaly_id: int):
    """Get all fixes for an anomaly"""
    return db.query(models.Fix)\
        .filter(models.Fix.anomaly_id == anomaly_id)\
        .order_by(models.Fix.proposed_at.desc())\
        .all()


def approve_fix(db: Session, fix_id: int):
    """Approve a fix"""
    fix = get_fix(db, fix_id)
    if fix:
        fix.status = 'approved'
        fix.approved_at = datetime.utcnow()
        db.commit()
        db.refresh(fix)
    return fix


def reject_fix(db: Session, fix_id: int, reason: str = None):
    """Reject a fix"""
    fix = get_fix(db, fix_id)
    if fix:
        fix.status = 'rejected'
        fix.rejected_at = datetime.utcnow()
        fix.rejection_reason = reason
        db.commit()
        db.refresh(fix)
    return fix


# ============= AUDIT LOG OPERATIONS =============

def create_audit_log(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: int,
    details: Dict,
    ai_model_used: str = None,
    confidence_score: float = None,
    user_id: str = None
):
    """Create audit log entry for EU AI Act compliance"""
    db_log = models.AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ai_model_used=ai_model_used,
        confidence_score=confidence_score,
        user_id=user_id
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def get_audit_logs(db: Session, entity_type: str = None, limit: int = 100):
    """Get audit logs"""
    query = db.query(models.AuditLog)
    
    if entity_type:
        query = query.filter(models.AuditLog.entity_type == entity_type)
    
    return query.order_by(models.AuditLog.timestamp.desc()).limit(limit).all()