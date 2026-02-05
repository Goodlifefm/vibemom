import type { ProjectDetails } from '../types';

interface ProjectDetailsViewProps {
  project: ProjectDetails;
  isLoading: boolean;
  onBack: () => void;
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

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  const date = new Date(dateStr);
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

function ProjectDetailsView({
  project,
  isLoading,
  onBack,
}: ProjectDetailsViewProps) {
  const title = project.fields.project_title || 'Без названия';

  return (
    <>
      <header className="header">
        <button className="btn btn-icon" onClick={onBack}>
          ←
        </button>
        <span className="header-title" style={{ flex: 1, textAlign: 'center' }}>
          Проект
        </span>
        <div style={{ width: 40 }} />
      </header>

      <div className="project-details">
        {isLoading ? (
          <div className="loading">
            <div className="spinner" />
          </div>
        ) : (
          <>
            {/* Header section */}
            <div className="card">
              <div className="card-header">
                <h2 className="card-title" style={{ fontSize: '1.25rem' }}>
                  {title}
                </h2>
                <span className={`badge ${getStatusBadgeClass(project.status)}`}>
                  {getStatusLabel(project.status)}
                </span>
              </div>

              {project.fields.project_subtitle && (
                <p className="card-subtitle">{project.fields.project_subtitle}</p>
              )}

              <div className="meta" style={{ marginTop: '0.75rem' }}>
                <span className="meta-item">📝 {project.completion_percent}%</span>
                <span className="meta-item">🔄 Rev {project.revision}</span>
                <span className="meta-item">📅 {formatDate(project.updated_at)}</span>
              </div>

              <div className="progress">
                <div
                  className="progress-bar"
                  style={{ width: `${project.completion_percent}%` }}
                />
              </div>
            </div>

            {/* Fix request alert */}
            {project.fix_request && (
              <div
                className="card"
                style={{
                  borderLeft: '3px solid var(--tg-theme-destructive-text-color)',
                }}
              >
                <div className="project-section-title">⚠️ Требуются правки</div>
                <p style={{ fontSize: '0.9375rem' }}>{project.fix_request}</p>
              </div>
            )}

            {/* Missing fields */}
            {project.missing_fields.length > 0 && (
              <div className="project-section">
                <div className="project-section-title">Незаполненные поля</div>
                <div className="card">
                  {project.missing_fields.map((field) => (
                    <div
                      key={field}
                      style={{
                        padding: '0.5rem 0',
                        borderBottom: '1px solid var(--tg-theme-secondary-bg-color)',
                        fontSize: '0.875rem',
                      }}
                    >
                      • {field}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Preview */}
            {project.preview_html && (
              <div className="project-section">
                <div className="project-section-title">Предпросмотр</div>
                <div
                  className="project-preview"
                  dangerouslySetInnerHTML={{ __html: project.preview_html }}
                />
              </div>
            )}

            {/* Info sections */}
            <div className="project-section">
              <div className="project-section-title">Информация</div>
              <div className="card">
                {project.fields.author_name && (
                  <InfoRow label="Автор" value={project.fields.author_name} />
                )}
                {project.fields.author_contact && (
                  <InfoRow label="Контакт" value={project.fields.author_contact} />
                )}
                {project.fields.niche && (
                  <InfoRow label="Ниша" value={project.fields.niche} />
                )}
                {project.fields.dev_time && (
                  <InfoRow label="Время разработки" value={project.fields.dev_time} />
                )}
                {project.fields.price_display && (
                  <InfoRow label="Цена" value={project.fields.price_display} />
                )}
                {project.fields.goal && (
                  <InfoRow label="Цель" value={project.fields.goal} />
                )}
              </div>
            </div>

            {/* Timestamps */}
            <div className="project-section">
              <div className="project-section-title">Даты</div>
              <div className="card">
                <InfoRow label="Создан" value={formatDate(project.created_at)} />
                <InfoRow label="Обновлён" value={formatDate(project.updated_at)} />
                {project.submitted_at && (
                  <InfoRow label="Отправлен" value={formatDate(project.submitted_at)} />
                )}
                {project.moderated_at && (
                  <InfoRow label="Модерация" value={formatDate(project.moderated_at)} />
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="action-row">
              <button className="btn btn-secondary" onClick={onBack}>
                ← Назад
              </button>
            </div>
          </>
        )}
      </div>
    </>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        padding: '0.5rem 0',
        borderBottom: '1px solid var(--tg-theme-secondary-bg-color)',
        fontSize: '0.875rem',
      }}
    >
      <span style={{ color: 'var(--tg-theme-hint-color)' }}>{label}</span>
      <span style={{ fontWeight: 500 }}>{value}</span>
    </div>
  );
}

export default ProjectDetailsView;
