/**
 * API types matching backend DTOs
 */

export type ProjectStatus = 'draft' | 'pending' | 'needs_fix' | 'approved' | 'rejected';
export type NextActionType = 'continue' | 'fix' | 'wait' | 'view' | 'archived';

export interface NextAction {
  action: NextActionType;
  label: string;
  cta_enabled: boolean;
}

export interface ProjectListItem {
  id: string;
  status: ProjectStatus;
  revision: number;
  title_short: string;
  completion_percent: number;
  next_action: NextAction;
  can_edit: boolean;
  can_submit: boolean;
  can_archive: boolean;
  can_delete: boolean;
  created_at: string;
  updated_at: string;
  submitted_at: string | null;
  has_fix_request: boolean;
  fix_request_preview: string | null;
  current_step: string | null;
  missing_fields: string[];
}

export interface ProjectFields {
  author_name: string | null;
  author_contact: string | null;
  author_role: string | null;
  project_title: string | null;
  project_subtitle: string | null;
  problem: string | null;
  audience_type: string | null;
  niche: string | null;
  what_done: string | null;
  project_status: string | null;
  stack_ai: string | null;
  stack_tech: string | null;
  stack_infra: string | null;
  stack_reason: string | null;
  dev_time: string | null;
  price_display: string | null;
  monetization: string | null;
  potential: string | null;
  goal: string | null;
  inbound_ready: string | null;
  links: string[];
  cool_part: string | null;
  hardest_part: string | null;
}

export interface ProjectDetails {
  id: string;
  status: ProjectStatus;
  revision: number;
  current_step: string | null;
  answers: Record<string, unknown> | null;
  fields: ProjectFields;
  preview_html: string | null;
  completion_percent: number;
  missing_fields: string[];
  filled_fields: string[];
  next_action: NextAction;
  can_edit: boolean;
  can_submit: boolean;
  can_archive: boolean;
  can_delete: boolean;
  fix_request: string | null;
  moderated_at: string | null;
  created_at: string;
  updated_at: string;
  submitted_at: string | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: {
    telegram_id: number;
    username: string | null;
    full_name: string | null;
    is_admin: boolean;
  };
}

export interface ApiError {
  detail: string;
  code?: string;
}
