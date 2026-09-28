# Project Context: Google Photos Memory-Based Retrieval

> **Source:** Problemstatement.txt
> **Project Type:** Graduate Research & AI-Native MVP
> **Domain:** Human-Computer Interaction � AI/ML � Information Retrieval

---

## 1. Background

As people use **Google Photos** over many years, their libraries accumulate thousands of photos, videos, screenshots, documents, and other visual memories. Locating a specific old photo becomes increasingly difficult when a user remembers the **memory or experience** associated with a photo, but **cannot recall the exact details** needed to surface it through conventional search.

---

## 2. Core Problem

There is a gap between:

- **How people naturally remember a photo** (contextual, experiential, sensory memories)
- **How they are able to retrieve it** from their photo library (keyword search, dates, filenames, albums)

### Illustrative Example

> *"I'm looking for the photo from our Goa trip where we stopped at a small cafe after the beach."*

The user may remember:
- The **people** in the photo
- The **place** or **activity**
- The general **appearance** or **context**

But may **not** remember:
- The exact date
- The cafe name or precise location
- The album it was saved in
- The filename or text visible in the photo

---

## 3. What the Problem Is NOT

Google Photos already provides rich search capabilities:
- People recognition
- Places & locations
- Objects & scenes
- Dates
- On-image text (OCR)
- Natural-language / Ask Photos experiences

Therefore, **the problem is not simply that users need a better search box**. The gap lies in the mismatch between memory-based recall and search-optimised retrieval.

---

| # | Research Question | Validation from UX Research |
|---|-------------------|-----------------------------|
| 1 | What **types of photos** are difficult to retrieve when memory is incomplete? | Life events without dedicated albums, scanned documents without OCR-friendly text, technical/how-to shots, and location-heavy travel photos where GPS is stripped. |
| 2 | What **information do users naturally remember** about those photos? | People/relationships, explicit events, semantic locations (e.g. "East Tennessee"), objects/actions, and emotional context. |
| 3 | What **information do they typically forget**? | Exact dates, file names, precise GPS coordinates, and original folder/album structures. |
| 4 | How do they **describe or search** for the photo? | Concept-first natural language ("person + relationship", "event + season", "object + action"). |
| 5 | Where exactly does the **retrieval journey break down**? | When users rely on AI to infer semantic meaning, but the AI lacks confidence or the raw metadata (GPS/Date) is missing or corrupted. |
| 6 | What **workarounds** do users employ? | Manual scrolling, ad-hoc tagging (OCR stuffing), moving to desktop for OS-level search, or creating redundant albums. |
| 7 | Which of these problems are **already addressed by Google Photos**, and which **gaps remain**? | Google Photos handles keyword search and facial recognition well, but fails on *compound semantic queries* (e.g. "Location + Activity") and lacks user-controlled metadata tagging when AI fails. |

---

## 5. Methodology

Answers to the research questions will be derived through:

1. **Analysis of publicly available user conversations and reviews** � to surface real-world retrieval pain points at scale
2. **Secondary research** � to understand existing literature on memory, search behaviour, and photo management
3. **Task-based user interviews** � to observe retrieval journeys in a controlled, qualitative setting

---

## 6. Project Objective

To identify a **specific, evidence-backed retrieval problem** rather than assume a solution in advance.

The research-first approach ensures that any AI intervention is grounded in validated user needs, not assumptions.

---

## 7. AI-Native MVP

Based on the validated problem, the project will:
- Determine **where AI can provide meaningful assistance**
- Build an **AI-native MVP** that helps users retrieve a specific photo from an available photo library using **incomplete or vague memories**

---

## 8. Success Criteria

> The final measure of success is **not** whether the AI can understand a user's description.
>
> It **is** whether the user can **successfully retrieve the photo they were trying to find**.

This outcome-focused definition of success prioritises the user's end goal over technical benchmarks.

---

## 9. Key Concepts & Terms

| Term | Definition in Context |
|------|-----------------------|
| **Memory-based retrieval** | Finding a photo by describing the experience or memory, not exact metadata |
| **Incomplete memory** | User recalls partial context but not enough to query successfully |
| **Retrieval journey** | The full sequence of steps a user takes to find a photo |
| **Retrieval breakdown** | The point where the user's search strategy fails or stalls |
| **AI-native MVP** | A minimum viable product where AI is core to the retrieval experience |

---

## 10. Stakeholders

- **Primary users:** Long-term Google Photos users with large libraries
- **Platform:** Google Photos
- **Research team:** Graduate project team
- **Beneficiary:** Any photo management or personal AI retrieval system
