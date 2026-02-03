# TaskTracker

A full-stack task tracker app built with React, TypeScript, Tailwind CSS, and Supabase.

## Features

- **Authentication**: Sign up, log in, log out (email/password)
- **CRUD tasks**: Create, view, edit, delete tasks
- **Task fields**: Title, description, deadline, priority, status
- **Filters & sort**: By status, priority, deadline, created date
- **Mark complete**: Quick toggle to mark tasks as Done
- **Overdue indicator**: Tasks past deadline highlighted in red
- **Empty state**: Friendly UI when no tasks exist
- **Responsive design**: Works on mobile and desktop

## Setup

### 1. Create a Supabase project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Wait for the project to finish provisioning

### 2. Run the database schema

1. In Supabase Dashboard, go to **SQL Editor**
2. Create a new query
3. Copy the contents of `supabase/schema.sql` and run it

This creates the `tasks` table with RLS policies so users can only access their own tasks.

### 3. Configure environment variables

1. Copy `.env.example` to `.env`
2. Fill in your Supabase credentials from **Settings → API**:
   - `VITE_SUPABASE_URL` = Project URL
   - `VITE_SUPABASE_ANON_KEY` = anon public key

### 4. Install and run

```bash
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

## Scripts

- `npm run dev` – Start dev server
- `npm run build` – Production build
- `npm run preview` – Preview production build
- `npm run lint` – Run ESLint

## Tech stack

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, React Router
- **Backend**: Supabase (Auth + PostgreSQL)
- **Icons**: Lucide React
