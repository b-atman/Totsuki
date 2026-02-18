# Totsuki - Project Context Export

## Project Overview

**Totsuki** is a grocery optimizer application that helps users manage their pantry inventory and generate personalized meal plans. The name appears to be inspired by the culinary school from the anime "Food Wars" (Shokugeki no Soma).

**Current Status:** Milestone 3 Complete (Receipt Ingestion & Spending Analytics)

---

## Core Goal / Problem Being Solved

Totsuki aims to reduce food waste and simplify meal planning by:

1. **Pantry Management** - Track what ingredients you have, their quantities, and expiration dates
2. **Intelligent Meal Planning** - Generate 7-day meal plans based on user preferences (diet, budget, time constraints)
3. **Shopping List Generation** - Automatically aggregate ingredients needed for meal plans
4. **Receipt Ingestion** - Upload CSV receipts to auto-update pantry and track prices ✅ DONE
5. **Spending Analytics** - View spending breakdown by category, store, and time ✅ DONE
6. **Future Goals** - User authentication, user-created recipes

---

## Tech Stack

### Backend
| Component | Technology | Version |
|-----------|------------|---------|
| Framework | FastAPI | ≥0.109.0 |
| Server | Uvicorn | ≥0.27.0 |
| ORM | SQLAlchemy (async) | ≥2.0.25 |
| Database | SQLite (dev) / PostgreSQL (prod-ready) | aiosqlite ≥0.19.0 |
| Migrations | Alembic | ≥1.13.0 |
| Validation | Pydantic + Pydantic Settings | ≥2.6.0 / ≥2.1.0 |
| File Upload | python-multipart | ≥0.0.6 |
| Utilities | python-dateutil, python-dotenv | - |

### Frontend
| Component | Technology | Version |
|-----------|------------|---------|
| Framework | React | ^18.3.1 |
| Router | React Router DOM | ^6.22.0 |
| Build Tool | Vite | ^5.1.0 |
| Language | TypeScript | ^5.3.3 |
| Styling | Tailwind CSS | ^3.4.1 |
| Icons | Lucide React | ^0.344.0 |

---

## Architecture Decisions

### Backend - Layered Architecture
```
Routes (API) → Services (Business Logic) → CRUD (Data Access) → Models (ORM)
```

**Why this was chosen:**
- **Separation of concerns** - Each layer has a single responsibility
- **Testability** - Easy to mock dependencies for unit testing
- **Maintainability** - Changes in one layer don't cascade to others
- **FastAPI's Dependency Injection** - `Depends()` makes this pattern natural

### Frontend - Component-Based with API Client Layer
```
Pages (Logic) → Components (Presentation) → API Client → Backend
```

**Why this was chosen:**
- **Type safety** - TypeScript types mirror Pydantic schemas exactly
- **Reusability** - Modals, tables, badges are reusable components
- **Single source of truth** - API client centralizes all HTTP logic

### Database Design Decisions
- **JSON fields for ingredients/tags** - Flexibility over normalization (recipes have varying ingredient structures)
- **`canonical_name` field on PantryItem** - Enables receipt matching (e.g., "2% MILK" → "milk")
- **`ReceiptItem` for price history** - Stores every receipt line item permanently for analytics
- **`receipt_batch_id`** - Groups items from same upload for viewing/deleting entire receipts
- **Default `user_id = 1`** - Multi-user schema ready, but auth deferred to later milestone
- **Indexes on analytics queries** - Optimized for spend-by-category, spend-by-store, spend-by-month

---

## Folder / File Structure

```
Totsuki/
├── backend/
│   ├── alembic/                 # Database migrations (ACTIVE)
│   │   ├── versions/            # Migration scripts
│   │   │   ├── 133321c4ec16_initial_schema.py
│   │   │   └── aea5fadf0609_add_receipt_items_table.py
│   │   └── env.py               # Async SQLAlchemy config
│   ├── alembic.ini              # Alembic configuration
│   ├── app/
│   │   ├── api/routes/          # FastAPI endpoint definitions
│   │   │   ├── inventory.py     # Pantry CRUD endpoints
│   │   │   ├── planner.py       # Meal plan generation endpoints
│   │   │   └── receipt.py       # Receipt ingestion & analytics endpoints
│   │   ├── core/
│   │   │   ├── config.py        # Pydantic Settings (env vars)
│   │   │   └── database.py      # SQLAlchemy async engine setup
│   │   ├── crud/                # Data access layer
│   │   │   ├── pantry.py
│   │   │   ├── recipe.py
│   │   │   └── receipt.py       # Receipt CRUD + analytics queries
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── pantry.py
│   │   │   ├── recipe.py
│   │   │   └── receipt.py       # ReceiptItem model
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   │   ├── pantry.py
│   │   │   ├── recipe.py
│   │   │   ├── planner.py
│   │   │   └── receipt.py       # CSV upload, preview, analytics schemas
│   │   ├── services/            # Business logic
│   │   │   ├── planner.py       # Meal plan generation algorithm
│   │   │   └── receipt.py       # CSV parsing, category inference, pantry matching
│   │   ├── utils/               # Utility functions
│   │   │   └── normalize.py     # Receipt name normalization (brand removal, abbreviation expansion)
│   │   ├── data/
│   │   │   └── recipes_seed.json
│   │   └── main.py              # FastAPI app entry point
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/                 # API client functions
│   │   │   ├── pantry.ts
│   │   │   ├── planner.ts
│   │   │   └── receipt.ts       # Receipt upload & analytics API
│   │   ├── components/          # Reusable UI components
│   │   │   ├── AddItemModal.tsx
│   │   │   ├── EditItemModal.tsx
│   │   │   ├── ExpiryBadge.tsx
│   │   │   ├── PantryTable.tsx
│   │   │   ├── ReceiptUploadForm.tsx   # Drag & drop CSV upload
│   │   │   ├── ReceiptPreviewTable.tsx # Parsed items review
│   │   │   └── SpendSummary.tsx        # Analytics dashboard with charts
│   │   ├── pages/               # Route-level pages
│   │   │   ├── PantryPage.tsx
│   │   │   ├── PlanPage.tsx
│   │   │   └── ReceiptPage.tsx  # Upload, analytics, history tabs
│   │   ├── types/               # TypeScript type definitions
│   │   │   ├── pantry.ts
│   │   │   ├── planner.ts
│   │   │   └── receipt.ts       # Receipt & analytics types
│   │   ├── App.tsx              # Main app + routing
│   │   ├── main.tsx             # React entry point
│   │   └── index.css            # Tailwind imports
│   ├── vite.config.ts           # Vite config with API proxy
│   ├── tailwind.config.js
│   └── package.json
│
└── .gitignore
```

---

## Completed Milestones

| Commit | Milestone | Description |
|--------|-----------|-------------|
| `5085f66` | Initial Setup | Project scaffolding, .gitignore, basic structure |
| `93a639b` | Milestone 1A | Database schema + Pantry CRUD API complete |
| `740aa7a` | Milestone 1A Frontend | Pantry Dashboard UI (table, modals, expiry badges) |
| `b0f6183` | Milestone 2 | 7-day meal planner with filtering, scoring, shopping list |
| `7007e1f` | Pre-Milestone 3 | Alembic migrations + name normalization utility |
| `941aa40` | Milestone 3 | Receipt ingestion with CSV upload and spending analytics |

---

## API Endpoints

### Pantry (`/api/v1/inventory`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/inventory` | List all pantry items |
| POST | `/inventory/item` | Add new item |
| PUT | `/inventory/item/{id}` | Update item |
| DELETE | `/inventory/item/{id}` | Delete item |
| POST | `/inventory/consume` | Consume quantity |

### Meal Planner (`/api/v1/plan`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/plan/generate` | Generate 7-day meal plan |
| GET | `/plan/cuisines` | List available cuisines |
| GET | `/plan/diets` | List available diets |

### Receipts (`/api/v1`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ingest-receipt` | Upload CSV, get preview |
| POST | `/ingest-receipt/confirm` | Confirm receipt, update pantry |
| GET | `/analytics/spend-breakdown` | Get spending analytics |
| GET | `/receipts` | List recent receipts |
| GET | `/receipts/{batch_id}` | Get receipt details |
| DELETE | `/receipts/{batch_id}` | Delete receipt batch |

---

## Known Bugs / Technical Debt

| Issue | Severity | Notes |
|-------|----------|-------|
| **No authentication** | Medium | `user_id = 1` hardcoded; schema supports multi-user |
| **SQLite in dev** | Low | PostgreSQL config exists, needs migration |
| **Recipe data read-only** | Low | Recipes are seeded, no CRUD endpoints for user recipes |
| **No `.env.example`** | Low | Config uses defaults; new devs need to know env vars |
| **No README** | Low | Documentation only in code comments |

---

## Environment Variables / Config Requirements

Create a `.env` file in `backend/` with these variables:

```env
# App settings
APP_NAME=Totsuki              # Default: "Totsuki"
APP_VERSION=0.1.0             # Default: "0.1.0"
DEBUG=true                    # Default: true

# Database
DATABASE_URL=sqlite+aiosqlite:///./totsuki.db
# For PostgreSQL: postgresql+asyncpg://user:pass@localhost/totsuki
DB_POOL_SIZE=5                # PostgreSQL only
DB_MAX_OVERFLOW=10            # PostgreSQL only

# API
API_V1_PREFIX=/api/v1         # Default: "/api/v1"

# CORS (comma-separated or JSON array)
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

**Frontend:** No `.env` needed - Vite proxies `/api` to backend at `http://127.0.0.1:8000`

---

## Design Patterns Used

### Backend
| Pattern | Where Used | Purpose |
|---------|------------|---------|
| Repository | `crud/*.py` | Abstract data access from routes |
| Dependency Injection | FastAPI `Depends()` | Inject DB sessions into routes |
| Singleton | `config.settings` | Single source of configuration |
| Factory | `AsyncSessionLocal` | Create database sessions |
| Strategy | `services/planner.py` | Filtering/scoring strategies for meal planning |
| Pipeline | `services/receipt.py` | CSV parse → normalize → match → categorize |

### Frontend
| Pattern | Where Used | Purpose |
|---------|------------|---------|
| Component Composition | `components/` | Reusable UI pieces |
| API Client | `api/*.ts` | Centralized HTTP logic |
| Container/Presentational | Pages vs Components | Separate logic from presentation |
| Type Mirroring | `types/*.ts` | TypeScript types match Pydantic schemas |
| State Machine | `ReceiptPage.tsx` | Upload → Preview → Confirm → Success flow |

---

## Constraints / Assumptions

1. **Single-user MVP** - Auth deferred; `user_id = 1` is default
2. **Recipe data is static** - Seeded from JSON; user recipe creation is future work
3. **SQLite for development** - PostgreSQL for production (config ready)
4. **Vite dev proxy** - Frontend assumes backend runs on port 8000
5. **7-day meal plans** - Hardcoded for simplicity; could be parameterized
6. **No external API calls** - All data is local (no Spoonacular, Edamam, etc.)
7. **CSV receipts only** - OCR/image upload is future work

---

## Important Reasoning Decisions Made

1. **JSON fields over normalized tables for ingredients**
   - Recipes have highly variable ingredient structures
   - Avoids complex join queries for read-heavy operations
   - Trade-off: Harder to query "all recipes with chicken"

2. **`canonical_name` on PantryItem**
   - Prepared for receipt matching (e.g., "2% MILK" → "milk")
   - Enables fuzzy matching without modifying display name

3. **Async everything**
   - SQLAlchemy 2.0 async + aiosqlite + FastAPI async
   - Future-proofs for PostgreSQL asyncpg
   - Better performance under concurrent requests

4. **Pydantic Settings for config**
   - Type-safe configuration with validation
   - Automatic `.env` loading
   - Sensible defaults for local development

5. **Meal plan algorithm: Filter → Score → Promote Variety**
   - Hard constraints (time, diet) filter first
   - Soft preferences (cuisine, protein) score next
   - Variety promotion prevents repetitive plans

6. **ReceiptItem as price history**
   - Every receipt line item stored permanently
   - Enables spend analytics without separate price history table
   - `receipt_batch_id` groups items for viewing/deleting uploads

7. **Name normalization pipeline**
   - Strip brand names (whole word match to avoid "ee" in "cheese")
   - Expand abbreviations (CHKN → chicken)
   - Remove size descriptors (1GAL, 2LB)
   - Infer category from keywords

8. **CSS bar charts over external library**
   - No chart library dependency for MVP
   - Simple percentage-based bars work well
   - Can upgrade to Recharts/Chart.js later if needed

---

## How to Run

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
# API docs at http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# App at http://localhost:5173
```

### Database Migrations
```bash
cd backend
.\venv\Scripts\alembic current    # Check current revision
.\venv\Scripts\alembic upgrade head    # Apply all migrations
.\venv\Scripts\alembic revision --autogenerate -m "description"    # Create new migration
```

---

## Next Steps (Suggested)

1. **Milestone 4:** User authentication (JWT or session-based)
2. **Milestone 5:** User-created recipes with CRUD
3. **Milestone 6:** Receipt OCR (image upload with Tesseract or cloud API)
4. **Tech debt:** Add README, `.env.example`, PostgreSQL migration

---

## User's Working Rules

These rules were established for AI pair-programming sessions:

### Core Workflow Rules
1. **Work on ONE milestone at a time** - Complete each milestone fully before moving to the next
2. **Work on ONE file at a time within a milestone** - Don't generate multiple files in one response
3. **Explain WHY each part is needed** - Educational approach, not just code dumps
4. **Provide content and test instructions for each file** - Path → Content → Test → Confirm
5. **Stop for confirmation before proceeding** - Wait for user approval before next file
6. **Commit after logical chunks** - Git commit after completing backend, frontend, or significant features
7. **Push to GitHub after commits** - Keep remote repository updated

### Additional Conventions Observed
- **Verify imports work** after creating each file
- **Test each component** before moving to the next
- **Run full verification** before committing (backend check, frontend check, TypeScript compilation)
- **Clean up test files** after verification
- **Use descriptive commit messages** following pattern: `Milestone X: Description`
- **Start servers and test** the full application flow before marking milestone complete
- **Keep milestone A (backend) and B (frontend) in the same chat** for context continuity

### File Creation Order (Backend)
1. Model (SQLAlchemy ORM)
2. Schema (Pydantic validation)
3. Seed Data (if applicable)
4. CRUD (database operations)
5. Service (business logic)
6. Routes (API endpoints)
7. Update main.py to register routes

### File Creation Order (Frontend)
1. Types (TypeScript interfaces matching backend schemas)
2. API client (fetch wrapper)
3. Components (reusable UI pieces)
4. Pages (route-level components)
5. Update App.tsx for routing

---

*Generated: February 18, 2026*
*Updated: February 18, 2026 - Milestone 3 Complete (Receipt Ingestion & Spending Analytics)*
