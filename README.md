# Ludex — AI Assistant for Game Developers

**Ludex** is a full-stack, cloud-deployed Retrieval-Augmented Generation (RAG) application designed to help game developers find reliable technical information from official game-engine documentation.

Instead of relying exclusively on a language model's existing knowledge, Ludex searches indexed documentation from Unity and Godot, retrieves relevant passages, and uses them to generate contextual explanations and code examples with clickable source citations.

The project was developed as an individual software engineering and cloud application project at the **University of Eastern Finland (UEF)**.

## Live Demo

- **Web Application:** https://ludex-8xs.pages.dev/
- **Backend API:** https://cloud-rag-api.icypebble-38736748.swedencentral.azurecontainerapps.io
- **Interactive API Documentation:** https://cloud-rag-api.icypebble-38736748.swedencentral.azurecontainerapps.io/docs

## Key Features

- **Documentation-grounded AI:** Generates responses using retrieved official Unity and Godot documentation.
- **Multi-engine support:** Users can select Unity, Godot, or automatic engine selection.
- **Clickable source citations:** Answers include references to the documentation used.
- **Intelligent retrieval:** Combines semantic search, engine filtering, relevant API detection, and neighboring document context.
- **Google authentication:** Users can sign in using Google through Supabase Auth.
- **Persistent chat history:** Authenticated users can access previously saved conversations.
- **Guest mode:** Visitors can use the assistant without signing in, with temporary conversation history.
- **Modern responsive interface:** React-based chat application with engine selection and conversation management.
- **Automated documentation pipeline:** Discovers, downloads, processes, and incrementally indexes documentation.
- **Cloud deployment:** Dockerized FastAPI backend deployed on Azure Container Apps.
- **Continuous integration:** Automated Python tests and GitHub Actions workflows.

> **Current engine support:** Unity and Godot. Unreal Engine integration is not enabled while documentation-access permission remains unresolved.

## System Architecture

Ludex consists of three main components: a React frontend, a FastAPI RAG backend, and an automated documentation ingestion pipeline.

### 1. Frontend

The frontend is built with React and Vite and hosted on Cloudflare Pages. It provides the chat interface, engine selection, authentication, conversation history, and documentation citations.

Supabase handles Google authentication and persistent conversation storage for signed-in users. Guest conversations are temporarily stored in application memory.

### 2. RAG Backend

The backend is implemented using Python and FastAPI.

When a user submits a question:

1. The frontend sends the question and selected game engine to the FastAPI backend.
2. The backend searches the ChromaDB vector database using semantic similarity and engine-specific filters.
3. Relevant documentation

## Repository Structure

```text
cloud-rag-pipeline/
├── frontend/                    # React and Vite web application
│   ├── src/
│   │   ├── components/          # Chat interface components
│   │   ├── api/                 # Backend API integration
│   │   └── lib/                 # Authentication and chat storage
│   └── package.json
├── tests/                       # Automated Python tests
├── data/                        # Documentation samples and local data
├── .github/workflows/           # CI/CD and documentation automation
├── main.py                      # RAG retrieval and question answering
├── api.py                       # FastAPI application and health endpoint
├── ingestion_engine.py          # Incremental documentation ingestion
├── ingest_ludex_docs.py         # Unity and Godot ingestion
├── documentation_discovery.py   # Official documentation discovery
├── download_discovered_docs.py  # Documentation downloader
├── documentation_state.py       # Persistent crawler state in Azure
├── normalize_chroma_sources.py  # Legacy Chroma metadata migration
├── source_citations.py          # Source citation processing
├── validate_chroma.py           # Database validation
├── snapshot_chroma.py           # Chroma snapshot creation
├── restore_chroma.py            # Azure snapshot restoration
├── Dockerfile                   # Backend container configuration
└── requirements.txt             # Python dependencies
```

Generated documentation, local Chroma databases, and temporary snapshot archives are excluded from Git.

## Local Development

### Prerequisites

- Python 3.12
- Node.js and npm
- Git
- A Groq API key
- A Supabase project configured for authentication and conversation storage
- A populated Chroma database containing Unity and Godot documentation

Azure access is also required if restoring a Chroma database directly from Azure Blob Storage.

### Backend Setup

**1. Clone the repository**

```bash
git clone https://github.com/ShadowStormez/cloud-rag-pipeline.git
cd cloud-rag-pipeline
```

**2. Create and activate a Python virtual environment**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies**

```bash
python -m pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
```

**4. Configure environment variables**

Create a `.env` file in the project root:

```dotenv
GROQ_API_KEY=your_groq_api_key
CHROMA_DB_DIR=./chroma_unity_test
CHROMA_BLOB_NAME=chroma-ludex-expanded-v2.tar.gz
```

Do not commit `.env` or private credentials to Git.

**5. Prepare the Chroma database**

You can either ingest downloaded documentation locally or restore an existing snapshot from Azure.

For Azure restoration, authenticate using an Azure identity with permission to read the configured Blob Storage container, then run:

```bash
python restore_chroma.py
```

**6. Start the backend**

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The backend provides:

- `GET /health` — health check
- `POST /ask` — RAG question answering
- `GET /docs` — interactive Swagger API documentation

### Frontend Setup

**1. Open the frontend directory**

```bash
cd frontend
```

**2. Install dependencies**

```bash
npm ci
```

**3. Configure frontend environment variables**

Create `frontend/.env.local`:

```dotenv
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_key
VITE_API_BASE_URL=http://localhost:8000
```

Supabase Google OAuth and the required conversation and message tables must be configured separately. Appropriate Row Level Security policies should restrict access to each user's own data.

**4. Start the frontend**

```bash
npm run dev
```

Open the local address displayed by Vite, typically:

http://localhost:5173

The frontend communicates with the FastAPI backend running on port 8000.

## API Documentation

Ludex exposes a REST API through FastAPI.

### Health Check

**Endpoint:** `GET /health`

Returns the backend's health status.

Example response:

```json
{
  "status": "healthy",
  "service": "game-mechanics-rag-api"
}
```

### Ask a Question

**Endpoint:** `POST /ask`

Accepts a technical question and a selected game engine.

Example request:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I detect collisions using OnCollisionEnter2D?",
    "engine": "unity"
  }'
```

Supported engine values are `auto`, `unity`, and `godot`.

The response contains an `answer` string and a `sources` array with documentation metadata and supporting excerpts.

If the retrieved documentation cannot adequately support an answer, Ludex may return an insufficient-evidence response without citations.

Interactive API documentation is available at `/docs`.

## Testing and Quality Assurance

Ludex uses automated testing to verify the backend, documentation processing, retrieval functionality, and ingestion pipeline.

The repository contains **15 Python test files**, covering:

- FastAPI request validation and response behavior.
- Documentation fetching, parsing, and hashing.
- Documentation discovery and download handling.
- Incremental ingestion and ChromaDB integration.
- Engine-specific retrieval.
- Source citation processing.
- Crawler progress and documentation selection.

### Run Backend Tests

From the repository root:

```bash
python -m pytest tests/ -q
```

During development, **95 tests passed locally**, and the corresponding GitHub Actions CI checks completed successfully.

### Frontend Validation

From the `frontend` directory:

```bash
npm run lint
npm run build
```

These commands perform frontend linting and production build checks.

### GitHub Actions Validation

GitHub Actions workflow syntax can be checked locally using `actionlint`:

```bash
actionlint .github/workflows/*.yml
```

The project workflows have passed static validation.

Passing automated tests and static validation does not guarantee that every generated answer or code example is correct. Ludex relies on retrieved documentation and provides source citations so users can verify technical details.


## Cloud Deployment

Ludex is deployed using Docker, Azure Container Apps, Azure Blob Storage, and Cloudflare Pages.

### Backend Deployment

The FastAPI backend runs in Azure Container Apps using a Docker image published to GitHub Container Registry (GHCR).

The Dockerfile uses Python 3.12 and CPU-only PyTorch to reduce image size and avoid unnecessary GPU dependencies.

When the container starts:

1. The application checks whether a local Chroma database already exists.
2. If necessary, it downloads the configured database snapshot from Azure Blob Storage.
3. The snapshot is validated and extracted.
4. Uvicorn starts the FastAPI server on port 8000.

The production configuration currently uses:

| Resource | Configuration |
|---|---|
| Azure region | Sweden Central |
| CPU | 1 vCPU |
| Memory | 2 GiB |
| Minimum replicas | 1 |
| Maximum replicas | 1 |
| Container port | 8000 |
| Database snapshot | `chroma-ludex-expanded-v2.tar.gz` |

The minimum replica count is set to one to avoid scaling to zero during demonstrations.

### Frontend Deployment

The React frontend is hosted on Cloudflare Pages.

The production frontend communicates with the Azure-hosted FastAPI backend and uses Supabase for Google authentication and persistent conversation storage.

### Current Documentation Database

The verified production Chroma snapshot contains:

| Engine | Indexed chunks |
|---|---:|
| Unity | 55,239 |
| Godot | 27,031 |
| **Total** | **82,270** |

These figures describe the verified production snapshot, not the latest local documentation download progress.

## Documentation Automation

Ludex includes an automated documentation pipeline designed to maintain an up-to-date knowledge base for supported game engines.

The pipeline performs the following operations:

1. Discovers official documentation URLs through sitemaps.
2. Downloads documentation while respecting configured crawler restrictions.
3. Stores downloaded text and source URL manifests.
4. Tracks download progress and failed URLs.
5. Detects new or modified documentation using content hashes.
6. Restores an existing Chroma database from Azure Blob Storage.
7. Normalizes legacy source paths to maintain stable document identities.
8. Incrementally generates embeddings for new or changed documentation.
9. Validates and packages the resulting Chroma database.
10. Uses backup and conditional upload mechanisms for deployment.
11. Verifies the deployed API and preserves crawler state in Azure.

### GitHub Actions Workflows

| Workflow | Purpose |
|---|---|
| `ci.yml` | Runs automated Python checks and tests |
| `docker-publish.yml` | Publishes Docker images and supports manual Azure deployment |
| `update-docs.yml` | Downloads, ingests, validates, and deploys documentation updates |

The Docker workflow publishes images automatically when relevant changes are pushed to `main`. Deployment to Azure requires manual execution.

The documentation-update workflow is also currently **manual-only**. Its YAML and shell configuration have passed static validation, but the updated workflow has not yet been verified through a complete production deployment run.

Automatic scheduling can be enabled after successful end-to-end testing.

## Known Limitations

- Production RAG functionality currently supports Unity and Godot, not Unreal Engine.
- Unreal Engine documentation ingestion is deferred pending permission.
- Documentation coverage depends on the availability and successful retrieval of official pages.
- Some documentation URLs may fail to download or require retries.
- Generated answers and code examples should be verified against the linked official documentation.
- Guest conversations are temporary and are not preserved across page reloads.
- Authenticated chat persistence requires a correctly configured Supabase project.
- The documentation-update workflow still requires end-to-end production verification before scheduled updates are enabled.
- Running cloud infrastructure and external AI services may incur usage costs.

## Future Improvements

Potential improvements include:

- Completing the remaining Unity documentation downloads and indexing.
- Improving retry and recovery mechanisms for unavailable documentation pages.
- Testing the full documentation-update workflow in GitHub Actions.
- Introducing automated documentation refresh schedules after deployment validation.
- Expanding documentation coverage where permitted.
- Improving retrieval quality through additional evaluation questions and regression tests.
- Adding more monitoring and performance metrics.

## Project Status

Ludex currently provides:

- A deployed React frontend.
- A functioning Azure-hosted FastAPI backend.
- Retrieval-augmented answers for Unity and Godot.
- Clickable official documentation citations.
- Google authentication and persistent chat history for signed-in users.
- A Chroma knowledge base with 82,270 verified indexed chunks.
- Automated Python tests and CI.
- Docker image publishing and controlled Azure deployment.
- A documentation discovery and incremental ingestion pipeline.

The application has been tested through live Unity and Godot questions, with both engines returning successful HTTP responses and relevant source citations.

## License and Attribution

No repository-wide software license has currently been declared.

Unity and Godot documentation belong to their respective rights holders. Ludex references their official documentation and does not claim ownership of third-party content.

---

**Developed as an individual software engineering and cloud application project at the University of Eastern Finland (UEF).**