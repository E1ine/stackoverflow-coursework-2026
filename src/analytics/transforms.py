"""
transforms.py — чистые (без обращения к БД) функции преобразования данных.

Вся «аналитическая математика» из task1–task5 и loader вынесена сюда,
чтобы её можно было покрыть модульными тестами без реальной PostgreSQL.
"""
from __future__ import annotations

import re
import numpy as np
import pandas as pd

# Константа: ответ дольше 7 суток считаем выбросом (см. task4).
MAX_RESPONSE_HOURS = 168


# ─────────────────────────── loader: разбор тегов ───────────────────────────
def parse_tags(raw) -> list[str]:
    """Stack Overflow хранит теги строкой '<python><pandas>'. Достаём список.

    Не-строки (NaN, None, числа) → пустой список.
    """
    if not isinstance(raw, str):
        return []
    return re.findall(r"<([^>]+)>", raw)


def deduplicate(df: pd.DataFrame, key: str = "Id") -> pd.DataFrame:
    """Удаление дубликатов по первичному ключу (логика из loader.load_*)."""
    return df.drop_duplicates(subset=[key]).reset_index(drop=True)


# ───────────────────────── task1: тренды технологий ─────────────────────────
def get_top_tags(df: pd.DataFrame, n: int = 10) -> list[str]:
    """Топ-N тегов по суммарному числу вопросов."""
    return (
        df.groupby("tag_name")["question_count"]
        .sum()
        .sort_values(ascending=False)
        .head(n)
        .index.tolist()
    )


def compute_growth(df: pd.DataFrame, tags: list[str]) -> pd.DataFrame:
    """Изменение популярности (%) первый месяц → последний.

    Знаменатель (first + 1) защищает от деления на ноль (сглаживание Лапласа).
    """
    filtered = df[df["tag_name"].isin(tags)]
    pivot = filtered.pivot_table(
        index="month", columns="tag_name", values="question_count", fill_value=0
    )
    first, last = pivot.iloc[0], pivot.iloc[-1]
    change = ((last - first) / (first + 1) * 100).round(1)
    out = change.reset_index()
    out.columns = ["tag_name", "change_pct"]
    return out.sort_values("change_pct", ascending=False).reset_index(drop=True)


# ─────────────────── task2: поведенческие признаки юзеров ────────────────────
def compute_user_features(df: pd.DataFrame) -> pd.DataFrame:
    """Поведенческие признаки для кластеризации.

    answer_ratio    — доля ответов в активности (0..1)
    acceptance_rate — доля принятых среди ответов (0..1)
    log_reputation  — log1p репутации (сжатие тяжёлого хвоста)
    avg_score       — средний score публикаций
    Все «+1» — сглаживание, исключающее деление на ноль.
    """
    out = df.copy()
    total = out["question_count"] + out["answer_count"]
    out["answer_ratio"] = out["answer_count"] / (total + 1)
    out["acceptance_rate"] = out["accepted_answers"] / (out["answer_count"] + 1)
    out["log_reputation"] = np.log1p(out["reputation"])
    out["avg_score"] = (out["avg_question_score"] + out["avg_answer_score"]) / 2
    return out


def drop_score_outliers(df: pd.DataFrame, col: str = "avg_score",
                        q: float = 0.99) -> pd.DataFrame:
    """Отсечение верхнего 1% по score (винзоризация хвоста)."""
    threshold = df[col].quantile(q)
    return df[df[col] <= threshold].reset_index(drop=True)


# ─────────────────── task3: признаки для предсказания ────────────────────────
def prepare_prediction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Лог-преобразование тяжёлых хвостов + заполнение пропусков."""
    out = df.copy()
    out["log_views"] = np.log1p(out["view_count"])
    out["log_reputation"] = np.log1p(out["owner_reputation"])
    return out.fillna(0)


# ─────────────────── task4: время ожидания ответа ────────────────────────────
def prepare_response_times(df: pd.DataFrame,
                           max_hours: float = MAX_RESPONSE_HOURS) -> pd.DataFrame:
    """Отсечение нереалистичных ожиданий (> 7 суток) + лог-признаки."""
    out = df[(df["hours_to_answer"] > 0) & (df["hours_to_answer"] <= max_hours)].copy()
    out["log_hours"] = np.log1p(out["hours_to_answer"])
    out["log_reputation"] = np.log1p(out["owner_reputation"])
    return out.reset_index(drop=True)


# ─────────────────── task5: временные признаки ───────────────────────────────
def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Извлечение час/день недели/выходной из created_at."""
    out = df.copy()
    out["created_at"] = pd.to_datetime(out["created_at"])
    out["hour"] = out["created_at"].dt.hour
    out["day_of_week"] = out["created_at"].dt.dayofweek
    out["is_weekend"] = out["day_of_week"].isin([5, 6]).astype(int)
    return out


def weekend_share(df: pd.DataFrame) -> float:
    """Доля вопросов, заданных в выходные (0..1)."""
    if len(df) == 0:
        return 0.0
    return df["is_weekend"].mean()
