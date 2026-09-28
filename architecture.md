# System Architecture: AI-Native Photo Retrieval MVP
**Project:** Google Photos — Memory-Based Retrieval  
**Source:** Problemstatement.txt  
**Version:** 1.0  
**Date:** 2026-09-22

---

## 1. Overview

This document describes the end-to-end system architecture for an **AI-native MVP** that enables users to retrieve photos from their Google Photos library using **incomplete or vague memories**. The system bridges the gap between how humans naturally recall a memory (contextual, experiential) and how photo libraries are traditionally queried (metadata, keywords, dates).

---

## 2. Architecture Principles

| Principle | Rationale |
|-----------|-----------|
| **Memory-First Design** | The system treats user descriptions as memory fragments, not search queries |
| **Conversational Retrieval** | Iterative dialogue to progressively narrow down candidates |
| **Multi-Modal Reasoning** | Combines visual, temporal, semantic, and contextual signals |
| **Outcome-Oriented Success** | Success = user finds the photo, not AI understanding the query |
| **Research-Validated** | Architecture shaped by empirical findings, not assumptions |
| **Non-Invasive** | Works on top of existing Google Photos without replacing native search |

---

## 3. High-Level Architecture

```
+---------------------------------------------------------------+
|                        USER INTERFACE                         |
|          (Conversational UI / Memory Elicitation Chat)        |
+----------------------------+---------------------------------+-+
                             |
                             v
+---------------------------------------------------------------+
|                  MEMORY ELICITATION ENGINE                    |
|  - Intent Parsing                                             |
|  - Memory Fragment Extraction                                 |
|  - Clarifying Question Generator                              |
+----------------------------+----------------------------------+
                             |
              +--------------+--------------+
              |                             |
              v                             v
+---------------------------+  +----------------------------+
|  STRUCTURED CONTEXT MODEL |  |  SEMANTIC EMBEDDING ENGINE |
|  - Who (people)           |  |  - Text Embeddings (NLP)   |
|  - Where (place)          |  |  - Image Embeddings (CLIP) |
|  - When (time/period)     |  |  - Cross-modal Matching    |
|  - What (activity/object) |  +----------------------------+
|  - How (appearance/mood)  |
+---------------------------+
              |
              v
+---------------------------------------------------------------+
|                    QUERY SYNTHESIS LAYER                      |
|  - Multi-Signal Query Builder                                 |
|  - Confidence Scoring per Memory Dimension                    |
|  - Fallback Strategy Selector                                 |
+---------------------------------------------------------------+
              |
              v
+---------------------------------------------------------------+
|                  PHOTO LIBRARY INTEGRATION                    |
|  - Google Photos API Adapter                                  |
|  - Metadata Index (EXIF, Albums, Tags, Faces)                 |
|  - Content Index (AI-generated captions, scene labels)        |
+---------------------------------------------------------------+
              |
              v
+---------------------------------------------------------------+
|                    RETRIEVAL & RANKING ENGINE                 |
|  - Candidate Retrieval (Approximate Nearest Neighbour)        |
|  - Multi-factor Re-ranker                                     |
|  - Result Clustering & Grouping                               |
+---------------------------------------------------------------+
              |
              v
+---------------------------------------------------------------+
|                  RESULT PRESENTATION LAYER                    |
|  - Photo Grid with Confidence Scores                          |
|  - Explanation of Why Each Photo Was Retrieved                |
|  - User Feedback Loop (Was this it?)                          |
+---------------------------------------------------------------+
              |
              v
+---------------------------------------------------------------+
|                    FEEDBACK & LEARNING MODULE                 |
|  - Session-level refinement (within retrieval journey)        |
|  - Longitudinal learning (across sessions, opt-in)            |
+---------------------------------------------------------------+
```

---

## 4. Component Deep-Dive

### 4.1 User Interface (Conversational UI)

**Purpose:** Accept vague, natural-language memory descriptions from the user.

**Key Design Decisions:**
- **Chat-first interface** — mirrors how users naturally describe memories
- **Progressive disclosure** — starts simple, gets more specific through dialogue
- **No form fields** — avoids forcing users into structured categories they don't naturally recall
- **Visual feedback** — shows candidate thumbnails as context builds up

**Inputs:**
- Free-text description of the memory
- Optional: voice input
- Optional: rough time-period gesture (slider, not exact date)

**Outputs:**
- Conversational responses with clarifying questions
- Live-updating photo grid of current candidates

---

### 4.2 Memory Elicitation Engine

**Purpose:** Transform a vague user description into a structured set of memory fragments. This is the **core differentiator** of the system.

**Sub-components:**

#### 4.2.1 Intent Parser
- Determines whether the user is describing: a specific event, a general time period, a recurring activity, a person-centric memory, or a place-centric memory
- Uses **Groq API** (Llama 3.3 70B / Mixtral 8x7B) with a structured JSON output schema — chosen for ultra-low latency inference

#### 4.2.2 Memory Fragment Extractor
Extracts the following memory dimensions from the user's input:

| Dimension | Example | Typical Recall Strength |
|-----------|---------|------------------------|
| **People** | "my college friends", "grandma" | High |
| **Place** | "Goa", "the beach", "a small cafe" | Medium |
| **Time Period** | "last summer", "around my birthday" | Medium |
| **Activity** | "we were eating", "after the swim" | High |
| **Object / Subject** | "a yellow scooter", "the sunset" | Medium |
| **Appearance / Mood** | "it was golden hour", "everyone was laughing" | Variable |
| **Relative Context** | "the one after the market visit" | Low |

#### 4.2.3 Clarifying Question Generator
- Prioritises the **most discriminating** missing dimension
- Avoids overwhelming the user (max 1-2 questions at a time)
- Adapts based on which dimensions already have high-confidence values
- Example: If place=Goa, time=vague → asks "Was this during the day or evening?"

---

### 4.3 Structured Context Model

**Purpose:** Maintain a stateful, structured representation of everything the user has told the system during the retrieval session.

```
MemoryContext {
  session_id:       string
  raw_descriptions: [string]      // history of user inputs
  people:           [PersonRef]   // resolved face/person IDs
  places:           [PlaceRef]    // geo-locations or named places
  time_window:      TimeRange     // e.g., { start: 2022-06, end: 2022-08 }
  activities:       [string]      // "beach", "eating", "travelling"
  objects:          [string]      // "scooter", "sunset", "food"
  appearance:       [string]      // "golden hour", "crowded", "indoor"
  confidence:       {             // per-dimension confidence (0-1)
    people: 0.9,
    places: 0.6,
    time:   0.3,
    ...
  }
  candidate_pool:   [PhotoRef]    // current set of candidate photos
}
```

---

### 4.4 Semantic Embedding Engine

**Purpose:** Enable similarity-based matching between user descriptions and photo content that goes beyond keyword matching.

**Components:**

#### Text Embeddings
- Model: **BGE-M3** (`BAAI/bge-m3`) — multilingual, multi-functionality dense retrieval model
- Encodes user descriptions into a 1024-dim dense vector space
- Outperforms sentence-transformers on retrieval benchmarks (MTEB); runs fully locally via `FlagEmbedding`
- Enables "café after the beach" to match photos with relevant visual semantics

#### Image Embeddings
- Model: **BGE-Visualized** (`BAAI/bge-visualized-m3`) — extends BGE-M3 to images, producing image embeddings in the **same vector space** as BGE text embeddings
- Each photo in the library is pre-encoded as a 1024-dim vector
- Enables direct text-to-image cosine similarity without a separate cross-modal bridge
- Fallback: CLIP (ViT-L/14) for any photos where BGE-Visualized fails

#### Cross-Modal Matching
- Computes similarity between text embedding (user description) and image embeddings (photo library)
- Uses Approximate Nearest Neighbour (ANN) search (e.g., FAISS, ScaNN)

---

### 4.5 Query Synthesis Layer

**Purpose:** Combine all memory fragments and embeddings into a unified, multi-signal retrieval query.

**Strategy:**

```
Query = weighted_combination(
    semantic_similarity(user_description, photo_embeddings),
    metadata_match(people_filter, place_filter, time_filter),
    activity_scene_match(activity_labels),
    object_detection_match(object_labels),
    appearance_match(colour, lighting, crowd_density)
)
```

**Fallback Strategy Selector:**
- If confidence on time is low → broaden date window
- If place is vague → use related place clusters
- If first retrieval fails → suggest switching strategy (e.g., "Try describing the people instead")

---

### 4.6 Photo Library Integration

**Purpose:** Interface with the user's Google Photos library to retrieve candidate photos and their metadata.

**Data Sources:**

| Source | Data Available |
|--------|---------------|
| **Google Photos API** | Albums, shared photos, creation date, GPS, favourites |
| **EXIF Metadata** | Camera settings, GPS coordinates, timestamp |
| **Face Recognition Index** | Labelled people in photos |
| **Scene / Object Labels** | AI-generated tags (already in Google Photos) |
| **AI-generated Captions** | Auto-descriptions of photo content |
| **Text in Photos (OCR)** | Signboards, menus, names visible in photos |

**Privacy Consideration:**
- All photo data is processed on behalf of the authenticated user only
- No cross-user data sharing
- Embeddings stored per-user, not in a shared index

---

### 4.7 Retrieval & Ranking Engine

**Purpose:** Score and rank candidate photos from the library against the structured memory context.

**Stage 1 — Candidate Retrieval:**
- Apply hard filters: date range, face IDs, GPS bounding box
- ANN search over image embeddings using text description vector
- Output: top-N candidates (e.g., N=200)

**Stage 2 — Multi-factor Re-ranking:**

| Signal | Weight (indicative) | Notes |
|--------|---------------------|-------|
| Semantic embedding similarity | 40% | Core memory-to-image match |
| People match | 20% | If user mentioned specific people |
| Place / GPS match | 15% | If location is known |
| Time window match | 10% | Broader is less penalised |
| Activity / scene label match | 10% | "beach", "restaurant", etc. |
| Appearance / mood match | 5% | Colour temperature, crowd, lighting |

**Stage 3 — Clustering:**
- Group top results by event/day to avoid showing near-duplicates
- Surface the best representative photo per cluster

---

### 4.8 Result Presentation Layer

**Purpose:** Show ranked results with explanatory context to help the user confirm or reject candidates.

**UI Elements:**
- **Photo grid** ordered by confidence score
- **Confidence pill** on each photo ("Strong match", "Possible match")
- **Explanation chip** — e.g., "Matched: Goa location · beach scene · evening"
- **"Is this it?"** interaction — Yes / No / Getting Warmer
- **Highlight panel** — zooms into the top candidate with a full explanation

---

### 4.9 Feedback & Learning Module

**Purpose:** Use user interactions to refine results within the session and improve the system over time.

**Session-Level (In-session refinement):**
- User says "No" → down-rank photos with similar features
- User says "Getting warmer" → up-rank photos from the same event cluster
- Adjusts dimension weights dynamically based on what the user confirms/rejects

**Longitudinal Learning (Opt-in, cross-session):**
- Learns which memory dimensions the user typically recalls well
- Personalises clarifying question ordering
- Builds a user-specific retrieval difficulty profile

---

## 5. Data Flow Diagram

```
User Input (vague description)
        |
        v
[Memory Elicitation Engine]
        |
        +---> [Structured Context Model] <--- [Clarifying Q&A loop]
        |
        v
[Semantic Embedding Engine]
        |  (text embedding of user description)
        v
[Query Synthesis Layer]
        |  (multi-signal structured query)
        v
[Photo Library Integration]
        |  (candidates from API + metadata index)
        v
[Retrieval & Ranking Engine]
        |  (ranked candidates)
        v
[Result Presentation Layer]
        |  (user sees grid + explanations)
        v
[User Feedback: Yes / No / Warmer]
        |
        v
[Feedback & Learning Module]
        |
        +---> (updates MemoryContext → loops back to Retrieval)
```

---

## 6. Technology Stack (Proposed)

| Layer | Technology Options |
|-------|--------------------|
| **Frontend / UI** | React (web), Flutter (mobile) |
| **Conversational AI** | **Groq API** — Llama 3.3 70B (primary) / Mixtral 8x7B (fallback) |
| **Text Embeddings** | **BGE-M3** (`BAAI/bge-m3`) via `FlagEmbedding` — local, no API cost |
| **Image Embeddings** | **BGE-Visualized** (`BAAI/bge-visualized-m3`) + CLIP (ViT-L/14) fallback |
| **Vector Search** | FAISS / Google ScaNN / Pinecone |
| **Photo Library API** | Google Photos Library API (OAuth 2.0) |
| **Backend** | Python (FastAPI) / Node.js |
| **Session State** | Redis (in-session MemoryContext) |
| **Database** | PostgreSQL (user profiles, feedback logs) |
| **Deployment** | Google Cloud Run / Firebase |

---

## 7. Key Architectural Challenges

| Challenge | Description | Mitigation |
|-----------|-------------|------------|
| **Vague input handling** | User descriptions are ambiguous and incomplete by design | Multi-turn dialogue + progressive memory extraction |
| **Large library scale** | Libraries with 100k+ photos need fast retrieval | Pre-computed embeddings + ANN indexing |
| **Privacy & Auth** | Photos are private; must not cross user boundaries | Per-user isolated indices + OAuth scopes |
| **Cold-start problem** | New users have no personalisation history | Rely on universal memory extraction heuristics |
| **Retrieval failure graceful degradation** | Some photos may truly be unfindable | Show "best guess" + explain why it might not match |
| **Google Photos API rate limits** | Bulk indexing is rate-limited | Background incremental indexing with caching |
| **Memory dimension coverage** | User may give only 1-2 dimensions | Robust fallbacks + strategic clarifying questions |

---

## 8. Research-to-Architecture Mapping

Each research question from the problem statement informs a specific architectural component:

| Research Question | Validation from Data | Architecture Component Informed |
|-------------------|----------------------|---------------------------------|
| What types of photos are hard to retrieve? | Life events, docs without OCR, location-heavy trips without GPS | Fallback Strategy Selector (4.5) & multi-modal Semantic Matching |
| What do users naturally remember? | People, events, semantic locations, objects, emotions | Memory Fragment Extractor dimensions (4.2.2) |
| What do they typically forget? | Exact dates, file names, GPS coords, folder structure | Confidence scoring + clarifying Q generator (4.2.3) drops these filters |
| How do they describe/search? | Concept-first NLP (person+relationship, event+season) | Intent Parser (4.2.1) + Chat UI design (4.1) |
| How do they change strategy on failure? | Frustrated manual scrolling or rigid OCR keywords | Feedback & Learning Module (4.9) allows dynamic pivot |
| Where does retrieval break down? | When AI fails to infer un-captured semantic meaning | Session analytics + drop-off tracking + toggle to raw metadata |
| What workarounds do users use? | Custom albums, PC downloads, third-party backups | Compound retrieval strategies in Query Synthesis (4.5) |
| What gaps remain in Google Photos? | Compound semantic queries & custom tag overrides | Semantic Embedding Engine + Memory Elicitation (4.2, 4.4) |

---

## 9. MVP Scope vs. Full Vision

| Feature | MVP | Full Vision |
|---------|-----|-------------|
| Conversational memory input | YES | YES |
| Structured context model | YES | YES |
| Semantic text-to-image search | YES | YES |
| Google Photos API integration | YES | YES |
| Multi-turn clarifying dialogue | YES | YES |
| Result explanation chips | YES | YES |
| In-session feedback refinement | YES | YES |
| Cross-session personalisation | NO | YES |
| Voice input | NO | YES |
| Longitudinal learning | NO | YES |
| Multi-library support (iCloud, etc.) | NO | YES |
| Proactive memory surfacing | NO | YES |

---

## 10. Success Metrics

> **Primary Metric:** Retrieval Success Rate — % of sessions where the user confirms finding the target photo.

| Metric | Definition | Target (MVP) |
|--------|-----------|--------------|
| **Retrieval Success Rate** | User confirms finding the photo | >60% |
| **Session Length** | Number of turns before success | <5 turns |
| **Time to Retrieval** | Wall-clock time from first input to success | <2 minutes |
| **Abandonment Rate** | % of sessions where user gives up | <25% |
| **Clarification Effectiveness** | % of cases where a clarifying Q narrows candidates by >50% | >70% |

---

## 11. File & Module Structure (Backend)

```
photo-retrieval-mvp/
+-- api/
|   +-- main.py                   # FastAPI entry point
|   +-- routes/
|       +-- session.py            # Session management endpoints
|       +-- retrieval.py          # Retrieval API endpoints
|       +-- feedback.py           # Feedback submission
+-- core/
|   +-- memory_elicitation.py     # Memory fragment extraction
|   +-- context_model.py          # MemoryContext state management
|   +-- query_synthesis.py        # Multi-signal query builder
|   +-- ranking.py                # Re-ranking logic
+-- integrations/
|   +-- google_photos.py          # Google Photos API adapter
|   +-- embedding_service.py      # Text + image embedding calls
|   +-- vector_store.py           # FAISS/ScaNN interface
+-- models/
|   +-- memory_context.py         # Pydantic schema: MemoryContext
|   +-- photo_candidate.py        # Pydantic schema: PhotoCandidate
+-- llm/
|   +-- elicitation_prompts.py    # System prompts for memory extraction
|   +-- question_generator.py     # Clarifying question generation
+-- frontend/
|   +-- src/
|       +-- components/
|           +-- ChatPanel.jsx     # Conversational input
|           +-- PhotoGrid.jsx     # Candidate photo display
|           +-- ExplanationChip.jsx # Match explanation UI
```

---

*Architecture derived from: [Problemstatement.txt](file:///c:/Users/nagas/Downloads/Grad%20project-%20google%20photos/Problemstatement.txt) | See also: [context.md](file:///c:/Users/nagas/Downloads/Grad%20project-%20google%20photos/context.md)*
