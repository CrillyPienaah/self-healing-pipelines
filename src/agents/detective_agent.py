from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, List
import os
from dotenv import load_dotenv
import json

load_dotenv()


class DetectiveAgent:
    '''Analyzes failures and determines root causes using RAG over past incidents'''
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError('OpenAI API key required')
        
        self.llm = ChatOpenAI(
            model='gpt-4',
            temperature=0.3,  # Slightly higher for creative root cause analysis
            api_key=self.api_key
        )
        
        # In-memory store of past incidents (will be replaced with vector DB)
        self.past_incidents = []
    
    def analyze_failure(self, anomaly: Dict, past_fixes: List[Dict] = None) -> Dict:
        '''
        Analyzes a failure and determines root cause.
        Uses RAG to find similar past incidents.
        '''
        
        details = anomaly.get('details', {})
        old_columns = details.get('old_columns', [])
        new_columns = details.get('new_columns', [])
        
        # Find similar past incidents
        similar_incidents = self._find_similar_incidents(anomaly, past_fixes or [])
        
        # Create analysis prompt
        prompt = ChatPromptTemplate.from_template('''You are a senior data engineer detective. Analyze this pipeline failure and determine the root cause.

CURRENT FAILURE:
- Type: {failure_type}
- Description: {description}
- Old Schema: {old_schema}
- New Schema: {new_schema}

SIMILAR PAST INCIDENTS:
{similar_incidents}

Your task: Provide a detailed root cause analysis.

Consider:
1. What likely triggered this change? (upstream API, business requirement, migration)
2. Is this intentional or accidental?
3. What are the downstream implications?
4. How urgent is this? (critical, high, medium, low)

Respond in this format:

ROOT_CAUSE:
[1-2 sentence definitive statement of what caused this]

TRIGGER:
[upstream_api | business_requirement | data_migration | schema_refactor | unknown]

INTENTIONAL:
[yes | no | unclear]

URGENCY:
[critical | high | medium | low]

DOWNSTREAM_IMPACT:
[Which tables/dashboards/reports are affected]

RECOMMENDED_ACTION:
[immediate_fix | investigate_further | defer | ignore]

REASONING:
[2-3 sentences explaining your analysis]''')
        
        try:
            chain = prompt | self.llm
            
            similar_text = self._format_similar_incidents(similar_incidents)
            
            response = chain.invoke({
                'failure_type': anomaly.get('type', 'unknown'),
                'description': anomaly.get('description', ''),
                'old_schema': json.dumps(old_columns, indent=2),
                'new_schema': json.dumps(new_columns, indent=2),
                'similar_incidents': similar_text or 'No similar incidents found'
            })
            
            analysis_text = response.content
            analysis_data = self._parse_analysis(analysis_text)
            
            return {
                'root_cause': analysis_data.get('root_cause', 'Unknown cause'),
                'trigger': analysis_data.get('trigger', 'unknown'),
                'intentional': analysis_data.get('intentional', 'unclear'),
                'urgency': analysis_data.get('urgency', 'medium'),
                'downstream_impact': analysis_data.get('downstream_impact', 'Unknown'),
                'recommended_action': analysis_data.get('recommended_action', 'investigate_further'),
                'reasoning': analysis_data.get('reasoning', ''),
                'similar_incidents_found': len(similar_incidents),
                'raw_response': analysis_text
            }
            
        except Exception as e:
            raise Exception(f'Detective analysis failed: {str(e)}')
    
    def _find_similar_incidents(self, anomaly: Dict, past_fixes: List[Dict]) -> List[Dict]:
        '''
        Find similar past incidents using simple similarity matching.
        In production, this would use vector embeddings.
        '''
        if not past_fixes:
            return []
        
        current_type = anomaly.get('type', '')
        similar = []
        
        for fix in past_fixes:
            # Simple matching - same anomaly type
            if fix.get('anomaly', {}).get('type') == current_type:
                similar.append(fix)
        
        # Return top 3 most similar
        return similar[:3]
    
    def _format_similar_incidents(self, incidents: List[Dict]) -> str:
        '''Format similar incidents for prompt context'''
        if not incidents:
            return 'None'
        
        formatted = []
        for i, incident in enumerate(incidents, 1):
            anomaly = incident.get('anomaly', {})
            fix = incident.get('fix', {})
            formatted.append(f'''
Incident {i}:
- Type: {anomaly.get('type')}
- Description: {anomaly.get('description')}
- Fix Applied: {fix.get('fix_code', 'N/A')[:100]}...
- Outcome: {fix.get('status', 'unknown')}
''')
        
        return '\n'.join(formatted)
    
    def _parse_analysis(self, response: str) -> Dict:
        '''Parse detective analysis response'''
        import re
        
        sections = {}
        
        # Extract each section using regex
        patterns = {
            'root_cause': r'ROOT_CAUSE:\s*(.+?)(?=TRIGGER:|INTENTIONAL:|$)',
            'trigger': r'TRIGGER:\s*(.+?)(?=INTENTIONAL:|URGENCY:|$)',
            'intentional': r'INTENTIONAL:\s*(.+?)(?=URGENCY:|DOWNSTREAM_IMPACT:|$)',
            'urgency': r'URGENCY:\s*(.+?)(?=DOWNSTREAM_IMPACT:|RECOMMENDED_ACTION:|$)',
            'downstream_impact': r'DOWNSTREAM_IMPACT:\s*(.+?)(?=RECOMMENDED_ACTION:|REASONING:|$)',
            'recommended_action': r'RECOMMENDED_ACTION:\s*(.+?)(?=REASONING:|$)',
            'reasoning': r'REASONING:\s*(.+?)(?=$)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                sections[key] = match.group(1).strip()
        
        return sections
    
    def log_incident(self, anomaly: Dict, fix: Dict, outcome: str):
        '''Log incident for future RAG retrieval'''
        self.past_incidents.append({
            'anomaly': anomaly,
            'fix': fix,
            'outcome': outcome,
            'timestamp': anomaly.get('detected_at')
        })
