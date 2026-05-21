"""
Интеграционные тесты — проверяют, что несколько этапов конвейера
работают вместе (дедупликация → разбор тегов → агрегация → топ-теги).

Запуск:  pytest tests/test_integration_pipeline.py -v
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from analytics import transforms as T  # noqa: E402


def test_csv_to_top_tags_pipeline(raw_questions_csv):
    """Полный мини-ETL: сырой CSV → чистые теги → подсчёт → топ-теги.

    Проверяем, что дубликат вопроса №3 не задваивает счётчик тегов.
    """
    # 1. Дедупликация (как в loader.load_questions)
    deduped = T.deduplicate(raw_questions_csv, key="Id")
    assert len(deduped) == 3

    # 2. Разбор тегов в длинную форму (как в loader._load_tags)
    rows = []
    for _, r in deduped.iterrows():
        for tag in T.parse_tags(r["Tags"]):
            rows.append({"tag_name": tag, "question_count": 1, "month": "2025-01-01"})
    long = pd.DataFrame(rows)
    long["month"] = pd.to_datetime(long["month"])

    # 3. Агрегация + топ-теги (как в task1)
    agg = long.groupby(["month", "tag_name"], as_index=False)["question_count"].sum()
    top = T.get_top_tags(agg, n=10)

    # python встречается у вопросов 1 и 3 → 2 раза; java и pandas по 1.
    assert top[0] == "python"
    counts = agg.groupby("tag_name")["question_count"].sum()
    assert counts["python"] == 2
    assert counts["java"] == 1


def test_user_feature_then_outlier_drop(user_aggregates):
    """Признаки пользователей → отсечение выбросов score, без падения схемы."""
    feats = T.compute_user_features(user_aggregates)
    cleaned = T.drop_score_outliers(feats, q=0.99)
    # Колонки признаков сохранились после второго этапа
    assert {"answer_ratio", "acceptance_rate", "log_reputation"} <= set(cleaned.columns)
    assert len(cleaned) >= 1


def test_time_pipeline_consistency(time_questions):
    """add_time_features → weekend_share согласованы между собой."""
    feats = T.add_time_features(time_questions)
    share = T.weekend_share(feats)
    manual = (feats["day_of_week"] >= 5).mean()
    assert share == manual
