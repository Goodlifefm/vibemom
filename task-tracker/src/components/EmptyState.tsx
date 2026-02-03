import { CheckSquare } from 'lucide-react';

interface EmptyStateProps {
  onCreateClick: () => void;
}

export function EmptyState({ onCreateClick }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-600/50 bg-slate-800/30 py-16 px-6">
      <div className="flex h-24 w-24 items-center justify-center rounded-full bg-slate-700/50">
        <CheckSquare className="h-12 w-12 text-slate-500" />
      </div>
      <h3 className="mt-4 font-display text-lg font-medium text-slate-300">
        No tasks yet
      </h3>
      <p className="mt-2 max-w-sm text-center text-sm text-slate-500">
        Get started by creating your first task. Click the button below to add one.
      </p>
      <button
        onClick={onCreateClick}
        className="mt-6 rounded-lg bg-brand-500 px-6 py-3 font-medium text-white transition hover:bg-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 focus:ring-offset-slate-900"
      >
        Create your first task
      </button>
    </div>
  );
}
