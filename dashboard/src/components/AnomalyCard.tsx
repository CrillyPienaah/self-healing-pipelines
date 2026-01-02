import { AlertTriangle, CheckCircle, Loader2, XCircle } from 'lucide-react';
import { useState } from 'react';
import type { Anomaly, Fix } from '../api/client';

interface Props {
  anomaly: Anomaly;
  fix?: Fix;
  onGenerateFix: () => Promise<void>;
  onApproveFix: (fixId: number) => Promise<void>;
  onRejectFix: (fixId: number) => Promise<void>;
}

export const AnomalyCard = ({ anomaly, fix, onGenerateFix, onApproveFix, onRejectFix }: Props) => {
  const [generating, setGenerating] = useState(false);
  const [approving, setApproving] = useState(false);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const handleGenerateFix = async () => {
    setGenerating(true);
    try {
      await onGenerateFix();
    } finally {
      setGenerating(false);
    }
  };

  const handleApproveFix = async () => {
    if (!fix) return;
    setApproving(true);
    try {
      await onApproveFix(fix.id);
    } finally {
      setApproving(false);
    }
  };

  return (
    <div className="border rounded-lg p-6 bg-white shadow-sm">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-yellow-600 mt-1" />
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getSeverityColor(anomaly.severity)}`}>
                {anomaly.severity}
              </span>
              <span className="text-sm text-gray-600">{anomaly.type}</span>
            </div>
            <p className="text-gray-800 font-medium">{anomaly.description}</p>
            <p className="text-sm text-gray-500 mt-1">
              Detected: {new Date(anomaly.detected_at).toLocaleString()}
            </p>
          </div>
        </div>
        
        {!fix && (
          <button
            onClick={handleGenerateFix}
            disabled={generating}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 flex items-center gap-2"
          >
            {generating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Generating...
              </>
            ) : (
              <>🔧 Generate Fix</>
            )}
          </button>
        )}
      </div>

      {fix && (
        <div className="mt-4 bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="flex items-center justify-between mb-3">
            <div className="font-bold text-lg">AI-Generated Fix</div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Confidence:</span>
              <span className={`font-bold text-lg ${
                fix.confidence_score >= 80 ? 'text-green-600' : 
                fix.confidence_score >= 60 ? 'text-yellow-600' : 'text-red-600'
              }`}>
                {fix.confidence_score}%
              </span>
            </div>
          </div>

          <div className="mb-3">
            <div className="text-sm font-semibold text-gray-700 mb-1">Root Cause:</div>
            <p className="text-sm text-gray-800 bg-white p-3 rounded border">{fix.root_cause}</p>
          </div>

          <div className="mb-3">
            <div className="text-sm font-semibold text-gray-700 mb-1">Fix Code:</div>
            <pre className="bg-gray-900 text-green-400 p-4 rounded overflow-x-auto text-sm font-mono">
              {fix.fix_code}
            </pre>
          </div>

          <div className="mb-3">
            <div className="text-sm font-semibold text-gray-700 mb-1">Rollback Plan:</div>
            <p className="text-sm text-gray-800 bg-white p-3 rounded border">{fix.rollback_plan}</p>
          </div>

          <div className="mb-4">
            <div className="text-sm font-semibold text-gray-700 mb-1">Risks:</div>
            <p className="text-sm text-gray-800 bg-white p-3 rounded border">{fix.risks}</p>
          </div>

          {fix.status === 'pending' && (
            <div className="flex gap-3">
              <button
                onClick={handleApproveFix}
                disabled={approving}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 flex items-center justify-center gap-2"
              >
                {approving ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                Approve Fix
              </button>
              <button
                onClick={() => onRejectFix(fix.id)}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center justify-center gap-2"
              >
                <XCircle className="w-4 h-4" />
                Reject Fix
              </button>
            </div>
          )}

          {fix.status === 'approved' && (
            <div className="px-4 py-2 bg-green-100 text-green-800 rounded-lg text-center font-semibold">
              ✅ Fix Approved
            </div>
          )}

          {fix.status === 'rejected' && (
            <div className="px-4 py-2 bg-red-100 text-red-800 rounded-lg text-center font-semibold">
              ❌ Fix Rejected
            </div>
          )}
        </div>
      )}
    </div>
  );
};