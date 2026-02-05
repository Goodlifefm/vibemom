import { useState, useEffect, useCallback } from 'react'
import { api, diagnosticInfo, isApiConfigured, isDemoMode } from './api'
import type { ProjectListItem, ProjectDetails, AuthResponse } from './types'
import Dashboard from './components/Dashboard'
import ProjectDetailsView from './components/ProjectDetails'

type Screen = 'loading' | 'dashboard' | 'project-details';

/**
 * Demo mode banner - shown when app runs without real API
 */
function DemoBanner() {
  return (
    <div className="demo-banner">
      <span>🎭 Demo Mode</span>
      <span style={{ fontSize: '0.75rem', opacity: 0.8 }}>
        Данные — заглушки. API не подключён.
      </span>
    </div>
  );
}

/**
 * Diagnostic banner component for debugging Mini App issues
 */
function DiagnosticBanner({ error }: { error: string | null }) {
  const [expanded, setExpanded] = useState(false);
  
  return (
    <div className="diagnostic-banner">
      <button 
        className="diagnostic-toggle"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? '▼' : '▶'} Diagnostic Info
      </button>
      {expanded && (
        <div className="diagnostic-content">
          <div><strong>Demo mode:</strong> {diagnosticInfo.demoMode ? 'yes' : 'no'}</div>
          <div><strong>initData present:</strong> {diagnosticInfo.initDataPresent() ? 'yes' : 'no'}</div>
          <div><strong>API base URL:</strong> {diagnosticInfo.apiBaseUrl}</div>
          <div><strong>Last error:</strong> {error || diagnosticInfo.lastError || 'none'}</div>
        </div>
      )}
    </div>
  );
}

interface AppState {
  screen: Screen;
  isLoading: boolean;
  error: string | null;
  user: AuthResponse['user'] | null;
  projects: ProjectListItem[];
  selectedProject: ProjectDetails | null;
}

function App() {
  const [state, setState] = useState<AppState>({
    screen: 'loading',
    isLoading: true,
    error: null,
    user: null,
    projects: [],
    selectedProject: null,
  });

  const tg = window.Telegram?.WebApp;

  // Initialize app: authenticate and load projects
  const init = useCallback(async () => {
    try {
      setState(s => ({ ...s, isLoading: true, error: null }));

      // Authenticate with Telegram initData
      const authResponse = await api.authenticate();
      
      // Load projects
      const projects = await api.getMyProjects();

      setState(s => ({
        ...s,
        screen: 'dashboard',
        isLoading: false,
        user: authResponse.user,
        projects,
      }));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Ошибка загрузки';
      setState(s => ({ ...s, isLoading: false, error: message }));
    }
  }, []);

  // Initialize on mount
  useEffect(() => {
    init();
  }, [init]);

  // Setup Telegram BackButton
  useEffect(() => {
    if (!tg) return;

    const handleBack = () => {
      if (state.screen === 'project-details') {
        setState(s => ({ ...s, screen: 'dashboard', selectedProject: null }));
      }
    };

    if (state.screen === 'project-details') {
      tg.BackButton.show();
      tg.BackButton.onClick(handleBack);
    } else {
      tg.BackButton.hide();
    }

    return () => {
      tg.BackButton.offClick(handleBack);
    };
  }, [state.screen, tg]);

  // Refresh projects
  const handleRefresh = useCallback(async () => {
    try {
      setState(s => ({ ...s, isLoading: true, error: null }));
      const projects = await api.getMyProjects();
      setState(s => ({ ...s, projects, isLoading: false }));
      tg?.hapticFeedback?.impactOccurred('light');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Ошибка обновления';
      setState(s => ({ ...s, isLoading: false, error: message }));
    }
  }, [tg]);

  // Open project details
  const handleOpenProject = useCallback(async (projectId: string) => {
    try {
      setState(s => ({ ...s, isLoading: true, error: null }));
      const project = await api.getProject(projectId);
      setState(s => ({
        ...s,
        screen: 'project-details',
        selectedProject: project,
        isLoading: false,
      }));
      tg?.hapticFeedback?.impactOccurred('light');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Ошибка загрузки проекта';
      setState(s => ({ ...s, isLoading: false, error: message }));
    }
  }, [tg]);

  // Create new draft
  const handleCreateDraft = useCallback(async () => {
    try {
      setState(s => ({ ...s, isLoading: true, error: null }));
      const project = await api.createDraft();
      
      // Refresh project list
      const projects = await api.getMyProjects();
      
      setState(s => ({
        ...s,
        screen: 'project-details',
        selectedProject: project,
        projects,
        isLoading: false,
      }));
      
      tg?.hapticFeedback?.notificationOccurred('success');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Ошибка создания проекта';
      setState(s => ({ ...s, isLoading: false, error: message }));
      tg?.hapticFeedback?.notificationOccurred('error');
    }
  }, [tg]);

  // Go back to dashboard
  const handleBack = useCallback(() => {
    setState(s => ({ ...s, screen: 'dashboard', selectedProject: null }));
  }, []);

  const inDemoMode = isDemoMode();

  // Loading screen
  if (state.screen === 'loading' && state.isLoading) {
    return (
      <div className="loading">
        <div className="spinner" />
        <div>Загрузка...</div>
      </div>
    );
  }

  // Config error screen (API not configured) - skip in demo mode
  if (!isApiConfigured() && !inDemoMode) {
    return (
      <div className="error">
        <div className="error-title">Configuration Error</div>
        <div className="error-text">
          VITE_API_PUBLIC_URL is not set.
          <br />
          Configure it in Vercel environment variables.
        </div>
        <DiagnosticBanner error={null} />
      </div>
    );
  }

  // Error screen (only if no data) - skip in demo mode since it always works
  if (state.error && !state.user && !inDemoMode) {
    return (
      <div className="error">
        <div className="error-title">Ошибка</div>
        <div className="error-text">{state.error}</div>
        <DiagnosticBanner error={state.error} />
        <button className="btn btn-primary" onClick={init}>
          Попробовать снова
        </button>
      </div>
    );
  }

  // Project details screen
  if (state.screen === 'project-details' && state.selectedProject) {
    return (
      <>
        {inDemoMode && <DemoBanner />}
        <ProjectDetailsView
          project={state.selectedProject}
          isLoading={state.isLoading}
          onBack={handleBack}
        />
      </>
    );
  }

  // Dashboard (default)
  return (
    <>
      {inDemoMode && <DemoBanner />}
      <Dashboard
        projects={state.projects}
        isLoading={state.isLoading}
        error={state.error}
        onRefresh={handleRefresh}
        onOpenProject={handleOpenProject}
        onCreateDraft={handleCreateDraft}
      />
    </>
  );
}

export default App
