"""
task2_clustering.py — Кластеризация пользователей по паттернам активности

Запуск:
    python src/analytics/task2_clustering.py
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
from dotenv import load_dotenv
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

# Подключение
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
engine = create_engine(os.getenv("DATABASE_URL"))

# Данные
def load_data() -> pd.DataFrame:
    query = """
        SELECT
            u.user_id,
            u.reputation,
            COUNT(DISTINCT q.question_id)  AS question_count,
            COUNT(DISTINCT a.answer_id)    AS answer_count,
            COALESCE(AVG(q.score), 0)      AS avg_question_score,
            COALESCE(AVG(a.score), 0)      AS avg_answer_score,
            COALESCE(SUM(CASE WHEN a.is_accepted = 1 THEN 1 ELSE 0 END), 0) AS accepted_answers
        FROM users u
        LEFT JOIN questions q ON q.owner_user_id = u.user_id
        LEFT JOIN answers   a ON a.owner_user_id = u.user_id
        GROUP BY u.user_id, u.reputation
        HAVING COUNT(DISTINCT q.question_id) > 0
            OR COUNT(DISTINCT a.answer_id)   > 0
    """
    df = pd.read_sql(query, engine)

    # Считаем поведенческие признаки
    total = df["question_count"] + df["answer_count"]
    df["answer_ratio"] = df["answer_count"] / (total + 1)
    df["acceptance_rate"] = df["accepted_answers"] / (df["answer_count"] + 1)
    df["log_reputation"] = np.log1p(df["reputation"])
    df["avg_score"] = (df["avg_question_score"] + df["avg_answer_score"]) / 2
    # Финальная очистка выбросов по score
    q99 = df["avg_score"].quantile(0.99)
    df = df[df["avg_score"] <= q99]

    return df


# Подбор оптимального k
def plot_elbow(X_scaled: np.ndarray) -> None:
    inertias = []
    silhouettes = []
    k_range = range(2, 10)

    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        inertias.append(km.inertia_)
        silhouettes.append(silhouette_score(X_scaled, labels))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(k_range, inertias, marker="o", linewidth=2, color="#2196F3")
    ax1.set_title("Метод локтя", fontsize=14, fontweight="bold")
    ax1.set_xlabel("Количество кластеров (k)")
    ax1.set_ylabel("Инерция")
    ax1.grid(True, alpha=0.3)

    ax2.plot(k_range, silhouettes, marker="o", linewidth=2, color="#4CAF50")
    ax2.set_title("Силуэтный коэффициент", fontsize=14, fontweight="bold")
    ax2.set_xlabel("Количество кластеров (k)")
    ax2.set_ylabel("Силуэт")
    ax2.grid(True, alpha=0.3)

    sns.despine()
    plt.tight_layout()
    plt.savefig(ROOT / "notebooks" / "task2_elbow.png", dpi=150, bbox_inches="tight")
    print("График локтя сохранён: notebooks/task2_elbow.png")
    plt.show()


# Кластеризация
def cluster(df: pd.DataFrame, X_scaled: np.ndarray, k: int = 4) -> pd.DataFrame:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    df["cluster"] = km.fit_predict(X_scaled)
    return df


# PCA визуализация
def plot_pca(df: pd.DataFrame, X_scaled: np.ndarray) -> None:
    pca = PCA(n_components=2, random_state=42)
    components = pca.fit_transform(X_scaled)

    fig, ax = plt.subplots(figsize=(12, 8))
    colors = ["#2196F3", "#4CAF50", "#FF9800", "#E91E63"]
    cluster_names = ["Спрашивающие", "Отвечающие", "Активные", "Эксперты"]

    for i, (color, name) in enumerate(zip(colors, cluster_names)):
        mask = df["cluster"] == i
        ax.scatter(
            components[mask, 0],
            components[mask, 1],
            c=color,
            label=f"Кластер {i}: {name} (n={mask.sum()})",
            alpha=0.6,
            s=30
        )

    ax.set_title(
        "Кластеризация пользователей Stack Overflow (PCA)",
        fontsize=15, fontweight="bold", pad=15
    )
    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%} дисперсии)")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%} дисперсии)")
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    sns.despine()

    plt.tight_layout()
    plt.savefig(ROOT / "notebooks" / "task2_pca.png", dpi=150, bbox_inches="tight")
    print("PCA график сохранён: notebooks/task2_pca.png")
    plt.show()


# Профили кластеров
def plot_profiles(df: pd.DataFrame) -> None:
    features = [
        "answer_ratio", "acceptance_rate",
        "log_reputation", "avg_score"
    ]
    labels = [
        "Доля ответов", "Процент принятых",
        "Репутация (log)", "Средний score"
    ]

    profile = df.groupby("cluster")[features].mean()

    fig, ax = plt.subplots(figsize=(12, 6))
    profile.T.plot(
        kind="bar", ax=ax,
        color=["#2196F3", "#4CAF50", "#FF9800", "#E91E63"],
        width=0.7
    )
    ax.set_title(
        "Профили кластеров пользователей",
        fontsize=15, fontweight="bold", pad=15
    )
    plt.xticks(range(len(labels)), labels, rotation=30, ha="right")
    ax.set_ylabel("Среднее значение")
    ax.legend(
        title="Кластер",
        labels=["Спрашивающие", "Отвечающие", "Активные", "Эксперты"]
    )
    ax.grid(True, alpha=0.3, axis="y")
    sns.despine()

    plt.tight_layout()
    plt.savefig(ROOT / "notebooks" / "task2_profiles.png", dpi=150, bbox_inches="tight")
    print("Профили кластеров сохранены: notebooks/task2_profiles.png")
    plt.show()


# Статистика
def print_stats(df: pd.DataFrame) -> None:
    features = [
        "reputation", "question_count", "answer_count",
        "avg_question_score", "avg_answer_score", "accepted_answers"
    ]
    print("\n📊 Средние показатели по кластерам:")
    print(df.groupby("cluster")[features].mean().round(2).to_string())
    print("\n📊 Размеры кластеров:")
    print(df["cluster"].value_counts().sort_index().to_string())


# Main
if __name__ == "__main__":
    print("Загружаем данные...")
    df = load_data()
    print(f"Пользователей для кластеризации: {len(df)}")

    features = [
        "answer_ratio",
        "acceptance_rate", 
        "log_reputation",
        "avg_score"
    ]

    X = df[features].fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print("Подбираем оптимальное k...")
    plot_elbow(X_scaled)

    print("Кластеризуем с k=4...")
    df = cluster(df, X_scaled, k=4)

    print_stats(df)
    plot_pca(df, X_scaled)
    plot_profiles(df)

    print("\nЗадача 2 завершена!")