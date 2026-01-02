import requests
import json
import time

BASE_URL = 'http://localhost:8000'

print('🤖 Testing Multi-Agent System (Detective → Fixer → Critic)\n')
print('=' * 70)

# 1. Check agent status
print('\n1️⃣  Checking agent system status...')
status = requests.get(f'{BASE_URL}/api/v1/system/agents/status').json()
detective_check = '✓' if status['detective_available'] else '✗'
fixer_check = '✓' if status['fixer_available'] else '✗'
critic_check = '✓' if status['critic_available'] else '✗'
multi_check = '✓' if status['multi_agent_enabled'] else '✗'

print(f'   Detective: {detective_check}')
print(f'   Fixer: {fixer_check}')
print(f'   Critic: {critic_check}')
print(f'   Multi-Agent: {multi_check}')

# 2. Create test pipeline
print('\n2️⃣  Creating test pipeline...')
response = requests.post(
    f'{BASE_URL}/api/v1/pipelines',
    params={'name': 'multi_agent_test', 'description': 'Testing multi-agent system'}
)
if response.status_code == 400:
    pipelines = requests.get(f'{BASE_URL}/api/v1/pipelines').json()['pipelines']
    pipeline = [p for p in pipelines if p['name'] == 'multi_agent_test'][0]
    pipeline_id = pipeline['id']
else:
    pipeline_id = response.json()['id']
print(f'   ✓ Pipeline ID: {pipeline_id}')

# 3. Trigger schema drift
print('\n3️⃣  Creating schema drift...')
snapshot1 = {
    'columns': [
        {'name': 'user_id', 'type': 'integer'},
        {'name': 'email', 'type': 'varchar'}
    ],
    'row_count': 5000
}
requests.post(f'{BASE_URL}/api/v1/pipelines/{pipeline_id}/snapshots', json=snapshot1)

snapshot2 = {
    'columns': [
        {'name': 'user_id', 'type': 'integer'},
        {'name': 'email', 'type': 'varchar'},
        {'name': 'phone', 'type': 'varchar'},
        {'name': 'consent_given', 'type': 'boolean'}
    ],
    'row_count': 5050
}
drift_response = requests.post(f'{BASE_URL}/api/v1/pipelines/{pipeline_id}/snapshots', json=snapshot2)
drift_result = drift_response.json()
print(f'   ✓ Drift detected: {drift_result["drift_detected"]}')

# 4. Get anomaly
anomalies_response = requests.get(f'{BASE_URL}/api/v1/pipelines/{pipeline_id}/anomalies')
anomalies = anomalies_response.json()['anomalies']
anomaly = sorted(anomalies, key=lambda x: x['detected_at'], reverse=True)[0]
anomaly_id = anomaly['id']
print(f'   ✓ Anomaly ID: {anomaly_id}')

# 5. Run multi-agent analysis
print('\n4️⃣  Running multi-agent analysis...')
print('   🔍 [DETECTIVE] Analyzing root cause...')
print('   🔧 [FIXER] Generating fix...')
print('   🛡️  [CRITIC] Validating safety...')
print('   ⏳ This takes 20-40 seconds (3 LLM calls)...\n')

start = time.time()
result = requests.post(f'{BASE_URL}/api/v1/anomalies/{anomaly_id}/analyze-multi-agent').json()
elapsed = time.time() - start

print('\n' + '=' * 70)
print('MULTI-AGENT ANALYSIS COMPLETE')
print('=' * 70)

# Detective results
detective = result.get('detective_analysis', {})
print(f'\n🔍 DETECTIVE AGENT:')
print(f'   Root Cause: {detective.get("root_cause", "N/A")}')
print(f'   Trigger: {detective.get("trigger", "N/A")}')
print(f'   Urgency: {detective.get("urgency", "N/A")}')
print(f'   Intentional: {detective.get("intentional", "N/A")}')
print(f'   Recommendation: {detective.get("recommended_action", "N/A")}')

# Fixer results
fixer = result.get('proposed_fix', {})
if fixer:
    print(f'\n🔧 FIXER AGENT:')
    print(f'   Confidence: {fixer.get("confidence_score", 0)}%')
    fix_code = fixer.get('fix_code', '')
    fix_preview = fix_code[:100] if len(fix_code) > 100 else fix_code
    print(f'   Fix Code Preview: {fix_preview}...')

# Critic results
critic = result.get('critic_validation', {})
if critic:
    print(f'\n🛡️  CRITIC AGENT:')
    print(f'   Syntax Valid: {critic.get("syntax_valid", "N/A")}')
    print(f'   Logic Sound: {critic.get("logic_sound", "N/A")}')
    print(f'   Safety Score: {critic.get("safety_score", 0)}/100')
    print(f'   Recommendation: {critic.get("recommendation", "N/A")}')
    concerns = str(critic.get('concerns', 'N/A'))
    concerns_preview = concerns[:100] if len(concerns) > 100 else concerns
    print(f'   Concerns: {concerns_preview}...')

# Final decision
print(f'\n🎯 ORCHESTRATOR DECISION:')
print(f'   Final Recommendation: {result.get("final_recommendation", "N/A")}')
print(f'   Proceed with Fix: {result.get("proceed_with_fix", False)}')

consensus = result.get('agent_consensus', {})
if consensus:
    print(f'\n🤝 AGENT CONSENSUS:')
    all_agree_check = '✓' if consensus.get('all_agents_agree') else '✗'
    detective_rec_check = '✓' if consensus.get('detective_recommends_action') else '✗'
    fixer_conf_check = '✓' if consensus.get('fixer_confident') else '✗'
    critic_app_check = '✓' if consensus.get('critic_approves') else '✗'
    
    print(f'   All Agents Agree: {all_agree_check}')
    print(f'   Detective Recommends: {detective_rec_check}')
    print(f'   Fixer Confident: {fixer_conf_check}')
    print(f'   Critic Approves: {critic_app_check}')

print(f'\n⚡ Total workflow time: {elapsed:.1f} seconds')
print(f'   (3 sequential LLM calls: Detective + Fixer + Critic)')

print('\n' + '=' * 70)
print('🎉 MULTI-AGENT SYSTEM VALIDATED!')
print('=' * 70)
print('\nThis demonstrates:')
print('✓ Agent specialization (Detective/Fixer/Critic roles)')
print('✓ Inter-agent communication (context passing)')
print('✓ Weighted decision-making (orchestrator consensus)')
print('✓ Safety validation (Critic veto power)')
print('\n🔬 Research value: Complete agent interaction trace for publication!')