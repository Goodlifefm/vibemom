import type { ProjectListItem } from '../types';

interface DashboardProps {
  projects: ProjectListItem[];
  isLoading: boolean;
  error: string | null;
  onRefresh: () => void;
  onOpenProject: (id: string) => void;
  onCreateDraft: () => void;
}

function getStatusBadgeClass(status: string): string {
  const statusMap: Record<string, string> = {
    draft: 'badge-draft',
    pending: 'badge-pending',
    needs_fix: 'badge-needs-fix',
    approved: 'badge-approved',
    rejected: 'badge-rejected',
  };
  return statusMap[status] || 'badge-draft';
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: 'Черновик',
    pending: 'На модерации',
    needs_fix: 'Нужны правки',
    approved: 'Опубликован',
    rejected: 'Отклонён',
  };
  return labels[status] || status;
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
  });
}

function ProjectCard({
  project,
  onClick,
}: {
  project: ProjectListItem;
  onClick: () => void;
}) {
  return (
    <div className="card card-clickable" onClick={onClick}>
      <div className="card-header">
        <h3 className="card-title">{project.title_short || 'Без названия'}</h3>
        <span className={`badge ${getStatusBadgeClass(project.status)}`}>
          {getStatusLabel(project.status)}
        </span>
      </div>
      
      <div className="card-body">
        <div className="meta">
          <span className="meta-item">📅 {formatDate(project.updated_at)}</span>
          <span className="meta-item">📝 {project.completion_percent}% заполнено</span>
        </div>
        
        <div className="progress">
          <div
            className="progress-bar"
            style={{ width: `${project.completion_percent}%` }}
          />
        </div>
        
        {project.has_fix_request && project.fix_request_preview && (
          <div style={{ marginTop: '0.5rem', fontSize: '0.8125rem', color: 'var(--tg-theme-destructive-text-color)' }}>
            ⚠️ {project.fix_request_preview}
          </div>
        )}
      </div>
      
      <div className="card-footer">
        <span style={{ fontSize: '0.875rem', color: 'var(--tg-theme-accent-text-color)' }}>
          {project.next_action.label} →
        </span>
      </div>
    </div>
  );
}

function Dashboard({
  projects,
  isLoading,
  error,
  onRefresh,
  onOpenProject,
  onCreateDraft,
}: DashboardProps) {
  return (
    <>
      <header className="header">
        <span className="header-title">Мои проекты</span>
        <button
          className="btn btn-icon"
          onClick={onRefresh}
          disabled={isLoading}
          title="Обновить"
        >
          🔄
        </button>
      </header>

      <div className="container">
        {error && (
          <div className="error" style={{ padding: '1rem' }}>
            <div className="error-text">{error}</div>
          </div>
        )}

        {isLoading && projects.length === 0 ? (
          <div className="loading">
            <div className="spinner" />
            <div>Загрузка проектов...</div>
          </div>
        ) : projects.length === 0 ? (
          <div className="empty">
            <div className="empty-icon">📁</div>
            <div className="empty-title">Пока нет проектов</div>
            <div className="empty-text">
              Создайте свой первый проект для публикации
            </div>
            <button
              className="btn btn-primary"
              onClick={onCreateDraft}
              disabled={isLoading}
            >
              ➕ Создать проект
            </button>
          </div>
        ) : (
          <>
            {projects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onClick={() => onOpenProject(project.id)}
              />
            ))}
            
            <button
              className="btn btn-primary btn-full"
              onClick={onCreateDraft}
              disabled={isLoading}
              style={{ marginTop: '1rem' }}
            >
              ➕ Создать проект
            </button>
          </>
        )}
      </div>
    </>
  );
}

export default Dashboard;
