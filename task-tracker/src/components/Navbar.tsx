import { Link } from 'react-router-dom';
import { LogOut, CheckSquare } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import clsx from 'clsx';

export function Navbar() {
  const { user, signOut } = useAuth();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 h-16 border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-xl">
      <div className="mx-auto flex h-full max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link
          to="/"
          className="flex items-center gap-2 font-display text-xl font-semibold tracking-tight text-white transition hover:text-brand-400"
        >
          <CheckSquare className="h-6 w-6" />
          TaskTracker
        </Link>

        <div className="flex items-center gap-3 sm:gap-4">
          <span className="max-w-[160px] truncate text-sm text-slate-400 sm:max-w-[240px]">
            {user?.email}
          </span>
          <button
            onClick={() => signOut()}
            className={clsx(
              'flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium',
              'bg-slate-700/50 text-slate-300 transition',
              'hover:bg-red-500/20 hover:text-red-400',
              'focus:outline-none focus:ring-2 focus:ring-red-500/50'
            )}
          >
            <LogOut className="h-4 w-4" />
            <span className="hidden sm:inline">Log out</span>
          </button>
        </div>
      </div>
    </nav>
  );
}
