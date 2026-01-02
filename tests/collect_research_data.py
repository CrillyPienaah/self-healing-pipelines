import requests
import json
import time
import csv
from datetime import datetime
import os

BASE_URL = 'http://localhost:8000'

# Define test scenarios
scenarios = [
    # Basic column additions
    {
        'name': 'add_single_column',
        'old': [
            {'name': 'id', 'type': 'integer'},
            {'name': 'name', 'type': 'varchar'}
        ],
        'new': [
            {'name': 'id', 'type': 'integer'},
            {'name': 'name', 'type': 'varchar'},
            {'name': 'email', 'type': 'varchar'}
        ]
    },
    {
        'name': 'add_timestamp_column',
        'old': [
            {'name': 'user_id', 'type': 'integer'},
            {'name': 'action', 'type': 'varchar'}
        ],
        'new': [
            {'name': 'user_id', 'type': 'integer'},
            {'name': 'action', 'type': 'varchar'},
            {'name': 'created_at', 'type': 'timestamp'}
        ]
    },
    {
        'name': 'add_foreign_key',
        'old': [
            {'name': 'order_id', 'type': 'integer'},
            {'name': 'total', 'type': 'decimal'}
        ],
        'new': [
            {'name': 'order_id', 'type': 'integer'},
            {'name': 'total', 'type': 'decimal'},
            {'name': 'customer_id', 'type': 'integer'}
        ]
    },
    {
        'name': 'add_boolean_flag',
        'old': [
            {'name': 'product_id', 'type': 'integer'},
            {'name': 'price', 'type': 'decimal'}
        ],
        'new': [
            {'name': 'product_id', 'type': 'integer'},
            {'name': 'price', 'type': 'decimal'},
            {'name': 'is_active', 'type': 'boolean'}
        ]
    },
    {
        'name': 'add_currency_support',
        'old': [
            {'name': 'account_id', 'type': 'integer'},
            {'name': 'balance', 'type': 'decimal'}
        ],
        'new': [
            {'name': 'account_id', 'type': 'integer'},
            {'name': 'balance', 'type': 'decimal'},
            {'name': 'currency', 'type': 'varchar'}
        ]
    },
    {
        'name': 'add_audit_fields',
        'old': [
            {'name': 'record_id', 'type': 'integer'},
            {'name': 'data', 'type': 'text'}
        ],
        'new': [
            {'name': 'record_id', 'type': 'integer'},
            {'name': 'data', 'type': 'text'},
            {'name': 'created_at', 'type': 'timestamp'},
            {'name': 'updated_at', 'type': 'timestamp'}
        ]
    },
    {
        'name': 'remove_deprecated_column',
        'old': [
            {'name': 'id', 'type': 'integer'},
            {'name': 'legacy_field', 'type': 'varchar'},
            {'name': 'name', 'type': 'varchar'}
        ],
        'new': [
            {'name': 'id', 'type': 'integer'},
            {'name': 'name', 'type': 'varchar'}
        ]
    },
    {
        'name': 'add_shipping_address',
        'old': [
            {'name': 'order_id', 'type': 'integer'},
            {'name': 'total', 'type': 'decimal'}
        ],
        'new': [
            {'name': 'order_id', 'type': 'integer'},
            {'name': 'total', 'type': 'decimal'},
            {'name': 'shipping_address', 'type': 'text'}
        ]
    },
    {
        'name': 'add_payment_method',
        'old': [
            {'name': 'txn_id', 'type': 'integer'},
            {'name': 'amount', 'type': 'decimal'}
        ],
        'new': [
            {'name': 'txn_id', 'type': 'integer'},
            {'name': 'amount', 'type': 'decimal'},
            {'name': 'payment_method', 'type': 'varchar'}
        ]
    },
    {
        'name': 'add_user_segments',
        'old': [
            {'name': 'user_id', 'type': 'integer'},
            {'name': 'signup_date', 'type': 'date'}
        ],
        'new': [
            {'name': 'user_id', 'type': 'integer'},
            {'name': 'signup_date', 'type': 'date'},
            {'name': 'segment', 'type': 'varchar'}
        ]
    }
]

# Generate more scenarios programmatically
additional_scenarios = []

# Different data types
data_types = ['integer', 'varchar', 'decimal', 'boolean', 'timestamp', 'date', 'text', 'json']
for i, dtype in enumerate(data_types):
    additional_scenarios.append({
        'name': f'add_{dtype}_field',
        'old': [
            {'name': 'id', 'type': 'integer'},
            {'name': 'data', 'type': 'text'}
        ],
        'new': [
            {'name': 'id', 'type': 'integer'},
            {'name': 'data', 'type': 'text'},
            {'name': f'new_{dtype}', 'type': dtype}
        ]
    })

# Multi-column additions
for num_cols in [2, 3, 4, 5]:
    cols = [{'name': f'col_{j}', 'type': 'varchar'} for j in range(num_cols)]
    additional_scenarios.append({
        'name': f'add_{num_cols}_columns',
        'old': [{'name': 'id', 'type': 'integer'}],
        'new': [{'name': 'id', 'type': 'integer'}] + cols
    })

scenarios.extend(additional_scenarios)

print(f' Research Data Collection: Testing {len(scenarios)} scenarios\n')
print('=' * 70)

# Storage for results
results = []

# Create filename without f-string backslash issue
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
csv_filename = f'research_data/fix_generation_results_{timestamp}.csv'

# Create directory
os.makedirs('research_data', exist_ok=True)

# Run scenarios
for idx, scenario in enumerate(scenarios, 1):
    print(f'\n[{idx}/{len(scenarios)}] Testing: {scenario["name"]}')
    print('-' * 70)
    
    try:
        # Create pipeline
        pipeline_name = f'test_{scenario["name"]}'
        response = requests.post(
            f'{BASE_URL}/api/v1/pipelines',
            params={'name': pipeline_name, 'description': f'Test: {scenario["name"]}'}
        )
        
        if response.status_code == 400:
            pipelines = requests.get(f'{BASE_URL}/api/v1/pipelines').json()['pipelines']
            pipeline = [p for p in pipelines if p['name'] == pipeline_name][0]
            pipeline_id = pipeline['id']
        else:
            pipeline_id = response.json()['id']
        
        # Record old schema
        requests.post(
            f'{BASE_URL}/api/v1/pipelines/{pipeline_id}/snapshots',
            json={'columns': scenario['old'], 'row_count': 1000 + idx}
        )
        
        # Record new schema (trigger drift)
        drift_response = requests.post(
            f'{BASE_URL}/api/v1/pipelines/{pipeline_id}/snapshots',
            json={'columns': scenario['new'], 'row_count': 1100 + idx}
        )
        
        if not drift_response.json().get('drift_detected'):
            print('    No drift detected')
            continue
        
        # Get anomaly
        anomalies_resp = requests.get(f'{BASE_URL}/api/v1/pipelines/{pipeline_id}/anomalies')
        anomalies = anomalies_resp.json()['anomalies']
        if not anomalies:
            print('    No anomaly created')
            continue
        
        anomaly = sorted(anomalies, key=lambda x: x['detected_at'], reverse=True)[0]
        
        # Generate fix
        print('   Calling GPT-4...')
        start_time = time.time()
        fix_response = requests.post(f'{BASE_URL}/api/v1/anomalies/{anomaly["id"]}/propose-fix')
        gen_time = time.time() - start_time
        
        if fix_response.status_code == 200:
            fix = fix_response.json()
            print(f'   Generated in {gen_time:.1f}s | Confidence: {fix["confidence_score"]}%')
            
            results.append({
                'scenario': scenario['name'],
                'old_cols': len(scenario['old']),
                'new_cols': len(scenario['new']),
                'cols_added': len(scenario['new']) - len(scenario['old']),
                'gen_time': round(gen_time, 2),
                'confidence': fix['confidence_score'],
                'root_cause': fix['root_cause'][:100],
                'fix_length': len(fix['fix_code']),
                'timestamp': datetime.now().isoformat()
            })
        else:
            print(f'   Failed: {fix_response.status_code}')
        
        time.sleep(1)  # Rate limiting
        
    except Exception as e:
        print(f'   Error: {str(e)}')

# Save results
print(f'\n{"=" * 70}')
print('RESULTS')
print('=' * 70)

if results:
    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    
    print(f'\n Collected {len(results)} examples')
    print(f' Saved to: {csv_filename}')
    
    avg_conf = sum(r['confidence'] for r in results) / len(results)
    avg_time = sum(r['gen_time'] for r in results) / len(results)
    high_conf = len([r for r in results if r['confidence'] >= 80])
    
    print(f'\n Statistics:')
    print(f'   Avg Confidence: {avg_conf:.1f}%')
    print(f'   Avg Time: {avg_time:.1f}s')
    print(f'   High Confidence (80%): {high_conf}/{len(results)} ({high_conf/len(results)*100:.1f}%)')
else:
    print('\n  No results collected')
