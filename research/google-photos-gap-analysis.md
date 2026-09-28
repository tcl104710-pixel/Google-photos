# Google Photos Gap Analysis
## Phase 0.1 — Capability vs. Gap Assessment

**Project:** AI-Native Google Photos Memory-Based Retrieval
**Timeline:** Week 1-2
**Status:** [ ] In Progress  [ ] Complete

---

## Purpose

Map every current Google Photos search and retrieval capability against each of the 7 memory dimensions (People, Place, Time, Activity, Object, Appearance, Relative Context). Identify which dimensions are well-served by existing features and which represent the genuine gap our MVP must address.

---

## Scoring Key

| Score | Meaning |
|-------|---------|
| STRONG | Feature directly addresses this dimension; high user success rate |
| PARTIAL | Feature partially helps but has significant limitations |
| WEAK | Feature exists but rarely helps in practice |
| GAP | No existing feature addresses this dimension |

---

## Dimension-by-Feature Matrix

| Memory Dimension | Face Grouping | Places Map | Date Search | Object Labels | OCR/Text | Ask Photos | Albums | Memories |
|-----------------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **People** | STRONG | - | - | PARTIAL | WEAK | PARTIAL | PARTIAL | PARTIAL |
| **Place** | - | STRONG | - | PARTIAL | PARTIAL | PARTIAL | PARTIAL | PARTIAL |
| **Time (exact)** | - | - | STRONG | - | - | PARTIAL | WEAK | PARTIAL |
| **Time (relative)** | - | - | WEAK | - | - | PARTIAL | - | WEAK |
| **Activity** | - | - | - | PARTIAL | - | PARTIAL | WEAK | WEAK |
| **Object / Subject** | - | - | - | PARTIAL | PARTIAL | PARTIAL | - | - |
| **Appearance / Mood** | - | - | - | WEAK | - | WEAK | - | - |
| **Relative Context** | - | - | - | - | - | WEAK | - | - |

> Update scores after hands-on testing and research review.

---

## Feature Deep-Dives

### 1. Face Grouping ("People" Feature)

**How it works:** Google Photos uses on-device ML to group photos by detected faces. Users can name face clusters.

**Strengths:**
- Excellent when user remembers a specific named person
- Works across thousands of photos silently in the background
- Handles face changes over time reasonably well

**Limitations:**
- Fails when face is obscured, turned away, or in low light
- Does not handle "my college friends" (group of unnamed people)
- No way to query by relationship ("photos with family members")
- Fails for very old or low-resolution photos

**Gap Score for Memory Dimension "People":** STRONG for named individuals; WEAK for unnamed groups

---

### 2. Places Map

**How it works:** Uses GPS EXIF data to place photos on a map; clusters into named locations.

**Strengths:**
- Works well for geotagged photos with clear GPS coordinates
- Shows photos on a world map; browsable by location

**Limitations:**
- Completely fails for photos taken without GPS (indoor, airplane mode, old phones)
- No GPS = no place, regardless of visual content
- Cannot infer location from visual cues (e.g., Eiffel Tower in background)
- Cannot handle vague descriptions ("a small cafe", "the beach near our hotel")

**Gap Score for Memory Dimension "Place":** STRONG when GPS available; COMPLETE GAP without GPS

---

### 3. Date/Time Search

**How it works:** Allows filtering by specific dates, months, years, or date ranges.

**Strengths:**
- Excellent precision when user knows exact date or date range
- Integrated into search with calendar picker

**Limitations:**
- Requires user to know the date — which is exactly what they often cannot remember
- Cannot handle relative time ("last summer", "around my birthday", "a few years ago")
- No semantic time understanding
- Cannot infer time from visual cues (seasonal clothing, holiday decorations)

**Gap Score for Memory Dimension "Time":** STRONG when user knows date; COMPLETE GAP for relative/vague time

---

### 4. Object and Scene Labels

**How it works:** Vision AI automatically labels scene types, objects, and activities in photos.

**Strengths:**
- Enables searches like "beach", "dog", "birthday cake", "sunset"
- Works without GPS or face recognition
- Covers a wide range of common objects and scenes

**Limitations:**
- Labels are coarse (cannot distinguish "the small red cafe after the beach" from any cafe)
- Cannot handle compound scenes ("beach + eating + evening")
- Label coverage is uneven; unusual objects or contexts may not be labelled
- Does not understand the emotional or contextual significance of a scene

**Gap Score for Memory Dimension "Activity" and "Object":** PARTIAL — covers common cases, misses nuance

---

### 5. Ask Photos (Natural Language)

**How it works:** LLM-powered conversational interface that understands natural language queries over the photo library.

**Strengths:**
- Understands natural language descriptions
- Can combine multiple dimensions: "photos of me with John at the beach"
- Handles some relative time: "last summer"

**Limitations (critical for our project):**
- Single-turn: does not conduct a multi-turn dialogue to elicit missing memory details
- Cannot ask the user clarifying questions
- Does not track the user's retrieval journey or help when first attempt fails
- Does not surface confidence levels or explain why a photo was returned
- Relies on existing metadata/labels; cannot reason about visual content not in labels
- Cannot handle "the photo from the trip where we stopped at a small cafe" when cafe is not labelled
- Unknown performance on vague, incomplete, or emotionally-cued descriptions

**Gap Score (critical assessment):** PARTIAL for well-described queries; COMPLETE GAP for multi-turn, memory-based, incomplete-information retrieval

---

### 6. Albums

**How it works:** User-created or auto-generated collections of photos.

**Strengths:**
- Useful when user remembers the album name or event
- Shared albums are browsable

**Limitations:**
- Requires user to have created or named an album at the time
- Most photos are not in albums; casual photos are unorganised
- Does not help with "I don't know which album it would be in"

**Gap Score:** PARTIAL for organised libraries; WEAK for typical unorganised libraries

---

## Consolidated Gap Table

| Memory Dimension | Best Existing Feature | Coverage | Our MVP Adds |
|-----------------|----------------------|----------|--------------|
| People (named) | Face Grouping | STRONG | Multi-turn dialogue when user is unsure of name |
| People (unnamed/group) | - | GAP | "Who else was there?" clarification loop |
| Place (GPS-tagged) | Places Map | STRONG | Fallback when GPS missing |
| Place (vague/no GPS) | Object Labels | WEAK | Semantic "beach", "cafe" + scene matching |
| Time (exact date) | Date Search | STRONG | Widened time window inference |
| Time (relative/vague) | Ask Photos | WEAK | "Last summer" -> date range normalisation |
| Activity | Object Labels | PARTIAL | Activity scene matching + clarifying questions |
| Object | Object Labels + OCR | PARTIAL | BGE-Visualized semantic similarity |
| Appearance / Mood | - | GAP | BGE-Visualized colour/mood embedding |
| Relative Context | - | GAP | Conversational context tracking across turns |

---

## Our MVP Positioning

### What We Do NOT Duplicate
- Face grouping (existing, strong)
- GPS-based place detection (existing, strong)
- Exact date search (existing, strong)
- Basic object label search (existing, adequate)

### What We Address That Google Photos Does Not
1. **Vague or relative time** — "last summer", "a few years ago"
2. **Place without GPS** — inferring location from visual content
3. **Multi-turn memory elicitation** — asking follow-up questions when user's memory is incomplete
4. **Compound scene matching** — "beach + cafe + evening" as a combined query
5. **Retrieval journey support** — helping users change strategy when first attempt fails
6. **Appearance/mood matching** — "the golden hour photo", "when we were all laughing"
7. **Relative context** — "the photo after the market visit"
8. **Confidence transparency** — explaining why a photo was retrieved

---

## Conclusion

> Fill in after completing this analysis and the secondary research.

The most significant gap in Google Photos is:

The specific scenario our MVP should target:

---

*Feeds into: [validated-problem-statement.md](./validated-problem-statement.md)*
*Phase 0 tracker: [implementation-plan.md](../implementation-plan.md)*
