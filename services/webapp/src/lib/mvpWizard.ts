import type { Project, ProjectDetails } from './api';

export type MvpFieldKey =
  | 'project_title'
  | 'problem'
  | 'audience_type'
  | 'niche'
  | 'goal'
  | 'author_name'
  | 'author_contact_value';

export const MVP_REQUIRED_FIELDS: MvpFieldKey[] = [
  'project_title',
  'problem',
  'audience_type',
  'niche',
  'goal',
  'author_name',
  'author_contact_value',
];

function isFilledValue(value: unknown): boolean {
  if (value === null || value === undefined) {
    return false;
  }
  if (typeof value === 'string') {
    return value.trim().length > 0;
  }
  if (Array.isArray(value)) {
    return value.length > 0;
  }
  return true;
}

export function isMvpFieldFilled(details: ProjectDetails | null, key: MvpFieldKey): boolean {
  const answers = details?.answers ?? {};
  if (key === 'author_contact_value') {
    const mode = (answers as Record<string, unknown>)['author_contact_mode'];
    const value = (answers as Record<string, unknown>)['author_contact_value'];
    return isFilledValue(mode) && isFilledValue(value);
  }
  return isFilledValue((answers as Record<string, unknown>)[key]);
}

export function calcMvpProgressFromDetails(details: ProjectDetails | null): {
  filled: number;
  total: number;
  percent: number;
} {
  const total = MVP_REQUIRED_FIELDS.length;
  const filled = MVP_REQUIRED_FIELDS.reduce((acc, key) => acc + (isMvpFieldFilled(details, key) ? 1 : 0), 0);
  const percent = total > 0 ? Math.round((filled / total) * 100) : 0;
  return { filled, total, percent };
}

export function getNextMvpField(details: ProjectDetails | null): MvpFieldKey | null {
  for (const key of MVP_REQUIRED_FIELDS) {
    if (!isMvpFieldFilled(details, key)) {
      return key;
    }
  }
  return null;
}

export function calcMvpPercentFromListItem(project: Project): number {
  const missing = new Set(project.missing_fields || []);
  const total = MVP_REQUIRED_FIELDS.length;
  const missingMvp = MVP_REQUIRED_FIELDS.filter((key) => {
    if (key === 'author_contact_value') {
      return missing.has('author_contact_mode') || missing.has('author_contact_value');
    }
    return missing.has(key);
  }).length;
  const filled = Math.max(0, total - missingMvp);
  return total > 0 ? Math.round((filled / total) * 100) : 0;
}

