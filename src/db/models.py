"""
SQLAlchemy Models for PostgreSQL
Replaces in-memory storage with persistent database
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class Pipeline(Base):
    __tablename__ = 'pipelines'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    source_type = Column(String(50), default='dbt')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    snapshots = relationship('Snapshot', back_populates='pipeline', cascade='all, delete-orphan')
    anomalies = relationship('Anomaly', back_populates='pipeline', cascade='all, delete-orphan')


class Snapshot(Base):
    __tablename__ = 'snapshots'
    
    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey('pipelines.id'), nullable=False, index=True)
    schema_hash = Column(String(64), nullable=False)
    columns = Column(JSON, nullable=False)
    row_count = Column(Integer, nullable=True)
    column_stats = Column(JSON, nullable=True)  # For null spike detection
    snapshot_time = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    pipeline = relationship('Pipeline', back_populates='snapshots')


class Anomaly(Base):
    __tablename__ = 'anomalies'
    
    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey('pipelines.id'), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)  # schema_drift, null_spike, etc.
    severity = Column(String(20), nullable=False, index=True)  # critical, high, medium, low
    description = Column(Text, nullable=False)
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved = Column(DateTime, nullable=True)
    details = Column(JSON, nullable=True)
    
    # Relationships
    pipeline = relationship('Pipeline', back_populates='anomalies')
    fixes = relationship('Fix', back_populates='anomaly', cascade='all, delete-orphan')


class Fix(Base):
    __tablename__ = 'fixes'
    
    id = Column(Integer, primary_key=True, index=True)
    anomaly_id = Column(Integer, ForeignKey('anomalies.id'), nullable=False, index=True)
    proposed_at = Column(DateTime, default=datetime.utcnow)
    fix_type = Column(String(50), nullable=False)
    root_cause = Column(Text, nullable=False)
    fix_code = Column(Text, nullable=False)
    rollback_plan = Column(Text, nullable=False)
    confidence_score = Column(Integer, nullable=False)
    risks = Column(Text, nullable=False)
    status = Column(String(20), default='pending', index=True)  # pending, approved, rejected
    applied_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Multi-agent metadata (stored as JSON)
    detective_analysis = Column(JSON, nullable=True)
    critic_validation = Column(JSON, nullable=True)
    final_recommendation = Column(String(50), nullable=True)
    agent_consensus = Column(JSON, nullable=True)
    
    # Relationships
    anomaly = relationship('Anomaly', back_populates='fixes')


class AuditLog(Base):
    """
    EU AI Act compliance: Complete audit trail of all AI decisions
    """
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    action = Column(String(50), nullable=False, index=True)  # detect, propose_fix, approve, reject
    entity_type = Column(String(50), nullable=False)  # pipeline, anomaly, fix
    entity_id = Column(Integer, nullable=False)
    user_id = Column(String(255), nullable=True)  # Future: auth integration
    details = Column(JSON, nullable=False)
    ai_model_used = Column(String(50), nullable=True)  # gpt-4, claude, etc.
    confidence_score = Column(Float, nullable=True)