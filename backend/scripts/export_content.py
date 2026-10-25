"""Export small public demo assets from recorded experiments; never train."""

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "model/src"))

from bike_demand.data import load_hourly


def records(path):
    return pd.read_csv(path).to_dict(orient="records")


def export_content():
    output = ROOT / "backend/app/assets"
    output.mkdir(parents=True, exist_ok=True)
    experiment = ROOT / "outputs/experiments"
    metadata = json.loads((experiment / "hgb_grid_search/metadata.json").read_text())
    final = json.loads((experiment / "final_test/metadata.json").read_text())
    model_hash = hashlib.sha256((ROOT / "outputs/models/tuned_forecast_pipeline.joblib").read_bytes()).hexdigest()
    if model_hash != final["model_sha256"]:
        raise ValueError("Model differs from the recorded final evaluation. Review the evaluation artifacts before publishing new scores.")
    summary = json.loads((ROOT / "outputs/reports/eda_summary.json").read_text())
    hourly = load_hourly(ROOT / "data/raw/hour.csv")
    pretest = hourly.loc[hourly.index < metadata["test_split"]["test_start_inclusive"]].dropna(subset=["cnt"]).copy()
    heatmap = pretest.groupby([pretest.index.dayofweek, pretest.index.hour])["cnt"].mean()
    learning = pd.read_csv(experiment / "hgb_grid_search/learning_progress.csv").groupby("iteration")[["training_mae", "validation_mae"]].mean().reset_index()
    candidates = pd.read_csv(experiment / "hgb_grid_search/cv_results.csv").sort_values("rank_test_score")
    candidate_columns = ["rank_test_score", "mean_validation_mae", "param_regressor__learning_rate", "param_regressor__max_iter", "param_regressor__max_leaf_nodes", "param_regressor__l2_regularization", "param_select__feature_set"]
    study = {
        "model_hash": model_hash[:12],
        "data": summary,
        "selection": metadata["best_parameters"],
        "validation": records(experiment / "hgb_grid_search/mean_cv_metrics.csv"),
        "initial_comparison": records(experiment / "initial_fixed_settings/mean_cv_metrics.csv"),
        "final": records(experiment / "final_test/metrics.csv"),
        "coverage": final["coverage"],
        "heatmap": [{"weekday": int(day), "hour": int(hour), "demand": round(value, 1)} for (day, hour), value in heatmap.items()],
        "learning": learning.iloc[::4].to_dict(orient="records") + learning.tail(1).to_dict(orient="records"),
        "candidates": candidates[candidate_columns].head(8).to_dict(orient="records"),
        "hour_errors": records(experiment / "final_test/errors_by_hour.csv"),
    }
    (output / "study.json").write_text(json.dumps(study, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    definitions = [
        ("morning", "Morning commute", "2012-10-03 08:00", "A working-day morning peak."),
        ("midday", "Midday demand", "2012-10-03 12:00", "The same working day, between commute peaks."),
        ("evening", "Evening commute", "2012-10-03 17:00", "A busy working-day evening."),
        ("weekend", "Weekend afternoon", "2012-10-06 13:00", "A Saturday with a different daily rhythm."),
        ("overnight", "Quiet overnight", "2012-10-04 03:00", "A low-demand hour: relative errors can be large."),
    ]
    scenarios = []
    for name, label, timestamp, description in definitions:
        target = pd.Timestamp(timestamp)
        index = pd.date_range(target - pd.Timedelta(hours=168), periods=168, freq="h")
        history = hourly["cnt"].reindex(index)
        scenarios.append({
            "id": name, "label": label, "description": description,
            "actual": int(hourly.loc[target, "cnt"]),
            "request": {
                "target_timestamp": target.isoformat(),
                "holiday": bool(hourly.loc[target, "holiday"]),
                "workingday": bool(hourly.loc[target, "workingday"]),
                "history": [{"timestamp": time.isoformat(), "count": None if pd.isna(count) else float(count)} for time, count in history.items()],
            },
        })
    (output / "scenarios.json").write_text(json.dumps(scenarios, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Exported recorded study results and {len(scenarios)} past-only replay scenarios to {output}")


if __name__ == "__main__":
    export_content()
