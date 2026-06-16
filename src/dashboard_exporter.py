import os
import numpy as np
import pandas as pd


def export_executive_kpis(production_df: pd.DataFrame, save_dir: str):
    overall = {
        "total_production_records": int(len(production_df)),
        "total_actual_output": int(production_df["actual_output_units"].sum()),
        "total_good_units": int(production_df["good_units"].sum()),
        "total_rejected_units": int(production_df["rejected_units"].sum()),
        "total_downtime_min": round(
            float(production_df["downtime_min"].sum()), 2
        ),
        "avg_oee": round(float(production_df["oee"].mean()), 4),
        "avg_availability": round(
            float(production_df["availability_rate"].mean()), 4
        ),
        "avg_performance": round(
            float(production_df["performance_rate"].mean()), 4
        ),
        "avg_quality": round(float(production_df["quality_rate"].mean()), 4),
        "overall_rejection_rate": round(
            float(
                production_df["rejected_units"].sum()
                / production_df["actual_output_units"].sum()
            ),
            4,
        ),
        "world_class_pct": round(
            float(
                (production_df["oee"] >= 0.85).sum()
                / len(production_df)
                * 100
            ),
            2,
        ),
    }

    kpi_df = pd.DataFrame([overall])
    path = os.path.join(save_dir, "pbi_executive_kpis.csv")
    kpi_df.to_csv(path, index=False)
    return kpi_df


def export_oee_summary(production_df: pd.DataFrame, save_dir: str):
    oee_line = (
        production_df.groupby("production_line")
        .agg(
            avg_oee=("oee", "mean"),
            avg_availability=("availability_rate", "mean"),
            avg_performance=("performance_rate", "mean"),
            avg_quality=("quality_rate", "mean"),
            total_output=("actual_output_units", "sum"),
            total_good_units=("good_units", "sum"),
            total_rejected=("rejected_units", "sum"),
            total_downtime_min=("downtime_min", "sum"),
        )
        .reset_index()
    )
    for col in [
        "avg_oee",
        "avg_availability",
        "avg_performance",
        "avg_quality",
    ]:
        oee_line[col] = oee_line[col].round(4)
    oee_line["rejection_rate_pct"] = (
        oee_line["total_rejected"] / oee_line["total_output"] * 100
    ).round(2)
    oee_line["oee_vs_world_class"] = (oee_line["avg_oee"] - 0.85).round(4)
    oee_line["oee_label"] = oee_line["avg_oee"].apply(
        lambda x: (
            "World Class"
            if x >= 0.85
            else (
                "Good"
                if x >= 0.75
                else (
                    "Average"
                    if x >= 0.60
                    else "Below Average" if x >= 0.40 else "Poor"
                )
            )
        )
    )

    path = os.path.join(save_dir, "pbi_oee_summary.csv")
    oee_line.to_csv(path, index=False)
    return oee_line


def export_monthly_oee(production_df: pd.DataFrame, save_dir: str):
    monthly = (
        production_df.groupby(
            ["year", "month", "month_name", "quarter", "production_line"]
        )
        .agg(
            avg_oee=("oee", "mean"),
            avg_availability=("availability_rate", "mean"),
            avg_performance=("performance_rate", "mean"),
            avg_quality=("quality_rate", "mean"),
            total_output=("actual_output_units", "sum"),
            total_good_units=("good_units", "sum"),
            total_rejected=("rejected_units", "sum"),
            total_downtime_min=("downtime_min", "sum"),
        )
        .reset_index()
        .sort_values(["year", "month", "production_line"])
    )
    for col in [
        "avg_oee",
        "avg_availability",
        "avg_performance",
        "avg_quality",
    ]:
        monthly[col] = monthly[col].round(4)

    monthly["month_year"] = monthly["year"].astype(str) + "-" + monthly[
        "month"
    ].astype(str).str.zfill(2)
    monthly["oee_target_gap"] = (monthly["avg_oee"] - 0.85).round(4)

    path = os.path.join(save_dir, "pbi_monthly_oee.csv")
    monthly.to_csv(path, index=False)
    return monthly


def export_shift_performance(production_df: pd.DataFrame, save_dir: str):
    shift = (
        production_df.groupby(["shift", "production_line"])
        .agg(
            avg_oee=("oee", "mean"),
            avg_availability=("availability_rate", "mean"),
            avg_performance=("performance_rate", "mean"),
            avg_quality=("quality_rate", "mean"),
            total_output=("actual_output_units", "sum"),
            total_good_units=("good_units", "sum"),
            avg_downtime_min=("downtime_min", "mean"),
            total_downtime_min=("downtime_min", "sum"),
        )
        .reset_index()
    )
    for col in [
        "avg_oee",
        "avg_availability",
        "avg_performance",
        "avg_quality",
    ]:
        shift[col] = shift[col].round(4)
    shift["avg_downtime_min"] = shift["avg_downtime_min"].round(2)

    shift_order = {"Morning": 1, "Afternoon": 2, "Night": 3}
    shift["shift_order"] = shift["shift"].map(shift_order)
    shift = shift.sort_values(["production_line", "shift_order"])
    shift = shift.drop(columns=["shift_order"])

    path = os.path.join(save_dir, "pbi_shift_performance.csv")
    shift.to_csv(path, index=False)
    return shift


def export_downtime_analysis(downtime_df: pd.DataFrame, save_dir: str):
    by_reason = (
        downtime_df.groupby("downtime_reason")
        .agg(
            occurrence_count=("downtime_id", "count"),
            total_downtime_min=("downtime_min", "sum"),
            avg_downtime_min=("downtime_min", "mean"),
        )
        .reset_index()
        .sort_values("total_downtime_min", ascending=False)
    )
    by_reason["avg_downtime_min"] = by_reason["avg_downtime_min"].round(2)
    by_reason["cumulative_pct"] = (
        by_reason["total_downtime_min"].cumsum()
        / by_reason["total_downtime_min"].sum()
        * 100
    ).round(2)
    by_reason["pct_of_total"] = (
        by_reason["total_downtime_min"]
        / by_reason["total_downtime_min"].sum()
        * 100
    ).round(2)

    by_line = (
        downtime_df.groupby(["production_line", "downtime_reason"])
        .agg(
            occurrence_count=("downtime_id", "count"),
            total_downtime_min=("downtime_min", "sum"),
            avg_downtime_min=("downtime_min", "mean"),
        )
        .reset_index()
        .sort_values(
            ["production_line", "total_downtime_min"], ascending=[True, False]
        )
    )
    by_line["avg_downtime_min"] = by_line["avg_downtime_min"].round(2)

    monthly_downtime = (
        downtime_df.groupby(["year", "month", "production_line"])
        .agg(
            total_downtime_min=("downtime_min", "sum"),
            occurrence_count=("downtime_id", "count"),
        )
        .reset_index()
        .sort_values(["year", "month", "production_line"])
    )
    monthly_downtime["month_year"] = monthly_downtime["year"].astype(
        str
    ) + "-" + monthly_downtime["month"].astype(str).str.zfill(2)

    reason_path = os.path.join(save_dir, "pbi_downtime_by_reason.csv")
    line_path = os.path.join(save_dir, "pbi_downtime_by_line.csv")
    monthly_path = os.path.join(save_dir, "pbi_downtime_monthly.csv")

    by_reason.to_csv(reason_path, index=False)
    by_line.to_csv(line_path, index=False)
    monthly_downtime.to_csv(monthly_path, index=False)

    return by_reason, by_line, monthly_downtime


def export_quality_analysis(
    production_df: pd.DataFrame, defect_df: pd.DataFrame, save_dir: str
):
    quality_line = (
        production_df.groupby("production_line")
        .agg(
            avg_quality_rate=("quality_rate", "mean"),
            total_output=("actual_output_units", "sum"),
            total_good_units=("good_units", "sum"),
            total_rejected=("rejected_units", "sum"),
        )
        .reset_index()
    )
    quality_line["avg_quality_rate"] = quality_line["avg_quality_rate"].round(4)
    quality_line["rejection_rate_pct"] = (
        quality_line["total_rejected"] / quality_line["total_output"] * 100
    ).round(2)

    defect_by_type = (
        defect_df.groupby("defect_type")
        .agg(
            occurrence_count=("defect_id", "count"),
            total_defects=("defect_count", "sum"),
        )
        .reset_index()
        .sort_values("total_defects", ascending=False)
    )
    defect_by_type["pct_of_total"] = (
        defect_by_type["total_defects"]
        / defect_by_type["total_defects"].sum()
        * 100
    ).round(2)

    defect_by_line_type = (
        defect_df.groupby(["production_line", "defect_type"])
        .agg(
            occurrence_count=("defect_id", "count"),
            total_defects=("defect_count", "sum"),
        )
        .reset_index()
        .sort_values(
            ["production_line", "total_defects"], ascending=[True, False]
        )
    )

    monthly_defects = (
        defect_df.groupby(["year", "month", "production_line"])
        .agg(
            total_defects=("defect_count", "sum"),
            occurrence_count=("defect_id", "count"),
        )
        .reset_index()
        .sort_values(["year", "month", "production_line"])
    )
    monthly_defects["month_year"] = monthly_defects["year"].astype(
        str
    ) + "-" + monthly_defects["month"].astype(str).str.zfill(2)

    monthly_quality = (
        production_df.groupby(["year", "month", "production_line"])
        .agg(
            avg_quality_rate=("quality_rate", "mean"),
            total_rejected=("rejected_units", "sum"),
            total_output=("actual_output_units", "sum"),
        )
        .reset_index()
        .sort_values(["year", "month", "production_line"])
    )
    monthly_quality["avg_quality_rate"] = monthly_quality[
        "avg_quality_rate"
    ].round(4)
    monthly_quality["rejection_rate_pct"] = (
        monthly_quality["total_rejected"] / monthly_quality["total_output"] * 100
    ).round(2)
    monthly_quality["month_year"] = monthly_quality["year"].astype(
        str
    ) + "-" + monthly_quality["month"].astype(str).str.zfill(2)

    quality_line.to_csv(
        os.path.join(save_dir, "pbi_quality_by_line.csv"), index=False
    )
    defect_by_type.to_csv(
        os.path.join(save_dir, "pbi_defect_by_type.csv"), index=False
    )
    defect_by_line_type.to_csv(
        os.path.join(save_dir, "pbi_defect_by_line_type.csv"), index=False
    )
    monthly_defects.to_csv(
        os.path.join(save_dir, "pbi_monthly_defects.csv"), index=False
    )
    monthly_quality.to_csv(
        os.path.join(save_dir, "pbi_monthly_quality.csv"), index=False
    )

    return quality_line, defect_by_type, defect_by_line_type


def export_machine_utilization(production_df: pd.DataFrame, save_dir: str):
    machine = (
        production_df.groupby("machine_id")
        .agg(
            avg_oee=("oee", "mean"),
            avg_availability=("availability_rate", "mean"),
            total_output=("actual_output_units", "sum"),
            total_good_units=("good_units", "sum"),
            total_downtime_min=("downtime_min", "sum"),
            total_run_time=("run_time_min", "sum"),
            total_planned_time=("planned_time_min", "sum"),
        )
        .reset_index()
    )
    machine["avg_oee"] = machine["avg_oee"].round(4)
    machine["avg_availability"] = machine["avg_availability"].round(4)
    machine["utilization_pct"] = (
        machine["total_run_time"] / machine["total_planned_time"] * 100
    ).round(2)
    machine["oee_label"] = machine["avg_oee"].apply(
        lambda x: (
            "World Class"
            if x >= 0.85
            else (
                "Good"
                if x >= 0.75
                else "Average" if x >= 0.60 else "Below Average"
            )
        )
    )
    machine = machine.sort_values("avg_oee", ascending=False)

    path = os.path.join(save_dir, "pbi_machine_utilization.csv")
    machine.to_csv(path, index=False)
    return machine


def export_product_performance(production_df: pd.DataFrame, save_dir: str):
    product = (
        production_df.groupby("product")
        .agg(
            avg_oee=("oee", "mean"),
            avg_quality_rate=("quality_rate", "mean"),
            total_output=("actual_output_units", "sum"),
            total_good_units=("good_units", "sum"),
            total_rejected=("rejected_units", "sum"),
        )
        .reset_index()
    )
    product["avg_oee"] = product["avg_oee"].round(4)
    product["avg_quality_rate"] = product["avg_quality_rate"].round(4)
    product["rejection_rate_pct"] = (
        product["total_rejected"] / product["total_output"] * 100
    ).round(2)
    product = product.sort_values("avg_oee", ascending=False)

    path = os.path.join(save_dir, "pbi_product_performance.csv")
    product.to_csv(path, index=False)
    return product


def run_dashboard_export(cleaned_data: dict, save_dir: str = "data/processed"):
    production_df = cleaned_data["production"]
    defect_df = cleaned_data["defects"]
    downtime_df = cleaned_data["downtime"]

    export_executive_kpis(production_df, save_dir)
    export_oee_summary(production_df, save_dir)
    export_monthly_oee(production_df, save_dir)
    export_shift_performance(production_df, save_dir)
    export_downtime_analysis(downtime_df, save_dir)
    export_quality_analysis(production_df, defect_df, save_dir)
    export_machine_utilization(production_df, save_dir)
    export_product_performance(production_df, save_dir)