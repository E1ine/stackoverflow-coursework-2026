"""
task3_accepted_answer_prediction.py — Предсказание получит ли вопрос принятый ответ

Запуск:
    python src/analytics/task3_score_prediction.py
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
from dotenv import load_dotenv
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, roc_curve, auc
)

# Подключение
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
engine = create_engine(os.getenv("DATABASE_URL"))

# Данные
def load_data() -> pd.DataFrame:
    query = """
        SELECT
            q.question_id,
            CASE WHEN q.accepted_answer_id IS NOT NULL THEN 1 ELSE 0 END AS has_accepted,
            q.answer_count,
            q.view_count,
            q.favorite_count,
            q.score,
            CASE WHEN q.closed_at IS NOT NULL THEN 1 ELSE 0 END AS is_closed,
            COALESCE(u.reputation, 0) AS owner_reputation,
            COUNT(qt.tag_id) AS tag_count,
            EXTRACT(HOUR FROM q.created_at)        AS hour,
            EXTRACT(DOW  FROM q.created_at)        AS day_of_week,
            EXTRACT(MONTH FROM q.created_at)       AS month
        FROM questions q
        LEFT JOIN users u ON u.user_id = q.owner_user_id
        LEFT JOIN question_tags qt ON qt.question_id = q.question_id
        GROUP BY
            q.question_id, q.accepted_answer_id, q.answer_count,
            q.view_count, q.favorite_count, q.score,
            q.closed_at, u.reputation, q.created_at
    """
    df = pd.read_sql(query, engine)
    df["log_views"]      = np.log1p(df["view_count"])
    df["log_reputation"] = np.log1p(df["owner_reputation"])
    df = df.fillna(0)
    return df


# Обучение
def train_models(df: pd.DataFrame):
    features = [
        "answer_count", "log_views", "favorite_count",
        "score", "is_closed", "log_reputation",
        "tag_count", "hour", "day_of_week", "month"
    ]

    X = df[features]
    y = df["has_accepted"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Обучающая выборка: {len(X_train)}, тестовая: {len(X_test)}")
    print(f"Баланс классов: {y.mean():.1%} вопросов с принятым ответом")

    models = {
        "Random Forest": RandomForestClassifier(
            n_estimators=100, random_state=42, n_jobs=-1
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=100, random_state=42
        ),
    }

    results = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        results[name] = {
            "model":     model,
            "y_test":    y_test,
            "y_pred":    y_pred,
            "y_prob":    y_prob,
            "accuracy":  accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred),
            "recall":    recall_score(y_test, y_pred),
            "f1":        f1_score(y_test, y_pred),
        }
        print(f"\n{name}:")
        print(f"  Accuracy:  {results[name]['accuracy']:.3f}")
        print(f"  Precision: {results[name]['precision']:.3f}")
        print(f"  Recall:    {results[name]['recall']:.3f}")
        print(f"  F1:        {results[name]['f1']:.3f}")

    return results, features


# Визуализация
def plot_confusion_matrices(results: dict) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for ax, (name, res) in zip(axes, results.items()):
        cm = confusion_matrix(res["y_test"], res["y_pred"])
        sns.heatmap(
            cm, annot=True, fmt="d", cmap="Blues", ax=ax,
            xticklabels=["Нет ответа", "Есть ответ"],
            yticklabels=["Нет ответа", "Есть ответ"]
        )
        ax.set_title(f"Confusion Matrix — {name}", fontsize=13, fontweight="bold")
        ax.set_xlabel("Предсказано")
        ax.set_ylabel("Реально")

    plt.tight_layout()
    plt.savefig(ROOT / "notebooks" / "task3_confusion.png", dpi=150, bbox_inches="tight")
    print("Confusion matrix сохранена: notebooks/task3_confusion.png")
    plt.show()


def plot_roc(results: dict) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ["#2196F3", "#4CAF50"]

    for (name, res), color in zip(results.items(), colors):
        fpr, tpr, _ = roc_curve(res["y_test"], res["y_prob"])
        roc_auc = auc(fpr, tpr)
        ax.plot(fpr, tpr, color=color, linewidth=2,
                label=f"{name} (AUC = {roc_auc:.3f})")

    ax.plot([0, 1], [0, 1], "r--", linewidth=1.5, label="Случайная модель")
    ax.set_title("ROC-кривая", fontsize=14, fontweight="bold")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    sns.despine()

    plt.tight_layout()
    plt.savefig(ROOT / "notebooks" / "task3_roc.png", dpi=150, bbox_inches="tight")
    print("ROC-кривая сохранена: notebooks/task3_roc.png")
    plt.show()


def plot_feature_importance(results: dict, features: list) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    for ax, (name, res) in zip(axes, results.items()):
        importances = res["model"].feature_importances_
        idx = np.argsort(importances)[::-1]

        ax.barh(
            [features[i] for i in idx],
            importances[idx],
            color="#2196F3" if "Random" in name else "#4CAF50"
        )
        ax.set_title(f"Важность признаков — {name}", fontsize=13, fontweight="bold")
        ax.set_xlabel("Важность")
        ax.grid(True, alpha=0.3, axis="x")
        sns.despine()

    plt.tight_layout()
    plt.savefig(ROOT / "notebooks" / "task3_importance.png", dpi=150, bbox_inches="tight")
    print("Feature importance сохранён: notebooks/task3_importance.png")
    plt.show()


def plot_metrics(results: dict) -> None:
    metrics = ["accuracy", "precision", "recall", "f1"]
    labels  = ["Accuracy", "Precision", "Recall", "F1"]
    names   = list(results.keys())
    colors  = ["#2196F3", "#4CAF50"]
    x = np.arange(len(metrics))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))
    for i, (name, color) in enumerate(zip(names, colors)):
        vals = [results[name][m] for m in metrics]
        ax.bar(x + i * width, vals, width, label=name, color=color)

    ax.set_title("Сравнение метрик моделей", fontsize=14, fontweight="bold")
    ax.set_xticks(x + width / 2)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Значение метрики")
    ax.set_ylim(0, 1)
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    sns.despine()

    plt.tight_layout()
    plt.savefig(ROOT / "notebooks" / "task3_metrics.png", dpi=150, bbox_inches="tight")
    print("Метрики сохранены: notebooks/task3_metrics.png")
    plt.show()


# Main
if __name__ == "__main__":
    print("Загружаем данные...")
    df = load_data()
    print(f"Вопросов: {len(df)}")

    print("\nОбучаем модели...")
    results, features = train_models(df)

    plot_confusion_matrices(results)
    plot_roc(results)
    plot_feature_importance(results, features)
    plot_metrics(results)

    print("\nЗадача 3 завершена!")