import { useEffect } from 'react';
import { X } from 'lucide-react';
import type { Task, TaskPriority, TaskStatus } from '../types/database';

const PRIORITIES: { value: TaskPriority; label: string }[] = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' },
];

const STATUSES: { value: TaskStatus; label: string }[] = [
  { value: 'todo', label: 'To Do' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'done', label: 'Done' },
];

interface TaskFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: {
    title: string;
    description: string;
    deadline: string;
    priority: TaskPriority;
    status: TaskStatus;
  }) => void;
  task?: Task | null;
  loading?: boolean;
  error?: string;
}

export function TaskFormModal({
  isOpen,
  onClose,
  onSubmit,
  task,
  loading = false,
  error,
}: TaskFormModalProps) {
  const isEdit = !!task;

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const formData = new FormData(form);
    onSubmit({
      title: formData.get('title') as string,
      description: (formData.get('description') as string) || '',
      deadline: (formData.get('deadline') as string) || '',
      priority: (formData.get('priority') as TaskPriority) || 'medium',
      status: (formData.get('status') as TaskStatus) || 'todo',
    });
  };

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const formatDateTimeLocal = (iso: string | null) => {
    if (!iso) return '';
    const d = new Date(iso);
    const pad = (n: number) => n.toString().padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        className="relative w-full max-w-lg animate-fade-in rounded-2xl border border-slate-700/50 bg-slate-800 shadow-2xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <div className="flex items-center justify-between border-b border-slate-700/50 px-6 py-4">
          <h2 id="modal-title" className="font-display text-xl font-semibold text-white">
            {isEdit ? 'Edit task' : 'New task'}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-700/50 hover:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="title" className="mb-2 block text-sm font-medium text-slate-300">
              Title <span className="text-red-400">*</span>
            </label>
            <input
              id="title"
              name="title"
              type="text"
              required
              defaultValue={task?.title}
              maxLength={200}
              className="w-full rounded-lg border border-slate-600 bg-slate-900/50 px-4 py-3 text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
              placeholder="Task title"
            />
          </div>

          <div>
            <label htmlFor="description" className="mb-2 block text-sm font-medium text-slate-300">
              Description
            </label>
            <textarea
              id="description"
              name="description"
              rows={3}
              defaultValue={task?.description ?? ''}
              className="w-full rounded-lg border border-slate-600 bg-slate-900/50 px-4 py-3 text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 resize-none"
              placeholder="Add details..."
            />
          </div>

          <div>
            <label htmlFor="deadline" className="mb-2 block text-sm font-medium text-slate-300">
              Deadline
            </label>
            <input
              id="deadline"
              name="deadline"
              type="datetime-local"
              defaultValue={formatDateTimeLocal(task?.deadline ?? null)}
              className="w-full rounded-lg border border-slate-600 bg-slate-900/50 px-4 py-3 text-white focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="priority" className="mb-2 block text-sm font-medium text-slate-300">
                Priority
              </label>
              <select
                id="priority"
                name="priority"
                defaultValue={task?.priority ?? 'medium'}
                className="w-full rounded-lg border border-slate-600 bg-slate-900/50 px-4 py-3 text-white focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
              >
                {PRIORITIES.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="status" className="mb-2 block text-sm font-medium text-slate-300">
                Status
              </label>
              <select
                id="status"
                name="status"
                defaultValue={task?.status ?? 'todo'}
                className="w-full rounded-lg border border-slate-600 bg-slate-900/50 px-4 py-3 text-white focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
              >
                {STATUSES.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-lg border border-slate-600 px-4 py-3 font-medium text-slate-300 transition hover:bg-slate-700/50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 rounded-lg bg-brand-500 px-4 py-3 font-medium text-white transition hover:bg-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 focus:ring-offset-slate-800 disabled:opacity-50"
            >
              {loading ? 'Saving...' : isEdit ? 'Save changes' : 'Create task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
