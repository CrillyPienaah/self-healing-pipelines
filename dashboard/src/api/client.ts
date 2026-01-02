import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

export interface Pipeline {
  id: number;
  name: string;
  description: string;
  source_type: string;
  created_at: string;
}

export interface Anomaly {
  id: number;
  pipeline_id: number;
  type: string;
  severity: string;
  description: string;
  detected_at: string;
  resolved: string | null;
  details: {
    old_columns: Array<{ name: string; type: string }>;
    new_columns: Array<{ name: string; type: string }>;
  };
}

export interface Fix {
  id: number;
  anomaly_id: number;
  proposed_at: string;
  fix_type: string;
  root_cause: string;
  fix_code: string;
  rollback_plan: string;
  confidence_score: number;
  risks: string;
  status: string;
  applied_at: string | null;
}

export const healthCheck = async () => {
  const { data } = await api.get('/health');
  return data;
};

export const getPipelines = async () => {
  const { data } = await api.get('/api/v1/pipelines');
  return data;
};

export const getAnomalies = async (pipelineId: number, unresolvedOnly = true) => {
  const { data } = await api.get(`/api/v1/pipelines/${pipelineId}/anomalies`, {
    params: { unresolved_only: unresolvedOnly }
  });
  return data;
};

export const proposeFix = async (anomalyId: number) => {
  const { data } = await api.post(`/api/v1/anomalies/${anomalyId}/propose-fix`);
  return data;
};

export const approveFix = async (fixId: number) => {
  const { data } = await api.post(`/api/v1/fixes/${fixId}/approve`);
  return data;
};

export const rejectFix = async (fixId: number, reason?: string) => {
  const { data } = await api.post(`/api/v1/fixes/${fixId}/reject`, { reason });
  return data;
};

export const getFixesForAnomaly = async (anomalyId: number) => {
  const { data } = await api.get(`/api/v1/anomalies/${anomalyId}/fixes`);
  return data;
};