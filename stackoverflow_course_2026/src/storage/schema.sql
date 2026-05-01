-- ============================================================
-- Схема базы данных — PostgreSQL (Neon.tech)
-- Применяется автоматически через: python src/storage/loader.py --init
-- ============================================================

-- ------------------------------------------------------------
-- Пользователи
-- ------------------------------------------------------------
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

-- ------------------------------------------------------------
-- Вопросы
-- ------------------------------------------------------------
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
    owner_user_id       INTEGER REFERENCES users(user_id),
    closed_at           TIMESTAMP,
    last_activity_at    TIMESTAMP
);

-- ------------------------------------------------------------
-- Теги (нормализованные)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tags (
    tag_id      SERIAL PRIMARY KEY,
    tag_name    TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS question_tags (
    question_id INTEGER REFERENCES questions(question_id),
    tag_id      INTEGER REFERENCES tags(tag_id),
    PRIMARY KEY (question_id, tag_id)
);

-- ------------------------------------------------------------
-- Ответы
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS answers (
    answer_id       INTEGER PRIMARY KEY,
    question_id     INTEGER REFERENCES questions(question_id),
    created_at      TIMESTAMP NOT NULL,
    score           INTEGER DEFAULT 0,
    owner_user_id   INTEGER REFERENCES users(user_id),
    is_accepted     SMALLINT DEFAULT 0
);

-- ------------------------------------------------------------
-- Индексы
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_questions_created_at  ON questions(created_at);
CREATE INDEX IF NOT EXISTS idx_questions_score       ON questions(score);
CREATE INDEX IF NOT EXISTS idx_questions_owner       ON questions(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_answers_question_id   ON answers(question_id);
CREATE INDEX IF NOT EXISTS idx_answers_created_at    ON answers(created_at);
CREATE INDEX IF NOT EXISTS idx_question_tags_tag     ON question_tags(tag_id);
