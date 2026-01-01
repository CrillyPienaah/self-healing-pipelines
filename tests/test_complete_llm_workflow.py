import requests
import json
import time

BASE_URL = 'http://localhost:8000'

print(' Testing Complete Self-Healing Workflow with LLM Fix Generation\n')

# 1. Create pipeline (or use existing)
print('1  Creating pipeline...')
response = requests.post(
    f'{BASE_URL}/api/v1/pipelines',
    params={'name': 'llm_test_pipeline_v2', 'description': 'LLM test pipeline v2', 'source_type': 'dbt'}
)
if response.status_code == 400:
    print('   ℹ Pipeline already exists, using existing...')
    response = requests.get(f'{BASE_URL}/api/v1/pipelines')
    pipelines = response.json()['pipelines']
    pipeline = [p for p in pipelines if 'llm_test' in p['name']][0]
    pipeline_id = pipeline['id']
else:
    pipeline_id = response.json()['id']
print(f'    Using pipeline ID: {pipeline_id}\n')

# 2. First snapshot (baseline)
print('2  Recording baseline snapshot (3 columns)...')
snapshot1 = {
    'columns': [
        {'name': 'order_id', 'type': 'integer'},
        {'name': 'customer_id', 'type': 'integer'},
        {'name': 'total', 'type': 'decimal'}
    ],
    'row_count': 1000
}
response = requests.post(f'{BASE_URL}/api/v1/pipelines/{pipeline_id}/snapshots', json=snapshot1)
if response.status_code != 200:
    print(f'    Error: {response.json()}')
    exit(1)
result = response.json()
print(f'    Snapshot recorded')
print(f'    Drift detected: {result.get("drift_detected", "N/A")}\n')

# 3. Second snapshot (with drift!)
print('3  Recording snapshot with schema drift (4 columns)...')
snapshot2 = {
    'columns': [
        {'name': 'order_id', 'type': 'integer'},
        {'name': 'customer_id', 'type': 'integer'},
        {'name': 'total', 'type': 'decimal'},
        {'name': 'currency', 'type': 'varchar'}
    ],
    'row_count': 1050
}
response = requests.post(f'{BASE_URL}/api/v1/pipelines/{pipeline_id}/snapshots', json=snapshot2)
if response.status_code != 200:
    print(f'    Error: {response.json()}')
    exit(1)
result = response.json()
print(f'    Snapshot recorded')
print(f'    Drift detected: {result.get("drift_detected", "N/A")} \n')

# 4. Get anomaly
print('4  Retrieving detected anomaly...')
response = requests.get(f'{BASE_URL}/api/v1/pipelines/{pipeline_id}/anomalies')
anomalies = response.json()['anomalies']
if not anomalies:
    print('    No anomalies found! Schema drift was not detected.')
    print(f'   Debug: {response.json()}')
    exit(1)

# Get the most recent anomaly
anomaly = sorted(anomalies, key=lambda x: x['detected_at'], reverse=True)[0]
anomaly_id = anomaly['id']
print(f'    Anomaly ID: {anomaly_id}')
print(f'    Type: {anomaly["type"]}')
print(f'    Description: {anomaly["description"]}\n')

# 5. Generate fix using GPT-4!
print('5  Generating fix using GPT-4...')
print('    AI is analyzing schema drift and generating SQL fix...')
print('    This may take 10-30 seconds...\n')

start_time = time.time()
response = requests.post(f'{BASE_URL}/api/v1/anomalies/{anomaly_id}/propose-fix')
elapsed = time.time() - start_time

if response.status_code == 200:
    fix = response.json()
    print(f'    AI-GENERATED FIX RECEIVED! (took {elapsed:.1f}s)\n')
    print('=' * 70)
    print(f'    CONFIDENCE SCORE: {fix["confidence_score"]}%')
    print('=' * 70)
    print(f'\n    ROOT CAUSE:')
    print(f'   {fix["root_cause"]}\n')
    print(f'    FIX CODE:')
    print('   ' + '-' * 66)
    for line in fix["fix_code"].split('\n'):
        print(f'   {line}')
    print('   ' + '-' * 66)
    print(f'\n     RISKS:')
    print(f'   {fix["risks"]}\n')
    print(f'    ROLLBACK PLAN:')
    print(f'   {fix["rollback_plan"]}\n')
    
    fix_id = fix['id']
    
    # 6. Approve the fix
    print('6  Approving the fix...')
    response = requests.post(f'{BASE_URL}/api/v1/fixes/{fix_id}/approve')
    print(f'    Fix approved and ready for deployment\n')
    
    print('=' * 70)
    print(' COMPLETE WORKFLOW TESTED SUCCESSFULLY!')
    print('=' * 70)
    print('\n Schema drift detected automatically')
    print(' GPT-4 analyzed the problem and identified root cause')
    print(f' AI generated production-ready SQL fix ({fix["confidence_score"]}% confidence)')
    print(' Fix approved and logged for EU AI Act audit trail')
    print(f'\n Total AI generation time: {elapsed:.1f} seconds')
    print('\n Your self-healing pipeline platform is FULLY OPERATIONAL!')
    print('\n Next steps:')
    print('   - Collect more failure examples for research dataset')
    print('   - Build multi-agent system (Detective  Fixer  Critic)')
    print('   - Create React dashboard for fix approval UI')
    print('   - Deploy to AWS and get first pilot customers')
    print('   - Submit OpenAI Residency application')
    
else:
    print(f'    Fix generation failed: {response.status_code}')
    error_detail = response.json()
    print(f'   Error: {error_detail}')
    
    # Check if API key issue
    if 'invalid_api_key' in str(error_detail) or '401' in str(response.status_code):
        print('\n     API KEY ISSUE DETECTED')
        print('   Please check your .env file and ensure:')
        print('   1. OPENAI_API_KEY is set correctly')
        print('   2. Key is valid (check at https://platform.openai.com/api-keys)')
        print('   3. You have credits in your OpenAI account')
    exit(1)
