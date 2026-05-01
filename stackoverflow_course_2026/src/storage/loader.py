"""
loader.py — создание схемы и загрузка данных из CSV в PostgreSQL (Neon.tech)

Использование:
    python src/storage/loader.py --init   # создать таблицы
    python src/storage/loader.py --load   # загрузить CSV в БД
    python src/storage/loader.py --all    # init + load

Требует файл .env в корне проекта:
    DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require

Ожидаемые входные файлы:
    data/raw/questions.csv
    data/raw/answers.csv
    data/raw/users.csv
"""

import argparse
import os
import re
import sys
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from tqdm import tqdm

# ─── Пути ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

# ─── Подключение ─────────────────────────────────────────────────────────────
load_dotenv(ROOT / ".env")

def get_connection() -> psycopg2.extensions.connection:
    url = os.getenv("DATABASE_URL")
    if not url:
        print("❌ DATABASE_URL не найден в .env")
        sys.exit(1)
    return psycopg2.connect(url)


# ─── Инициализация схемы ─────────────────────────────────────────────────────
def init_schema(conn) -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(schema)
    conn.commit()
    print("✅ Схема БД создана")


# ─── Загрузка пользователей ──────────────────────────────────────────────────
def load_users(conn) -> None:
    path = RAW_DIR / "users.csv"
    if not path.exists():
        print(f"⚠️  {path.name} не найден — пропускаем")
        return

    df = pd.read_csv(path)
    df = df.rename(columns={
        "Id":             "user_id",
        "DisplayName":    "display_name",
        "Reputation":     "reputation",
        "CreationDate":   "created_at",
        "Location":       "location",
        "UpVotes":        "up_votes",
        "DownVotes":      "down_votes",
        "Views":          "views",
        "LastAccessDate": "last_access_at",
    })
    df = df[[
        "user_id", "display_name", "reputation", "created_at",
        "location", "up_votes", "down_votes", "views", "last_access_at"
    ]]

    with conn.cursor() as cur:
        for _, row in tqdm(df.iterrows(), total=len(df), desc="users"):
            cur.execute("""
                INSERT INTO users
                    (user_id, display_name, reputation, created_at,
                     location, up_votes, down_votes, views, last_access_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (user_id) DO NOTHING
            """, tuple(None if pd.isna(v) else v for v in row))
    conn.commit()
    print(f"✅ users: {len(df)} строк")


# ─── Загрузка вопросов ───────────────────────────────────────────────────────
def load_questions(conn) -> None:
    path = RAW_DIR / "questions.csv"
    if not path.exists():
        print(f"⚠️  {path.name} не найден — пропускаем")
        return

    df = pd.read_csv(path)
    df = df.rename(columns={
        "Id":               "question_id",
        "Title":            "title",
        "Body":             "body",
        "Tags":             "tags_raw",
        "CreationDate":     "created_at",
        "Score":            "score",
        "ViewCount":        "view_count",
        "AnswerCount":      "answer_count",
        "FavoriteCount":    "favorite_count",
        "AcceptedAnswerId": "accepted_answer_id",
        "OwnerUserId":      "owner_user_id",
        "ClosedDate":       "closed_at",
        "LastActivityDate": "last_activity_at",
    })

    cols = [
        "question_id", "title", "body", "tags_raw", "created_at",
        "score", "view_count", "answer_count", "favorite_count",
        "accepted_answer_id", "owner_user_id", "closed_at", "last_activity_at"
    ]
    df = df[[c for c in cols if c in df.columns]]

    with conn.cursor() as cur:
        for _, row in tqdm(df.iterrows(), total=len(df), desc="questions"):
            cur.execute("""
                INSERT INTO questions
                    (question_id, title, body, tags_raw, created_at,
                     score, view_count, answer_count, favorite_count,
                     accepted_answer_id, owner_user_id, closed_at, last_activity_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (question_id) DO NOTHING
            """, tuple(None if pd.isna(v) else v for v in row))
    conn.commit()
    print(f"✅ questions: {len(df)} строк")

    _load_tags(conn, df)


# ─── Нормализация тегов ──────────────────────────────────────────────────────
def _parse_tags(raw) -> list:
    if not isinstance(raw, str):
        return []
    return re.findall(r"<([^>]+)>", raw)


def _load_tags(conn, df: pd.DataFrame) -> None:
    tag_set = set()
    pairs = []

    for _, row in df.iterrows():
        parsed = _parse_tags(row.get("tags_raw", ""))
        for t in parsed:
            tag_set.add(t)
            pairs.append((row["question_id"], t))

    with conn.cursor() as cur:
        # Вставляем уникальные теги
        for tag in tag_set:
            cur.execute(
                "INSERT INTO tags (tag_name) VALUES (%s) ON CONFLICT (tag_name) DO NOTHING",
                (tag,)
            )

        # Получаем tag_id
        cur.execute("SELECT tag_name, tag_id FROM tags")
        tag_id_map = {row[0]: row[1] for row in cur.fetchall()}

        # Связываем вопросы с тегами
        for question_id, tag_name in pairs:
            tag_id = tag_id_map.get(tag_name)
            if tag_id:
                cur.execute("""
                    INSERT INTO question_tags (question_id, tag_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (question_id, tag_id))

    conn.commit()
    print(f"✅ tags: {len(tag_set)} уникальных, {len(pairs)} связей")


# ─── Загрузка ответов ────────────────────────────────────────────────────────
def load_answers(conn) -> None:
    path = RAW_DIR / "answers.csv"
    if not path.exists():
        print(f"⚠️  {path.name} не найден — пропускаем")
        return

    df = pd.read_csv(path)
    df = df.rename(columns={
        "Id":           "answer_id",
        "ParentId":     "question_id",
        "CreationDate": "created_at",
        "Score":        "score",
        "OwnerUserId":  "owner_user_id",
        "IsAccepted":   "is_accepted",
    })

    with conn.cursor() as cur:
        for _, row in tqdm(df.iterrows(), total=len(df), desc="answers"):
            cur.execute("""
                INSERT INTO answers
                    (answer_id, question_id, created_at, score, owner_user_id, is_accepted)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT (answer_id) DO NOTHING
            """, tuple(None if pd.isna(v) else v for v in row))
    conn.commit()
    print(f"✅ answers: {len(df)} строк")


# ─── CLI ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Загрузка данных в PostgreSQL")
    parser.add_argument("--init", action="store_true", help="Создать схему БД")
    parser.add_argument("--load", action="store_true", help="Загрузить CSV в БД")
    parser.add_argument("--all",  action="store_true", help="init + load")
    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()
        return

    conn = get_connection()
    print(f"✅ Подключение к БД установлено\n")

    try:
        if args.init or args.all:
            init_schema(conn)

        if args.load or args.all:
            load_users(conn)
            load_questions(conn)
            load_answers(conn)

        print("\n🎉 Готово!")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
