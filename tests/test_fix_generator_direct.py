from src.agents.fix_generator import FixGenerator
from dotenv import load_dotenv

load_dotenv()

# Create test anomaly
test_anomaly = {
    'id': 999,
    'pipeline_id': 1,
    'type': 'schema_drift',
    'severity': 'medium',
    'description': 'Schema changed from 3 to 4 columns',
    'detected_at': '2026-01-01T13:00:00',
    'details': {
        'old_columns': [
            {'name': 'order_id', 'type': 'integer'},
            {'name': 'customer_id', 'type': 'integer'},
            {'name': 'total', 'type': 'decimal'}
        ],
        'new_columns': [
            {'name': 'order_id', 'type': 'integer'},
            {'name': 'customer_id', 'type': 'integer'},
            {'name': 'total', 'type': 'decimal'},
            {'name': 'currency', 'type': 'varchar'}
        ]
    }
}

print('🤖 Testing Fix Generator directly...\n')
print('Calling GPT-4 to generate fix...\n')

generator = FixGenerator()
result = generator.generate_schema_drift_fix(test_anomaly)

print('=' * 70)
print('GPT-4 RAW RESPONSE')
print('=' * 70)
print(result.get('raw_response', 'No raw response'))
print('\n' + '=' * 70)
print('PARSED RESULT')
print('=' * 70)
print(f'\nRoot Cause: {result["root_cause"]}')
print(f'\nConfidence: {result["confidence_score"]}%')
print(f'\nFix Code:\n{result["fix_code"]}')
print(f'\nRollback: {result["rollback_plan"]}')
print(f'\nRisks: {result["risks"]}')
