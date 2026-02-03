export type TaskPriority = 'low' | 'medium' | 'high' | 'critical';
export type TaskStatus = 'todo' | 'in_progress' | 'done';

export interface Task {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  deadline: string | null;
  priority: TaskPriority;
  status: TaskStatus;
  created_at: string;
  updated_at: string;
}

export interface TaskInsert {
  user_id: string;
  title: string;
  description?: string | null;
  deadline?: string | null;
  priority: TaskPriority;
  status?: TaskStatus;
}

export interface TaskUpdate {
  title?: string;
  description?: string | null;
  deadline?: string | null;
  priority?: TaskPriority;
  status?: TaskStatus;
  updated_at?: string;
}
