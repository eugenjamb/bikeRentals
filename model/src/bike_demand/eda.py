"""Pre-test exploration only. All plots describe observations, not causation."""

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .config import OUTPUT_DIR, PROCESSED_DATA_DIR, RAW_DATA_PATH, TEST_PERIOD_DAYS
from .data import load_hourly


def save_plot(fig, name):
    destination = OUTPUT_DIR / "figures" / f"{name}.png"
    fig.savefig(destination, dpi=150, bbox_inches="tight")
    plt.close(fig)


def run_eda():
    hourly = load_hourly(RAW_DATA_PATH)
    test_end = hourly.index.max().normalize() + pd.Timedelta(days=1)
    test_start = test_end - pd.Timedelta(days=TEST_PERIOD_DAYS)
    split = {
        "test_start_inclusive": str(test_start),
        "test_end_exclusive": str(test_end),
        "evaluation": "rolling one-hour-ahead",
    }
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    split_path = PROCESSED_DATA_DIR / "split.json"
    if split_path.exists() and json.loads(split_path.read_text()) != split:
        raise ValueError("Frozen split differs; investigate before changing it")
    split_path.write_text(json.dumps(split, indent=2) + "\n")
    # Only timestamp presence is audited globally. No held-out target EDA.
    development = hourly.loc[hourly.index < test_start].copy()
    observed = development.dropna(subset=["cnt"]).copy()
    observed["hour"] = observed.index.hour
    observed["weekday_name"] = observed.index.day_name()
    observed["month"] = observed.index.month
    # Keep original normalized units: archive and website disagree on Celsius conversion.
    for folder in ("figures", "reports"):
        (OUTPUT_DIR / folder).mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    sns.histplot(observed["cnt"], bins=50, ax=axes[0])
    axes[0].set(title="Hourly demand distribution (pre-test)", xlabel="Rentals per hour")
    daily = development["cnt"].resample("D").mean()
    daily.plot(ax=axes[1], linewidth=0.8)
    axes[1].set(title="Daily mean hourly demand (pre-test)", ylabel="Mean observed hourly rentals", xlabel="Date")
    fig.tight_layout()
    save_plot(fig, "01_demand_distribution_and_trend")

    fig, ax = plt.subplots(figsize=(11, 4))
    table = observed.pivot_table(index="weekday_name", columns="hour", values="cnt", aggfunc="mean")
    table = table.reindex(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    sns.heatmap(table, cmap="YlOrRd", ax=ax, cbar_kws={"label": "Mean rentals"})
    ax.set(title="Demand by weekday and hour (pre-test)", xlabel="Hour", ylabel="")
    save_plot(fig, "02_weekday_hour_heatmap")

    fig, axes = plt.subplots(1, 2, figsize=(13, 4))
    table = observed.pivot_table(index="month", columns="hour", values="temp", aggfunc="mean")
    sns.heatmap(table, cmap="coolwarm", ax=axes[0], cbar_kws={"label": "Normalized temperature"})
    axes[0].set(title="Observed temperature by month and hour", xlabel="Hour", ylabel="Month")
    scatter = axes[1].hexbin(observed["temp"], observed["cnt"], gridsize=35, mincnt=1, cmap="viridis")
    fig.colorbar(scatter, ax=axes[1], label="Observed hours")
    axes[1].set(title="Observed temperature and demand (pre-test)", xlabel="Normalized temperature", ylabel="Hourly rentals")
    fig.tight_layout()
    save_plot(fig, "03_temperature_patterns")

    fig, axes = plt.subplots(1, 2, figsize=(13, 4))
    sns.lineplot(data=observed, x="hour", y="cnt", hue="workingday", errorbar=None, ax=axes[0])
    axes[0].set(title="Working-day demand profiles", ylabel="Mean rentals")
    columns = ["cnt", "temp", "atemp", "hum", "windspeed"]
    sns.heatmap(observed[columns].corr(), annot=True, fmt=".2f", cmap="vlag", center=0, vmin=-1, vmax=1, ax=axes[1])
    axes[1].set_title("Observed weather correlations (descriptive only)")
    fig.tight_layout()
    save_plot(fig, "04_profiles_and_correlations")

    fig, ax = plt.subplots(figsize=(11, 3))
    absent = development["cnt"].isna().groupby(development.index.to_period("M")).sum()
    absent.plot.bar(ax=ax, color="#477b9e")
    ax.set(title="Absent hourly timestamps before test", xlabel="Month", ylabel="Missing hours")
    save_plot(fig, "05_missing_hours")

    summary = {
        "first_timestamp": str(hourly.index.min()),
        "last_timestamp": str(hourly.index.max()),
        "observed_rows": int(hourly["cnt"].notna().sum()),
        "expected_hourly_rows": len(hourly),
        "missing_timestamps": int(hourly["cnt"].isna().sum()),
        "development_observed_rows": len(observed),
        "development_missing_hours": int(development["cnt"].isna().sum()),
        "test_start": str(test_start),
        "development_target_summary": observed["cnt"].describe().to_dict(),
        "missing_values_in_observed_rows": observed.isna().sum().to_dict(),
        "development_weather_correlations": observed[columns].corr()["cnt"].to_dict(),
        "peak_mean_hour_workingday": int(observed.loc[observed.workingday == 1].groupby("hour")["cnt"].mean().idxmax()),
        "peak_mean_hour_nonworkingday": int(observed.loc[observed.workingday == 0].groupby("hour")["cnt"].mean().idxmax()),
    }
    (OUTPUT_DIR / "reports" / "eda_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    observed[columns].describe().to_csv(OUTPUT_DIR / "reports" / "development_statistics.csv")
    return summary
