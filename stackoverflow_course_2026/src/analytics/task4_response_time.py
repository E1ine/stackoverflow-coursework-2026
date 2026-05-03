"""
task4_response_time.py — Анализ времени ожидания ответа и факторов влияния

Запуск:
    python src/analytics/task4_response_time.py
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
from dotenv import load_dotenv
from pathlib import Path
from scipy import stats

# Подключение
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
engine = create_engine(os.getenv("DATABASE_URL"))

# Данные
def load_data() -> pd.DataFrame:
    query = """
        SELECT
            q.question_id,
            q.created_at                            AS question_created,
            MIN(a.created_at)                       AS first_answer_at,
            EXTRACT(EPOCH FROM (MIN(a.created_at) - q.created_at)) / 3600
                                                    AS hours_to_answer,
            q.score,
            q.view_count,
            COALESCE(u.reputation, 0)               AS owner_reputation,
            COUNT(DISTINCT qt.tag_id)               AS tag_count,
            CASE WHEN q.accepted_answer_id IS NOT NULL THEN 1 ELSE 0 END AS has_accepted,
            EXTRACT(HOUR FROM q.created_at)         AS hour,
            EXTRACT(DOW FROM q.created_at)          AS day_of_week
        FROM questions q
        JOIN answers a ON a.question_id = q.question_id
        LEFT JOIN users u ON u.user_id = q.owner_user_id
        LEFT JOIN question_tags qt ON qt.question_id = q.question_id
        GROUP BY
            q.question_id, q.created_at, q.score,
            q.view_count, u.reputation, q.accepted_answer_id
        HAVING EXTRACT(EPOCH FROM (MIN(a.created_at) - q.created_at)) > 0
    """
    df = pd.read_sql(query, engine)
    df["question_created"] = pd.to_datetime(df["question_created"])

    # Убираем выбросы — больше 7 суток ждать ответа нереалистично
    df = df[df["hours_to_answer"] <= 168]
    df["log_hours"] = np.log1p(df["hours_to_answer"])
    df["log_reputation"] = np.log1p(df["owner_reputation"])

    return df


# Визуализация
def plot_distribution(df: pd.DataFrame) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.hist(df["hours_to_answer"], bins=50, color="#2196F3", alpha=0.8, edgecolor="white")
    ax1.set_title("Распределение времени до первого ответа", fontsize=13, fontweight="bold")
    ax1.set_xlabel("Часов до ответа")
    ax1.set_ylabel("Количество вопросов")
    ax1.axvline(df["hours_to_answer"].median(), color="red", linestyle="--",
                linewidth=2, label=f"Медиана: {df['hours_to_answer'].median():.1f}ч")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.hist(df["log_hours"], bins=50, color="#4CAF50", alpha=0.8, edgecolor="white")
    ax2.set_title("Распределение (логарифмическая шкала)", fontsize=13, fontweight="bold")
    ax2.set_xlabel("log(часов до ответа)")
    ax2.set_ylabel("Количество вопросов")
    ax2.grid(True, alpha=0.3)

    sns.despine()
    plt.tight_layout()
    plt.savefig(ROOT / "notebooks" / "task4_distribution.png", dpi=150, bbox_inches="tight")
    print("Распределение сохранено: notebooks/task4_distribution.png")
    plt.show()


def plot_by_hour(df: pd.DataFrame) -> None:
    hourly = df.groupby("hour")["hours_to_answer"].median().reset_index()

    fig, ax = plt.subplots(figsize=(14, 5))
    bars = ax.bar(hourly["hour"], hourly["hours_to_answer"],
                  color="#2196F3", alpha=0.85, edgecolor="white")

    ax.set_title("Медианное время ответа по часам публикации вопроса",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Час публикации (UTC)")
    ax.set_ylabel("Медианное время до ответа (часы)")
    ax.set_xticks(range(24))
    ax.grid(True, alpha=0.3, axis="y")
    sns.despine()

    plt.tight_layout()
    plt.savefig(ROOT / "notebooks" / "task4_by_hour.png", dpi=150, bbox_inches="tight")
    print("По часам сохранено: notebooks/task4_by_hour.png")
    plt.show()


def plot_by_weekday(df: pd.DataFrame) -> None:
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    weekly = df.groupby("day_of_week")["hours_to_answer"].median().reset_index()

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ["#2196F3"] * 5 + ["#FF9800"] * 2  # будни синие, выходные оранжевые
    ax.bar(weekly["day_of_week"], weekly["hours_to_answer"],
           color=colors, alpha=0.85, edgecolor="white")

    ax.set_title("Медианное время ответа по дням недели",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("День недели")
    ax.set_ylabel("Медианное время до ответа (часы)")
    ax.set_xticks(range(7))
    ax.set_xticklabels(days)
    ax.grid(True, alpha=0.3, axis="y")
    sns.despine()

    plt.tight_layout()
    plt.savefig(ROOT / "notebooks" / "task4_by_weekday.png", dpi=150, bbox_inches="tight")
    print("По дням недели сохранено: notebooks/task4_by_weekday.png")
    plt.show()


def plot_reputation_vs_time(df: pd.DataFrame) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # График 1 — время ответа: с принятым vs без
    accepted = df[df["has_accepted"] == 1]["hours_to_answer"]
    not_accepted = df[df["has_accepted"] == 0]["hours_to_answer"]

    ax1.hist(accepted, bins=40, alpha=0.7, color="#4CAF50",
             label=f"С принятым ответом (медиана: {accepted.median():.1f}ч)")
    ax1.hist(not_accepted, bins=40, alpha=0.7, color="#F44336",
             label=f"Без принятого ответа (медиана: {not_accepted.median():.1f}ч)")
    ax1.axvline(accepted.median(), color="#4CAF50", linestyle="--", linewidth=2)
    ax1.axvline(not_accepted.median(), color="#F44336", linestyle="--", linewidth=2)
    ax1.set_title("Время ожидания: принятый vs непринятый ответ",
                  fontsize=13, fontweight="bold")
    ax1.set_xlabel("Часов до первого ответа")
    ax1.set_ylabel("Количество вопросов")
    ax1.legend(fontsize=10)
    ax1.set_xlim(0, 50)
    ax1.grid(True, alpha=0.3)
    sns.despine()

    # График 2 — медианное время по количеству тегов
    tag_time = df.groupby("tag_count")["hours_to_answer"].median().reset_index()
    tag_time = tag_time[tag_time["tag_count"] <= 5]

    ax2.bar(tag_time["tag_count"], tag_time["hours_to_answer"],
            color="#2196F3", alpha=0.85, edgecolor="white")
    ax2.set_title("Медианное время ответа по количеству тегов",
                  fontsize=13, fontweight="bold")
    ax2.set_xlabel("Количество тегов")
    ax2.set_ylabel("Медианное время до ответа (часы)")
    ax2.set_xticks(tag_time["tag_count"])
    ax2.grid(True, alpha=0.3, axis="y")
    sns.despine()

    plt.tight_layout()
    plt.savefig(ROOT / "notebooks" / "task4_reputation.png", dpi=150, bbox_inches="tight")
    print("График сохранён: notebooks/task4_reputation.png")
    plt.show()


def plot_correlation(df: pd.DataFrame) -> None:
    features = {
        "score": "Score вопроса",
        "view_count": "Просмотры",
        "log_reputation": "Репутация (log)",
        "tag_count": "Кол-во тегов",
        "hour": "Час публикации",
        "has_accepted": "Принятый ответ"
    }

    corr_data = {}
    for col, label in features.items():
        corr, pval = stats.spearmanr(df[col], df["hours_to_answer"])
        corr_data[label] = corr

    corr_df = pd.DataFrame.from_dict(
        corr_data, orient="index", columns=["correlation"]
    ).sort_values("correlation")

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["#F44336" if v < 0 else "#4CAF50" for v in corr_df["correlation"]]
    ax.barh(corr_df.index, corr_df["correlation"], color=colors, alpha=0.85)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_title("Корреляция факторов со временем ожидания ответа\n(коэффициент Спирмена)",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Корреляция")
    ax.grid(True, alpha=0.3, axis="x")
    sns.despine()

    plt.tight_layout()
    plt.savefig(ROOT / "notebooks" / "task4_correlation.png", dpi=150, bbox_inches="tight")
    print("Корреляция сохранена: notebooks/task4_correlation.png")
    plt.show()


# ─── Статистика ──────────────────────────────────────────────────────────────
def print_stats(df: pd.DataFrame) -> None:
    print(f"\nСтатистика времени ожидания ответа:")
    print(f"  Вопросов с ответами: {len(df)}")
    print(f"  Медиана: {df['hours_to_answer'].median():.1f} часов")
    print(f"  Среднее: {df['hours_to_answer'].mean():.1f} часов")
    print(f"  25%: {df['hours_to_answer'].quantile(0.25):.1f} часов")
    print(f"  75%: {df['hours_to_answer'].quantile(0.75):.1f} часов")

    print(f"\nВремя ответа: принятый vs непринятый:")
    accepted = df[df["has_accepted"] == 1]["hours_to_answer"].median()
    not_accepted = df[df["has_accepted"] == 0]["hours_to_answer"].median()
    print(f"  С принятым ответом:  {accepted:.1f} часов")
    print(f"  Без принятого ответа: {not_accepted:.1f} часов")


# ─── Main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Загружаем данные...")
    df = load_data()
    print(f"Вопросов с ответами: {len(df)}")

    print_stats(df)
    plot_distribution(df)
    plot_by_hour(df)
    plot_by_weekday(df)
    plot_reputation_vs_time(df)
    plot_correlation(df)

    print("\nЗадача 4 завершена!")