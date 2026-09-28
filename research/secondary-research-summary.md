# Secondary Research Summary
## Phase 0.1 — Literature Review

**Project:** AI-Native Google Photos Memory-Based Retrieval
**Timeline:** Week 1-2
**Status:** [ ] In Progress  [ ] Complete

---

## Purpose

This document synthesises academic and industry literature across four domains:
1. Personal photo retrieval and management
2. Episodic memory and recall in humans
3. Cross-modal retrieval (text-to-image)
4. Conversational search and information retrieval

Findings feed directly into the Memory Fragment Extractor 7-dimension model and the retrieval strategy.

---

## Domain 1: Personal Photo Management and Retrieval

### Key Papers to Review

| Paper | Authors | Year | Relevance |
|-------|---------|------|-----------|
| "Why Do People Collect Photos?" | Van House et al. | 2004 | Motivations for photo-taking and retrieval intent |
| "Personal Photo Management and Sharing on Camera Phones" | Kindberg et al. | 2005 | Early PIM in mobile context |
| "Stuff I've Seen: A System for Personal Information Retrieval" | Dumais et al. | 2003 | Personal information recall strategies |
| "Photo Retrieval by Content: User Evaluation" | Enser et al. | 2007 | How users describe desired photos vs. system capabilities |
| "Challenges in Personal Photo Retrieval" | TBD | TBD | Fill in after search |

### Key Findings

> Fill in after reviewing papers above.

- Finding 1:
- Finding 2:
- Finding 3:

### Implication for Architecture

> How do these findings affect the Memory Fragment Extractor dimensions or the Clarifying Question Generator?

---

## Domain 2: Episodic Memory and Human Recall

### Background

Episodic memory is the memory of autobiographical events including the time, place, and emotional context of a past experience. This is exactly what users leverage when trying to retrieve a photo.

### Key Concepts to Research

- Encoding specificity principle (Tulving, 1983): memory retrieval is most effective when retrieval cues match encoding conditions
- Contextual reinstatement: imagining the context of the original experience improves recall
- Recall vs. recognition: users may not recall a photo date, but can recognise it when shown
- Fade patterns: which memory dimensions (time, place, people, objects) fade fastest

### Key Papers to Review

| Paper | Authors | Year | Relevance |
|-------|---------|------|-----------|
| "Episodic Memory: From Mind to Brain" | Tulving | 2002 | Foundation of episodic memory theory |
| "Memory for Everyday Events" | Conway | 1996 | How everyday memories are structured |
| "Forgetting Curves and Memory Traces" | TBD | TBD | What users forget first about photos |

### Key Findings

> Fill in after reviewing papers above.

- Finding 1:
- Finding 2:
- Finding 3:

### Implication for Architecture

> Which memory dimensions do people most reliably retain? Which do they lose first? This determines confidence weights in the MemoryContext and clarifying question priority order.

---

## Domain 3: Cross-Modal Retrieval (Text-to-Image)

### Background

Our system uses BGE-Visualized to match text descriptions to images in the same embedding space. Understanding the state of the art is critical for setting accuracy expectations.

### Key Papers and Models to Review

| Resource | Type | Relevance |
|----------|------|-----------|
| CLIP (Radford et al., 2021) | Model paper | Original cross-modal embedding approach |
| BGE-M3 (Chen et al., 2024) | Model paper | Our chosen text embedding; multilingual, multi-functional |
| BGE-Visualized (BAAI, 2024) | Model paper | Our chosen image embedding; unified space with BGE-M3 |
| BLIP-2 | Model paper | Image captioning for label enrichment |
| MTEB: Massive Text Embedding Benchmark | Benchmark | Where BGE-M3 ranks vs. alternatives |

### Key Findings

> Fill in after reviewing.

- BGE-M3 performance on retrieval tasks (MTEB score):
- BGE-Visualized accuracy on image-text matching:
- Known failure modes of cross-modal models:

### Implication for Architecture

> What retrieval accuracy can we realistically expect from BGE-Visualized? Where does semantic search degrade and metadata filtering must compensate?

---

## Domain 4: Conversational Search and Clarification

### Background

The Memory Elicitation Engine is essentially a conversational retrieval system. Understanding how dialogue-based clarification improves search outcomes informs our Clarifying Question Generator design.

### Key Papers to Review

| Paper | Authors | Year | Relevance |
|-------|---------|------|-----------|
| "Asking Clarifying Questions in Open-Domain IR" | Aliannejadi et al. | 2019 | When and how to ask clarifying questions |
| "Conversational Information Seeking" | Radlinski and Craswell | 2017 | Framework for dialogue-based retrieval |
| "Mixed-Initiative Conversational Search" | TBD | TBD | User and AI collaboration in search |

### Key Findings

> Fill in after reviewing.

- Finding 1:
- Finding 2:
- Finding 3:

### Implication for Architecture

> When should the system ask questions vs. retrieve immediately? What makes a clarifying question effective vs. annoying?

---

## Domain 5: Google Photos Existing Capabilities

### Feature Inventory

| Feature | How It Works | User-Facing | Dimension Covered |
|---------|-------------|-------------|-------------------|
| Face grouping | Clusters photos by detected faces | People album | People |
| Place detection | EXIF GPS + reverse geocoding | Places map | Place |
| Object/scene labels | Vision AI labels | Searchable via search bar | Object, Activity |
| Date/time search | EXIF metadata | Date picker in search | Time |
| OCR / text in photos | On-device OCR | Searchable via search bar | Object (text) |
| Ask Photos (natural language) | LLM over photo metadata | Conversational search | Multi-dimension |
| Memories | Auto-generated highlight reels | Shown on home screen | Time, Place |
| Albums | Manual user-created groupings | Manual organisation | Context |

### Ask Photos Deep Dive

> Research and document exactly what Ask Photos can and cannot do.

**What Ask Photos CAN do:**
-
-

**What Ask Photos CANNOT do (documented gaps):**
-
-

---

## Research Question Mapping

| Research Question | Evidence Found | Source(s) | Confidence |
|-------------------|---------------|-----------|------------|
| 1. What types of photos are hard to retrieve? | | | |
| 2. What do users naturally remember? | | | |
| 3. What do they typically forget? | | | |
| 4. How do they describe/search? | | | |
| 5. How do they change strategy on failure? | | | |
| 6. Where does retrieval break down? | | | |
| 7. What workarounds do users use? | | | |
| 8. What gaps remain in Google Photos? | | | |

---

## Summary of Key Findings

> Fill in after all domains are reviewed.

### Top 5 Most Important Findings

1.
2.
3.
4.
5.

### Architecture Assumptions Confirmed or Challenged

| Assumption in architecture.md | Status | Evidence |
|-------------------------------|--------|----------|
| People dimension has high recall strength | | |
| Time dimension has low recall strength | | |
| Place dimension has medium recall strength | | |
| Activity dimension has high recall strength | | |

---

*Next: [google-photos-gap-analysis.md](./google-photos-gap-analysis.md)*
