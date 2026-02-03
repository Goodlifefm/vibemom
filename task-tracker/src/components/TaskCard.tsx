import { Calendar, Pencil, Trash2 } from 'lucide-react';
import type { Task, TaskPriority, TaskStatus } from '../types/database';
import clsx from 'clsx';

const PRIORITY_STYLES: Record<TaskPriority, string> = {
  low: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
  medium: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  high: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  critical: 'bg-red-500/20 text-red-400 border-red-500/30',
};

const STATUS_STYLES: Record<TaskStatus, string> = {
  todo: 'bg-slate-500/20 text-slate-300',
  in_progress: 'bg-brand-500/20 text-brand-300',
  done: 'bg-emerald-500/20 text-emerald-300',
};

const STATUS_LABELS: Record<TaskStatus, string> = {
  todo: 'To Do',
  in_progress: 'In Progress',
  done: 'Done',
};

interface TaskCardProps {
  task: Task;
  onEdit: (task: Task) => void;
  onDelete: (task: Task) => void;
  onStatusToggle?: (task: Task) => void;
}

export function TaskCard({ task, onEdit, onDelete, onStatusToggle }: TaskCardProps) {
  const isOverdue =
    task.deadline &&
    task.status !== 'done' &&
    new Date(task.deadline) < new Date();

  const formatDeadline = (iso: string | null) => {
    if (!iso) return null;
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div
      className={clsx(
        'group rounded-xl border bg-slate-800/50 p-5 transition',
        'border-slate-700/50 hover:border-slate-600/50',
        isOverdue && 'border-red-500/30 bg-red-500/5'
      )}
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3
              className={clsx(
                'font-medium text-white',
                task.status === 'done' && 'line-through text-slate-400'
              )}
            >
              {task.title}
            </h3>
            <span
              className={clsx(
                'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium',
                PRIORITY_STYLES[task.priority]
              )}
            >
              {task.priority.charAt(0).toUpperCase() + task.priority.slice(1)}
            </span>
            <span
              className={clsx(
                'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                STATUS_STYLES[task.status]
              )}
            >
              {STATUS_LABELS[task.status]}
            </span>
          </div>

          {task.description && (
            <p className="mt-2 line-clamp-2 text-sm text-slate-400">
              {task.description}
            </p>
          )}

          {task.deadline && (
            <div
              className={clsx(
                'mt-2 flex items-center gap-1.5 text-sm',
                isOverdue ? 'text-red-400' : 'text-slate-500'
              )}
            >
              <Calendar className="h-4 w-4 shrink-0" />
              <span>
                {formatDeadline(task.deadline)}
                {isOverdue && ' (Overdue)'}
              </span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {task.status !== 'done' && onStatusToggle && (
            <button
              onClick={() => onStatusToggle(task)}
              className="rounded-lg border border-emerald-500/50 px-3 py-2 text-sm font-medium text-emerald-400 transition hover:bg-emerald-500/20"
            >
              Mark done
            </button>
          )}
          <button
            onClick={() => onEdit(task)}
            className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-700/50 hover:text-white"
            aria-label="Edit task"
          >
            <Pencil className="h-4 w-4" />
          </button>
          <button
            onClick={() => onDelete(task)}
            className="rounded-lg p-2 text-slate-400 transition hover:bg-red-500/20 hover:text-red-400"
            aria-label="Delete task"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
