# MVP Use Case Definition
## Phase 0.4 — The Exact Scenario the MVP Will Target

**Project:** AI-Native Google Photos Memory-Based Retrieval
**Timeline:** Week 4
**Status:** [ ] Draft  [ ] Team Review  [ ] Final / Approved

---

## Instructions

This document defines the EXACT use case the MVP will be built for. It must be:
- Specific (not "photo retrieval" but "retrieval of a specific photo from a one-off social event using vague time and place memory")
- Evidence-backed (every choice justified by research findings)
- Scoped (what is in MVP vs. future)
- Agreed upon by the team before Phase 1 engineering begins

Complete this AFTER validated-problem-statement.md is approved.

---

## 1. The Primary User

**Who they are:**
> [Fill in after interview analysis]

**Demographic profile:**
- Age range:
- Device:
- Library size:
- Usage pattern:

**Their primary motivation for wanting the photo:**
> [What do people typically want old photos for? Evidence from interviews.]

**Their current pain:**
> [1-2 sentence description of their current painful experience when searching fails]

---

## 2. The Trigger Scenario

> Describe the exact moment when the user turns to our MVP. What just happened? What have they already tried?

**Scenario:**

A user wants to find [type of photo]. They remember [memory signals available]. They have already tried [previous Google Photos searches / strategies that failed]. They are now trying our AI-native retrieval system for the first time.

[FILL IN after research]

---

## 3. The Target Photo Characteristics

Based on the most common retrieval failure type from our taxonomy:

| Characteristic | Value | Evidence Source |
|---------------|-------|-----------------|
| Photo type | | |
| Approx library age of photo | | |
| Typical event type | | |
| GPS tag present? | | |
| Faces tagged in Google Photos? | | |
| In an album? | | |
| Number of similar photos in library | | |

---

## 4. Available Memory Signals at Session Start

These are the signals the user WILL have when they come to our system. MVP must work with these and no more.

| Memory Dimension | Availability | Typical Specificity | Confidence (user-rated) |
|-----------------|-------------|---------------------|------------------------|
| People | | | |
| Place | | | |
| Time (period) | | | |
| Activity | | | |
| Object / subject | | | |
| Appearance / mood | | | |
| Relative context | | | |

**The key insight:** The MVP must be able to retrieve the photo when only [N] of these dimensions are available, and when the available dimensions are [typical specificity level].

---

## 5. The Ideal MVP Interaction Flow

> Describe the ideal step-by-step interaction for the primary use case.

**Step 1 — User opens the system and types their memory description:**
> Example: "I'm looking for a photo from a Goa trip where we stopped at a small cafe after the beach. It was probably 2-3 years ago."

**Step 2 — System extracts memory fragments and responds:**
> Example: The system identifies: place=Goa (medium confidence), activity=cafe+beach (high confidence), time=2-3 years ago (low specificity). It asks: "Was this a solo trip or were you with others?"

**Step 3 — User provides clarifying information:**
> Example: "With my college friends, about 4-5 of us."

**Step 4 — System narrows candidates and shows results:**
> Example: Shows top 6 event clusters from Goa-tagged photos or beach+food scene matches from 2-3 years ago, grouped by trip.

**Step 5 — User confirms or rejects:**
> Example: User says "Getting warmer" on one cluster; system narrows further.

**Step 6 — User finds the photo:**
> Example: Within 3-4 turns, user identifies the correct photo.

---

## 6. MVP Success Criteria (Use Case Specific)

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Retrieval success rate | >60% | User confirms finding the photo |
| Session length | <5 turns | Count of message exchanges |
| Time to retrieval | <2 minutes | Wall clock from first message to success |
| Abandonment rate | <25% | Sessions ended without confirmation |

---

## 7. What Is In Scope for MVP

| Feature | In Scope? | Rationale |
|---------|-----------|-----------|
| Conversational memory input | YES | Core of MVP |
| Multi-turn clarifying dialogue | YES | Needed for incomplete memory |
| BGE-M3 text embedding | YES | Core semantic search |
| BGE-Visualized image embedding | YES | Core image matching |
| Google Photos API integration | YES | Library access required |
| Multi-signal re-ranking | YES | Core retrieval quality |
| In-session feedback loop | YES | Core of retrieval refinement |
| Result explanation chips | YES | Trust and transparency |
| Voice input | NO | Post-MVP |
| Cross-session personalisation | NO | Post-MVP |
| Multi-library support | NO | Post-MVP |
| Proactive memory surfacing | NO | Post-MVP |
| Longitudinal learning | NO | Post-MVP |

---

## 8. What the MVP Explicitly Does NOT Do

> This list prevents scope creep during engineering phases.

1. The MVP does not retrieve photos that are not in the user's Google Photos library
2. The MVP does not replace Ask Photos or any existing Google Photos feature
3. The MVP does not learn across sessions (each session starts fresh)
4. The MVP does not require the user to provide a specific date, location, or person name — it works with vague, partial information
5. The MVP does not work on photos from iCloud, Samsung Gallery, or other libraries
6. The MVP does not generate or create images — it only retrieves existing ones

---

## 9. Definition of Done for Phase 0

Phase 0 is complete when:

- [ ] All 8 research questions have evidence-backed answers (documented in validated-problem-statement.md)
- [ ] The validated problem statement has been reviewed and approved by the team
- [ ] This MVP use case document is finalised and agreed upon
- [ ] The research findings have been checked against architecture.md for any assumption updates needed
- [ ] Any required architecture.md updates have been made
- [ ] The team is aligned that no further research is needed before Phase 1 begins

---

## 10. Team Sign-Off

| Team Member | Role | Comment | Date |
|-------------|------|---------|------|
| | | | |
| | | | |
| | | | |

**Approved to proceed to Phase 1:** [ ] YES  [ ] NO — additional research needed

---

*Approved use case feeds into Phase 1: [implementation-plan.md Phase 1](../implementation-plan.md)*
*May require updates to: [architecture.md](../architecture.md)*
