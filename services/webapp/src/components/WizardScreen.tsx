import { useCallback, useEffect, useMemo, useState } from 'react';
import { getApiErrorInfo, getProject, patchProject, publishProject, type ApiErrorInfo, type ProjectDetails } from '../lib/api';
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

async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // Fallback for older WebViews.
    try {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.setAttribute('readonly', 'true');
      textarea.style.position = 'fixed';
      textarea.style.top = '-1000px';
      textarea.style.left = '-1000px';
      document.body.appendChild(textarea);
      textarea.select();
      const ok = document.execCommand('copy');
      document.body.removeChild(textarea);
      return ok;
    } catch {
      return false;
    }
  }
}

function goalLabel(value: unknown): string | null {
  const raw = typeof value === 'string' ? value : value ? String(value) : '';
  const v = raw.trim();
  if (!v) return null;
  const opt = goalOptions().find((o) => o.value === v);
  return opt?.label || v;
}

export function WizardScreen({
  projectId,
  onBack,
  onOpenDetails,
  onOpenPublic,
  onAfterSave,
}: {
  projectId: string;
  onBack: () => void;
  onOpenDetails: (id: string) => void;
  onOpenPublic?: (idOrSlug: string) => void;
  onAfterSave?: () => Promise<void> | void;
}) {
  const [details, setDetails] = useState<ProjectDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [showContacts, setShowContacts] = useState(false);
  const [publishedUrl, setPublishedUrl] = useState<string | null>(null);
  const [publishedIdOrSlug, setPublishedIdOrSlug] = useState<string | null>(null);
  const [copyStatus, setCopyStatus] = useState<'idle' | 'ok' | 'error'>('idle');
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
      setCopyStatus('idle');
      const existingShow = Boolean((data as any)?.show_contacts);
      setShowContacts(existingShow);
      if (Boolean((data as any)?.published)) {
        const slug = typeof (data as any)?.public_slug === 'string' ? String((data as any).public_slug) : '';
        const idOrSlug = slug.trim() ? slug.trim() : projectId;
        setPublishedIdOrSlug(idOrSlug);
        setPublishedUrl(`${window.location.origin}/p/${encodeURIComponent(idOrSlug)}`);
      } else {
        setPublishedIdOrSlug(null);
        setPublishedUrl(null);
      }
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
    const answersDone = (details?.answers ?? {}) as Record<string, unknown>;
    const title =
      typeof answersDone.project_title === 'string'
        ? answersDone.project_title
        : answersDone.project_title
          ? String(answersDone.project_title)
          : '';
    const problem =
      typeof answersDone.problem === 'string' ? answersDone.problem : answersDone.problem ? String(answersDone.problem) : '';
    const audience =
      typeof answersDone.audience_type === 'string'
        ? answersDone.audience_type
        : answersDone.audience_type
          ? String(answersDone.audience_type)
          : '';
    const niche = typeof answersDone.niche === 'string' ? answersDone.niche : answersDone.niche ? String(answersDone.niche) : '';
    const whatDone =
      typeof answersDone.what_done === 'string' ? answersDone.what_done : answersDone.what_done ? String(answersDone.what_done) : '';
    const devTime =
      typeof answersDone.dev_time === 'string' ? answersDone.dev_time : answersDone.dev_time ? String(answersDone.dev_time) : '';
    const potential =
      typeof answersDone.potential === 'string'
        ? answersDone.potential
        : answersDone.potential
          ? String(answersDone.potential)
          : '';

    const stackFree =
      typeof answersDone.stack_reason === 'string'
        ? answersDone.stack_reason
        : answersDone.stack_reason
          ? String(answersDone.stack_reason)
          : '';
    const stackParts = [
      typeof answersDone.stack_ai === 'string' ? answersDone.stack_ai : answersDone.stack_ai ? String(answersDone.stack_ai) : '',
      typeof answersDone.stack_tech === 'string' ? answersDone.stack_tech : answersDone.stack_tech ? String(answersDone.stack_tech) : '',
      typeof answersDone.stack_infra === 'string' ? answersDone.stack_infra : answersDone.stack_infra ? String(answersDone.stack_infra) : '',
    ].filter((v) => v.trim().length > 0);
    const stack = stackFree.trim() ? stackFree.trim() : stackParts.length > 0 ? stackParts.join(', ') : '';

    const authorName =
      typeof answersDone.author_name === 'string' ? answersDone.author_name : answersDone.author_name ? String(answersDone.author_name) : '';
    const contactValue =
      typeof answersDone.author_contact_value === 'string'
        ? answersDone.author_contact_value
        : answersDone.author_contact_value
          ? String(answersDone.author_contact_value)
          : '';

    const goal = goalLabel(answersDone.goal);

    const publishUrl =
      publishedUrl ||
      (publishedIdOrSlug ? `${window.location.origin}/p/${encodeURIComponent(publishedIdOrSlug)}` : null);

    const postText = [
      `Заголовок: «Сделал(а) ${title || 'проект'} с помощью вайбкодинга»`,
      '',
      `Что за проект: ${title || 'укажу позже'}`,
      `Проблема: ${problem || 'укажу позже'}`,
      `Для кого: ${audience || 'укажу позже'}`,
      `Ниша: ${niche || 'укажу позже'}`,
      `Что сделано: ${whatDone || 'укажу позже'}`,
      `Стек/инструменты: ${stack || 'укажу позже'}`,
      `Срок разработки: ${devTime || 'укажу позже'}`,
      `Потенциал/эффект: ${potential || 'укажу позже'}`,
      `Цель: ${goal || 'укажу позже'}`,
      `Контакт: ${showContacts ? `${authorName ? authorName + ' ' : ''}${contactValue || 'укажу позже'}` : 'пиши в личку автору в Vibe Market'}`,
      '',
      publishUrl ? publishUrl : '(ссылка появится после публикации)',
    ].join('\n');

    const doPublish = async () => {
      if (publishing) return;
      setPublishing(true);
      setErrorMessage(null);
      setErrorInfo(null);
      setCopyStatus('idle');
      try {
        const res = await publishProject(projectId, { show_contacts: showContacts });
        const idOrSlug = res.public_id || projectId;
        setPublishedIdOrSlug(idOrSlug);
        setPublishedUrl(res.public_url || `${window.location.origin}/p/${encodeURIComponent(idOrSlug)}`);

        const refreshed = await getProject(projectId);
        setDetails(refreshed);
        await onAfterSave?.();
      } catch (err) {
        const info = getApiErrorInfo(err);
        setErrorInfo(info);
        setErrorMessage(info.message || 'Не удалось опубликовать');
      } finally {
        setPublishing(false);
      }
    };

    return (
      <div className="detail-screen">
        <div className="detail-header">
          <button className="btn btn-secondary" onClick={onBack}>
            Назад
          </button>
          <h2>Готово</h2>
        </div>
        <div className="card">
          <div className="card-body">
            <h3 className="section-title" style={{ marginBottom: 8 }}>
              Проект готов
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              Опубликуйте проект, чтобы получить публичную ссылку и шаблон поста.
            </p>

            <label style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 12 }}>
              <input
                type="checkbox"
                checked={showContacts}
                onChange={(e) => setShowContacts(Boolean(e.target.checked))}
                style={{ width: 18, height: 18 }}
              />
              <span>Показывать контакты на публичной странице</span>
            </label>

            {publishUrl ? (
              <div style={{ marginTop: 12 }}>
                <p className="progress-text" style={{ marginBottom: 6 }}>
                  Публичная ссылка
                </p>
                <div className="detail-preview-html" style={{ maxHeight: 'unset' }}>
                  {publishUrl}
                </div>
              </div>
            ) : null}

            {copyStatus !== 'idle' ? (
              <p className="progress-text" style={{ marginTop: 10, color: copyStatus === 'ok' ? '#34c759' : '#ff3b30' }}>
                {copyStatus === 'ok' ? 'Скопировано' : 'Не удалось скопировать'}
              </p>
            ) : null}

            <WizardError info={errorInfo} message={errorMessage} />
          </div>

          <div className="card-footer" style={{ gap: 8, display: 'flex', flexWrap: 'wrap' }}>
            <button className="btn btn-primary" onClick={doPublish} disabled={publishing}>
              {publishing ? 'Публикация...' : 'Опубликовать проект'}
            </button>
            <button
              className="btn btn-secondary"
              onClick={async () => {
                if (!publishUrl) return;
                const ok = await copyToClipboard(publishUrl);
                setCopyStatus(ok ? 'ok' : 'error');
              }}
              disabled={!publishUrl}
            >
              Скопировать ссылку
            </button>
            <button
              className="btn btn-secondary"
              onClick={async () => {
                const ok = await copyToClipboard(postText);
                setCopyStatus(ok ? 'ok' : 'error');
              }}
              disabled={!publishUrl}
            >
              Скопировать текст для поста
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => {
                const idOrSlug = publishedIdOrSlug || projectId;
                if (onOpenPublic) {
                  onOpenPublic(idOrSlug);
                  return;
                }
                if (publishUrl) {
                  window.location.href = publishUrl;
                }
              }}
              disabled={!publishUrl}
            >
              Открыть публичную страницу
            </button>
            <button className="btn btn-secondary" onClick={() => onOpenDetails(projectId)}>
              Открыть проект
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
