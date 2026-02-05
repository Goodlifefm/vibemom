import './index.css'

type ProjectStatus = 'draft' | 'pending' | 'approved';

interface Project {
  id: string;
  title: string;
  status: ProjectStatus;
  description: string;
}

const DEMO_PROJECTS: Project[] = [
  {
    id: '1',
    title: 'AI-помощник для стартапов',
    status: 'draft',
    description: 'MVP с базовым функционалом, нужно добавить интеграции',
  },
  {
    id: '2',
    title: 'Telegram-бот для учёта финансов',
    status: 'pending',
    description: 'Полностью готовый продукт, на модерации',
  },
  {
    id: '3',
    title: 'Генератор контента на GPT-4',
    status: 'approved',
    description: 'SaaS-платформа с 50+ пользователями',
  },
];

const STATUS_LABELS: Record<ProjectStatus, { label: string; className: string }> = {
  draft: { label: 'Черновик', className: 'badge-draft' },
  pending: { label: 'На модерации', className: 'badge-pending' },
  approved: { label: 'Одобрен', className: 'badge-approved' },
};

function ProjectCard({ project }: { project: Project }) {
  const statusInfo = STATUS_LABELS[project.status];
  
  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">{project.title}</h3>
        <span className={`badge ${statusInfo.className}`}>
          {statusInfo.label}
        </span>
      </div>
      <p className="card-body">{project.description}</p>
    </div>
  );
}

function App() {
  const handleCreateProject = () => {
    // TODO: будет реализовано с API
    alert('Создание проекта будет доступно после подключения API');
  };

  return (
    <div className="container">
      <header className="header">
        <h1 className="header-title">VibeMom Mini App</h1>
        <p className="header-subtitle">Demo mode — API не подключён</p>
      </header>

      <main className="main">
        <section className="projects">
          <h2 className="section-title">Мои проекты</h2>
          {DEMO_PROJECTS.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </section>

        <button className="btn btn-primary btn-full" onClick={handleCreateProject}>
          ➕ Создать проект
        </button>
      </main>
    </div>
  );
}

export default App
