# VibeMom Mini App (Frontend)

Telegram Mini App frontend for VibeMom marketplace. Built with React + Vite + TypeScript.

## Quick Start

```bash
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in browser.

## Environment Variables

Create `.env.local` for local development or set in Vercel for production:

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_PUBLIC_URL` | No | Recommended API base URL for Vercel/client build (e.g., `https://api.yourdomain.com`). |
| `API_PUBLIC_URL` | No | Fallback API base URL for local/monorepo builds when `VITE_API_PUBLIC_URL` is empty. |

Priority at runtime:
1. `VITE_API_PUBLIC_URL`
2. `API_PUBLIC_URL`

If both are empty, app runs in demo mode.

### Demo Mode

When both `VITE_API_PUBLIC_URL` and `API_PUBLIC_URL` are not set:
- App shows mock data
- "Create project" button shows alert
- No authentication required

### Production Mode

When API URL is configured (`VITE_API_PUBLIC_URL` or `API_PUBLIC_URL`):
- App authenticates via Telegram WebApp initData
- Projects loaded from API (`GET /projects/my`)
- "Create project" calls `POST /projects/create_draft`

## Deployment (Vercel)

1. Import project from GitHub
2. Set root directory: `services/webapp`
3. Add environment variable:
   - `VITE_API_PUBLIC_URL` = `https://api.yourdomain.com`
4. Deploy (or Redeploy after env var changes)

> Important: after changing environment variables in Vercel, trigger a new deployment. Existing deployments do not pick up new env values automatically.

### Required API CORS

The API must allow CORS from your Vercel domain. On the API side, set:

```env
ALLOWED_ORIGINS=https://your-app.vercel.app,https://web.telegram.org,https://t.me
# or
WEBAPP_URL=https://your-app.vercel.app
```

## Verify Production Build (No Vercel UI)

After a deployment, you can confirm which build is serving `app.vibemom.ru` via a static build stamp endpoint:

```bash
curl -s https://app.vibemom.ru/build.json
```

Expected shape:

```json
{ "git_sha": "<sha>", "build_time": "<iso>", "env": "<production|preview>" }
```

## Scripts

- `npm run dev` — Start dev server
- `npm run build` — Build for production
- `npm run preview` — Preview production build
- `npm run lint` — Lint code

## Architecture

```
src/
├── App.tsx         # Main app component
├── lib/
│   └── api.ts      # API client (fetch wrapper, auth, projects)
├── index.css       # Styles
├── main.tsx        # Entry point
└── vite-env.d.ts   # Vite types
```

## API Integration

The app uses JWT authentication:

1. On load, tries to get Telegram WebApp initData
2. Sends initData to `POST /auth/telegram`
3. Stores JWT token in localStorage
4. Uses token for authenticated API calls

If authentication fails, falls back to demo mode.
