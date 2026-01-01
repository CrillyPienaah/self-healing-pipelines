from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict
import os
from dotenv import load_dotenv
import json
import re

load_dotenv()


class FixGenerator:
    '''Generates fixes for detected anomalies using GPT-4 via LangChain'''
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError('OpenAI API key not found. Set OPENAI_API_KEY in .env file.')
        
        self.llm = ChatOpenAI(
            model='gpt-4',
            temperature=0.2,
            api_key=self.api_key
        )
    
    def generate_schema_drift_fix(self, anomaly: Dict) -> Dict:
        '''Generate a fix for schema drift anomaly'''
        
        details = anomaly.get('details', {})
        old_columns = details.get('old_columns', [])
        new_columns = details.get('new_columns', [])
        
        old_col_names = {col['name'] for col in old_columns}
        new_col_names = {col['name'] for col in new_columns}
        
        added_columns = list(new_col_names - old_col_names)
        removed_columns = list(old_col_names - new_col_names)
        
        prompt = ChatPromptTemplate.from_template('''You are a senior data engineer. Analyze this schema drift and provide a fix.

SCHEMA DRIFT DETECTED:
- Old columns ({old_count}): {old_col_list}
- New columns ({new_count}): {new_col_list}
- Added: {added}
- Removed: {removed}

Provide your response in this EXACT format (no numbers):

ROOT_CAUSE:
[One sentence explaining what caused this]

FIX_CODE:
[SQL ALTER TABLE or dbt model code]

ROLLBACK:
[How to undo this fix]

CONFIDENCE:
[Just a number 0-100]

RISKS:
[Potential issues]''')
        
        try:
            chain = prompt | self.llm
            
            old_col_list = ', '.join([c['name'] for c in old_columns])
            new_col_list = ', '.join([c['name'] for c in new_columns])
            
            response = chain.invoke({
                'old_count': len(old_columns),
                'new_count': len(new_columns),
                'old_col_list': old_col_list,
                'new_col_list': new_col_list,
                'added': ', '.join(added_columns) if added_columns else 'None',
                'removed': ', '.join(removed_columns) if removed_columns else 'None'
            })
            
            fix_text = response.content
            
            # Better parsing that handles numbered or non-numbered sections
            fix_data = self._parse_fix_response(fix_text)
            
            return {
                'anomaly_id': anomaly.get('id'),
                'fix_type': 'schema_drift_sql',
                'root_cause': fix_data.get('root_cause', 'Schema drift detected'),
                'fix_code': fix_data.get('fix_code', '-- No code generated'),
                'rollback_plan': fix_data.get('rollback', 'Manual rollback'),
                'confidence_score': fix_data.get('confidence', 70),
                'risks': fix_data.get('risks', 'Unknown'),
                'generated_by': 'gpt-4-langchain',
                'raw_response': fix_text
            }
            
        except Exception as e:
            raise Exception(f'LLM fix generation failed: {str(e)}')
    
    def _parse_fix_response(self, response: str) -> Dict:
        '''Parse the LLM response - handles numbered or non-numbered format'''
        sections = {}
        
        # Match patterns with optional numbers (e.g., "1. ROOT_CAUSE:" or "ROOT_CAUSE:")
        root_cause_match = re.search(
            r'(?:\d+\.\s*)?ROOT_CAUSE:\s*(.+?)(?=(?:\d+\.\s*)?(?:FIX_CODE:|ROLLBACK:|CONFIDENCE:|RISKS:)|\Z)',
            response,
            re.DOTALL | re.IGNORECASE
        )
        if root_cause_match:
            sections['root_cause'] = root_cause_match.group(1).strip()
        
        fix_code_match = re.search(
            r'(?:\d+\.\s*)?FIX_CODE:\s*(.+?)(?=(?:\d+\.\s*)?(?:ROLLBACK:|CONFIDENCE:|RISKS:)|\Z)',
            response,
            re.DOTALL | re.IGNORECASE
        )
        if fix_code_match:
            # Clean up code blocks
            code = fix_code_match.group(1).strip()
            # Remove markdown code fences if present
            code = re.sub(r'`(?:sql|yml|yaml)?\s*', '', code)
            code = re.sub(r'`\s*$', '', code)
            sections['fix_code'] = code.strip()
        
        rollback_match = re.search(
            r'(?:\d+\.\s*)?ROLLBACK:\s*(.+?)(?=(?:\d+\.\s*)?(?:CONFIDENCE:|RISKS:)|\Z)',
            response,
            re.DOTALL | re.IGNORECASE
        )
        if rollback_match:
            sections['rollback'] = rollback_match.group(1).strip()
        
        confidence_match = re.search(r'(?:\d+\.\s*)?CONFIDENCE:\s*(\d+)', response, re.IGNORECASE)
        if confidence_match:
            sections['confidence'] = int(confidence_match.group(1))
        
        risks_match = re.search(
            r'(?:\d+\.\s*)?RISKS:\s*(.+?)(?=\Z)',
            response,
            re.DOTALL | re.IGNORECASE
        )
        if risks_match:
            sections['risks'] = risks_match.group(1).strip()
        
        return sections
