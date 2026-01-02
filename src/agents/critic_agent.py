from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict
import os
from dotenv import load_dotenv
import re

load_dotenv()


class CriticAgent:
    '''Validates proposed fixes for safety, correctness, and completeness'''
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError('OpenAI API key required')
        
        self.llm = ChatOpenAI(
            model='gpt-4',
            temperature=0.1,  # Very low - we want conservative, safe validation
            api_key=self.api_key
        )
    
    def validate_fix(self, anomaly: Dict, proposed_fix: Dict, detective_analysis: Dict = None) -> Dict:
        '''
        Validates a proposed fix for:
        - Syntax correctness
        - Logical soundness
        - Potential side effects
        - Alignment with root cause
        '''
        
        prompt = ChatPromptTemplate.from_template('''You are a critical code reviewer specializing in data infrastructure.

Your job: Review this AI-generated fix and identify ANY potential issues.

ANOMALY:
{anomaly_description}

DETECTIVE'S ROOT CAUSE ANALYSIS:
{root_cause_analysis}

PROPOSED FIX:
{fix_code}

FIXER'S CONFIDENCE: {confidence}%

Your review must cover:

1. SYNTAX_CHECK: Is the SQL/code syntactically valid?
2. LOGIC_CHECK: Does this actually solve the root cause?
3. SIDE_EFFECTS: What could break downstream?
4. SAFETY_SCORE: 0-100 (how safe is this to apply?)
5. RECOMMENDATION: approve | approve_with_caution | reject | needs_revision
6. CONCERNS: List specific issues (or "None" if safe)

Be harsh. Better to catch issues now than in production.

Format:

SYNTAX_CHECK:
[valid | invalid | uncertain]

LOGIC_CHECK:
[solves_root_cause | partial_solution | misses_root_cause]

SIDE_EFFECTS:
[List potential downstream impacts]

SAFETY_SCORE:
[0-100]

RECOMMENDATION:
[approve | approve_with_caution | reject | needs_revision]

CONCERNS:
[Specific issues, or "None"]

REASONING:
[Why you gave this assessment]''')
        
        try:
            chain = prompt | self.llm
            
            detective_summary = 'Not available'
            if detective_analysis:
                detective_summary = f"{detective_analysis.get('root_cause', '')}\nUrgency: {detective_analysis.get('urgency', 'unknown')}"
            
            response = chain.invoke({
                'anomaly_description': anomaly.get('description', ''),
                'root_cause_analysis': detective_summary,
                'fix_code': proposed_fix.get('fix_code', ''),
                'confidence': proposed_fix.get('confidence_score', 0)
            })
            
            critique_text = response.content
            critique_data = self._parse_critique(critique_text)
            
            return {
                'syntax_valid': critique_data.get('syntax_check', 'uncertain'),
                'logic_sound': critique_data.get('logic_check', 'uncertain'),
                'side_effects': critique_data.get('side_effects', 'Unknown'),
                'safety_score': critique_data.get('safety_score', 50),
                'recommendation': critique_data.get('recommendation', 'needs_revision'),
                'concerns': critique_data.get('concerns', 'Review required'),
                'reasoning': critique_data.get('reasoning', ''),
                'raw_response': critique_text
            }
            
        except Exception as e:
            raise Exception(f'Critic validation failed: {str(e)}')
    
    def _parse_critique(self, response: str) -> Dict:
        '''Parse critic response'''
        sections = {}
        
        patterns = {
            'syntax_check': r'SYNTAX_CHECK:\s*(.+?)(?=LOGIC_CHECK:|$)',
            'logic_check': r'LOGIC_CHECK:\s*(.+?)(?=SIDE_EFFECTS:|$)',
            'side_effects': r'SIDE_EFFECTS:\s*(.+?)(?=SAFETY_SCORE:|$)',
            'safety_score': r'SAFETY_SCORE:\s*(\d+)',
            'recommendation': r'RECOMMENDATION:\s*(.+?)(?=CONCERNS:|$)',
            'concerns': r'CONCERNS:\s*(.+?)(?=REASONING:|$)',
            'reasoning': r'REASONING:\s*(.+?)(?=$)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if key == 'safety_score':
                    try:
                        sections[key] = int(value)
                    except:
                        sections[key] = 50
                else:
                    sections[key] = value
        
        return sections
