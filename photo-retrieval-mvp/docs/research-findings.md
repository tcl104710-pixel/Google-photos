# Phase 0 Research Findings

This document summarizes the foundational research conducted during Phase 0 of the Antigravity Photos project. This research directly influenced the product architecture and UX decisions.

## Primary Hypothesis
Users often fail to retrieve photos because they only remember fragments of the memory (e.g., "that cafe in Paris," "wearing a red jacket," "sometime last summer") and current photo search engines require exact keyword matches or rigid filtering.

## Methodology
- Scraping Reddit (`r/googlephotos`, `r/DataHoarder`, `r/ApplePhotos`) for pain points related to photo search.
- Scraping App Store & Play Store reviews for Google Photos.
- Synthesizing pain points using LLMs.

## Key Pain Points Discovered

1. **Rigid Ontology**: Google Photos search requires the user to guess the exact tags the AI assigned. If the AI tagged a "dog" but the user searches for "puppy", it often fails.
2. **Boolean Blindness**: Users want to combine dimensions (Place + Time + Object) but the UI doesn't support complex logical queries naturally.
3. **The "Tip of the Tongue" Phenomenon**: Users have fuzzy memories. They know it was "a few years ago" and "near a beach" but can't formulate a direct query.

## Solution Derived

We concluded that a **conversational interface** is the most effective solution. By using an LLM to elicit memories from the user incrementally, we can:
1. Translate fuzzy human memory into structured machine queries (Date ranges, Bounding Boxes, Vector Embeddings).
2. Ask clarifying questions ("Do you remember what time of day it was?") if the search space is still too large.
3. Use a multi-factor ranking system that weighs explicit filters against semantic vector similarity.

## Impact on Architecture
- **MemoryContext**: Instead of a simple search string, the backend maintains a stateful `MemoryContext` object that builds up as the user chats.
- **Groq Vision / BGE-M3**: We chose dense vector embeddings to capture the "vibe" and semantic content of photos that traditional tags miss.
- **Feedback Loop**: We implemented "Getting Warmer" feedback to dynamically adjust ranking weights without requiring the user to type more words.
