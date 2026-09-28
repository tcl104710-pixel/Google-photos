# Public Data Analysis
## Phase 0.2 — User Conversations and Reviews Coding

**Project:** AI-Native Google Photos Memory-Based Retrieval
**Timeline:** Week 2-3
**Status:** [ ] In Progress  [ ] Complete

---

## Data Sources

### Sources to Collect From

| Source | URL / Search Query | Collection Method | Volume Target |
|--------|--------------------|-------------------|---------------|
| Reddit r/GooglePhotos | reddit.com/r/GooglePhotos — search "can't find", "lost photo", "search" | Manual + PRAW API | 100+ posts |
| Reddit r/androidquestions | Similar search queries | Manual | 30+ posts |
| Google Play Store reviews | "Google Photos" app — filter 1-2 star reviews mentioning search | Manual export | 50+ reviews |
| Apple App Store reviews | Same app | Manual | 50+ reviews |
| Twitter/X | "google photos can't find" "lost photo google photos" | Twitter API or manual | 30+ posts |
| Tech forums (Reddit, XDA) | Targeted search for photo retrieval complaints | Manual | 20+ threads |

### Collection Log

| Date | Source | Query Used | Items Collected | Notes |
|------|--------|-----------|----------------|-------|
| | | | | |
| | | | | |

---

## Coding Scheme

### Dimension A: Type of Retrieval Problem

Code each item with ONE primary retrieval problem type:

| Code | Label | Definition | Example Quote |
|------|-------|-----------|---------------|
| A1 | No date memory | User cannot recall when the photo was taken | "I have no idea when it was, sometime last year?" |
| A2 | No location memory | User cannot recall where it was taken | "I don't remember the exact place, it was some beach" |
| A3 | No album/folder | User does not know where they saved it | "It's not in any album, just floating somewhere" |
| A4 | Vague person recall | User knows people were in it but cannot name/find them | "It was with some friends but I don't have them tagged" |
| A5 | Search term mismatch | User knows what they want but cannot find the right search word | "I searched beach but nothing came up" |
| A6 | Too many results | Search returns thousands; impossible to browse | "I searched 'birthday' and got 3000 results" |
| A7 | Wrong person match | Face grouping misidentifies or mixes up faces | "It keeps putting my sister in my mom's album" |
| A8 | Object not labelled | The specific object is not a recognised label | "I searched for 'small red cafe' and got nothing" |
| A9 | Memory mismatch | User's memory of the photo is wrong | "I thought it was summer but it might have been spring" |
| A10 | Other | Does not fit above categories | |

### Dimension B: Search Strategy Used

| Code | Label | Definition |
|------|-------|-----------|
| B1 | Keyword search | Typed a word/phrase in the search bar |
| B2 | Date/calendar scroll | Scrolled through photos by date |
| B3 | Album browsing | Looked in albums |
| B4 | People filter | Used the people feature |
| B5 | Places filter | Used the map/places feature |
| B6 | Ask Photos | Used the natural language query feature |
| B7 | Scroll from beginning | Scrolled all photos from a starting point |
| B8 | Multiple strategies | Used more than one strategy |
| B9 | No strategy found | Gave up without finding the photo |

### Dimension C: Workaround Attempted

| Code | Label | Definition |
|------|-------|-----------|
| C1 | Asked someone else | Asked another person who might remember or have the photo |
| C2 | Checked other apps | Looked in WhatsApp, iCloud, camera roll, etc. |
| C3 | Checked messages | Searched through message history where photo may have been shared |
| C4 | Context reconstruction | Looked at calendar, messages to infer the date |
| C5 | Accepted failure | Gave up on finding the photo |
| C6 | Keyword variation | Tried multiple different search terms |
| C7 | AI/assistant | Asked an AI tool to help find it |
| C8 | None attempted | No workaround tried yet |

### Dimension D: Emotional Tone

| Code | Label |
|------|-------|
| D1 | Frustrated |
| D2 | Resigned/accepting |
| D3 | Confused |
| D4 | Neutral/informational |
| D5 | Requesting help |

---

## Data Entry Table

| ID | Source | Date | Primary Problem (A-code) | Search Strategy (B-code) | Workaround (C-code) | Emotion (D-code) | Raw Quote | Notes |
|----|--------|------|--------------------------|--------------------------|---------------------|-----------------|-----------|-------|
| 001 | | | | | | | | |
| 002 | | | | | | | | |
| 003 | | | | | | | | |
| 004 | | | | | | | | |
| 005 | | | | | | | | |

> Add rows as you collect data. Aim for minimum 100 coded items before analysis.

---

## Frequency Analysis

> Fill in after coding is complete.

### Problem Type Frequency (Dimension A)

| Code | Label | Count | Percentage |
|------|-------|-------|-----------|
| A1 | No date memory | | |
| A2 | No location memory | | |
| A3 | No album/folder | | |
| A4 | Vague person recall | | |
| A5 | Search term mismatch | | |
| A6 | Too many results | | |
| A7 | Wrong person match | | |
| A8 | Object not labelled | | |
| A9 | Memory mismatch | | |
| A10 | Other | | |
| **Total** | | | |

### Search Strategy Frequency (Dimension B)

| Code | Label | Count | Percentage |
|------|-------|-------|-----------|
| B1 | Keyword search | | |
| B2 | Date/calendar scroll | | |
| B3 | Album browsing | | |
| B4 | People filter | | |
| B5 | Places filter | | |
| B6 | Ask Photos | | |
| B7 | Scroll from beginning | | |
| B8 | Multiple strategies | | |
| B9 | No strategy found | | |

### Workaround Frequency (Dimension C)

| Code | Label | Count | Percentage |
|------|-------|-------|-----------|
| C1 | Asked someone else | | |
| C2 | Checked other apps | | |
| C3 | Checked messages | | |
| C4 | Context reconstruction | | |
| C5 | Accepted failure | | |
| C6 | Keyword variation | | |
| C7 | AI/assistant | | |
| C8 | None attempted | | |

---

## Thematic Analysis

### Theme 1: [Name]
> Description of the theme, frequency, representative quotes

**Supporting quotes:**
- "..."
- "..."

**Implication for MVP:**

---

### Theme 2: [Name]
> Description of the theme, frequency, representative quotes

**Supporting quotes:**
- "..."
- "..."

**Implication for MVP:**

---

### Theme 3: [Name]

> Add as many themes as emerge from the data.

---

## Mapping to 8 Research Questions

| Research Question | Key Finding from Public Data | Supporting Evidence (item IDs) |
|-------------------|-----------------------------|-------------------------------|
| 1. What types of photos are hard to retrieve? | | |
| 2. What do users naturally remember? | | |
| 3. What do they typically forget? | | |
| 4. How do they describe/search? | | |
| 5. How do they change strategy on failure? | | |
| 6. Where does retrieval break down? | | |
| 7. What workarounds do users use? | | |
| 8. What gaps remain in Google Photos? | | |

---

## Saturation Check

> Track whether new data items are adding new codes or repeating existing ones.

| After N items | New codes introduced | Saturation reached? |
|--------------|---------------------|---------------------|
| 20 | | |
| 40 | | |
| 60 | | |
| 80 | | |
| 100 | | |

Data collection can stop when no new codes emerge for 20 consecutive items.

---

*Next: [retrieval-failure-taxonomy.md](./retrieval-failure-taxonomy.md)*
*Phase 0 tracker: [implementation-plan.md](../implementation-plan.md)*
