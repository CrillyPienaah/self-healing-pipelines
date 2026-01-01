from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Pipeline(Base):
    '''Represents a data pipeline being monitored'''
    __tablename__ = 'pipelines'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(String)
    source_type = Column(String)  # e.g., 'dbt', 'airflow', 'custom'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    snapshots = relationship('SchemaSnapshot', back_populates='pipeline')
    anomalies = relationship('Anomaly', back_populates='pipeline')


class SchemaSnapshot(Base):
    '''Stores schema snapshots for drift detection'''
    __tablename__ = 'schema_snapshots'
    
    id = Column(Integer, primary_key=True)
    pipeline_id = Column(Integer, ForeignKey('pipelines.id'), nullable=False)
    snapshot_time = Column(DateTime, default=datetime.utcnow, index=True)
    schema_hash = Column(String, nullable=False)
    columns = Column(JSON, nullable=False)  # List of column metadata
    row_count = Column(Integer)
    
    # Relationships
    pipeline = relationship('Pipeline', back_populates='snapshots')


class Anomaly(Base):
    '''Records detected anomalies (schema drift, data quality issues)'''
    __tablename__ = 'anomalies'
    
    id = Column(Integer, primary_key=True)
    pipeline_id = Column(Integer, ForeignKey('pipelines.id'), nullable=False)
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    anomaly_type = Column(String, nullable=False)  # 'schema_drift', 'null_spike', etc.
    severity = Column(String)  # 'low', 'medium', 'high', 'critical'
    description = Column(String)
    metadata = Column(JSON)  # Additional context
    resolved = Column(DateTime)
    
    # Relationships
    pipeline = relationship('Pipeline', back_populates='anomalies')
    fix = relationship('RemediationFix', back_populates='anomaly', uselist=False)


class RemediationFix(Base):
    '''Stores proposed and applied fixes'''
    __tablename__ = 'remediation_fixes'
    
    id = Column(Integer, primary_key=True)
    anomaly_id = Column(Integer, ForeignKey('anomalies.id'), nullable=False)
    proposed_at = Column(DateTime, default=datetime.utcnow)
    fix_type = Column(String)  # 'code_patch', 'config_change', 'manual_intervention'
    fix_code = Column(String)  # The actual fix (SQL, Python, etc.)
    confidence_score = Column(Integer)  # 0-100
    approved = Column(DateTime)
    applied = Column(DateTime)
    applied_by = Column(String)  # 'auto', 'user@example.com'
    
    # Relationships
    anomaly = relationship('Anomaly', back_populates='fix')
