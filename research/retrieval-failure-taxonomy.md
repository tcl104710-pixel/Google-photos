# Retrieval Failure Taxonomy
## Phase 0.2 — Types of Photos Hard to Find and Why

**Project:** AI-Native Google Photos Memory-Based Retrieval
**Timeline:** Week 2-3 (derived from public data analysis)
**Status:** [ ] Draft  [ ] Validated  [ ] Final

---

## Purpose

A systematic taxonomy of photo retrieval failures. Built from public data analysis and refined through user interviews. Used to:
1. Confirm the MVP's target problem is real and prevalent
2. Inform which memory dimensions the system must handle
3. Guide edge case handling in the engineering phases

---

## Taxonomy Structure

Each failure type is characterised by:
- **What the user is trying to find** (photo category)
- **What they remember** (available memory signals)
- **What they do NOT remember** (missing signals)
- **Why existing search fails**
- **Prevalence** (from public data coding — fill after analysis)
- **MVP relevance** (does our system address this?)

---

## Failure Type 1: The Orphaned Event Photo

**Description:** A photo from a one-off social event (party, trip, dinner) that was never organised into an album.

**User typically remembers:**
- The event type ("my friend's birthday", "that Goa trip")
- Roughly who was there
- A general time period ("last year", "before I moved")

**User typically does NOT remember:**
- The exact date
- The precise location with GPS accuracy
- The album it might be in (because it is not in one)

**Why Google Photos search fails:**
- Keyword "birthday" returns hundreds of results across years
- Date picker requires knowing the year and month
- Not in any album; face grouping may work if person is tagged

**Prevalence from public data:** __ / __ items coded (fill after analysis)

**MVP relevance:** HIGH — primary target scenario

---

## Failure Type 2: The Anonymous Place Photo

**Description:** A photo taken at a specific but hard-to-name location (a small restaurant, a viewpoint on a road trip, a local market).

**User typically remembers:**
- The visual appearance of the place ("small cafe", "colourful walls", "waterfall")
- What activity was happening ("we were eating", "the kids were playing")
- The general geography ("somewhere in Coorg", "near our hotel")

**User typically does NOT remember:**
- The exact place name
- GPS coordinates (or the phone may not have had GPS at the time)
- Any searchable text visible in the photo

**Why Google Photos search fails:**
- No GPS tag means no Places entry
- Object labels may say "restaurant" but cannot narrow to the specific place
- "Colourful walls" is not a searchable label

**Prevalence from public data:** __ / __ items coded

**MVP relevance:** HIGH — semantic search over visual content is our core differentiator

---

## Failure Type 3: The Temporal Blur Photo

**Description:** A photo from a specific period that the user cannot date precisely — they know "it was around X" but not the exact date.

**User typically remembers:**
- A relative time reference ("around Diwali", "when I was in college", "right after the wedding")
- The season or approximate year
- Other events nearby in time

**User typically does NOT remember:**
- The specific date or even month
- Whether it was taken on their phone or someone else's

**Why Google Photos search fails:**
- Date picker requires a specific date or narrow range
- Ask Photos can handle some relative queries but not well for compound relative time

**Prevalence from public data:** __ / __ items coded

**MVP relevance:** HIGH — relative time normalisation is a key feature

---

## Failure Type 4: The Group Without Names Photo

**Description:** A photo with multiple people, some of whom are not named/tagged in Google Photos.

**User typically remembers:**
- That specific people were in it (by relationship: "my college roommates", "my in-laws")
- What the group was doing
- The general setting

**User typically does NOT remember:**
- Exact names of everyone present
- Whether all faces are tagged in the system

**Why Google Photos search fails:**
- Face grouping only works for individually identified faces
- No way to search by relationship label ("photos with family")
- "My college roommates" is not a queryable concept

**Prevalence from public data:** __ / __ items coded

**MVP relevance:** MEDIUM — clarifying questions can extract more specific people signals

---

## Failure Type 5: The Needle in a Haystack Photo

**Description:** A photo that is visually very generic — a selfie, a landscape, a sky shot — that looks like thousands of other photos in the library.

**User typically remembers:**
- What is in the photo (but it is not distinctive)
- General context ("it was during my trip")

**User typically does NOT remember:**
- Any distinguishing feature that separates this photo from similar ones

**Why Google Photos search fails:**
- Keyword search returns too many results
- Semantic search cannot distinguish between 500 similar beach sunsets
- No unique signal to retrieve specifically this photo

**Prevalence from public data:** __ / __ items coded

**MVP relevance:** MEDIUM — clustering and event-based grouping may help; some cases may be truly unresolvable

---

## Failure Type 6: The Cross-Device Photo

**Description:** A photo that may be on a different device, was taken by someone else, or was received via WhatsApp/message and saved to Google Photos.

**User typically remembers:**
- The content of the photo
- That it exists somewhere

**User typically does NOT remember:**
- Which device/account it is associated with
- Whether it was ever saved to Google Photos at all

**Why Google Photos search fails:**
- Photo may simply not be in the library
- If it is in the library, metadata may show receive date rather than capture date

**Prevalence from public data:** __ / __ items coded

**MVP relevance:** LOW for MVP (out of scope — MVP assumes photo IS in the library per problem statement)

---

## Failure Type 7: The Emotionally Indexed Photo

**Description:** The user remembers the photo by its emotional significance or narrative context, not by visual content or metadata.

**User typically remembers:**
- Why the photo was meaningful ("the last photo before she passed away", "the day I got the job")
- The feeling of the moment

**User typically does NOT remember:**
- Visual content, date, place, or any standard metadata

**Why Google Photos search fails:**
- No feature addresses emotional or narrative context
- No AI-generated emotional labelling

**Prevalence from public data:** __ / __ items coded

**MVP relevance:** MEDIUM — our memory elicitation can use emotional context as a probe to extract other dimensions (e.g., "when did that happen?", "where were you?")

---

## Failure Type 8: The Search Strategy Exhaustion

**Description:** The user has tried every available search method — keywords, dates, people, places, albums — and still cannot find the photo.

**User typically remembers:**
- All standard searchable metadata
- But the photo does not surface

**Why this happens:**
- Photo metadata is missing (no GPS, no EXIF date, no faces tagged)
- Photo is not labelled with the object the user searched for
- The photo exists but indexed under unexpected metadata (e.g., wrong date due to phone sync)

**Prevalence from public data:** __ / __ items coded

**MVP relevance:** HIGH — this is the highest frustration scenario; our multi-signal retrieval and fallback strategy directly address it

---

## Taxonomy Summary Table

| Failure Type | Primary Missing Signal | Google Photos Handles? | MVP Priority |
|-------------|----------------------|----------------------|--------------|
| 1. Orphaned Event Photo | Exact date, album | Partially | HIGH |
| 2. Anonymous Place Photo | GPS, place name | No | HIGH |
| 3. Temporal Blur Photo | Exact date | Partially (Ask Photos) | HIGH |
| 4. Group Without Names | Named people | Partially | MEDIUM |
| 5. Needle in a Haystack | Distinguishing signal | No | MEDIUM |
| 6. Cross-Device Photo | Library presence | Out of scope | LOW |
| 7. Emotionally Indexed Photo | Any standard metadata | No | MEDIUM |
| 8. Search Strategy Exhaustion | Multiple signals | No | HIGH |

---

## Prevalence Summary (Fill After Analysis)

> Rank failure types by frequency in public data:

1. Most common:
2.
3.
4.
5.
6.
7.
8. Least common:

---

## Implication for MVP Target Scenario

> Based on prevalence ranking, the MVP should target:

**Primary failure type to solve:**

**Reason (evidence):**

---

*Feeds into: [validated-problem-statement.md](./validated-problem-statement.md)*
*Built from: [public-data-analysis.md](./public-data-analysis.md)*
