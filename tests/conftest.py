"""Общие фикстуры: синтетические данные, повторяющие структуру БД."""
import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def raw_questions_csv():
    """Сырой CSV вопросов (как из SEDE) — с дубликатом и тегами-строкой."""
    return pd.DataFrame({
        "Id":   [1, 2, 3, 3],          # 3 задублирован
        "Tags": ["<python><pandas>", "<java>", "<python>", "<python>"],
        "Score": [10, 5, 0, 0],
    })


@pytest.fixture
def tag_counts():
    """Длинная форма: тег × месяц × число вопросов (вход task1)."""
    return pd.DataFrame({
        "month": pd.to_datetime(
            ["2024-01-01"] * 3 + ["2024-02-01"] * 3
        ),
        "tag_name": ["python", "java", "c#", "python", "java", "c#"],
        "question_count": [100, 50, 30, 150, 40, 60],
    })


@pytest.fixture
def user_aggregates():
    """Агрегаты по пользователям (вход task2, до вычисления признаков)."""
    return pd.DataFrame({
        "user_id":            [1, 2, 3, 4],
        "reputation":         [0, 100, 5000, 99999],
        "question_count":     [10, 0, 2, 1],
        "answer_count":       [0, 20, 50, 200],
        "avg_question_score": [1.0, 0.0, 2.0, 3.0],
        "avg_answer_score":   [0.0, 2.0, 4.0, 8.0],
        "accepted_answers":   [0, 5, 30, 150],
    })


@pytest.fixture
def response_times():
    """Время ответа в часах: есть выброс (500ч) и некорректное (-2ч)."""
    return pd.DataFrame({
        "question_id":     [1, 2, 3, 4, 5],
        "hours_to_answer": [0.5, 2.2, 500.0, -2.0, 24.0],
        "owner_reputation": [10, 0, 9999, 50, 100],
    })


@pytest.fixture
def time_questions():
    """Вопросы с временными метками (вход task5)."""
    return pd.DataFrame({
        "question_id": range(7),
        "created_at": [
            "2025-06-02 09:00:00",  # Пн
            "2025-06-03 14:00:00",  # Вт
            "2025-06-04 10:00:00",  # Ср
            "2025-06-05 11:00:00",  # Чт
            "2025-06-06 15:00:00",  # Пт
            "2025-06-07 12:00:00",  # Сб выходной
            "2025-06-08 20:00:00",  # Вс выходной
        ],
    })
