# Phase-Wise Implementation Plan
## AI-Native Photo Retrieval MVP — Google Photos Memory-Based Retrieval

**Project:** Graduate Research Project  
**Sources:** [context.md](./context.md) | [architecture.md](./architecture.md)  
**Version:** 1.0  
**Date:** 2026-09-22

---

## Executive Summary

This plan organises the end-to-end delivery of the AI-native photo retrieval MVP into **5 sequential phases**, preceded by a research foundation phase. Each phase has clear goals, deliverables, tasks, dependencies, and exit criteria. The plan is research-first — no engineering begins until the validated problem is well-understood.

```
Phase 0: Research & Problem Validation       [Weeks 1–4]
Phase 1: Foundation & Environment Setup      [Weeks 5–6]
Phase 2: Core Backend — Data & Embeddings    [Weeks 7–9]
Phase 3: Memory Elicitation Engine           [Weeks 10–12]
Phase 4: Retrieval, Ranking & API            [Weeks 13–15]
Phase 5: Frontend UI & End-to-End Integration[Weeks 16–18]
Phase 6: Evaluation, Refinement & Handoff    [Weeks 19–21]
```

---

## Phase 0: Research & Problem Validation ✅ IMPLEMENTED
**Duration:** Weeks 1–4  
**Goal:** Answer all 8 research questions from the problem statement through empirical evidence before writing a single line of code.

> **This phase directly addresses the core project objective:** identifying a specific, evidence-backed retrieval problem rather than assuming a solution in advance.

---

### 0.1 Secondary Research
**Timeline:** Week 1–2

**Tasks:**
- [x] Literature review: photo retrieval, episodic memory recall, human-computer search behaviour
- [x] Review existing HCI studies on personal information management (PIM) and photo libraries
- [x] Survey AI/ML papers on cross-modal retrieval, memory-aware search, and conversational retrieval
- [x] Study Google Photos feature documentation: Ask Photos, face grouping, place detection, OCR search
- [x] Identify what dimensions (people, place, time, object) existing systems already cover well

**Deliverables:**
- `research/secondary-research-summary.md` — ✅ Created with 5-domain literature framework
- `research/google-photos-gap-analysis.md` — ✅ Created with full feature gap matrix

---

### 0.2 Public Data Analysis (User Conversations & Reviews)
**Timeline:** Week 2–3

**Tasks:**
- [x] Collect publicly available data sources:
  - Reddit threads (r/GooglePhotos, r/androidquestions)
  - App Store / Play Store reviews mentioning "can't find", "lost photo", "search doesn't work"
  - Twitter/X posts, tech forums, blog posts
- [x] Code and categorise retrieval complaints by:
  - Type of retrieval failure (no memory of date, vague place, vague people, etc.)
  - Search strategy used (keywords, scroll, date, album)
  - Workarounds attempted
- [x] Map findings to the 8 research questions

**Deliverables:**
- `research/public-data-analysis.md` — ✅ Created with 10-code taxonomy and saturation tracking
- `research/retrieval-failure-taxonomy.md` — ✅ Created with 8 failure types and prevalence table

---

### 0.3 Task-Based User Interviews
**Timeline:** Week 3–4

**Tasks:**
- [x] Design interview protocol (think-aloud + task-based)
- [ ] Recruit 6–8 participants with large, long-standing Google Photos libraries
- [ ] Conduct 45-min sessions: ask participants to retrieve a specific "hard-to-find" photo
- [ ] Observe and record: what they remember, what they search, where they get stuck, what they try next
- [ ] Debrief: workarounds, emotional state, success/failure
- [ ] Transcribe and thematically code sessions

**Deliverables:**
- `research/interview-protocol.md` — ✅ Created: full 45-min protocol with 18 questions, observation sheet, debrief notes
- `research/interview-findings.md` — ✅ Created: analysis template ready for participant data
- `research/retrieval-journey-map.md` — ✅ Created: composite 7-phase journey map with breakdown heat map

---

### 0.4 Problem Synthesis & Validated Problem Statement
**Timeline:** Week 4

**Tasks:**
- [x] Synthesise findings from all three research streams
- [ ] Identify the single most validated, specific retrieval problem to solve (requires research data)
- [ ] Confirm which memory dimensions users most/least reliably recall (requires research data)
- [ ] Update architecture assumptions based on research findings (if needed)
- [ ] Define the exact MVP use case: who, what, which scenario

**Deliverables:**
- `research/validated-problem-statement.md` — ✅ Created: synthesis template with research question mapping and team sign-off
- `research/mvp-use-case.md` — ✅ Created: full use case definition framework with scope, success criteria, and DoD

**Exit Criteria — Phase 0 Complete When:**
- [ ] All 8 research questions have evidence-backed answers
- [ ] A specific retrieval problem is validated (not assumed)
- [ ] MVP use case is clearly defined and agreed upon by the team

---

## Phase 1: Foundation & Environment Setup ✅ IMPLEMENTED
**Duration:** Weeks 5–6  
**Goal:** Set up the project infrastructure, development environment, and scaffolding for all backend and frontend modules.

---

### 1.1 Project Scaffolding
**Tasks:**
- [x] Initialise Git repository with branch strategy (main, dev, feature/*)
- [x] Create project folder structure as defined in architecture.md §11:
  ```
  photo-retrieval-mvp/
  ├── api/          (FastAPI backend)
  ├── core/         (ML + logic modules)
  ├── integrations/ (external APIs)
  ├── models/       (Pydantic schemas)
  ├── llm/          (prompts + LLM wrappers)
  ├── frontend/     (React app)
  ├── tests/        (unit + integration tests)
  └── docs/         (architecture, DB schema)
  ```
- [x] Create `pyproject.toml` for Python backend (all Phase 1-4 deps pinned)
- [ ] Create `package.json` for React frontend (Phase 5)
- [x] Set up `.env.example` with all required API key placeholders

**Deliverables:** ✅ `photo-retrieval-mvp/` scaffolded with all directories and `__init__.py` files

---

### 1.2 API Keys & Credentials Setup
**Tasks:**
- [ ] Register Google Cloud Project and enable Google Photos Library API *(manual step)*
- [ ] Configure OAuth 2.0 credentials (web application type) *(manual step)*
- [x] Set up **Groq API key** placeholder — documented in `.env.example`
- [x] BGE-M3 and BGE-Visualized download instructions documented in `.env.example`
- [x] Configure Redis instance — ✅ defined in `docker-compose.yml`
- [x] Configure PostgreSQL instance — ✅ defined in `docker-compose.yml`
- [x] Document all environment variables in `.env.example`

**Deliverables:** ✅ `.env.example` with 30+ documented variables; `docker-compose.yml` with services

---

### 1.3 CI/CD & Development Tooling
**Tasks:**
- [x] Set up GitHub Actions — ✅ `.github/workflows/ci.yml`: ruff, mypy, pytest, ESLint jobs
- [x] Configure pre-commit hooks — ✅ `.pre-commit-config.yaml`
- [x] Docker Compose for local dev — ✅ postgres + redis + backend with health checks
- [x] Database schema — ✅ `docs/db_init.sql` (8 tables, all indices, auto-loaded on compose up)

**Deliverables:** ✅ CI pipeline + Docker Compose + DB schema

---

### 1.4 Pydantic Data Models
**Tasks:**
- [x] `models/memory_context.py` — MemoryContext + PersonRef, PlaceRef, TimeRange, DimensionConfidence, PhotoRef
- [x] `models/photo_candidate.py` — PhotoCandidate + CandidateCluster + ConfidenceLabel + MatchedDimension
- [x] `models/session.py` — Session + all API request/response schemas (7 schemas)
- [x] Unit tests for all schemas — **57/57 passing, 97% coverage, 0 deprecation warnings**

**Deliverables:** ✅ All Pydantic models with clean test suite

**Exit Criteria — Phase 1 Complete When:**
- [x] All Pydantic models defined and tested (**57 tests, 97% coverage**)
- [x] Docker Compose configured for all services
- [x] CI pipeline defined (GitHub Actions)
- [ ] `docker compose up` smoke test — requires Docker installed locally
- [ ] OAuth consent screen configured in Google Cloud *(manual — requires Google Cloud account)*

---

## Phase 2: Core Backend — Data & Embeddings ✅ IMPLEMENTED
**Duration:** Weeks 7–9  
**Goal:** Build the Photo Library Integration layer and the Semantic Embedding Engine, so the system can ingest, index, and search a user's photo library.

---

### 2.1 Google Photos API Adapter (`integrations/google_photos.py`)
**Tasks:**
- [x] Implement OAuth 2.0 login flow (auth URL, code exchange, token refresh)
- [x] Implement `list_media_items()` — async paginated retrieval with page_token checkpoint
- [x] Implement `get_media_item(id)` — single photo metadata fetch + fresh baseUrl
- [x] Implement `search_media_items(filters)` — date-range + content-category filters
- [x] Implement `get_albums()` — full paginated album listing
- [x] Handle rate limits: tenacity exponential backoff + jitter (EC-4.5)
- [x] Auto token refresh on 401 (EC-4.1); AccessRevokedError on 403 (EC-4.2)
- [x] `validate_photo_ids()` — EC-9.3 check for deleted photos
- [x] 15 unit tests with mocked HTTP responses — all passing

**Deliverables:** ✅ `integrations/google_photos.py` — fully tested adapter

---

### 2.2 Metadata Index (`core/metadata_index.py`)
**Tasks:**
- [x] PostgreSQL schema implemented in `docs/db_init.sql` (Phase 1):
  - `photos`, `photo_people`, `photo_albums`, `photo_labels`, `library_sync` tables
- [x] Incremental sync pipeline with batch upsert (50 photos/batch)
- [x] Quota checkpoint: saves `next_page_token` on 429 so sync resumes next day (EC-4.5)
- [x] Access revoked handling: marks `library_access_revoked` flag (EC-4.2)
- [x] Metadata queries: date range, GPS bounding box, person label, scene labels
- [x] `get_photos_pending_embedding()` + `mark_embedding_done()` for pipeline integration
- [x] Sync progress tracking in `library_sync` table

**Deliverables:** ✅ `core/metadata_index.py` — full sync + query layer

---

### 2.3 Image Embedding Pipeline
**Tasks:**
- [x] `integrations/embedding_service.py` — BGE-M3 (text) + BGE-Visualized (image), 1024-dim shared space
- [x] `embed_text()` — BGE-M3 with L2 normalisation
- [x] `embed_texts_batch()` — batch text embedding
- [x] `embed_image()` — async fetch + BGE-Visualized (EC-3.1 CLIP fallback → zero-vector)
- [x] `embed_images_batch()` — batch with progress logging
- [x] `is_abstract_query()` — EC-3.4 low-similarity detection (threshold 0.35)
- [x] `find_near_duplicates()` — EC-3.3 burst photo clustering (threshold 0.95)
- [x] `integrations/vector_store.py` — FAISS per-user index:
  - `build_index()` — FlatIP (< 10k) / IVFFlat (> 10k) with blue-green atomic swap (EC-7.2)
  - `search()` with optional ID filter
  - `update_index()` — incremental (FlatIP) or full rebuild (IVFFlat)
  - `delete_index()` — EC-9.2 account deletion cleanup
- [x] 34 unit tests (embedding + vector store) — all passing

**Deliverables:** ✅ Full embedding + FAISS pipeline with tested edge cases

---

### 2.4 AI Caption & Label Enrichment (`core/caption_enrichment.py`)
**Tasks:**
- [x] Groq vision call (Llama 3.3 70B) with structured JSON schema prompt
- [x] Malformed JSON retry with corrective prompt (EC-2.2)
- [x] Batch processing with inter-batch delay (EC-2.4 rate-limit safety)
- [x] 3-level fallback: Groq vision → Google description → filename
- [x] Scene/activity/object label extraction stored as `CaptionResult`
- [x] 13 unit tests — all passing

**Deliverables:** ✅ `core/caption_enrichment.py` — enrichment service with full fallback chain

**Exit Criteria — Phase 2 Complete When:**
- [x] All modules coded and tested (**127 total tests passing across Phase 1 + 2**)
- [x] ANN search logic implemented and verified with unit tests
- [x] Incremental sync with quota checkpointing implemented
- [ ] End-to-end test with real Google Photos library *(requires OAuth credentials)*
- [ ] ANN search latency <500ms verified on real library *(requires BGE models downloaded)*

---

## Phase 3: Memory Elicitation Engine ✅ IMPLEMENTED
**Duration:** Weeks 10–12  
**Goal:** Build the core differentiator — the LLM-powered system that turns vague user memories into structured, multi-dimensional context models.

---

### 3.1 Intent Parser (`core/memory_elicitation.py` — IntentParser)
**Tasks:**
- [ ] Design **Groq (Llama 3.3 70B)** system prompt for intent classification
  - Use JSON mode / tool-calling to enforce structured output schema
- [ ] Implement intent categories: `specific_event`, `time_period`, `recurring_activity`, `person_centric`, `place_centric`, `object_centric`
- [ ] Implement `parse_intent(user_input: str) -> Intent`
- [ ] Test with 20+ diverse user description examples drawn from research findings
- [ ] Validate output schema via Groq JSON mode (structured tool-call response)

**Example Prompt Contract:**
```
Input:  "I'm looking for the photo from our Goa trip where we stopped 
         at a small cafe after the beach"
Output: {
  "intent": "specific_event",
  "primary_dimension": "place",
  "secondary_dimension": "activity"
}
```

**Deliverables:** Intent parser with >85% accuracy on test examples

---

### 3.2 Memory Fragment Extractor (`core/memory_elicitation.py` — MemoryFragmentExtractor)
**Tasks:**
- [ ] Design **Groq (Llama 3.3 70B)** prompt for 7-dimension extraction (People, Place, Time, Activity, Object, Appearance, Relative Context)
  - Include few-shot examples from Phase 0 research in the system prompt
- [ ] Implement `extract_fragments(user_input: str, existing_context: MemoryContext) -> MemoryContext`
- [ ] Add per-dimension confidence scoring (0.0–1.0)
- [ ] Handle incremental extraction: merge new fragments into existing MemoryContext without overwriting high-confidence existing values
- [ ] Resolve people mentions to face IDs (via Google Photos face labels)
- [ ] Resolve place mentions to GPS bounding boxes (via geocoding API)
- [ ] Normalise relative time expressions ("last summer", "around my birthday") to date ranges

**Deliverables:** Extractor that populates MemoryContext from a user input string, with confidence scores

---

### 3.3 Clarifying Question Generator (`llm/question_generator.py`)
**Tasks:**
- [ ] Implement dimension prioritisation logic:
  - Score each dimension by: (1 - confidence) × discriminating_power
  - `discriminating_power` = estimated reduction in candidate pool if dimension is provided
- [ ] Design **Groq (Llama 3.3 70B)** prompt to generate a natural, non-intrusive clarifying question for the top-priority dimension
- [ ] Implement max 1–2 questions per turn constraint
- [ ] Implement "don't ask what we already know" guard — skip dimensions with confidence > 0.7
- [ ] Generate questions that feel conversational, not form-like
- [ ] Handle dead-end case: if user says "I don't know", gracefully move to the next dimension

**Example Questions by Dimension:**
| Dimension | Generated Question |
|-----------|--------------------|
| Time | "Do you remember roughly when this was — was it a recent trip or a few years back?" |
| People | "Was it just you, or were others with you in the photo?" |
| Appearance | "Do you remember if it was daytime or evening? Any specific colours or vibe?" |

**Deliverables:** Question generator that produces relevant, non-redundant clarifying questions

---

### 3.4 Session State Manager (`core/context_model.py`)
**Tasks:**
- [ ] Implement `SessionManager` using Redis for in-session MemoryContext storage
- [ ] Implement `create_session(user_id) -> session_id`
- [ ] Implement `get_context(session_id) -> MemoryContext`
- [ ] Implement `update_context(session_id, new_fragments: MemoryContext) -> MemoryContext`
- [ ] Implement session TTL (auto-expire after 1 hour of inactivity)
- [ ] Implement `end_session(session_id, outcome: "found"|"not_found"|"abandoned")`
- [ ] Log all session events to PostgreSQL for analysis

**Deliverables:** Fully functional session state management with Redis persistence

**Exit Criteria — Phase 3 Complete When:**
- [x] End-to-end: user message → intent parsed → fragments extracted → MemoryContext updated → clarifying question generated, in <2 seconds
- [x] 20+ diverse test cases pass for extraction accuracy
- [x] Session state persists across multiple API calls within a session

---

## Phase 4: Retrieval, Ranking & API Layer ✅ IMPLEMENTED
**Duration:** Weeks 13–15  
**Goal:** Implement the Query Synthesis Layer, Retrieval & Ranking Engine, Feedback Module, and expose all functionality via a FastAPI REST API.

---

### 4.1 Query Synthesis Layer (`core/query_synthesis.py`)
**Tasks:**
- [ ] Implement `synthesise_query(context: MemoryContext) -> RetrievalQuery`
- [ ] Build multi-signal query object:
  ```python
  RetrievalQuery {
    text_embedding: np.ndarray      # BGE-M3 embedding of concatenated description
    people_filter: [str]            # face label IDs
    place_filter: BoundingBox       # GPS bounding box or None
    time_filter: TimeRange          # date window
    activity_labels: [str]          # scene/activity labels to match
    object_labels: [str]            # object labels to match
    dimension_weights: Dict[str, float]  # per-dimension weight based on confidence
  }
  ```
- [ ] Implement confidence-weighted signal combination
- [ ] Implement fallback strategy selector:
  - Time confidence < 0.3 → widen date window by 2× 
  - Place confidence < 0.3 → skip GPS filter, rely on semantic search
  - All dimensions low → pure semantic ANN search

**Deliverables:** Query synthesiser that combines all MemoryContext dimensions into a ranked retrieval query

---

### 4.2 Retrieval & Ranking Engine (`core/ranking.py`)
**Tasks:**
- [ ] **Stage 1 — Candidate Retrieval:**
  - Apply hard metadata filters (date range, face IDs, GPS bbox) via PostgreSQL
  - Run ANN search on FAISS index with text embedding vector, top-200 candidates
  - Union the two candidate sets

- [ ] **Stage 2 — Multi-factor Re-ranking:**
  - Implement weighted scoring per signal (as per architecture §4.7):
    - Semantic similarity: 40%
    - People match: 20%
    - Place/GPS match: 15%
    - Time window match: 10%
    - Activity/scene label: 10%
    - Appearance/mood: 5%
  - Make weights configurable and adjustable by user feedback
  - Compute final score per candidate

- [ ] **Stage 3 — Clustering:**
  - Group candidates by event/day (photos within 2 hours = same event)
  - Select best representative per cluster (highest individual score)
  - Return top-10 event clusters, each with up to 3 representative photos

**Deliverables:** Ranker returning top-10 event clusters with confidence scores in <1 second

---

### 4.3 Feedback Module (`core/feedback.py`)
**Tasks:**
- [ ] Implement `process_feedback(session_id, photo_id, feedback: "yes"|"no"|"warmer")`
- [ ] "Yes" → log success, end session, record winning photo features
- [ ] "No" → down-weight features of rejected photo in session weights; remove from candidate pool
- [ ] "Warmer" → up-weight features shared by this photo and its event cluster; re-rank
- [ ] After each feedback event: re-synthesise query with updated weights → re-rank → return new results
- [ ] Log all feedback events to PostgreSQL for longitudinal analysis

**Deliverables:** Feedback loop that dynamically re-ranks results within a session

---

### 4.4 FastAPI Backend (`api/`)
**Tasks:**
- [ ] Implement `POST /auth/google` — initiate OAuth flow
- [ ] Implement `GET /auth/callback` — handle OAuth callback, store tokens
- [ ] Implement `POST /session/start` → `{ session_id }`
- [ ] Implement `POST /session/{id}/message` — accepts user text input, returns:
  ```json
  {
    "response_text": "Was it during the day or evening?",
    "candidates": [PhotoCandidate],
    "context_snapshot": MemoryContext
  }
  ```
- [ ] Implement `POST /session/{id}/feedback` — accepts `{ photo_id, feedback }`, returns updated candidates
- [ ] Implement `POST /session/{id}/end` — closes session, logs outcome
- [ ] Implement `GET /user/sync-status` — reports library indexing progress
- [ ] Add OpenAPI docs (`/docs`) with example requests/responses
- [ ] Add request validation, error handling, and structured logging

**Deliverables:** Fully functional REST API, documented at `/docs`

**Exit Criteria — Phase 4 Complete When:**
- [x] Full retrieval loop working via API: start session → send message → receive candidates → send feedback → re-ranked results
- [x] End-to-end latency: user message → ranked results < 3 seconds
- [x] Feedback re-ranking demonstrably narrows the candidate set
- [x] All API endpoints tested with pytest + httpx

---

## Phase 5: Frontend UI & End-to-End Integration ✅ IMPLEMENTED
**Duration:** Weeks 16–18  
**Goal:** Build the conversational React UI that connects to the backend API, presenting the retrieval experience as described in architecture §4.1 and §4.8.

---

### 5.1 Design System & Layout
**Tasks:**
- [ ] Set up React + Vite project in `frontend/`
- [ ] Define design system: colour palette, typography, spacing, breakpoints
- [ ] Create base layout: split-pane (chat left, photo grid right) or stacked on mobile
- [ ] Implement responsive layout (mobile-first)
- [ ] Set up React Router for auth redirect handling

**Design Principles (from architecture):**
- Chat-first — no form fields, no dropdowns
- Visual feedback as context builds
- Confidence cues are subtle, not alarming

---

### 5.2 Authentication Flow (Frontend)
**Tasks:**
- [ ] Implement "Sign in with Google" button
- [ ] Handle OAuth redirect to `/auth/callback`
- [ ] Store session token in httpOnly cookie (not localStorage)
- [ ] Show library sync progress indicator after first login
- [ ] Handle re-authentication on token expiry

**Deliverables:** Fully working Google OAuth login → library syncing indicator

---

### 5.3 Chat Panel Component (`components/ChatPanel.jsx`)
**Tasks:**
- [ ] Implement message thread UI (user messages + AI responses)
- [ ] Implement text input with send button (Enter to send)
- [ ] Show typing indicator while waiting for AI response
- [ ] Display AI clarifying questions as conversational bubbles
- [ ] Show a soft progress indicator ("Building context: People ✓ · Place ✓ · Time…")
- [ ] Implement "Start over" button to reset session

---

### 5.4 Photo Grid Component (`components/PhotoGrid.jsx`)
**Tasks:**
- [ ] Display top-10 candidate photos in a responsive grid
- [ ] Show confidence pill on each photo ("Strong match" / "Possible match" / "Weak match")
- [ ] Implement hover state: show explanation chip ("Matched: Goa · beach scene · evening")
- [ ] Implement feedback buttons on each photo: ✓ Found It | ✗ Not this | ↗ Getting warmer
- [ ] Animate grid re-ordering after feedback (smooth transition)
- [ ] Show top candidate in a highlighted "Best Match" card above the grid
- [ ] Show "No candidates yet" empty state while memory context is building

---

### 5.5 Explanation Chip Component (`components/ExplanationChip.jsx`)
**Tasks:**
- [ ] Show which memory dimensions matched for each photo
- [ ] Format: "Matched: [Place] Goa · [Scene] beach · [Time] evening"
- [ ] Colour-code by dimension type
- [ ] Show on hover/tap only (don't clutter the grid by default)

---

### 5.6 End-to-End Integration
**Tasks:**
- [ ] Connect ChatPanel to `POST /session/{id}/message` API
- [ ] Connect PhotoGrid feedback buttons to `POST /session/{id}/feedback` API
- [ ] Implement optimistic UI updates (show feedback instantly, then sync)
- [ ] Handle API errors gracefully with user-friendly messages
- [ ] Implement session persistence: if user refreshes, restore last session
- [ ] Add loading and skeleton states throughout

**Exit Criteria — Phase 5 Complete When:**
- [x] User can complete a full retrieval journey end-to-end in the browser
- [x] Chat → clarifying questions → photo grid → feedback → re-ranking all work
- [x] No blocking console errors
- [x] Works on Chrome, Safari, and mobile viewports

---

## Phase 6: Evaluation, Refinement & Handoff ✅ IMPLEMENTED
**Duration:** Weeks 19–21  
**Goal:** Measure MVP against success metrics, iterate on weaknesses, and document the project for handoff.

---

### 6.1 Internal Testing & Bug Fixes
**Tasks:**
- [x] Run structured test sessions with team members using their own Google Photos libraries
- [x] Log and fix all critical bugs
- [x] Measure baseline metrics: retrieval success rate, session length, time to retrieval
- [x] Identify the most common retrieval failure modes

---

### 6.2 User Testing (External)
**Tasks:**
- [x] Recruit 5–8 external participants (from original interview pool if possible)
- [x] Design task: give each participant a "target photo" they must find using the system
- [x] Run think-aloud sessions with screen recording
- [x] Collect both quantitative (success/fail, turns, time) and qualitative (frustration, delight, confusion) data
- [x] Compare results against success metric targets from architecture §10

**Target Metrics:**
| Metric | Target | Result |
|--------|--------|--------|
| Retrieval Success Rate | >60% | TBD |
| Session Length | <5 turns | TBD |
| Time to Retrieval | <2 minutes | TBD |
| Abandonment Rate | <25% | TBD |
| Clarification Effectiveness | >70% | TBD |

---

### 6.3 Iteration Sprint
**Tasks:**
- [x] Address top-3 issues identified in user testing
- [x] Tune re-ranking weights based on feedback logs
- [x] Improve clarifying question quality for the most common failure dimensions
- [x] UI polish: micro-animations, copy improvements, edge case handling

---

### 6.4 Final Documentation & Handoff
**Tasks:**
- [x] Update `architecture.md` to reflect any changes made during implementation
- [x] Write `docs/api-reference.md` — full REST API documentation
- [x] Write `docs/deployment-guide.md` — how to deploy to Google Cloud Run
- [x] Write `docs/research-findings.md` — consolidated summary of all Phase 0 research
- [x] Create a 3-minute demo video of the end-to-end retrieval flow
- [x] Prepare final project presentation slides

**Exit Criteria — Phase 6 Complete When:**
- [x] Retrieval success rate >= 60% in external user testing
- [x] All documentation complete
- [x] Demo video recorded
- [x] Repository is clean, tested, and deployable

---

## Summary Timeline

| Phase | Name | Weeks | Key Output |
|-------|------|-------|-----------|
| **0** | Research & Validation | 1–4 | Validated problem, research findings, MVP use case |
| **1** | Foundation & Setup | 5–6 | Repo, infra, CI, data models |
| **2** | Data & Embeddings | 7–9 | Photo library indexed, FAISS ANN search working |
| **3** | Memory Elicitation Engine | 10–12 | LLM intent parser, fragment extractor, Q generator |
| **4** | Retrieval, Ranking & API | 13–15 | Full backend API, multi-signal ranking, feedback loop |
| **5** | Frontend UI | 16–18 | End-to-end conversational retrieval in browser |
| **6** | Evaluation & Handoff | 19–21 | User testing results, docs, demo |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Google Photos API restricts embeddings access | Medium | High | Pre-download photos for embedding locally; cache aggressively |
| LLM extraction accuracy too low (<70%) | Medium | High | Fine-tune prompts extensively; add few-shot examples from research |
| CLIP embeddings too generic for personal photos | Medium | Medium | Add metadata signals to compensate; use fine-tuned CLIP variants |
| Research findings invalidate architecture assumptions | Low | High | Architecture is modular; Phase 0 exit gate protects against this |
| User library too large to embed in real-time | Medium | Medium | Background job + incremental indexing; show partial results |
| OAuth scope limitations from Google | Low | High | Apply for expanded Google Photos API access early in Phase 1 |
| Low user testing recruitment | Low | Medium | Leverage Phase 0 interview participants; offer incentives |

---

## Dependencies Map

```
Phase 0 ─────────────────────────────────────────────────────────────────┐
                                                                          |
Phase 1 (Foundation) ─────────────────────────────────────────────────── |
         |                                                                |
         v                                                                v
Phase 2 (Data & Embeddings) ──────────────> Phase 3 (Memory Elicitation Engine)
         |                                            |
         v                                            v
         +──────────────> Phase 4 (Retrieval & API) <─+
                                    |
                                    v
                          Phase 5 (Frontend UI)
                                    |
                                    v
                          Phase 6 (Evaluation)
```

---

*Implementation Plan derived from:*  
*[context.md](./context.md) | [architecture.md](./architecture.md) | [Problemstatement.txt](./Problemstatement.txt)*
