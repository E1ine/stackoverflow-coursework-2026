"""
task5_procrastination.py — Анализ временных паттернов активности разработчиков

Запуск:
    python src/analytics/task5_procrastination.py
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from sqlalchemy import create_engine
from dotenv import load_dotenv
from pathlib import Path

# Общая логика преобразований (тестируется в tests/)
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # .../src в sys.path
from analytics import transforms as T

# Подключение
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
engine = create_engine(os.getenv("DATABASE_URL"))

# Данные
def load_data() -> pd.DataFrame:
    query = """
        SELECT
            question_id,
            created_at,
            score,
            view_count,
            answer_count
        FROM questions
    """
    df = pd.read_sql(query, engine)
    # Базовые временные признаки (created_at, hour, day_of_week, is_weekend) — из общего модуля
    df = T.add_time_features(df)
    # Дополнительные поля, специфичные для task5
    df["month"]    = df["created_at"].dt.month
    df["week"]     = df["created_at"].dt.isocalendar().week.astype(int)
    df["year"]     = df["created_at"].dt.year
    df["day_name"] = df["created_at"].dt.day_name()
    return df


# Визуализация
def plot_heatmap(df: pd.DataFrame) -> None:
    pivot = df.groupby(["day_of_week", "hour"]).size().reset_index(name="count")
    pivot = pivot.pivot(index="day_of_week", columns="hour", values="count").fillna(0)
    pivot.index = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    fig, ax = plt.subplots(figsize=(18, 6))
    sns.heatmap(
        pivot, cmap="YlOrRd", ax=ax,
        linewidths=0.3, linecolor="white",
        cbar_kws={"label": "Количество вопросов"}
    )
    ax.set_title(
        "Тепловая карта активности разработчиков на Stack Overflow\n(день недели × час UTC)",
        fontsize=14, fontweight="bold", pad=15
    )
    ax.set_xlabel("Час суток (UTC)", fontsize=12)
    ax.set_ylabel("День недели", fontsize=12)

    plt.tight_layout()
    plt.savefig(ROOT / "notebooks" / "task5_heatmap.png", dpi=150, bbox_inches="tight")
    print("Тепловая карта сохранена: notebooks/task5_heatmap.png")
    plt.show()


def plot_hourly(df: pd.DataFrame) -> None:
    hourly = df.groupby("hour").size().reset_index(name="count")

    # Рабочие часы 9-18 UTC
    colors = ["#FF9800" if 9 <= h <= 18 else "#2196F3" for h in hourly["hour"]]

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.bar(hourly["hour"], hourly["count"], color=colors, alpha=0.85, edgecolor="white")
    ax.set_title("Распределение вопросов по часам суток",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Час суток (UTC)")
    ax.set_ylabel("Количество вопросов")
    ax.set_xticks(range(24))

    work = mpatches.Patch(color="#FF9800", alpha=0.85, label="Рабочие часы (9-18 UTC)")
    other = mpatches.Patch(color="#2196F3", alpha=0.85, label="Остальное время")
    ax.legend(handles=[work, other])
    ax.grid(True, alpha=0.3, axis="y")
    sns.despine()

    plt.tight_layout()
    plt.savefig(ROOT / "notebooks" / "task5_hourly.png", dpi=150, bbox_inches="tight")
    print("По часам сохранено: notebooks/task5_hourly.png")
    plt.show()


def plot_weekday(df: pd.DataFrame) -> None:
    days_order = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    day_map = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс"}
    df["day_ru"] = df["day_of_week"].map(day_map)

    weekly = df.groupby("day_ru").size().reindex(days_order).reset_index()
    weekly.columns = ["day", "count"]

    colors = ["#2196F3"] * 5 + ["#FF9800"] * 2

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(weekly["day"], weekly["count"], color=colors, alpha=0.85, edgecolor="white")
    ax.set_title("Количество вопросов по дням недели",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("День недели")
    ax.set_ylabel("Количество вопросов")

    work = mpatches.Patch(color="#2196F3", alpha=0.85, label="Рабочие дни")
    weekend = mpatches.Patch(color="#FF9800", alpha=0.85, label="Выходные")
    ax.legend(handles=[work, weekend])
    ax.grid(True, alpha=0.3, axis="y")
    sns.despine()

    plt.tight_layout()
    plt.savefig(ROOT / "notebooks" / "task5_weekday.png", dpi=150, bbox_inches="tight")
    print("По дням недели сохранено: notebooks/task5_weekday.png")
    plt.show()


def plot_weekend_vs_weekday(df: pd.DataFrame) -> None:
    hourly = df.groupby(["is_weekend", "hour"]).size().reset_index(name="count")
    weekday = hourly[hourly["is_weekend"] == 0]
    weekend = hourly[hourly["is_weekend"] == 1]

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(weekday["hour"], weekday["count"],
            marker="o", linewidth=2, color="#2196F3",
            label="Рабочие дни", markersize=5)
    ax.plot(weekend["hour"], weekend["count"],
            marker="o", linewidth=2, color="#FF9800",
            label="Выходные", markersize=5)

    ax.set_title("Активность по часам: рабочие дни vs выходные",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Час суток (UTC)")
    ax.set_ylabel("Количество вопросов")
    ax.set_xticks(range(24))
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    sns.despine()

    plt.tight_layout()
    plt.savefig(ROOT / "notebooks" / "task5_weekend_vs_weekday.png", dpi=150, bbox_inches="tight")
    print("Выходные vs рабочие сохранено: notebooks/task5_weekend_vs_weekday.png")
    plt.show()


# Статистика
def print_stats(df: pd.DataFrame) -> None:
    print(f"\nВсего вопросов: {len(df)}")

    peak_hour = df.groupby("hour").size().idxmax()
    print(f"Пиковый час активности: {peak_hour}:00 UTC")

    day_map = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс"}
    peak_day = df.groupby("day_of_week").size().idxmax()
    print(f"Самый активный день: {day_map[peak_day]}")

    weekday_count = df[df["is_weekend"] == 0].shape[0]
    weekend_count = df[df["is_weekend"] == 1].shape[0]
    print(f"Вопросов в рабочие дни: {weekday_count} ({weekday_count/len(df)*100:.1f}%)")
    print(f"Вопросов в выходные: {weekend_count} ({weekend_count/len(df)*100:.1f}%)")


# ─── Main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Загружаем данные...")
    df = load_data()

    print_stats(df)
    plot_heatmap(df)
    plot_hourly(df)
    plot_weekday(df)
    plot_weekend_vs_weekday(df)

    print("\nЗадача 5 завершена!")