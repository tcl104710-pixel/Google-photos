-- docs/db_init.sql
-- Initial PostgreSQL schema for photo-retrieval-mvp
-- Run automatically by Docker Compose on first start

-- ── Users / Auth ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              TEXT PRIMARY KEY,          -- Google OAuth sub
    email           TEXT UNIQUE NOT NULL,
    access_token    TEXT,
    refresh_token   TEXT,
    token_expires_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    library_access_revoked BOOLEAN DEFAULT FALSE
);

-- ── Photos ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS photos (
    id              TEXT PRIMARY KEY,          -- Google Photos media item ID
    user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename        TEXT,
    mime_type       TEXT,
    creation_time   TIMESTAMPTZ,
    width           INTEGER,
    height          INTEGER,
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION,
    base_url        TEXT,                     -- Expires; refreshed on demand
    base_url_expires_at TIMESTAMPTZ,
    embedding_status TEXT DEFAULT 'pending',  -- pending | done | failed | url_expired_retry_later
    description     TEXT,                     -- AI-generated caption
    synced_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_photos_user_id ON photos(user_id);
CREATE INDEX IF NOT EXISTS idx_photos_creation_time ON photos(user_id, creation_time);
CREATE INDEX IF NOT EXISTS idx_photos_embedding_status ON photos(embedding_status);

-- ── Photo People ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS photo_people (
    photo_id        TEXT NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
    person_label    TEXT NOT NULL,
    PRIMARY KEY (photo_id, person_label)
);

CREATE INDEX IF NOT EXISTS idx_photo_people_label ON photo_people(person_label);

-- ── Photo Albums ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS photo_albums (
    photo_id        TEXT NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
    album_id        TEXT NOT NULL,
    album_name      TEXT,
    PRIMARY KEY (photo_id, album_id)
);

-- ── Photo Labels (scene, object, activity) ────────────────────────────────────
CREATE TABLE IF NOT EXISTS photo_labels (
    id              SERIAL PRIMARY KEY,
    photo_id        TEXT NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
    label           TEXT NOT NULL,
    source          TEXT NOT NULL,            -- 'google_photos' | 'groq_vision' | 'clip'
    confidence      FLOAT
);

CREATE INDEX IF NOT EXISTS idx_photo_labels_photo ON photo_labels(photo_id);
CREATE INDEX IF NOT EXISTS idx_photo_labels_label ON photo_labels(label);

-- ── Sessions ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
    session_id      UUID PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    outcome         TEXT DEFAULT 'active',    -- active | found | not_found | abandoned
    turn_count      INTEGER DEFAULT 0,
    found_photo_id  TEXT,
    context_snapshot JSONB,                   -- Latest MemoryContext checkpoint
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    ended_at        TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_outcome ON sessions(outcome);

-- ── Session Events (feedback log) ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS session_events (
    id              SERIAL PRIMARY KEY,
    session_id      UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    event_type      TEXT NOT NULL,            -- 'message' | 'feedback' | 'strategy_shift'
    payload         JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_session ON session_events(session_id);

-- ── Library Sync Status ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS library_sync (
    user_id         TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    total_photos    INTEGER DEFAULT 0,
    indexed_photos  INTEGER DEFAULT 0,
    last_sync_at    TIMESTAMPTZ,
    sync_in_progress BOOLEAN DEFAULT FALSE,
    next_page_token TEXT                      -- Google Photos pagination checkpoint
);
