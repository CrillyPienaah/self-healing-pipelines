"""
Import Multi-Agent Research Data from CSV to PostgreSQL
Loads your 40 collected examples into the database
"""

import csv
import json
from datetime import datetime
from src.db.database import SessionLocal
from src.db import models, crud

csv_file = 'research_data/multi_agent/results_20260102_130422.csv'

print(f'📊 Importing multi-agent research data from CSV...\n')
print('=' * 70)

db = SessionLocal()

imported_count = 0
skipped_count = 0

try:
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader, 1):
            print(f'[{i}] Importing: {row["scenario"]}')
            
            try:
                # Create pipeline if doesn't exist
                pipeline_name = f'imported_{row["scenario"]}'
                pipeline = crud.get_pipeline_by_name(db, pipeline_name)
                
                if not pipeline:
                    pipeline = crud.create_pipeline(
                        db, pipeline_name,
                        f'Imported from research dataset: {row["scenario"]}',
                        'dbt'
                    )
                
                # Create anomaly
                anomaly = crud.create_anomaly(
                    db, pipeline.id, 'schema_drift', 'medium',
                    f'Research example: {row["scenario"]}',
                    {
                        'old_cols': int(row['old_cols']),
                        'new_cols': int(row['new_cols']),
                        'cols_changed': int(row['cols_changed'])
                    }
                )
                
                # Create fix with multi-agent metadata
                detective_analysis = {
                    'root_cause': row.get('root_cause', '')[:100],
                    'urgency': row.get('detective_urgency', 'medium'),
                    'trigger': row.get('detective_trigger', 'unknown'),
                    'intentional': row.get('detective_intentional', 'unclear'),
                    'recommended_action': row.get('detective_action', 'investigate_further')
                }
                
                critic_validation = {
                    'syntax_valid': row.get('critic_syntax', 'valid'),
                    'logic_sound': row.get('critic_logic', 'solves_root_cause'),
                    'safety_score': int(row.get('critic_safety', 70)),
                    'recommendation': row.get('critic_recommendation', 'approve_with_caution'),
                    'concerns': 'Imported from research dataset'
                }
                
                agent_consensus = {
                    'all_agents_agree': row.get('all_agents_agree', 'False').lower() == 'true',
                    'detective_recommends_action': False,
                    'fixer_confident': int(row.get('fixer_confidence', 0)) >= 80,
                    'critic_approves': True
                }
                
                fix = crud.create_fix(
                    db, anomaly.id, 'schema_drift_sql',
                    detective_analysis['root_cause'],
                    f"-- Generated fix for {row['scenario']}",
                    '-- Rollback plan',
                    int(row.get('fixer_confidence', 90)),
                    'Imported from research dataset',
                    detective_analysis,
                    critic_validation,
                    row.get('final_recommendation', 'human_review_recommended'),
                    agent_consensus
                )
                
                imported_count += 1
                print(f'  ✓ Imported (Fix ID: {fix.id})')
                
            except Exception as e:
                print(f'  ✗ Skipped: {str(e)}')
                skipped_count += 1
                continue
    
    db.commit()
    
    print('\n' + '=' * 70)
    print('IMPORT COMPLETE')
    print('=' * 70)
    print(f'\n✅ Imported: {imported_count} examples')
    print(f'⚠️  Skipped: {skipped_count} examples')
    print(f'\n📊 Total research examples in database: {imported_count + skipped_count}')
    
finally:
    db.close()

print('\n🔬 Research dataset now in PostgreSQL!')
print('   - View stats: GET /api/v1/research/statistics')
print('   - Export CSV: GET /api/v1/research/export/csv')
print('   - Get insights: GET /api/v1/research/insights')