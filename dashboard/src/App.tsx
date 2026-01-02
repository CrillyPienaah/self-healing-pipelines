import { QueryClient, QueryClientProvider, useMutation, useQuery } from '@tanstack/react-query';
import { Activity, AlertTriangle, Database, Wrench } from 'lucide-react';
import { useEffect, useState } from 'react';
import * as api from './api/client';
import './App.css';
import { AnomalyCard } from './components/AnomalyCard';
import { PipelineCard } from './components/PipelineCard';

const queryClient = new QueryClient();

function Dashboard() {
  const [selectedPipelineId, setSelectedPipelineId] = useState<number | null>(null);

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: api.healthCheck,
    refetchInterval: 5000,
  });

  const { data: pipelinesData } = useQuery({
    queryKey: ['pipelines'],
    queryFn: api.getPipelines,
    refetchInterval: 5000,
  });

  const { data: anomaliesData, refetch: refetchAnomalies } = useQuery({
    queryKey: ['anomalies', selectedPipelineId],
    queryFn: () => selectedPipelineId ? api.getAnomalies(selectedPipelineId, false) : Promise.resolve({ anomalies: [], count: 0 }),
    enabled: !!selectedPipelineId,
    refetchInterval: 5000,
  });

  const [anomaliesWithFixes, setAnomaliesWithFixes] = useState<Array<{ anomaly: api.Anomaly; fix?: api.Fix }>>([]);

  useEffect(() => {
    const fetchFixes = async () => {
      if (!anomaliesData?.anomalies) return;

      const withFixes = await Promise.all(
        anomaliesData.anomalies.map(async (anomaly: api.Anomaly) => {
          try {
            const fixesData = await api.getFixesForAnomaly(anomaly.id);
            return { anomaly, fix: fixesData.fixes[0] };
          } catch {
            return { anomaly };
          }
        })
      );

      setAnomaliesWithFixes(withFixes);
    };

    fetchFixes();
  }, [anomaliesData]);

  const generateFixMutation = useMutation({
    mutationFn: api.proposeFix,
    onSuccess: () => refetchAnomalies(),
  });

  const approveFixMutation = useMutation({
    mutationFn: api.approveFix,
    onSuccess: () => refetchAnomalies(),
  });

  const rejectFixMutation = useMutation({
    mutationFn: (fixId: number) => api.rejectFix(fixId),
    onSuccess: () => refetchAnomalies(),
  });

  const pipelines = pipelinesData?.pipelines || [];
  const totalAnomalies = anomaliesData?.count || 0;
  const pendingFixes = anomaliesWithFixes.filter(a => a.fix?.status === 'pending').length;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">
            🔧 Self-Healing Pipeline Dashboard
          </h1>
          <p className="text-gray-600 mt-1">AI-powered autonomous data pipeline remediation</p>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center gap-3">
              <Database className="w-8 h-8 text-blue-600" />
              <div>
                <div className="text-sm text-gray-500">Pipelines</div>
                <div className="text-3xl font-bold text-gray-900">{pipelines.length}</div>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-8 h-8 text-red-600" />
              <div>
                <div className="text-sm text-gray-500">Anomalies</div>
                <div className="text-3xl font-bold text-red-600">{totalAnomalies}</div>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center gap-3">
              <Wrench className="w-8 h-8 text-yellow-600" />
              <div>
                <div className="text-sm text-gray-500">Pending Fixes</div>
                <div className="text-3xl font-bold text-yellow-600">{pendingFixes}</div>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center gap-3">
              <Activity className="w-8 h-8 text-green-600" />
              <div>
                <div className="text-sm text-gray-500">LLM Status</div>
                <div className={`text-2xl font-bold ${health?.llm_available ? 'text-green-600' : 'text-gray-400'}`}>
                  {health?.llm_available ? '🤖 Online' : '❌ Offline'}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow mb-8">
          <div className="p-6 border-b">
            <h2 className="text-2xl font-bold">Pipelines</h2>
          </div>
          <div className="p-6">
            {pipelines.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <Database className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p>No pipelines registered yet</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {pipelines.map((pipeline: api.Pipeline) => (
                  <PipelineCard
                    key={pipeline.id}
                    pipeline={pipeline}
                    onClick={() => setSelectedPipelineId(pipeline.id)}
                    isSelected={selectedPipelineId === pipeline.id}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {selectedPipelineId && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b">
              <h2 className="text-2xl font-bold">Anomalies & AI-Generated Fixes</h2>
            </div>
            <div className="p-6">
              {anomaliesWithFixes.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Activity className="w-16 h-16 mx-auto mb-4 text-green-300" />
                  <p className="text-lg font-semibold">No anomalies detected</p>
                  <p className="text-sm">Pipeline is healthy!</p>
                </div>
              ) : (
                <div className="space-y-6">
                  {anomaliesWithFixes.map(({ anomaly, fix }) => (
                    <AnomalyCard
                      key={anomaly.id}
                      anomaly={anomaly}
                      fix={fix}
                      onGenerateFix={() => generateFixMutation.mutateAsync(anomaly.id)}
                      onApproveFix={(fixId) => approveFixMutation.mutateAsync(fixId)}
                      onRejectFix={(fixId) => rejectFixMutation.mutateAsync(fixId)}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Dashboard />
    </QueryClientProvider>
  );
}

export default App;