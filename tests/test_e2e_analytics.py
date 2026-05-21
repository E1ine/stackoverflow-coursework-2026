"""
E2E тесты — гоняют весь аналитический стек (как в task2/task3),
но на маленьком синтетическом наборе вместо реальной БД.
Проверяем, что пайплайн отрабатывает и выдаёт осмысленные результаты.

Запуск:  pytest tests/test_e2e_analytics.py -v
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from analytics import transforms as T  # noqa: E402

rng = np.random.default_rng(42)


def _make_users(n=300):
    """Два явных «типа» пользователей → кластеризация обязана их разделить."""
    askers = pd.DataFrame({
        "user_id": range(n // 2),
        "reputation": rng.integers(1, 50, n // 2),
        "question_count": rng.integers(5, 20, n // 2),
        "answer_count": rng.integers(0, 2, n // 2),
        "avg_question_score": rng.normal(1, 0.3, n // 2),
        "avg_answer_score": np.zeros(n // 2),
        "accepted_answers": np.zeros(n // 2),
    })
    answerers = pd.DataFrame({
        "user_id": range(n // 2, n),
        "reputation": rng.integers(5000, 50000, n // 2),
        "question_count": rng.integers(0, 2, n // 2),
        "answer_count": rng.integers(20, 80, n // 2),
        "avg_question_score": np.zeros(n // 2),
        "avg_answer_score": rng.normal(5, 1, n // 2),
        "accepted_answers": rng.integers(10, 40, n // 2),
    })
    return pd.concat([askers, answerers], ignore_index=True)


def test_e2e_clustering_separates_two_groups():
    """task2 end-to-end: признаки → масштаб → KMeans → силуэт > 0.5."""
    df = _make_users()
    feats = T.compute_user_features(df)
    feats = T.drop_score_outliers(feats)

    X = feats[["answer_ratio", "acceptance_rate", "log_reputation", "avg_score"]]
    X_scaled = StandardScaler().fit_transform(X)

    km = KMeans(n_clusters=2, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)

    assert len(set(labels)) == 2                       # оба кластера непустые
    assert silhouette_score(X_scaled, labels) > 0.5    # хорошо разделены


def test_e2e_prediction_beats_random():
    """task3 end-to-end: сигнал в данных → AUC заметно выше 0.5."""
    n = 800
    # has_accepted зависит от answer_count и score → модель должна это поймать
    answer_count = rng.integers(0, 6, n)
    score = rng.integers(-2, 10, n)
    logit = -1.5 + 0.6 * answer_count + 0.15 * score
    prob = 1 / (1 + np.exp(-logit))
    y = rng.binomial(1, prob)

    df = pd.DataFrame({
        "answer_count": answer_count,
        "score": score,
        "view_count": rng.integers(1, 1000, n),
        "owner_reputation": rng.integers(0, 9000, n),
        "favorite_count": rng.integers(0, 3, n),
        "is_closed": rng.integers(0, 2, n),
        "tag_count": rng.integers(1, 5, n),
        "hour": rng.integers(0, 24, n),
        "day_of_week": rng.integers(0, 7, n),
        "month": rng.integers(1, 13, n),
        "has_accepted": y,
    })
    df = T.prepare_prediction_features(df)

    features = ["answer_count", "log_views", "favorite_count", "score",
                "is_closed", "log_reputation", "tag_count",
                "hour", "day_of_week", "month"]
    X_tr, X_te, y_tr, y_te = train_test_split(
        df[features], df["has_accepted"], test_size=0.25,
        random_state=42, stratify=df["has_accepted"],
    )
    model = RandomForestClassifier(n_estimators=80, random_state=42, n_jobs=-1)
    model.fit(X_tr, y_tr)
    auc = roc_auc_score(y_te, model.predict_proba(X_te)[:, 1])

    assert auc > 0.65          # модель ловит заложенный сигнал
    assert 0.0 <= auc <= 1.0   # метрика корректна


def test_e2e_response_time_funnel():
    """task4 end-to-end: выбросы реально отсекаются на больших данных."""
    n = 5000
    hours = np.concatenate([
        rng.exponential(5, int(n * 0.95)),     # нормальные ответы
        rng.uniform(200, 1000, int(n * 0.05)), # выбросы > 7 суток
    ])
    df = pd.DataFrame({
        "hours_to_answer": hours,
        "owner_reputation": rng.integers(0, 9000, len(hours)),
    })
    cleaned = T.prepare_response_times(df)
    assert cleaned["hours_to_answer"].max() <= T.MAX_RESPONSE_HOURS
    assert len(cleaned) < len(df)   # что-то отсеяли
