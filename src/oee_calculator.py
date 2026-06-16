import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os


def compute_oee_by_line(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby("production_line")
        .agg(
            total_records=("record_id", "count"),
            avg_availability=("availability_rate", "mean"),
            avg_performance=("performance_rate", "mean"),
            avg_quality=("quality_rate", "mean"),
            avg_oee=("oee", "mean"),
            total_planned_time=("planned_time_min", "sum"),
            total_run_time=("run_time_min", "sum"),
            total_downtime=("downtime_min", "sum"),
            total_actual_output=("actual_output_units", "sum"),
            total_good_units=("good_units", "sum"),
            total_rejected_units=("rejected_units", "sum"),
        )
        .reset_index()
    )
    for col in ["avg_availability", "avg_performance", "avg_quality", "avg_oee"]:
        summary[col] = summary[col].round(4)
    summary["overall_rejection_rate"] = (
        summary["total_rejected_units"] / summary["total_actual_output"]
    ).round(4)
    summary = summary.sort_values("avg_oee", ascending=False)
    return summary


def compute_oee_by_shift(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby(["production_line", "shift"])
        .agg(
            avg_availability=("availability_rate", "mean"),
            avg_performance=("performance_rate", "mean"),
            avg_quality=("quality_rate", "mean"),
            avg_oee=("oee", "mean"),
            total_downtime=("downtime_min", "sum"),
            total_good_units=("good_units", "sum"),
            total_actual_output=("actual_output_units", "sum"),
        )
        .reset_index()
    )
    for col in ["avg_availability", "avg_performance", "avg_quality", "avg_oee"]:
        summary[col] = summary[col].round(4)
    return summary


def compute_monthly_oee(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby(["year", "month", "month_name", "production_line"])
        .agg(
            avg_oee=("oee", "mean"),
            avg_availability=("availability_rate", "mean"),
            avg_performance=("performance_rate", "mean"),
            avg_quality=("quality_rate", "mean"),
            total_good_units=("good_units", "sum"),
            total_actual_output=("actual_output_units", "sum"),
            total_downtime_min=("downtime_min", "sum"),
        )
        .reset_index()
        .sort_values(["year", "month", "production_line"])
    )
    for col in ["avg_oee", "avg_availability", "avg_performance", "avg_quality"]:
        summary[col] = summary[col].round(4)
    summary["month_year"] = (
        summary["year"].astype(str) + "-"
        + summary["month"].astype(str).str.zfill(2)
    )
    return summary


def compute_downtime_analysis(downtime_df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        downtime_df.groupby(["production_line", "downtime_reason"])
        .agg(
            occurrence_count=("downtime_id", "count"),
            total_downtime_min=("downtime_min", "sum"),
            avg_downtime_min=("downtime_min", "mean"),
        )
        .reset_index()
        .sort_values("total_downtime_min", ascending=False)
    )
    summary["avg_downtime_min"] = summary["avg_downtime_min"].round(2)
    return summary


def compute_defect_analysis(defect_df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        defect_df.groupby(["production_line", "defect_type"])
        .agg(
            occurrence_count=("defect_id", "count"),
            total_defect_count=("defect_count", "sum"),
        )
        .reset_index()
        .sort_values("total_defect_count", ascending=False)
    )
    return summary


def plot_oee_by_line(oee_by_line: pd.DataFrame, save_dir: str):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    colors = ["#2c7bb6", "#1a9641", "#fdae61", "#d7191c", "#7b2d8b"]
    lines = oee_by_line["production_line"].tolist()

    axes[0].barh(lines, oee_by_line["avg_oee"], color=colors, edgecolor="white")
    axes[0].axvline(0.85, color="green", linewidth=1.5,
                    linestyle="--", label="World Class (85%)")
    axes[0].axvline(0.60, color="orange", linewidth=1.5,
                    linestyle="--", label="Average (60%)")
    axes[0].set_title("Average OEE by Production Line",
                      fontsize=13, fontweight="bold")
    axes[0].set_xlabel("OEE")
    axes[0].set_xlim(0, 1.05)
    axes[0].legend(fontsize=9)
    for i, v in enumerate(oee_by_line["avg_oee"]):
        axes[0].text(v + 0.01, i, f"{v:.1%}", va="center", fontsize=10)

    metrics = ["avg_availability", "avg_performance", "avg_quality"]
    labels = ["Availability", "Performance", "Quality"]
    x = np.arange(len(lines))
    width = 0.25

    for i, (metric, label) in enumerate(zip(metrics, labels)):
        axes[1].bar(x + i * width, oee_by_line[metric],
                    width, label=label, edgecolor="white")
    axes[1].set_title("OEE Components by Production Line",
                      fontsize=13, fontweight="bold")
    axes[1].set_xticks(x + width)
    axes[1].set_xticklabels(lines, rotation=15, ha="right")
    axes[1].set_ylabel("Rate")
    axes[1].set_ylim(0, 1.1)
    axes[1].legend()
    axes[1].grid(True, axis="y", alpha=0.3)

    plt.tight_layout()
    path = os.path.join(save_dir, "oee_by_line.png")
    plt.savefig(path, dpi=150)
    plt.close()


def plot_monthly_oee_trend(monthly_oee: pd.DataFrame, save_dir: str):
    fig, ax = plt.subplots(figsize=(16, 6))
    lines = monthly_oee["production_line"].unique()
    colors = ["#2c7bb6", "#1a9641", "#fdae61", "#d7191c", "#7b2d8b"]

    for line, color in zip(lines, colors):
        subset = monthly_oee[monthly_oee["production_line"] == line]
        ax.plot(subset["month_year"], subset["avg_oee"],
                marker="o", markersize=3, linewidth=1.5,
                label=line, color=color)

    ax.axhline(0.85, color="green", linewidth=1,
               linestyle="--", label="World Class (85%)")
    ax.axhline(0.60, color="orange", linewidth=1,
               linestyle="--", label="Average (60%)")
    ax.set_title("Monthly OEE Trend by Production Line",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Month")
    ax.set_ylabel("OEE")
    ax.set_ylim(0, 1.05)
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.tight_layout()
    path = os.path.join(save_dir, "monthly_oee_trend.png")
    plt.savefig(path, dpi=150)
    plt.close()


def plot_shift_oee(oee_by_shift: pd.DataFrame, save_dir: str):
    pivot = oee_by_shift.pivot(
        index="production_line", columns="shift", values="avg_oee"
    )
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(pivot.index))
    width = 0.25
    shifts = pivot.columns.tolist()
    colors = ["#2c7bb6", "#fdae61", "#d7191c"]

    for i, (shift, color) in enumerate(zip(shifts, colors)):
        ax.bar(x + i * width, pivot[shift], width,
               label=shift, color=color, edgecolor="white")

    ax.set_title("OEE by Shift and Production Line",
                 fontsize=13, fontweight="bold")
    ax.set_xticks(x + width)
    ax.set_xticklabels(pivot.index, rotation=15, ha="right")
    ax.set_ylabel("Average OEE")
    ax.set_ylim(0, 1.0)
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    path = os.path.join(save_dir, "oee_by_shift.png")
    plt.savefig(path, dpi=150)
    plt.close()


def plot_downtime_pareto(downtime_analysis: pd.DataFrame, save_dir: str):
    top_reasons = (
        downtime_analysis.groupby("downtime_reason")["total_downtime_min"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    top_reasons["cumulative_pct"] = (
        top_reasons["total_downtime_min"].cumsum()
        / top_reasons["total_downtime_min"].sum() * 100
    )

    fig, ax1 = plt.subplots(figsize=(13, 6))
    ax2 = ax1.twinx()

    ax1.bar(top_reasons["downtime_reason"],
            top_reasons["total_downtime_min"],
            color="#2c7bb6", edgecolor="white")
    ax2.plot(top_reasons["downtime_reason"],
             top_reasons["cumulative_pct"],
             color="#d7191c", marker="o", linewidth=2)
    ax2.axhline(80, color="orange", linewidth=1, linestyle="--", label="80% threshold")

    ax1.set_title("Downtime Pareto Analysis by Reason",
                  fontsize=13, fontweight="bold")
    ax1.set_xlabel("Downtime Reason")
    ax1.set_ylabel("Total Downtime (minutes)")
    ax2.set_ylabel("Cumulative Percentage (%)")
    ax2.set_ylim(0, 110)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    path = os.path.join(save_dir, "downtime_pareto.png")
    plt.savefig(path, dpi=150)
    plt.close()


def plot_defect_breakdown(defect_analysis: pd.DataFrame, save_dir: str):
    top_defects = (
        defect_analysis.groupby("defect_type")["total_defect_count"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    axes[0].barh(
        top_defects["defect_type"],
        top_defects["total_defect_count"],
        color="#d7191c", edgecolor="white"
    )
    axes[0].set_title("Total Defects by Type",
                      fontsize=13, fontweight="bold")
    axes[0].set_xlabel("Total Defect Count")
    axes[0].grid(True, axis="x", alpha=0.3)

    axes[1].pie(
        top_defects["total_defect_count"],
        labels=top_defects["defect_type"],
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops={"edgecolor": "white"}
    )
    axes[1].set_title("Defect Type Distribution",
                      fontsize=13, fontweight="bold")

    plt.tight_layout()
    path = os.path.join(save_dir, "defect_breakdown.png")
    plt.savefig(path, dpi=150)
    plt.close()


def plot_oee_distribution(df: pd.DataFrame, save_dir: str):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].hist(df["oee"], bins=40, color="#2c7bb6", edgecolor="white")
    axes[0].axvline(df["oee"].mean(), color="red", linewidth=1.5,
                    linestyle="--", label=f"Mean: {df['oee'].mean():.3f}")
    axes[0].axvline(0.85, color="green", linewidth=1.5,
                    linestyle="--", label="World Class: 0.85")
    axes[0].set_title("OEE Distribution (All Lines & Shifts)",
                      fontsize=13, fontweight="bold")
    axes[0].set_xlabel("OEE")
    axes[0].set_ylabel("Frequency")
    axes[0].legend()

    oee_class_counts = df["oee_class"].value_counts()
    order = ["Poor", "Below Average", "Average", "Good", "World Class"]
    oee_class_counts = oee_class_counts.reindex(
        [o for o in order if o in oee_class_counts.index]
    )
    colors_map = {
        "Poor": "#d7191c",
        "Below Average": "#fdae61",
        "Average": "#ffffbf",
        "Good": "#a6d96a",
        "World Class": "#1a9641"
    }
    bar_colors = [colors_map[c] for c in oee_class_counts.index]
    axes[1].bar(oee_class_counts.index, oee_class_counts.values,
                color=bar_colors, edgecolor="white")
    axes[1].set_title("OEE Classification Distribution",
                      fontsize=13, fontweight="bold")
    axes[1].set_xlabel("OEE Class")
    axes[1].set_ylabel("Number of Records")
    for i, v in enumerate(oee_class_counts.values):
        axes[1].text(i, v + 10, f"{v:,}", ha="center", fontsize=10)

    plt.tight_layout()
    path = os.path.join(save_dir, "oee_distribution.png")
    plt.savefig(path, dpi=150)
    plt.close()


def plot_rejection_rate_by_line(oee_by_line: pd.DataFrame, save_dir: str):
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ["#2c7bb6", "#1a9641", "#fdae61", "#d7191c", "#7b2d8b"]
    bars = ax.bar(
        oee_by_line["production_line"],
        oee_by_line["overall_rejection_rate"] * 100,
        color=colors, edgecolor="white"
    )
    ax.set_title("Overall Rejection Rate by Production Line",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Production Line")
    ax.set_ylabel("Rejection Rate (%)")
    ax.grid(True, axis="y", alpha=0.3)
    for bar, val in zip(bars, oee_by_line["overall_rejection_rate"]):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.05,
                f"{val:.2%}", ha="center", fontsize=10)
    plt.tight_layout()
    path = os.path.join(save_dir, "rejection_rate_by_line.png")
    plt.savefig(path, dpi=150)
    plt.close()


def run_oee_analysis(cleaned_data: dict,
                     save_dir: str = "data/processed") -> dict:
    production_df = cleaned_data["production"]
    defect_df = cleaned_data["defects"]
    downtime_df = cleaned_data["downtime"]

    oee_by_line = compute_oee_by_line(production_df)
    oee_by_shift = compute_oee_by_shift(production_df)
    monthly_oee = compute_monthly_oee(production_df)
    downtime_analysis = compute_downtime_analysis(downtime_df)
    defect_analysis = compute_defect_analysis(defect_df)

    plot_oee_by_line(oee_by_line, save_dir)
    plot_monthly_oee_trend(monthly_oee, save_dir)
    plot_shift_oee(oee_by_shift, save_dir)
    plot_downtime_pareto(downtime_analysis, save_dir)
    plot_defect_breakdown(defect_analysis, save_dir)
    plot_oee_distribution(production_df, save_dir)
    plot_rejection_rate_by_line(oee_by_line, save_dir)

    oee_by_line.to_csv(
        os.path.join(save_dir, "oee_by_line.csv"), index=False)
    oee_by_shift.to_csv(
        os.path.join(save_dir, "oee_by_shift.csv"), index=False)
    monthly_oee.to_csv(
        os.path.join(save_dir, "monthly_oee.csv"), index=False)
    downtime_analysis.to_csv(
        os.path.join(save_dir, "downtime_analysis.csv"), index=False)
    defect_analysis.to_csv(
        os.path.join(save_dir, "defect_analysis.csv"), index=False)

    return {
        "oee_by_line": oee_by_line,
        "oee_by_shift": oee_by_shift,
        "monthly_oee": monthly_oee,
        "downtime_analysis": downtime_analysis,
        "defect_analysis": defect_analysis
    }