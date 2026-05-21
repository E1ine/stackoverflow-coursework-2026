"""
task1_trends.py — Анализ трендов популярности технологий по тегам

Запуск:
    python src/analytics/task1_trends.py
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
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
            DATE_TRUNC('month', q.created_at) AS month,
            t.tag_name,
            COUNT(*) AS question_count
        FROM questions q
        JOIN question_tags qt ON qt.question_id = q.question_id
        JOIN tags t ON t.tag_id = qt.tag_id
        GROUP BY month, t.tag_name
        ORDER BY month, question_count DESC
    """
    df = pd.read_sql(query, engine)
    df["month"] = pd.to_datetime(df["month"])
    return df


def get_top_tags(df: pd.DataFrame, n: int = 10) -> list:
    return T.get_top_tags(df, n)


# Визуализация
def plot_trends(df: pd.DataFrame, top_tags: list) -> None:
    filtered = df[df["tag_name"].isin(top_tags)]
    pivot = filtered.pivot_table(
        index="month", columns="tag_name", values="question_count", fill_value=0
    )

    fig, ax = plt.subplots(figsize=(14, 7))

    colors = sns.color_palette("tab10", len(top_tags))
    for i, tag in enumerate(top_tags):
        if tag in pivot.columns:
            ax.plot(
                pivot.index,
                pivot[tag],
                label=tag,
                linewidth=2,
                marker="o",
                markersize=4,
                color=colors[i],
            )

    ax.set_title(
        "Тренды популярности технологий на Stack Overflow (2024–2026)",
        fontsize=16, fontweight="bold", pad=20
    )
    ax.set_xlabel("Месяц", fontsize=13)
    ax.set_ylabel("Количество вопросов", fontsize=13)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.xticks(rotation=45, ha="right")
    ax.legend(title="Технология", bbox_to_anchor=(1.01, 1), loc="upper left")
    ax.grid(True, alpha=0.3)
    sns.despine()

    plt.tight_layout()
    plt.savefig(ROOT / "notebooks" / "task1_trends.png", dpi=150, bbox_inches="tight")
    print("График сохранён: notebooks/task1_trends.png")
    plt.show()


def plot_heatmap(df: pd.DataFrame, top_tags: list) -> None:
    filtered = df[df["tag_name"].isin(top_tags)]
    pivot = filtered.pivot_table(
        index="tag_name", columns="month", values="question_count", fill_value=0
    )
    pivot.columns = pivot.columns.strftime("%b %Y")

    fig, ax = plt.subplots(figsize=(16, 6))
    sns.heatmap(
        pivot,
        cmap="YlOrRd",
        annot=True,
        fmt=".0f",
        linewidths=0.5,
        ax=ax,
        cbar_kws={"label": "Количество вопросов"}
    )
    ax.set_title(
        "Тепловая карта активности по технологиям (2024–2026)",
        fontsize=15, fontweight="bold", pad=15
    )
    ax.set_xlabel("Месяц", fontsize=12)
    ax.set_ylabel("Технология", fontsize=12)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(ROOT / "notebooks" / "task1_heatmap.png", dpi=150, bbox_inches="tight")
    print("Тепловая карта сохранена: notebooks/task1_heatmap.png")
    plt.show()


# Статистика
def print_stats(df: pd.DataFrame, top_tags: list) -> None:
    print("\nТоп-10 технологий за весь период:")
    total = (
        df.groupby("tag_name")["question_count"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    total.columns = ["Технология", "Вопросов всего"]
    print(total.to_string(index=False))

    print("\nРост/падение за период (первый месяц vs последний):")
    change_df = T.compute_growth(df, top_tags)
    change_df.columns = ["Технология", "Изменение (%)"]
    print(change_df.to_string(index=False))


# Main
if __name__ == "__main__":
    print("Загружаем данные...")
    df = load_data()
    top_tags = get_top_tags(df, n=10)
    print(f"Топ тегов: {top_tags}")

    print_stats(df, top_tags)
    plot_trends(df, top_tags)
    plot_heatmap(df, top_tags)