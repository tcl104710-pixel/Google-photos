# Validated Problem Statement
## Phase 0.4 — Evidence-Backed, Specific Problem Definition

**Project:** AI-Native Google Photos Memory-Based Retrieval
**Timeline:** Week 4
**Status:** [ ] Draft  [ ] Team Review  [ ] Final / Approved

---

## Instructions

This document must be completed AFTER:
- [x] secondary-research-summary.md is complete
- [x] google-photos-gap-analysis.md is complete
- [x] public-data-analysis.md is complete (min 100 coded items)
- [x] interview-findings.md is complete (min 6 participants)
- [x] retrieval-journey-map.md is complete

It must NOT be completed by assumption before the research is done.

---

## 1. The Validated Core Problem

> Fill in after synthesising all research. State the problem in 2-3 sentences — specific enough to be testable, general enough to matter.

**Validated Problem Statement:**

[TO BE FILLED — do not fill until all research streams are complete]

---

## 2. Evidence Summary

### From Secondary Research

**Key finding that most directly informs the problem:**

**Source:**

**Confidence:** High / Medium / Low

---

**Key finding 2:**

**Source:**

**Confidence:**

---

### From Public Data Analysis

**Most common retrieval failure type (from taxonomy):**

**Frequency:** __ out of __ coded items (__ %)

**Representative user quote:**
> "..."

**Second most common:**

**Frequency:**

---

### From User Interviews

**Problem observed in N/N participants:**

**Most common breakdown point (from journey map):**

**Representative participant quote:**
> P0X: "..."

**Memory dimensions most commonly available at retrieval start:**
1.
2.
3.

**Memory dimensions most commonly MISSING:**
1.
2.
3.

---

## 3. What the Problem IS (Precise Definition)

> Write the validated problem with maximum precision. Avoid generalities.

**The specific scenario we are targeting:**

A Google Photos user with a library of [estimated size] photos is trying to find a specific photo from [type of event/situation]. They remember [specific memory signals available on average]. They do NOT remember [specific memory signals typically missing]. When they try to search in Google Photos using [their typical first strategy], they [what happens — too many results / no results / wrong results]. They then [what they typically do next]. In [X% of cases], they fail to find the photo.

[FILL IN BRACKETS after research is complete]

---

## 4. What the Problem Is NOT

> Explicitly document what we are NOT solving, to prevent scope creep.

This project does NOT address:
- Photos that are not in the user's Google Photos library
- General image search (search the internet for a photo)
- Improving Google Photos indexing quality
- Building a better search UI for users who already know what they are looking for
- Replacing Google Photos' existing Ask Photos feature
- Cross-library search (iCloud, camera roll, etc.)

---

## 5. Research Question Answers (Final)

| Research Question | Validated Answer | Primary Evidence Source |
|-------------------|-----------------|------------------------|
| 1. What types of photos are hard to retrieve? | | |
| 2. What do users naturally remember? | | |
| 3. What do they typically forget? | | |
| 4. How do they describe/search? | | |
| 5. How do they change strategy on failure? | | |
| 6. Where does retrieval break down? | | |
| 7. What workarounds do users use? | | |
| 8. What gaps remain in Google Photos? | | |

---

## 6. Architecture Assumption Validation

| Architecture Assumption | Validated? | Evidence | Action Required |
|------------------------|------------|----------|-----------------|
| People dimension has HIGH recall strength | | | |
| Time dimension has LOW recall strength | | | |
| Place dimension has MEDIUM recall strength | | | |
| Activity dimension has HIGH recall strength | | | |
| Users make on average < 5 retrieval attempts before giving up | | | |
| Ask Photos does not address multi-turn memory-based retrieval | | | |
| Semantic image-text matching fills the main retrieval gap | | | |

---

## 7. Confidence Assessment

| Research Stream | Quality | Coverage | Confidence in Findings |
|----------------|---------|----------|----------------------|
| Secondary research | | | |
| Public data analysis | | | |
| User interviews | | | |
| **Overall confidence** | | | |

**Are we confident enough to proceed to engineering?**
[ ] Yes — all 8 research questions answered with medium+ confidence
[ ] Partially — proceed with caveats noted below
[ ] No — additional research needed (describe what)

**Caveats / limitations:**

---

## 8. Team Sign-Off

| Team Member | Role | Signature | Date |
|-------------|------|-----------|------|
| | | | |
| | | | |
| | | | |

---

*Feeds directly into: [mvp-use-case.md](./mvp-use-case.md)*
*May require updates to: [architecture.md](../architecture.md)*
