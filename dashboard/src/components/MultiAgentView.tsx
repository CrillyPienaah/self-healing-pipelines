import { Brain, Loader2, Shield, Wrench } from 'lucide-react';
import { useState } from 'react';
import type { Anomaly, MultiAgentResult } from '../api/client';

interface Props {
  anomaly: Anomaly;
  onAnalyze: () => Promise<MultiAgentResult>;
}

export const MultiAgentView = ({ anomaly, onAnalyze }: Props) => {
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<MultiAgentResult | null>(null);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const analysis = await onAnalyze();
      setResult(analysis);
    } catch (error) {
      console.error('Multi-agent analysis failed:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="border rounded-lg p-6 bg-white shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-xl font-bold">🤖 Multi-Agent Analysis</h3>
          <p className="text-sm text-gray-600">Detective → Fixer → Critic</p>
        </div>
        
        {!result && (
          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 flex items-center gap-2"
          >
            {analyzing ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>🚀 Run Multi-Agent</>
            )}
          </button>
        )}
      </div>

      {result && (
        <div className="space-y-4">
          <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
            <div className="flex items-center gap-2 mb-2">
              <Brain className="w-5 h-5 text-blue-600" />
              <h4 className="font-bold">Detective</h4>
            </div>
            <p className="text-sm">{result.detective_analysis.root_cause}</p>
          </div>

          {result.proposed_fix && (
            <div className="border border-green-200 rounded-lg p-4 bg-green-50">
              <div className="flex items-center gap-2 mb-2">
                <Wrench className="w-5 h-5 text-green-600" />
                <h4 className="font-bold">Fixer ({result.proposed_fix.confidence_score}%)</h4>
              </div>
              <pre className="bg-gray-900 text-green-400 p-3 rounded text-xs">
                {result.proposed_fix.fix_code}
              </pre>
            </div>
          )}

          {result.critic_validation && (
            <div className="border border-purple-200 rounded-lg p-4 bg-purple-50">
              <div className="flex items-center gap-2 mb-2">
                <Shield className="w-5 h-5 text-purple-600" />
                <h4 className="font-bold">Critic (Safety: {result.critic_validation.safety_score}/100)</h4>
              </div>
              <p className="text-sm">{result.critic_validation.concerns}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};