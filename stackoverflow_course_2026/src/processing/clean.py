"""
clean.py — проверка данных после загрузки в PostgreSQL.

Использование:
    python src/processing/clean.py
"""

import os
import sys
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def get_connection():
    url = os.getenv("DATABASE_URL")
    if not url:
        print("❌ DATABASE_URL не найден в .env")
        sys.exit(1)
    return psycopg2.connect(url)


def check(conn) -> None:
    def q(sql):
        return pd.read_sql(sql, conn)

    print("─── Количество строк ───────────────────────────────")
    for table in ["users", "questions", "answers", "tags", "question_tags"]:
        n = q(f"SELECT COUNT(*) as n FROM {table}").iloc[0, 0]
        print(f"  {table:<20} {n:>8,}")

    print("\n─── Score (вопросы) ────────────────────────────────")
    print(q("SELECT MIN(score), MAX(score), ROUND(AVG(score),2) as avg FROM questions").to_string(index=False))

    print("\n─── Вопросов с принятым ответом ───────────────────")
    print(q("SELECT COUNT(*) as cnt FROM questions WHERE accepted_answer_id IS NOT NULL").to_string(index=False))

    print("\n─── Топ-10 тегов ───────────────────────────────────")
    print(q("""
        SELECT t.tag_name, COUNT(*) as cnt
        FROM question_tags qt
        JOIN tags t ON t.tag_id = qt.tag_id
        GROUP BY t.tag_name
        ORDER BY cnt DESC
        LIMIT 10
    """).to_string(index=False))

    print("\n─── Период данных ──────────────────────────────────")
    print(q("SELECT MIN(created_at), MAX(created_at) FROM questions").to_string(index=False))


if __name__ == "__main__":
    conn = get_connection()
    print("📊 Проверка БД\n")
    try:
        check(conn)
        print("\n✅ Всё в порядке")
    finally:
        conn.close()
