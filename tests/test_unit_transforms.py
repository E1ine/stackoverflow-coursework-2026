"""
Модульные (unit) тесты — проверяют каждую чистую функцию изолированно.

Запуск:  pytest tests/test_unit_transforms.py -v
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from analytics import transforms as T  # noqa: E402


# ───────────────────────────── parse_tags ───────────────────────────────────
class TestParseTags:
    def test_multiple_tags(self):
        assert T.parse_tags("<python><pandas><sql>") == ["python", "pandas", "sql"]

    def test_single_tag(self):
        assert T.parse_tags("<java>") == ["java"]

    def test_tag_with_special_chars(self):
        assert T.parse_tags("<c++><c#>") == ["c++", "c#"]

    def test_empty_string(self):
        assert T.parse_tags("") == []

    @pytest.mark.parametrize("bad", [np.nan, None, 123, 4.5, ["x"]])
    def test_non_string_returns_empty(self, bad):
        assert T.parse_tags(bad) == []


# ───────────────────────────── deduplicate ──────────────────────────────────
class TestDeduplicate:
    def test_removes_duplicates(self, raw_questions_csv):
        out = T.deduplicate(raw_questions_csv, key="Id")
        assert len(out) == 3
        assert out["Id"].tolist() == [1, 2, 3]

    def test_keeps_first_occurrence(self):
        df = pd.DataFrame({"Id": [1, 1], "v": ["a", "b"]})
        assert T.deduplicate(df, "Id")["v"].tolist() == ["a"]

    def test_no_duplicates_unchanged(self):
        df = pd.DataFrame({"Id": [1, 2, 3]})
        assert len(T.deduplicate(df, "Id")) == 3


# ───────────────────────────── get_top_tags ─────────────────────────────────
class TestGetTopTags:
    def test_ranking_by_total(self, tag_counts):
        # python=250, c#=90, java=90  →  python первый
        assert T.get_top_tags(tag_counts, n=1) == ["python"]

    def test_n_limits_result(self, tag_counts):
        assert len(T.get_top_tags(tag_counts, n=2)) == 2

    def test_returns_all_when_n_large(self, tag_counts):
        assert set(T.get_top_tags(tag_counts, n=99)) == {"python", "java", "c#"}


# ───────────────────────────── compute_growth ───────────────────────────────
class TestComputeGrowth:
    def test_growth_percentage(self, tag_counts):
        out = T.compute_growth(tag_counts, ["python", "java", "c#"])
        row = out.set_index("tag_name")["change_pct"]
        # python: (150-100)/(100+1)*100 = 49.5
        assert row["python"] == pytest.approx(49.5, abs=0.1)
        # c#: (60-30)/(30+1)*100 = 96.8  (рост)
        assert row["c#"] == pytest.approx(96.8, abs=0.1)
        # java: (40-50)/(50+1)*100 = -19.6 (падение)
        assert row["java"] < 0

    def test_no_division_by_zero(self):
        df = pd.DataFrame({
            "month": pd.to_datetime(["2024-01-01", "2024-02-01"]),
            "tag_name": ["new", "new"],
            "question_count": [0, 10],   # стартовали с нуля
        })
        out = T.compute_growth(df, ["new"])
        assert np.isfinite(out["change_pct"]).all()  # нет inf/NaN


# ───────────────────────── compute_user_features ────────────────────────────
class TestUserFeatures:
    def test_feature_columns_created(self, user_aggregates):
        out = T.compute_user_features(user_aggregates)
        for col in ["answer_ratio", "acceptance_rate", "log_reputation", "avg_score"]:
            assert col in out.columns

    def test_ratios_in_valid_range(self, user_aggregates):
        out = T.compute_user_features(user_aggregates)
        assert (out["answer_ratio"].between(0, 1)).all()
        assert (out["acceptance_rate"].between(0, 1)).all()

    def test_log_reputation_formula(self, user_aggregates):
        out = T.compute_user_features(user_aggregates)
        expected = np.log1p(user_aggregates["reputation"])
        pd.testing.assert_series_equal(
            out["log_reputation"], expected, check_names=False
        )

    def test_pure_questioner(self, user_aggregates):
        # user 1: только вопросы → answer_ratio ≈ 0
        out = T.compute_user_features(user_aggregates).set_index("user_id")
        assert out.loc[1, "answer_ratio"] < 0.1

    def test_does_not_mutate_input(self, user_aggregates):
        before = user_aggregates.copy()
        T.compute_user_features(user_aggregates)
        pd.testing.assert_frame_equal(user_aggregates, before)


# ───────────────────────── drop_score_outliers ──────────────────────────────
class TestScoreOutliers:
    def test_removes_top_percentile(self):
        df = pd.DataFrame({"avg_score": list(range(100)) + [10_000]})
        out = T.drop_score_outliers(df, q=0.99)
        assert out["avg_score"].max() < 10_000


# ─────────────────────── prepare_prediction_features ────────────────────────
class TestPredictionFeatures:
    def test_log_views(self):
        df = pd.DataFrame({"view_count": [0, 99], "owner_reputation": [0, 9],
                           "x": [np.nan, 1.0]})
        out = T.prepare_prediction_features(df)
        assert out["log_views"].iloc[1] == pytest.approx(np.log1p(99))

    def test_no_nan_after(self):
        df = pd.DataFrame({"view_count": [1], "owner_reputation": [1],
                           "x": [np.nan]})
        assert not T.prepare_prediction_features(df).isna().any().any()


# ─────────────────────── prepare_response_times ─────────────────────────────
class TestResponseTimes:
    def test_drops_outliers_and_negatives(self, response_times):
        out = T.prepare_response_times(response_times)
        # из [0.5, 2.2, 500, -2, 24] остаются 0.5, 2.2, 24
        assert len(out) == 3
        assert out["hours_to_answer"].max() <= T.MAX_RESPONSE_HOURS
        assert (out["hours_to_answer"] > 0).all()

    def test_log_hours_formula(self, response_times):
        out = T.prepare_response_times(response_times)
        expected = np.log1p(out["hours_to_answer"])
        pd.testing.assert_series_equal(out["log_hours"], expected, check_names=False)

    def test_custom_threshold(self, response_times):
        out = T.prepare_response_times(response_times, max_hours=10)
        assert out["hours_to_answer"].max() <= 10


# ───────────────────────── add_time_features ────────────────────────────────
class TestTimeFeatures:
    def test_hour_extracted(self, time_questions):
        out = T.add_time_features(time_questions)
        assert out["hour"].tolist() == [9, 14, 10, 11, 15, 12, 20]

    def test_weekend_flag(self, time_questions):
        out = T.add_time_features(time_questions)
        # последние два — Сб/Вс
        assert out["is_weekend"].tolist() == [0, 0, 0, 0, 0, 1, 1]

    def test_day_of_week_monday_zero(self, time_questions):
        out = T.add_time_features(time_questions)
        assert out["day_of_week"].iloc[0] == 0  # понедельник = 0


# ───────────────────────────── weekend_share ────────────────────────────────
class TestWeekendShare:
    def test_share_value(self, time_questions):
        out = T.add_time_features(time_questions)
        assert T.weekend_share(out) == pytest.approx(2 / 7)

    def test_empty_returns_zero(self):
        empty = pd.DataFrame({"is_weekend": []})
        assert T.weekend_share(empty) == 0.0
