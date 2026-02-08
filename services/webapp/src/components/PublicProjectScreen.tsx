import { useCallback, useEffect, useMemo, useState } from 'react';
import { getApiErrorInfo, getPublicProject, type ApiErrorInfo, type PublicProject } from '../lib/api';

function goalLabel(value: string | null | undefined): string | null {
  const v = String(value || '').trim();
  if (!v) return null;
  switch (v) {
    case 'sale':
      return 'Продажа';
    case 'investment':
      return 'Инвестиции';
    case 'partnership':
      return 'Партнерство';
    case 'team':
      return 'Поиск команды';
    case 'feedback':
      return 'Обратная связь';
    default:
      return v;
  }
}

function PublicError({
  info,
  message,
  onRetry,
}: {
  info: ApiErrorInfo | null;
  message: string | null;
  onRetry?: () => void;
}) {
  if (!info && !message) return null;
  const req = info?.request ?? null;
  return (
    <div className="error">
      <p>{message || 'Не удалось загрузить проект'}</p>
      {req ? (
        <p className="error-meta">
          <span className="diagnostics-key">request</span>{' '}
          <span className="diagnostics-value">
            {req.method} {req.url} status={info?.status ?? '-'}
          </span>
        </p>
      ) : null}
      {info?.errorReportRequestId ? (
        <p className="error-meta">
          <span className="diagnostics-key">error_report_id</span>{' '}
          <span className="diagnostics-value">{info.errorReportRequestId}</span>
        </p>
      ) : null}
      {onRetry ? (
        <button className="btn btn-secondary" onClick={onRetry}>
          Retry
        </button>
      ) : null}
    </div>
  );
}

function Section({ title, value }: { title: string; value: string | null }) {
  if (!value) return null;
  return (
    <div className="detail-section">
      <h3 className="detail-section-title">{title}</h3>
      <div className="detail-preview-html" style={{ maxHeight: 'unset' }}>
        {value}
      </div>
    </div>
  );
}

export function PublicProjectScreen({
  idOrSlug,
  onBack,
}: {
  idOrSlug: string;
  onBack?: () => void;
}) {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<PublicProject | null>(null);
  const [errorInfo, setErrorInfo] = useState<ApiErrorInfo | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setErrorInfo(null);
    setErrorMessage(null);
    try {
      const project = await getPublicProject(idOrSlug);
      setData(project);
    } catch (err) {
      const info = getApiErrorInfo(err);
      setErrorInfo(info);
      setErrorMessage(info.message || 'Не удалось загрузить проект');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [idOrSlug]);

  useEffect(() => {
    load();
  }, [load]);

  const publishedAt = useMemo(() => {
    if (!data?.published_at) return null;
    try {
      return new Date(data.published_at).toLocaleString('ru');
    } catch {
      return data.published_at;
    }
  }, [data?.published_at]);

  if (loading) {
    return (
      <div className="detail-screen">
        {onBack ? (
          <button className="btn-back" onClick={onBack}>
            ← Назад
          </button>
        ) : null}
        <p>Загрузка...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="detail-screen">
        {onBack ? (
          <button className="btn-back" onClick={onBack}>
            ← Назад
          </button>
        ) : null}
        <PublicError info={errorInfo} message={errorMessage} onRetry={load} />
      </div>
    );
  }

  const goal = goalLabel(data.goal);

  return (
    <div className="detail-screen">
      {onBack ? (
        <button className="btn-back" onClick={onBack}>
          ← Назад
        </button>
      ) : null}

      <div className="detail-card">
        <div className="detail-header">
          <h2 className="detail-title">{data.title || 'Без названия'}</h2>
          <span className="badge badge-approved">Опубликовано</span>
        </div>

        {publishedAt ? (
          <p className="progress-text" style={{ marginTop: -8 }}>
            {publishedAt}
          </p>
        ) : null}

        <Section title="Проблема" value={data.problem} />
        <Section title="Для кого" value={data.audience_type} />
        <Section title="Ниша" value={data.niche} />
        <Section title="Что сделано" value={data.what_done} />
        <Section title="Стек / инструменты" value={data.stack} />
        <Section title="Срок разработки" value={data.dev_time} />
        <Section title="Потенциал / эффект" value={data.potential} />
        <Section title="Цель" value={goal} />

        {data.show_contacts && data.contact_value ? (
          <div className="detail-section">
            <h3 className="detail-section-title">Контакты</h3>
            <div className="detail-preview-html" style={{ maxHeight: 'unset' }}>
              {data.author_name ? (
                <div style={{ marginBottom: 8 }}>
                  <strong>{data.author_name}</strong>
                </div>
              ) : null}
              <div>
                {data.contact_mode ? <span style={{ color: 'var(--text-muted)' }}>{data.contact_mode}: </span> : null}
                {data.contact_value}
              </div>
            </div>
          </div>
        ) : null}

        <div className="detail-meta">
          <div className="detail-meta-row">
            <span className="detail-meta-key">ID</span>
            <span className="detail-meta-value">{data.id.slice(0, 8)}…</span>
          </div>
          <div className="detail-meta-row">
            <span className="detail-meta-key">Ссылка</span>
            <span className="detail-meta-value">{data.public_url}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

