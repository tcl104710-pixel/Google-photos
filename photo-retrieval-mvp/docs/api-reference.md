# Antigravity Photos - REST API Reference

The Antigravity Photos API enables conversational retrieval of Google Photos using vague, multi-dimensional queries.

Base URL: `http://localhost:8000`

---

## Authentication

### `GET /auth/google`
Initiates the OAuth 2.0 flow for Google Photos.
- **Returns**: HTTP 302 Redirect to Google's OAuth consent screen.

### `GET /auth/callback`
Handles the OAuth redirect from Google, exchanges the code for access tokens, and initiates background library syncing.
- **Query Parameters**:
  - `code` (string): The authorization code from Google.
- **Returns**: HTTP 302 Redirect to frontend `/?auth=success`.

---

## User & Library State

### `GET /user/sync-status`
Returns the current progress of the background photo library indexer.
- **Response**:
  ```json
  {
    "total_photos": 1500,
    "indexed_photos": 1200,
    "sync_in_progress": true
  }
  ```

---

## Conversational Retrieval Sessions

### `POST /session/start`
Starts a new retrieval session and provisions memory context.
- **Response**:
  ```json
  {
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }
  ```

### `POST /session/{session_id}/message`
Submits a user description/memory, updates the context, and returns retrieval candidates and potentially an AI clarifying question.
- **Request Body**:
  ```json
  {
    "text": "It was at a beach, and someone was wearing a red hat."
  }
  ```
- **Response**:
  ```json
  {
    "response_text": "Do you remember if it was during the day or evening?",
    "candidates": [
      {
        "cluster_id": "cluster_abc",
        "representative": {
          "photo_id": "...",
          "base_url": "...",
          "confidence_label": "Possible match",
          "matched_dimensions": [{"dimension": "Scene", "value": "beach"}]
        }
      }
    ],
    "context_snapshot": {
      "places": [{"label": "beach"}],
      "objects": ["red hat"],
      "confidence": {"semantic": 0.8}
    }
  }
  ```

### `POST /session/{session_id}/feedback`
Provides positive or negative feedback on a specific candidate photo to re-rank the remaining candidates.
- **Request Body**:
  ```json
  {
    "photo_id": "abc123xyz",
    "feedback": "warmer" // Options: "yes", "no", "warmer"
  }
  ```
- **Response**:
  Returns the updated list of `candidates` and the adjusted `context_snapshot`.

### `POST /session/{session_id}/end`
Ends the session explicitly, logging the outcome as abandoned.
- **Response**:
  ```json
  {
    "status": "ended"
  }
  ```
