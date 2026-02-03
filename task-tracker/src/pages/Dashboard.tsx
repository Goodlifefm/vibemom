import { useState, useEffect } from 'react';
import { Plus } from 'lucide-react';
import { Navbar } from '../components/Navbar';
import { TaskCard } from '../components/TaskCard';
import { TaskFormModal } from '../components/TaskFormModal';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { EmptyState } from '../components/EmptyState';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../lib/supabase';
import type { Task, TaskPriority, TaskStatus } from '../types/database';

type SortField = 'created_at' | 'deadline' | 'priority' | 'status';
type SortDir = 'asc' | 'desc';

const PRIORITY_ORDER: Record<TaskPriority, number> = {
  low: 1,
  medium: 2,
  high: 3,
  critical: 4,
};

const STATUS_ORDER: Record<TaskStatus, number> = {
  todo: 1,
  in_progress: 2,
  done: 3,
};

export function Dashboard() {
  const { user } = useAuth();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [deleteTask, setDeleteTask] = useState<Task | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [filterStatus, setFilterStatus] = useState<TaskStatus | 'all'>('all');
  const [filterPriority, setFilterPriority] = useState<TaskPriority | 'all'>('all');
  const [sortField, setSortField] = useState<SortField>('created_at');
  const [sortDir, setSortDir] = useState<SortDir>('desc');

  const fetchTasks = async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    const { data, error: err } = await supabase
      .from('tasks')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false });

    if (err) {
      setError(err.message);
      setTasks([]);
    } else {
      setTasks(data ?? []);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchTasks();
  }, [user?.id]);

  const filteredAndSortedTasks = [...tasks]
    .filter((t) => {
      if (filterStatus !== 'all' && t.status !== filterStatus) return false;
      if (filterPriority !== 'all' && t.priority !== filterPriority) return false;
      return true;
    })
    .sort((a, b) => {
      let cmp = 0;
      switch (sortField) {
        case 'created_at':
          cmp =
            new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
        case 'deadline':
          const da = a.deadline ? new Date(a.deadline).getTime() : Infinity;
          const db = b.deadline ? new Date(b.deadline).getTime() : Infinity;
          cmp = da - db;
          break;
        case 'priority':
          cmp = PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority];
          break;
        case 'status':
          cmp = STATUS_ORDER[a.status] - STATUS_ORDER[b.status];
          break;
      }
      return sortDir === 'asc' ? cmp : -cmp;
    });

  const handleCreate = () => {
    setEditingTask(null);
    setFormError(null);
    setFormOpen(true);
  };

  const handleEdit = (task: Task) => {
    setEditingTask(task);
    setFormError(null);
    setFormOpen(true);
  };

  const handleFormSubmit = async (data: {
    title: string;
    description: string;
    deadline: string;
    priority: TaskPriority;
    status: TaskStatus;
  }) => {
    if (!user) return;
    setFormLoading(true);
    setFormError(null);

    const payload = {
      title: data.title.trim(),
      description: data.description.trim() || null,
      deadline: data.deadline || null,
      priority: data.priority,
      status: data.status,
      updated_at: new Date().toISOString(),
    };

    if (editingTask) {
      const { error: err } = await supabase
        .from('tasks')
        .update(payload)
        .eq('id', editingTask.id)
        .eq('user_id', user.id);

      if (err) {
        setFormError(err.message);
        setFormLoading(false);
        return;
      }
    } else {
      const { error: err } = await supabase.from('tasks').insert({
        ...payload,
        user_id: user.id,
      });

      if (err) {
        setFormError(err.message);
        setFormLoading(false);
        return;
      }
    }

    setFormOpen(false);
    setFormLoading(false);
    fetchTasks();
  };

  const handleDeleteClick = (task: Task) => {
    setDeleteTask(task);
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTask || !user) return;
    setDeleteLoading(true);
    const { error: err } = await supabase
      .from('tasks')
      .delete()
      .eq('id', deleteTask.id)
      .eq('user_id', user.id);

    setDeleteLoading(false);
    setDeleteTask(null);
    if (!err) fetchTasks();
  };

  const handleStatusToggle = async (task: Task) => {
    if (!user) return;
    await supabase
      .from('tasks')
      .update({ status: 'done' as TaskStatus, updated_at: new Date().toISOString() })
      .eq('id', task.id)
      .eq('user_id', user.id);
    fetchTasks();
  };

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-4xl px-4 pb-24 pt-24">
        <div className="mb-8">
          <h1 className="font-display text-2xl font-bold text-white">
            My tasks
          </h1>
          <p className="mt-1 text-slate-400">
            Manage your tasks and stay productive
          </p>
        </div>

        {/* Filters & Sort */}
        <div className="mb-6 flex flex-wrap items-center gap-3">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as TaskStatus | 'all')}
            className="rounded-lg border border-slate-600 bg-slate-800/50 px-3 py-2 text-sm text-white focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
          >
            <option value="all">All statuses</option>
            <option value="todo">To Do</option>
            <option value="in_progress">In Progress</option>
            <option value="done">Done</option>
          </select>
          <select
            value={filterPriority}
            onChange={(e) =>
              setFilterPriority(e.target.value as TaskPriority | 'all')
            }
            className="rounded-lg border border-slate-600 bg-slate-800/50 px-3 py-2 text-sm text-white focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
          >
            <option value="all">All priorities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
          <select
            value={`${sortField}-${sortDir}`}
            onChange={(e) => {
              const [field, dir] = e.target.value.split('-') as [SortField, SortDir];
              setSortField(field);
              setSortDir(dir);
            }}
            className="rounded-lg border border-slate-600 bg-slate-800/50 px-3 py-2 text-sm text-white focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
          >
            <option value="created_at-desc">Newest first</option>
            <option value="created_at-asc">Oldest first</option>
            <option value="deadline-asc">Deadline (soonest)</option>
            <option value="deadline-desc">Deadline (latest)</option>
            <option value="priority-desc">Priority (high to low)</option>
            <option value="priority-asc">Priority (low to high)</option>
            <option value="status-asc">Status (To Do → Done)</option>
          </select>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="h-10 w-10 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
            <p className="mt-4 text-sm text-slate-400">Loading tasks...</p>
          </div>
        ) : error ? (
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-6 text-red-400">
            {error}
          </div>
        ) : filteredAndSortedTasks.length === 0 ? (
          <EmptyState onCreateClick={handleCreate} />
        ) : (
          <div className="space-y-4">
            {filteredAndSortedTasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onEdit={handleEdit}
                onDelete={handleDeleteClick}
                onStatusToggle={handleStatusToggle}
              />
            ))}
          </div>
        )}
      </main>

      {/* Floating Add Button */}
      <button
        onClick={handleCreate}
        className="fixed bottom-6 right-6 flex h-14 w-14 items-center justify-center rounded-full bg-brand-500 text-white shadow-lg transition hover:bg-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 focus:ring-offset-slate-900"
        aria-label="Add new task"
      >
        <Plus className="h-6 w-6" />
      </button>

      <TaskFormModal
        isOpen={formOpen}
        onClose={() => setFormOpen(false)}
        onSubmit={handleFormSubmit}
        task={editingTask}
        loading={formLoading}
        error={formError ?? undefined}
      />

      <ConfirmDialog
        isOpen={!!deleteTask}
        onClose={() => setDeleteTask(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete task"
        message={`Are you sure you want to delete "${deleteTask?.title}"? This action cannot be undone.`}
        confirmLabel="Delete"
        loading={deleteLoading}
      />
    </div>
  );
}
