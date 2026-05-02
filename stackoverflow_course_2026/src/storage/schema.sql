-- ============================================================
-- Схема базы данных — PostgreSQL (Neon.tech)
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    user_id         INTEGER PRIMARY KEY,
    display_name    TEXT,
    reputation      INTEGER DEFAULT 0,
    created_at      TIMESTAMP,
    location        TEXT,
    up_votes        INTEGER DEFAULT 0,
    down_votes      INTEGER DEFAULT 0,
    views           INTEGER DEFAULT 0,
    last_access_at  TIMESTAMP
);

CREATE TABLE IF NOT EXISTS questions (
    question_id         INTEGER PRIMARY KEY,
    title               TEXT NOT NULL,
    body                TEXT,
    tags_raw            TEXT,
    created_at          TIMESTAMP NOT NULL,
    score               INTEGER DEFAULT 0,
    view_count          INTEGER DEFAULT 0,
    answer_count        INTEGER DEFAULT 0,
    favorite_count      INTEGER DEFAULT 0,
    accepted_answer_id  INTEGER,
    owner_user_id       INTEGER,
    closed_at           TIMESTAMP,
    last_activity_at    TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tags (
    tag_id      SERIAL PRIMARY KEY,
    tag_name    TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS question_tags (
    question_id INTEGER,
    tag_id      INTEGER,
    PRIMARY KEY (question_id, tag_id)
);

CREATE TABLE IF NOT EXISTS answers (
    answer_id       INTEGER PRIMARY KEY,
    question_id     INTEGER,
    created_at      TIMESTAMP NOT NULL,
    score           INTEGER DEFAULT 0,
    owner_user_id   INTEGER,
    is_accepted     SMALLINT DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_questions_created_at  ON questions(created_at);
CREATE INDEX IF NOT EXISTS idx_questions_score       ON questions(score);
CREATE INDEX IF NOT EXISTS idx_questions_owner       ON questions(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_answers_question_id   ON answers(question_id);
CREATE INDEX IF NOT EXISTS idx_answers_created_at    ON answers(created_at);
CREATE INDEX IF NOT EXISTS idx_question_tags_tag     ON question_tags(tag_id);