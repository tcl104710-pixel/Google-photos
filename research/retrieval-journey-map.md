# Retrieval Journey Map
## Phase 0.3 — Visualised User Journey with Breakdown Points

**Project:** AI-Native Google Photos Memory-Based Retrieval
**Timeline:** Week 3-4 (derived from interviews)
**Status:** [ ] Draft  [ ] Validated  [ ] Final

---

## What Is a Retrieval Journey?

A retrieval journey is the complete sequence of mental and physical steps a user takes from the moment they want to find a photo to the moment they either find it or give up. Understanding this journey reveals exactly where our MVP must intervene.

---

## Composite Journey Map

This map represents the most common pattern observed across all interview participants. It is a composite — individual participants may deviate.

```
TRIGGER
User wants to find a specific photo from memory
        |
        v
PHASE 1: MEMORY RECALL (Internal)
User tries to remember details about the photo
  - What comes to mind first? (people, place, activity, time)
  - What is vague or missing?
  - How confident are they?
        |
        | [Memory is partial — some details vivid, some vague]
        v
PHASE 2: STRATEGY SELECTION (Decision)
User decides how to search based on what they remember
  - "I remember it was around Diwali" -> try date filter
  - "I remember it was at a beach" -> try keyword "beach"
  - "My friend Priya was there" -> try People filter
        |
        v
PHASE 3: FIRST SEARCH ATTEMPT
User executes their chosen strategy in Google Photos
        |
        |----[SUCCESS: photo found]---> DONE (rare on first try for hard cases)
        |
        | [FAILURE: too many results / no results / wrong results]
        v
PHASE 4: STRATEGY REVISION (Decision under frustration)
User diagnoses why search failed and decides next move
  - "Let me try a different keyword"
  - "Maybe I can narrow by year"
  - "Let me check the Places view"
  Options:
  A -> Try different keyword   (most common first pivot)
  B -> Add a date range filter
  C -> Switch to People view
  D -> Browse chronologically from estimated date
  E -> Check albums
  F -> Try Ask Photos
        |
        v
PHASE 5: SECOND (and further) SEARCH ATTEMPTS
User iterates through strategies
  - Each failed attempt increases frustration
  - Mental model of "where the photo might be" shifts
  - Strategies become more exploratory and less targeted
        |
        |----[SUCCESS: photo found during iteration]---> DONE
        |
        | [All strategies exhausted OR frustration threshold reached]
        v
PHASE 6: WORKAROUNDS (Outside Google Photos)
User leaves Google Photos entirely:
  - Check WhatsApp / iMessage (was it shared?)
  - Ask the other people in the photo to send it
  - Look at the calendar to find the date, then come back
  - Check email (was it emailed?)
        |
        |----[Success via workaround]---> Photo found externally
        |
        | [Workaround also fails]
        v
PHASE 7: ABANDONMENT or ACCEPTANCE
User gives up
  - "I'll look for it another day"
  - "It must not be in Google Photos"
  - "I'll just do without it"
        |
        v
DONE (no photo retrieved)
```

---

## Detailed Phase Analysis

### Phase 1: Memory Recall

**What users do:**
- Think aloud about what they remember
- Often start with the most vivid memory (usually people or activity)
- Realise they are missing key details (usually date or place name)

**Observed patterns:**
- Users with vivid people memory -> immediately go to People filter
- Users with vivid activity memory -> immediately go to keyword search
- Users with only vague time memory -> feel stuck before even starting

**Breakdown risk:** LOW — this is internal; users are not yet frustrated
**Our MVP opportunity:** This is where the Memory Elicitation Engine operates. By asking the right questions, we can surface memory signals the user has but has not yet articulated.

---

### Phase 2: Strategy Selection

**What users do:**
- Map their strongest memory signal to the closest Google Photos feature
- Choose the feature they are most familiar with

**Observed patterns:**
- Most users default to keyword search regardless of memory signal type
- Date filter is used only when user is fairly confident about the date
- People filter used when a specific named person is clearly remembered
- Ask Photos rarely used as first strategy (low awareness or low trust)

**Breakdown risk:** MEDIUM — users often select a suboptimal strategy for their memory signal
**Our MVP opportunity:** The Query Synthesis Layer selects the optimal retrieval strategy based on available signals, not user familiarity with features.

---

### Phase 3: First Search Attempt

**What users do:**
- Execute their chosen strategy
- Evaluate the results (too many, none, or wrong)

**Common failure modes:**
- Keyword returns 500+ photos (e.g., "beach", "birthday")
- Date filter returns the wrong results (estimated date is wrong)
- People filter misidentifies or misses the right person
- Ask Photos returns unrelated photos with no explanation

**Breakdown risk:** HIGH — this is the most common point of failure
**Our MVP opportunity:** Our staged retrieval (Stage 1 hard filter + Stage 2 re-ranking + Stage 3 clustering) replaces the blunt single-feature approach.

---

### Phase 4: Strategy Revision

**What users do:**
- Diagnose why the search failed
- Form a hypothesis about what to try next

**Observed patterns:**
- Very few users have a systematic approach; most try things intuitively
- Keyword variation is most common pivot ("beach" -> "ocean", "sea")
- Many users do not know about Ask Photos or do not trust it
- Users rarely combine multiple filters simultaneously

**Breakdown risk:** HIGH — without guidance, users often pick equally ineffective strategies
**Our MVP opportunity:** The Feedback Module + Clarifying Question Generator actively guides the user's next move instead of leaving them to guess.

---

### Phase 5: Further Attempts

**What users do:**
- Iterate, with declining confidence and rising frustration
- Time investment starts to feel disproportionate

**Observed patterns:**
- Most users give up after 3-5 failed attempts
- Some users resort to chronological scrolling (very slow, low success)
- Emotional state: frustration, self-blame ("I should have organised my photos better")

**Breakdown risk:** VERY HIGH — abandonment is most likely here
**Our MVP opportunity:** The session feedback loop prevents the user from getting stuck in failing patterns.

---

### Phase 6: Workarounds

**What users do:**
- Leave Google Photos and search other systems
- Context reconstruction (check calendar, check messages for date clues)
- Social retrieval (ask other people in the photo)

**Observed patterns:**
- WhatsApp history is the most common workaround source
- Calendar lookup to find the date, then return to Google Photos, is common
- Asking other people in the photo to share it is effective but slow

**Breakdown risk:** MEDIUM — workarounds sometimes work but require significant effort
**Our MVP opportunity:** Our system replicates the "context reconstruction" workaround inside the product — asking the user clarifying questions to reconstruct date, place, and people context without leaving Google Photos.

---

### Phase 7: Abandonment

**What users do:**
- Accept that the photo cannot be found (for now)
- Express mild distress, especially if the photo had emotional significance

**Abandonment triggers:**
- Time spent exceeds perceived value of finding the photo
- All known strategies exhausted
- Belief that the photo is simply not in the library

**Breakdown risk:** TERMINAL — once abandoned, users rarely return to try again
**Our MVP opportunity:** A >60% retrieval success rate target directly attacks abandonment.

---

## Breakdown Point Heat Map

```
Phase 1: Memory Recall          [##.....] Low breakdown risk
Phase 2: Strategy Selection     [####...] Medium breakdown risk
Phase 3: First Search Attempt   [#######] HIGH breakdown risk
Phase 4: Strategy Revision      [######.] HIGH breakdown risk
Phase 5: Further Attempts       [#######] VERY HIGH breakdown risk
Phase 6: Workarounds            [####...] Medium breakdown risk
Phase 7: Abandonment            [#######] Terminal
```

---

## Emotional Arc

```
START        PHASE 1     PHASE 2     PHASE 3     PHASE 4     PHASE 5     END
             "What       "I'll try   "Hmm, that  "Let me     "This is    "I give up"
             do I        keyword     did not     try         taking
             remember?"  search"     work..."    something   forever..."
                                                 else"
MOTIVATION:  HIGH        HIGH        MEDIUM      MEDIUM-LOW  LOW         NONE
FRUSTRATION: NONE        LOW         MEDIUM      HIGH        VERY HIGH   PEAK
```

---

## MVP Intervention Points

| Journey Phase | Current Experience (No MVP) | MVP Experience |
|--------------|----------------------------|----------------|
| Phase 1 | User struggles to recall alone | MVP asks targeted questions to surface latent memories |
| Phase 2 | User guesses a search strategy | MVP selects optimal retrieval strategy from available signals |
| Phase 3 | Single-feature search returns too many or zero results | MVP runs multi-signal retrieval with ranked, clustered results |
| Phase 4 | User guesses next strategy | MVP interprets "not this" feedback and shifts strategy intelligently |
| Phase 5 | User exhausts strategies; frustration peaks | MVP's feedback loop keeps refining; prevents total dead-ends |
| Phase 6 | User leaves the app for workarounds | MVP simulates context reconstruction inside the conversation |
| Phase 7 | Abandonment | MVP's success rate target aims to prevent this outcome |

---

## Key Insight for Architecture

> Fill in after interviews are complete.

The most critical breakdown point across all participants was:

The single most effective intervention our system can make:

The memory dimension that, if elicited, would most often unblock a stuck retrieval:

---

*Built from: [interview-findings.md](./interview-findings.md)*
*Feeds into: [validated-problem-statement.md](./validated-problem-statement.md)*
