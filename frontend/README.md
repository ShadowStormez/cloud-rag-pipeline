# Ludex Frontend

The Ludex frontend is a responsive React application that provides a chat interface for an AI-powered Unity and Godot documentation assistant.

It is built with **React 19 and Vite 8** and deployed on Cloudflare Pages.

## Live Application

https://ludex-8xs.pages.dev/

## Features

- Unity, Godot, and automatic engine selection.
- AI-generated answers with clickable official documentation citations.
- Google sign-in through Supabase Authentication.
- Persistent chat history for authenticated users.
- Temporary in-memory conversations for guests.
- Responsive interface with mobile navigation.
- Markdown-rendered answers and code blocks.
- Loading indicators, error handling, and request cancellation.

## Technology Stack

- React 19
- Vite 8
- JavaScript
- Supabase JavaScript SDK
- React Markdown and Remark GFM
- Lucide React
- Oxlint

## Local Development

From the repository root:

```bash
cd frontend
npm ci
```

Create a `.env.local` file inside `frontend/`:

```dotenv
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_key
VITE_API_BASE_URL=http://localhost:8000
```

Start the development server:

```bash
npm run dev
```

The frontend normally runs at `http://localhost:5173`.

The FastAPI backend must be running separately for question answering to work.

## Available Commands

| Command | Purpose |
|---|---|
| `npm run dev` | Start the development server |
| `npm run build` | Create a production build |
| `npm run preview` | Preview the production build |
| `npm run lint` | Run Oxlint |

## Authentication and Conversation Storage

Ludex uses Supabase Auth for Google OAuth.

Authenticated users can create conversations, save messages with source citations, and retrieve previous conversations from Supabase.

Guest conversations are stored temporarily in JavaScript memory and are not preserved after reloading the application.

The Supabase project requires appropriate authentication settings, database tables, and Row Level Security policies to protect user data.

## Backend Integration

The frontend communicates with the FastAPI backend through `frontend/src/api/rag.js`.

Questions are submitted to the `POST /ask` endpoint with the selected engine:

- `auto`
- `unity`
- `godot`

The API returns an answer and an array of supporting documentation sources.

## Deployment

The frontend is hosted on Cloudflare Pages. Production builds use the environment variables configured for the Cloudflare Pages project.

The application communicates with the Azure-hosted backend:

https://cloud-rag-api.icypebble-38736748.swedencentral.azurecontainerapps.io

## Related Documentation

See the repository's root `README.md` for the complete Ludex architecture, backend setup, documentation pipeline, testing, and cloud deployment information.