import { Calendar, Database } from 'lucide-react';
import type { Pipeline } from '../api/client';

interface Props {
  pipeline: Pipeline;
  onClick: () => void;
  isSelected: boolean;
}

export const PipelineCard = ({ pipeline, onClick, isSelected }: Props) => {
  return (
    <div
      onClick={onClick}
      className={`p-4 border rounded-lg cursor-pointer transition-all ${
        isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <Database className="w-5 h-5 text-blue-600 mt-1" />
          <div>
            <h3 className="font-semibold text-lg">{pipeline.name}</h3>
            <p className="text-sm text-gray-600">{pipeline.description}</p>
            <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
              <Calendar className="w-3 h-3" />
              {new Date(pipeline.created_at).toLocaleDateString()}
            </div>
          </div>
        </div>
        <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
          {pipeline.source_type}
        </span>
      </div>
    </div>
  );
};