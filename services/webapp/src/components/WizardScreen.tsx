import { useCallback, useEffect, useMemo, useState } from 'react';
import { getApiErrorInfo, getProject, patchProject, type ApiErrorInfo, type ProjectDetails } from '../lib/api';
import { MVP_REQUIRED_FIELDS, calcMvpProgressFromDetails, getNextMvpField, type MvpFieldKey } from '../lib/mvpWizard';

function WizardError({ info, message }: { info: ApiErrorInfo | null; message: string | null }) {
  if (!info && !message) {
    return null;
  }
  const req = info?.request ?? null;
  return (
    <div className="error">
      <p>{message || 'Не удалось сохранить'}</p>
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
    </div>
  );
}

function fieldTitle(key: MvpFieldKey): string {
  switch (key) {
    case 'project_title':
      return 'Название проекта';
    case 'problem':
      return 'Проблема';
    case 'audience_type':
      return 'Аудитория';
    case 'niche':
      return 'Ниша';
    case 'goal':
      return 'Цель публикации';
    case 'author_name':
      return 'Ваше имя';
    case 'author_contact_value':
      return 'Контакт для связи';
  }
}

function goalOptions(): Array<{ value: string; label: string }> {
  return [
    { value: 'sale', label: 'Продажа' },
    { value: 'investment', label: 'Инвестиции' },
    { value: 'partnership', label: 'Партнерство' },
    { value: 'team', label: 'Поиск команды' },
    { value: 'feedback', label: 'Обратная связь' },
  ];
}

export function WizardScreen({
  projectId,
  onBack,
  onOpenDetails,
  onAfterSave,
}: {
  projectId: string;
  onBack: () => void;
  onOpenDetails: (id: string) => void;
  onAfterSave?: () => Promise<void> | void;
}) {
  const [details, setDetails] = useState<ProjectDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [errorInfo, setErrorInfo] = useState<ApiErrorInfo | null>(null);

  const nextKey = useMemo(() => getNextMvpField(details), [details]);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    setIndex(0);
  }, [projectId]);

  const load = useCallback(async () => {
    setLoading(true);
    setErrorMessage(null);
    setErrorInfo(null);
    try {
      const data = await getProject(projectId);
      setDetails(data);
      const next = getNextMvpField(data);
      const nextIndex = next ? MVP_REQUIRED_FIELDS.indexOf(next) : MVP_REQUIRED_FIELDS.length - 1;
      setIndex(Math.max(0, nextIndex));
    } catch (err) {
      const info = getApiErrorInfo(err);
      setErrorInfo(info);
      setErrorMessage(info.message || 'Не удалось загрузить проект');
      setDetails(null);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    load();
  }, [load]);

  const key: MvpFieldKey | null = useMemo(() => MVP_REQUIRED_FIELDS[index] || null, [index]);

  const answers = (details?.answers ?? {}) as Record<string, unknown>;
  const [value, setValue] = useState<string>('');
  const [contactMode, setContactMode] = useState<string>('telegram');

  useEffect(() => {
    if (!key) {
      return;
    }
    if (key === 'author_contact_value') {
      const mode = typeof answers.author_contact_mode === 'string' ? answers.author_contact_mode : 'telegram';
      const v = typeof answers.author_contact_value === 'string' ? answers.author_contact_value : '';
      setContactMode(String(mode));
      setValue(String(v));
      return;
    }
    const raw = answers[key];
    setValue(typeof raw === 'string' ? raw : raw ? String(raw) : '');
  }, [answers, key]);

  const progress = useMemo(() => calcMvpProgressFromDetails(details), [details]);
  const stepNumber = useMemo(() => Math.min(MVP_REQUIRED_FIELDS.length, Math.max(1, index + 1)), [index]);

  const submit = useCallback(async () => {
    if (!key) {
      return;
    }
    if (!value.trim()) {
      setErrorMessage('Заполните поле перед сохранением');
      setErrorInfo(null);
      return;
    }

    setSaving(true);
    setErrorMessage(null);
    setErrorInfo(null);
    try {
      if (key === 'author_contact_value') {
        await patchProject(projectId, {
          author_contact_mode: contactMode,
          author_contact_value: value.trim(),
        });
      } else {
        await patchProject(projectId, { [key]: value.trim() } as any);
      }

      const refreshed = await getProject(projectId);
      setDetails(refreshed);

      const next = getNextMvpField(refreshed);
      if (next) {
        const nextIndex = MVP_REQUIRED_FIELDS.indexOf(next);
        if (nextIndex >= 0) {
          setIndex(nextIndex);
        }
      }

      await onAfterSave?.();
    } catch (err) {
      const info = getApiErrorInfo(err);
      setErrorInfo(info);
      setErrorMessage('Не удалось сохранить');
    } finally {
      setSaving(false);
    }
  }, [contactMode, key, onAfterSave, projectId, value]);

  if (loading) {
    return (
      <div className="detail-screen">
        <div className="detail-header">
          <button className="btn btn-secondary" onClick={onBack}>
            Назад
          </button>
          <h2>Заполнение</h2>
        </div>
        <p>Загрузка...</p>
      </div>
    );
  }

  if (!details) {
    return (
      <div className="detail-screen">
        <div className="detail-header">
          <button className="btn btn-secondary" onClick={onBack}>
            Назад
          </button>
          <h2>Заполнение</h2>
        </div>
        <WizardError info={errorInfo} message={errorMessage} />
        <button className="btn btn-primary" onClick={load}>
          Retry
        </button>
      </div>
    );
  }

  if (!nextKey) {
    return (
      <div className="detail-screen">
        <div className="detail-header">
          <button className="btn btn-secondary" onClick={onBack}>
            Назад
          </button>
          <h2>Заполнение</h2>
        </div>
        <div className="card">
          <p>Все обязательные поля заполнены.</p>
          <div className="card-footer">
            <button className="btn btn-primary" onClick={() => onOpenDetails(projectId)}>
              Открыть
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="detail-screen">
      <div className="detail-header">
        <button className="btn btn-secondary" onClick={onBack}>
          Назад
        </button>
        <h2>Заполнение</h2>
      </div>

      <div className="card">
        <div className="card-body">
          <p>
            Шаг {stepNumber} из {MVP_REQUIRED_FIELDS.length} (прогресс {progress.percent}%)
          </p>
          <div className="progress-bar">
            <div className="progress-bar-fill" style={{ width: `${progress.percent}%` }} />
          </div>

          <h3 className="section-title" style={{ marginTop: 12 }}>
            {fieldTitle(key || nextKey)}
          </h3>

          {key === 'problem' ? (
            <textarea className="form-input" rows={6} value={value} onChange={(e) => setValue(e.target.value)} />
          ) : key === 'goal' ? (
            <select className="form-input" value={value} onChange={(e) => setValue(e.target.value)}>
              <option value="">Выберите...</option>
              {goalOptions().map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          ) : key === 'author_contact_value' ? (
            <>
              <select className="form-input" value={contactMode} onChange={(e) => setContactMode(e.target.value)}>
                <option value="telegram">Telegram</option>
                <option value="email">Email</option>
                <option value="phone">Телефон</option>
              </select>
              <input
                className="form-input"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="@username / email / phone"
              />
            </>
          ) : (
            <input className="form-input" value={value} onChange={(e) => setValue(e.target.value)} />
          )}

          <WizardError info={errorInfo} message={errorMessage} />
        </div>

        <div className="card-footer" style={{ gap: 8, display: 'flex' }}>
          <button
            className="btn btn-secondary"
            onClick={() => setIndex((v) => Math.max(0, v - 1))}
            disabled={index <= 0 || saving}
          >
            Назад
          </button>
          <button className="btn btn-primary" onClick={submit} disabled={saving}>
            {saving ? 'Сохранение...' : 'Сохранить и дальше'}
          </button>
        </div>
      </div>
    </div>
  );
}
