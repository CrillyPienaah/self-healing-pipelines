from typing import Dict, Optional, List
from .detective_agent import DetectiveAgent
from .fix_generator import FixGenerator
from .critic_agent import CriticAgent


class AgentOrchestrator:
    '''
    Coordinates Detective → Fixer → Critic workflow.
    Manages agent communication and decision-making.
    '''
    
    def __init__(self, api_key: str = None):
        self.detective = DetectiveAgent(api_key)
        self.fixer = FixGenerator(api_key)
        self.critic = CriticAgent(api_key)
    
    def process_anomaly(self, anomaly: Dict, past_fixes: List[Dict] = None) -> Dict:
        '''
        Full multi-agent workflow:
        1. Detective analyzes root cause
        2. Fixer generates fix
        3. Critic validates fix
        4. Return coordinated result
        '''
        
        print('[ORCHESTRATOR] Starting multi-agent analysis...')
        
        # Step 1: Detective analyzes
        print('[DETECTIVE] Analyzing root cause...')
        detective_analysis = self.detective.analyze_failure(anomaly, past_fixes)
        root_cause_preview = detective_analysis['root_cause'][:80] if len(detective_analysis['root_cause']) > 80 else detective_analysis['root_cause']
        print(f'[DETECTIVE] Root cause identified: {root_cause_preview}...')
        print(f'[DETECTIVE] Urgency: {detective_analysis["urgency"]} | Recommended: {detective_analysis["recommended_action"]}')
        
        # Check if detective recommends proceeding
        if detective_analysis['recommended_action'] in ['defer', 'ignore']:
            return {
                'proceed_with_fix': False,
                'reason': detective_analysis['reasoning'],
                'detective_analysis': detective_analysis
            }
        
        # Step 2: Fixer generates solution
        print('[FIXER] Generating fix...')
        proposed_fix = self.fixer.generate_schema_drift_fix(anomaly)
        print(f'[FIXER] Fix generated with {proposed_fix["confidence_score"]}% confidence')
        
        # Step 3: Critic validates
        print('[CRITIC] Validating proposed fix...')
        critique = self.critic.validate_fix(anomaly, proposed_fix, detective_analysis)
        print(f'[CRITIC] Safety score: {critique["safety_score"]}/100')
        print(f'[CRITIC] Recommendation: {critique["recommendation"]}')
        
        # Combine all agent outputs
        result = {
            'proceed_with_fix': critique['recommendation'] in ['approve', 'approve_with_caution'],
            'detective_analysis': detective_analysis,
            'proposed_fix': proposed_fix,
            'critic_validation': critique,
            'final_recommendation': self._make_final_decision(detective_analysis, proposed_fix, critique),
            'agent_consensus': self._check_consensus(detective_analysis, proposed_fix, critique)
        }
        
        return result
    
    def _make_final_decision(self, detective: Dict, fixer: Dict, critic: Dict) -> str:
        '''
        Make final recommendation based on all agent inputs.
        Uses weighted voting.
        '''
        
        # Urgency from detective
        urgency = detective.get('urgency', 'medium')
        if urgency == 'critical':
            urgency_score = 100
        elif urgency == 'high':
            urgency_score = 75
        elif urgency == 'medium':
            urgency_score = 50
        else:
            urgency_score = 25
        
        # Confidence from fixer
        fixer_score = fixer.get('confidence_score', 0)
        
        # Safety from critic
        critic_score = critic.get('safety_score', 0)
        
        # Weighted average (critic has veto power)
        if critic_score < 60:
            return 'reject_unsafe'
        
        final_score = (urgency_score * 0.3 + fixer_score * 0.4 + critic_score * 0.3)
        
        if final_score >= 80:
            return 'auto_approve_recommended'
        elif final_score >= 60:
            return 'human_review_recommended'
        else:
            return 'reject_low_confidence'
    
    def _check_consensus(self, detective: Dict, fixer: Dict, critic: Dict) -> Dict:
        '''Check if agents agree on the fix'''
        
        detective_action = detective.get('recommended_action', '')
        fixer_conf = fixer.get('confidence_score', 0)
        critic_rec = critic.get('recommendation', '')
        
        return {
            'detective_recommends_action': detective_action == 'immediate_fix',
            'fixer_confident': fixer_conf >= 80,
            'critic_approves': critic_rec in ['approve', 'approve_with_caution'],
            'all_agents_agree': (
                detective_action == 'immediate_fix' and
                fixer_conf >= 80 and
                critic_rec == 'approve'
            )
        }