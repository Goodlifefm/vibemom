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
| `VITE_API_PUBLIC_URL` | No | API base URL (e.g., `https://api.yourdomain.com`). If not set, app runs in demo mode. |

### Demo Mode

When `VITE_API_PUBLIC_URL` is not set:
- App shows mock data
- "Create project" button shows alert
- No authentication required

### Production Mode

When `VITE_API_PUBLIC_URL` is set:
- App authenticates via Telegram WebApp initData
- Projects loaded from API (`GET /projects/my`)
- "Create project" calls `POST /projects/create_draft`

## Deployment (Vercel)

1. Import project from GitHub
2. Set root directory: `services/webapp`
3. Add environment variable:
   - `VITE_API_PUBLIC_URL` = `https://api.yourdomain.com`
4. Deploy

### Required API CORS

The API must allow CORS from your Vercel domain. On the API side, set:

```env
ALLOWED_ORIGINS=https://your-app.vercel.app,https://web.telegram.org,https://t.me
# or
WEBAPP_URL=https://your-app.vercel.app
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
