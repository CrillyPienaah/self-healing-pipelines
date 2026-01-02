import requests
import json
import time
import csv
from datetime import datetime
import os

BASE_URL = 'http://localhost:8000'

# Define 50+ diverse test scenarios
scenarios = [
    # E-commerce scenarios
    {'name': 'add_payment_gateway', 'old': [{'name': 'order_id', 'type': 'int'}, {'name': 'total', 'type': 'decimal'}], 
     'new': [{'name': 'order_id', 'type': 'int'}, {'name': 'total', 'type': 'decimal'}, {'name': 'payment_gateway', 'type': 'varchar'}, {'name': 'gateway_txn_id', 'type': 'varchar'}]},
    
    {'name': 'add_shipping_tracking', 'old': [{'name': 'order_id', 'type': 'int'}, {'name': 'status', 'type': 'varchar'}], 
     'new': [{'name': 'order_id', 'type': 'int'}, {'name': 'status', 'type': 'varchar'}, {'name': 'tracking_number', 'type': 'varchar'}, {'name': 'carrier', 'type': 'varchar'}]},
    
    {'name': 'add_customer_loyalty', 'old': [{'name': 'customer_id', 'type': 'int'}, {'name': 'email', 'type': 'varchar'}], 
     'new': [{'name': 'customer_id', 'type': 'int'}, {'name': 'email', 'type': 'varchar'}, {'name': 'loyalty_tier', 'type': 'varchar'}, {'name': 'points', 'type': 'int'}]},
    
    # Healthcare/GDPR scenarios  
    {'name': 'add_patient_consent', 'old': [{'name': 'patient_id', 'type': 'int'}, {'name': 'name', 'type': 'varchar'}], 
     'new': [{'name': 'patient_id', 'type': 'int'}, {'name': 'name', 'type': 'varchar'}, {'name': 'consent_given', 'type': 'boolean'}, {'name': 'consent_date', 'type': 'timestamp'}]},
    
    {'name': 'add_hipaa_audit', 'old': [{'name': 'record_id', 'type': 'int'}, {'name': 'data', 'type': 'text'}], 
     'new': [{'name': 'record_id', 'type': 'int'}, {'name': 'data', 'type': 'text'}, {'name': 'accessed_by', 'type': 'varchar'}, {'name': 'access_timestamp', 'type': 'timestamp'}]},
    
    {'name': 'remove_ssn_pii', 'old': [{'name': 'user_id', 'type': 'int'}, {'name': 'ssn', 'type': 'varchar'}, {'name': 'email', 'type': 'varchar'}], 
     'new': [{'name': 'user_id', 'type': 'int'}, {'name': 'email', 'type': 'varchar'}]},
    
    # Financial/Banking scenarios
    {'name': 'add_multi_currency', 'old': [{'name': 'account_id', 'type': 'int'}, {'name': 'balance', 'type': 'decimal'}], 
     'new': [{'name': 'account_id', 'type': 'int'}, {'name': 'balance', 'type': 'decimal'}, {'name': 'currency_code', 'type': 'varchar'}, {'name': 'exchange_rate', 'type': 'decimal'}]},
    
    {'name': 'add_fraud_detection', 'old': [{'name': 'txn_id', 'type': 'int'}, {'name': 'amount', 'type': 'decimal'}], 
     'new': [{'name': 'txn_id', 'type': 'int'}, {'name': 'amount', 'type': 'decimal'}, {'name': 'fraud_score', 'type': 'decimal'}, {'name': 'is_flagged', 'type': 'boolean'}]},
    
    {'name': 'add_kyc_verification', 'old': [{'name': 'customer_id', 'type': 'int'}, {'name': 'account_type', 'type': 'varchar'}], 
     'new': [{'name': 'customer_id', 'type': 'int'}, {'name': 'account_type', 'type': 'varchar'}, {'name': 'kyc_verified', 'type': 'boolean'}, {'name': 'verification_date', 'type': 'date'}]},
    
    # SaaS/Analytics scenarios
    {'name': 'add_feature_flags', 'old': [{'name': 'user_id', 'type': 'int'}, {'name': 'plan', 'type': 'varchar'}], 
     'new': [{'name': 'user_id', 'type': 'int'}, {'name': 'plan', 'type': 'varchar'}, {'name': 'features_json', 'type': 'json'}]},
    
    {'name': 'add_usage_metrics', 'old': [{'name': 'session_id', 'type': 'int'}, {'name': 'user_id', 'type': 'int'}], 
     'new': [{'name': 'session_id', 'type': 'int'}, {'name': 'user_id', 'type': 'int'}, {'name': 'duration_seconds', 'type': 'int'}, {'name': 'pages_viewed', 'type': 'int'}]},
    
    {'name': 'add_ab_test_variant', 'old': [{'name': 'user_id', 'type': 'int'}, {'name': 'experiment', 'type': 'varchar'}], 
     'new': [{'name': 'user_id', 'type': 'int'}, {'name': 'experiment', 'type': 'varchar'}, {'name': 'variant', 'type': 'varchar'}, {'name': 'assigned_at', 'type': 'timestamp'}]},
    
    # IoT/Sensor scenarios
    {'name': 'add_iot_telemetry', 'old': [{'name': 'device_id', 'type': 'int'}, {'name': 'reading', 'type': 'decimal'}], 
     'new': [{'name': 'device_id', 'type': 'int'}, {'name': 'reading', 'type': 'decimal'}, {'name': 'battery_pct', 'type': 'int'}, {'name': 'signal_strength', 'type': 'int'}]},
    
    {'name': 'add_geo_location', 'old': [{'name': 'event_id', 'type': 'int'}, {'name': 'timestamp', 'type': 'timestamp'}], 
     'new': [{'name': 'event_id', 'type': 'int'}, {'name': 'timestamp', 'type': 'timestamp'}, {'name': 'latitude', 'type': 'decimal'}, {'name': 'longitude', 'type': 'decimal'}]},
    
    # Type changes (potential breaking changes)
    {'name': 'int_to_bigint_migration', 'old': [{'name': 'id', 'type': 'integer'}, {'name': 'count', 'type': 'integer'}], 
     'new': [{'name': 'id', 'type': 'bigint'}, {'name': 'count', 'type': 'integer'}]},
    
    {'name': 'varchar_to_text_expand', 'old': [{'name': 'id', 'type': 'int'}, {'name': 'description', 'type': 'varchar'}], 
     'new': [{'name': 'id', 'type': 'int'}, {'name': 'description', 'type': 'text'}]},
    
    # Refactoring scenarios (additions + removals)
    {'name': 'split_full_name', 'old': [{'name': 'user_id', 'type': 'int'}, {'name': 'full_name', 'type': 'varchar'}], 
     'new': [{'name': 'user_id', 'type': 'int'}, {'name': 'first_name', 'type': 'varchar'}, {'name': 'last_name', 'type': 'varchar'}]},
    
    {'name': 'normalize_address', 'old': [{'name': 'id', 'type': 'int'}, {'name': 'address', 'type': 'text'}], 
     'new': [{'name': 'id', 'type': 'int'}, {'name': 'street', 'type': 'varchar'}, {'name': 'city', 'type': 'varchar'}, {'name': 'zip', 'type': 'varchar'}]},
]

# Add programmatic variations
additional_scenarios = []

# Single column additions by type
for dtype in ['integer', 'varchar', 'decimal', 'boolean', 'timestamp', 'date', 'text', 'json', 'uuid', 'bigint']:
    additional_scenarios.append({
        'name': f'add_{dtype}_column',
        'old': [{'name': 'id', 'type': 'integer'}],
        'new': [{'name': 'id', 'type': 'integer'}, {'name': f'new_{dtype}', 'type': dtype}]
    })

# Multi-column additions
for num in [2, 3, 4, 5, 6]:
    cols = [{'name': f'attr_{i}', 'type': 'varchar'} for i in range(num)]
    additional_scenarios.append({
        'name': f'add_{num}_columns',
        'old': [{'name': 'id', 'type': 'integer'}],
        'new': [{'name': 'id', 'type': 'integer'}] + cols
    })

# Column removals
for i in range(5):
    additional_scenarios.append({
        'name': f'remove_column_{i}',
        'old': [{'name': 'id', 'type': 'int'}, {'name': f'deprecated_{i}', 'type': 'varchar'}, {'name': 'active', 'type': 'text'}],
        'new': [{'name': 'id', 'type': 'int'}, {'name': 'active', 'type': 'text'}]
    })

# Industry-specific
industry_scenarios = [
    {'name': 'retail_inventory_tracking', 'old': [{'name': 'product_id', 'type': 'int'}, {'name': 'quantity', 'type': 'int'}], 
     'new': [{'name': 'product_id', 'type': 'int'}, {'name': 'quantity', 'type': 'int'}, {'name': 'warehouse_id', 'type': 'int'}, {'name': 'last_restocked', 'type': 'timestamp'}]},
    
    {'name': 'edu_student_grades', 'old': [{'name': 'student_id', 'type': 'int'}, {'name': 'course_id', 'type': 'int'}], 
     'new': [{'name': 'student_id', 'type': 'int'}, {'name': 'course_id', 'type': 'int'}, {'name': 'grade', 'type': 'varchar'}, {'name': 'graded_at', 'type': 'timestamp'}]},
    
    {'name': 'logistics_route_optimization', 'old': [{'name': 'delivery_id', 'type': 'int'}, {'name': 'destination', 'type': 'varchar'}], 
     'new': [{'name': 'delivery_id', 'type': 'int'}, {'name': 'destination', 'type': 'varchar'}, {'name': 'route_json', 'type': 'json'}, {'name': 'estimated_duration', 'type': 'int'}]},
]

scenarios.extend(additional_scenarios)
scenarios.extend(industry_scenarios)

print(f'🔬 Multi-Agent Research Dataset Collection: {len(scenarios)} scenarios\n')
print('=' * 70)

# Create directory
os.makedirs('research_data/multi_agent', exist_ok=True)

# Storage for results
results = []
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
csv_filename = f'research_data/multi_agent/results_{timestamp}.csv'

# Run scenarios
for idx, scenario in enumerate(scenarios, 1):
    print(f'\n[{idx}/{len(scenarios)}] {scenario["name"]}')
    print('-' * 70)
    
    try:
        # Create pipeline
        pipeline_name = f'ma_test_{scenario["name"]}'
        response = requests.post(
            f'{BASE_URL}/api/v1/pipelines',
            params={'name': pipeline_name, 'description': f'Multi-agent test: {scenario["name"]}'}
        )
        
        if response.status_code == 400:
            pipelines = requests.get(f'{BASE_URL}/api/v1/pipelines').json()['pipelines']
            pipeline = [p for p in pipelines if p['name'] == pipeline_name][0]
            pipeline_id = pipeline['id']
        else:
            pipeline_id = response.json()['id']
        
        # Record schemas
        requests.post(f'{BASE_URL}/api/v1/pipelines/{pipeline_id}/snapshots',
                     json={'columns': scenario['old'], 'row_count': 1000 + idx})
        
        drift_resp = requests.post(f'{BASE_URL}/api/v1/pipelines/{pipeline_id}/snapshots',
                                   json={'columns': scenario['new'], 'row_count': 1100 + idx})
        
        if not drift_resp.json().get('drift_detected'):
            print('  ⚠️  No drift')
            continue
        
        # Get anomaly
        anomalies_resp = requests.get(f'{BASE_URL}/api/v1/pipelines/{pipeline_id}/anomalies')
        anomalies = anomalies_resp.json()['anomalies']
        if not anomalies:
            print('  ⚠️  No anomaly')
            continue
        
        anomaly = sorted(anomalies, key=lambda x: x['detected_at'], reverse=True)[0]
        
        # Run multi-agent analysis
        print('  🤖 Running Detective → Fixer → Critic...')
        start_time = time.time()
        ma_result = requests.post(f'{BASE_URL}/api/v1/anomalies/{anomaly["id"]}/analyze-multi-agent')
        
        if ma_result.status_code != 200:
            print(f'  ✗ Failed: {ma_result.status_code}')
            continue
        
        result = ma_result.json()
        gen_time = time.time() - start_time
        
        detective = result.get('detective_analysis', {})
        fixer = result.get('proposed_fix', {})
        critic = result.get('critic_validation', {})
        consensus = result.get('agent_consensus', {})
        
        print(f'  ✅ Complete in {gen_time:.1f}s')
        print(f'     Detective: {detective.get("urgency", "?")} urgency | {detective.get("recommended_action", "?")}')
        print(f'     Fixer: {fixer.get("confidence_score", 0)}% confidence')
        print(f'     Critic: {critic.get("safety_score", 0)}/100 safety | {critic.get("recommendation", "?")}')
        print(f'     Consensus: {"✓" if consensus.get("all_agents_agree") else "✗"}')
        
        # Store detailed result
        results.append({
            'scenario': scenario['name'],
            'pipeline_id': pipeline_id,
            'anomaly_id': anomaly['id'],
            'old_cols': len(scenario['old']),
            'new_cols': len(scenario['new']),
            'cols_changed': len(scenario['new']) - len(scenario['old']),
            # Detective metrics
            'detective_urgency': detective.get('urgency', ''),
            'detective_trigger': detective.get('trigger', ''),
            'detective_intentional': detective.get('intentional', ''),
            'detective_action': detective.get('recommended_action', ''),
            # Fixer metrics
            'fixer_confidence': fixer.get('confidence_score', 0) if fixer else 0,
            'fixer_code_length': len(fixer.get('fix_code', '')) if fixer else 0,
            # Critic metrics
            'critic_syntax': critic.get('syntax_valid', '') if critic else '',
            'critic_logic': critic.get('logic_sound', '') if critic else '',
            'critic_safety': critic.get('safety_score', 0) if critic else 0,
            'critic_recommendation': critic.get('recommendation', '') if critic else '',
            # Orchestrator metrics
            'final_recommendation': result.get('final_recommendation', ''),
            'proceed_with_fix': result.get('proceed_with_fix', False),
            'all_agents_agree': consensus.get('all_agents_agree', False),
            'generation_time_sec': round(gen_time, 2),
            'timestamp': datetime.now().isoformat()
        })
        
        # Rate limiting
        time.sleep(2)
        
    except Exception as e:
        print(f'  ✗ Error: {str(e)}')
        continue

# Save results
print(f'\n{"=" * 70}')
print('MULTI-AGENT RESEARCH DATASET COMPLETE')
print('=' * 70)

if results:
    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    
    print(f'\n✅ Collected {len(results)} multi-agent examples')
    print(f'💾 Saved to: {csv_filename}')
    
    # Statistics
    avg_detective_urgency = {}
    for r in results:
        urgency = r['detective_urgency']
        avg_detective_urgency[urgency] = avg_detective_urgency.get(urgency, 0) + 1
    
    avg_fixer_conf = sum(r['fixer_confidence'] for r in results if r['fixer_confidence'] > 0) / len([r for r in results if r['fixer_confidence'] > 0]) if results else 0
    avg_critic_safety = sum(r['critic_safety'] for r in results if r['critic_safety'] > 0) / len([r for r in results if r['critic_safety'] > 0]) if results else 0
    avg_time = sum(r['generation_time_sec'] for r in results) / len(results)
    
    consensus_count = len([r for r in results if r['all_agents_agree']])
    auto_approve = len([r for r in results if r['final_recommendation'] == 'auto_approve_recommended'])
    human_review = len([r for r in results if r['final_recommendation'] == 'human_review_recommended'])
    
    print(f'\n📈 Multi-Agent Statistics:')
    print(f'   Detective Urgency Distribution: {avg_detective_urgency}')
    print(f'   Avg Fixer Confidence: {avg_fixer_conf:.1f}%')
    print(f'   Avg Critic Safety: {avg_critic_safety:.1f}/100')
    print(f'   Avg Generation Time: {avg_time:.1f}s')
    print(f'   Full Consensus: {consensus_count}/{len(results)} ({consensus_count/len(results)*100:.1f}%)')
    print(f'   Auto-Approve: {auto_approve} | Human Review: {human_review}')
    
    print(f'\n🔬 Research Insights:')
    print(f'   - {len(results)} complete agent interaction traces')
    print(f'   - Agent disagreement rate: {100 - (consensus_count/len(results)*100):.1f}%')
    print(f'   - Safety validation patterns captured')
    print(f'   - Ready for hierarchical RL training')
    
    print(f'\n💰 API Cost: ~${len(results) * 3 * 0.03:.2f} (estimated)')
else:
    print('\n⚠️  No results collected')

print('\n' + '=' * 70)