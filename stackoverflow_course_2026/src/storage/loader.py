"""
loader.py — создание схемы и загрузка данных из CSV в PostgreSQL (Neon.tech)

Использование:
    python src/storage/loader.py --init   # создать таблицы
    python src/storage/loader.py --load   # загрузить CSV в БД
    python src/storage/loader.py --all    # init + load

Требует файл .env в корне проекта:
    DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require

Ожидаемые входные файлы:
    data/raw/questions_*.csv
    data/raw/answers_*.csv
    data/raw/users.csv
"""

import argparse
import os
import re
import sys
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from tqdm import tqdm

# Пути
ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

# Подключение 
load_dotenv(ROOT / ".env")


def get_connection():
    url = os.getenv("DATABASE_URL")
    if not url:
        print("DATABASE_URL не найден в .env")
        sys.exit(1)
    return psycopg2.connect(url)


# Инициализация схемы
def init_schema(conn) -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(schema)
    conn.commit()
    print("Схема БД создана")


# Загрузка пользователей
def load_users(conn) -> None:
    path = RAW_DIR / "users.csv"
    if not path.exists():
        print(f"{path.name} не найден — пропускаем")
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

    records = [
        tuple(None if pd.isna(v) else (str(v).replace('%', '%%') if isinstance(v, str) else v) for v in row)
        for _, row in df.iterrows()
    ]

    batch_size = 5000
    with conn.cursor() as cur:
        for i in tqdm(range(0, len(records), batch_size), desc="users"):
            batch = records[i:i + batch_size]
            cur.executemany("""
                INSERT INTO users
                    (user_id, display_name, reputation, created_at,
                     location, up_votes, down_votes, views, last_access_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (user_id) DO NOTHING
            """, batch)
            conn.commit()
    print(f"users: {len(df)} строк")


# Загрузка вопросов
def load_questions(conn) -> None:
    files = list(RAW_DIR.glob("questions_*.csv"))

    if not files:
        single = RAW_DIR / "questions.csv"
        if single.exists():
            files = [single]

    if not files:
        print("Файлы questions не найдены — пропускаем")
        return

    print(f"Найдено файлов с вопросами: {len(files)}")

    all_dfs = []
    for file in files:
        df = pd.read_csv(file)
        print(f"  Читаю {file.name}: {len(df)} строк")
        all_dfs.append(df)

    df = pd.concat(all_dfs, ignore_index=True)
    print(f"Итого до дедупликации: {len(df)} строк")
    df = df.drop_duplicates(subset=["Id"])
    print(f"После дедупликации: {len(df)} строк")

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

    records = [
        tuple(None if pd.isna(v) else (str(v).replace('%', '%%') if isinstance(v, str) else v) for v in row)
        for _, row in df.iterrows()
    ]

    batch_size = 100
    for i in tqdm(range(0, len(records), batch_size), desc="questions"):
        batch = records[i:i + batch_size]
        c = get_connection()
        with c.cursor() as cur:
            cur.executemany("""
                INSERT INTO questions
                    (question_id, title, body, tags_raw, created_at,
                     score, view_count, answer_count, favorite_count,
                     accepted_answer_id, owner_user_id, closed_at, last_activity_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (question_id) DO NOTHING
            """, batch)
            c.commit()
        c.close()
    print(f"questions: {len(df)} строк загружено")

    _load_tags(df)


# Нормализация тегов
def _parse_tags(raw) -> list:
    if not isinstance(raw, str):
        return []
    return re.findall(r"<([^>]+)>", raw)


def _load_tags(df: pd.DataFrame) -> None:
    tag_set = set()
    pairs = []

    for _, row in df.iterrows():
        parsed = _parse_tags(row.get("tags_raw", ""))
        for t in parsed:
            tag_set.add(t)
            pairs.append((row["question_id"], t))

    # Вставляем теги
    c = get_connection()
    with c.cursor() as cur:
        cur.executemany(
            "INSERT INTO tags (tag_name) VALUES (%s) ON CONFLICT (tag_name) DO NOTHING",
            [(t,) for t in tag_set]
        )
        c.commit()
        cur.execute("SELECT tag_name, tag_id FROM tags")
        tag_id_map = {row[0]: row[1] for row in cur.fetchall()}
    c.close()

    pair_records = [
        (qid, tag_id_map[t])
        for qid, t in pairs
        if t in tag_id_map
    ]

    batch_size = 1000
    for i in tqdm(range(0, len(pair_records), batch_size), desc="tags"):
        batch = pair_records[i:i + batch_size]
        c = get_connection()
        with c.cursor() as cur:
            cur.executemany(
                "INSERT INTO question_tags (question_id, tag_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                batch
            )
            c.commit()
        c.close()

    print(f"tags: {len(tag_set)} уникальных, {len(pairs)} связей")

# Загрузка ответов
def load_answers(conn) -> None:
    files = list(RAW_DIR.glob("answers_*.csv"))

    if not files:
        single = RAW_DIR / "answers.csv"
        if single.exists():
            files = [single]

    if not files:
        print("Файлы answers не найдены — пропускаем")
        return

    print(f"Найдено файлов с ответами: {len(files)}")

    all_dfs = []
    for file in files:
        df = pd.read_csv(file)
        print(f"  Читаю {file.name}: {len(df)} строк")
        all_dfs.append(df)

    df = pd.concat(all_dfs, ignore_index=True)
    print(f"Итого до дедупликации: {len(df)} строк")
    df = df.drop_duplicates(subset=["Id"])
    print(f"После дедупликации: {len(df)} строк")

    df = df.rename(columns={
        "Id":           "answer_id",
        "ParentId":     "question_id",
        "CreationDate": "created_at",
        "Score":        "score",
        "OwnerUserId":  "owner_user_id",
        "IsAccepted":   "is_accepted",
    })
    df = df[["answer_id", "question_id", "created_at", "score", "owner_user_id", "is_accepted"]]
    records = [
        tuple(None if pd.isna(v) else (str(v).replace('%', '%%') if isinstance(v, str) else v) for v in row)
        for _, row in df.iterrows()
    ]

    batch_size = 5000
    for i in tqdm(range(0, len(records), batch_size), desc="answers"):
        batch = records[i:i + batch_size]
        c = get_connection()
        with c.cursor() as cur:
            execute_values(cur, """
                INSERT INTO answers
                    (answer_id, question_id, created_at, score, owner_user_id, is_accepted)
                VALUES %s
                ON CONFLICT (answer_id) DO NOTHING
            """, batch)
            c.commit()
        c.close()
    print(f"answers: {len(df)} строк")


# CLI
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
    print("Подключение к БД установлено\n")

    try:
        if args.init or args.all:
            init_schema(conn)

        if args.load or args.all:
            conn.close()
            conn = get_connection()
            load_users(conn)
            conn.close()
            conn = get_connection()
            load_questions(conn)
            conn.close()
            conn = get_connection()
            load_answers(conn)

        print("\Готово!")
    finally:
        conn.close()


if __name__ == "__main__":
    main()