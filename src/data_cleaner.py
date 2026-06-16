import pandas as pd
import numpy as np
import os


def load_raw_data(data_dir: str = "data/raw") -> dict:
    production_df = pd.read_csv(os.path.join(data_dir, "production_log.csv"))
    defect_df = pd.read_csv(os.path.join(data_dir, "defect_log.csv"))
    downtime_df = pd.read_csv(os.path.join(data_dir, "downtime_log.csv"))

    production_df["date"] = pd.to_datetime(production_df["date"])
    defect_df["date"] = pd.to_datetime(defect_df["date"])
    downtime_df["date"] = pd.to_datetime(downtime_df["date"])

    return {
        "production": production_df,
        "defects": defect_df,
        "downtime": downtime_df
    }


def validate_production_data(df: pd.DataFrame) -> pd.DataFrame:
    initial_count = len(df)
    report = {}

    missing = df.isnull().sum()
    missing = missing[missing > 0]
    report["missing_values"] = missing.to_dict() if not missing.empty else "None"

    df = df.dropna(subset=["record_id", "date", "production_line",
                            "actual_output_units", "good_units", "oee"])

    invalid_oee = ((df["oee"] < 0) | (df["oee"] > 1)).sum()
    report["invalid_oee_records"] = int(invalid_oee)
    df = df[(df["oee"] >= 0) & (df["oee"] <= 1)]

    invalid_units = (df["good_units"] > df["actual_output_units"]).sum()
    report["invalid_unit_records"] = int(invalid_units)
    df = df[df["good_units"] <= df["actual_output_units"]]

    invalid_time = (df["run_time_min"] > df["planned_time_min"]).sum()
    report["invalid_time_records"] = int(invalid_time)
    df = df[df["run_time_min"] <= df["planned_time_min"]]

    invalid_downtime = (df["downtime_min"] < 0).sum()
    report["negative_downtime_records"] = int(invalid_downtime)
    df = df[df["downtime_min"] >= 0]

    df["availability_rate"] = df["availability_rate"].clip(0, 1)
    df["performance_rate"] = df["performance_rate"].clip(0, 1)
    df["quality_rate"] = df["quality_rate"].clip(0, 1)
    df["oee"] = df["oee"].clip(0, 1)

    report["initial_records"] = initial_count
    report["final_records"] = len(df)
    report["records_removed"] = initial_count - len(df)

    return df, report


def validate_defect_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["defect_id", "date", "production_line", "defect_type"])
    df = df[df["defect_count"] > 0]
    df = df[df["defect_count"] < 10000]
    return df


def validate_downtime_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["downtime_id", "date", "production_line", "downtime_reason"])
    df = df[df["downtime_min"] > 0]
    df = df[df["downtime_min"] <= 480]
    return df


def add_oee_benchmarks(df: pd.DataFrame) -> pd.DataFrame:
    df["oee_class"] = pd.cut(
        df["oee"],
        bins=[0, 0.40, 0.60, 0.75, 0.85, 1.01],
        labels=["Poor", "Below Average", "Average", "Good", "World Class"]
    ).astype(str)

    df["availability_class"] = pd.cut(
        df["availability_rate"],
        bins=[0, 0.70, 0.80, 0.90, 1.01],
        labels=["Low", "Moderate", "Good", "Excellent"]
    ).astype(str)

    df["performance_class"] = pd.cut(
        df["performance_rate"],
        bins=[0, 0.70, 0.80, 0.90, 1.01],
        labels=["Low", "Moderate", "Good", "Excellent"]
    ).astype(str)

    df["quality_class"] = pd.cut(
        df["quality_rate"],
        bins=[0, 0.90, 0.95, 0.98, 1.01],
        labels=["Low", "Moderate", "Good", "Excellent"]
    ).astype(str)

    return df


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df["date"] = pd.to_datetime(df["date"])
    df["is_weekend"] = df["date"].dt.dayofweek.isin([5, 6]).astype(int)
    df["month_year"] = df["date"].dt.to_period("M").astype(str)
    df["week_year"] = df["date"].dt.to_period("W").astype(str)
    return df


def run_data_cleaning(data_dir: str = "data/raw",
                      save_dir: str = "data/processed") -> dict:
    os.makedirs(save_dir, exist_ok=True)

    raw = load_raw_data(data_dir)

    production_clean, prod_report = validate_production_data(raw["production"])
    defect_clean = validate_defect_data(raw["defects"])
    downtime_clean = validate_downtime_data(raw["downtime"])

    production_clean = add_oee_benchmarks(production_clean)
    production_clean = add_time_features(production_clean)

    prod_path = os.path.join(save_dir, "production_clean.csv")
    defect_path = os.path.join(save_dir, "defect_clean.csv")
    downtime_path = os.path.join(save_dir, "downtime_clean.csv")

    production_clean.to_csv(prod_path, index=False)
    defect_clean.to_csv(defect_path, index=False)
    downtime_clean.to_csv(downtime_path, index=False)

    return {
        "production": production_clean,
        "defects": defect_clean,
        "downtime": downtime_clean,
        "validation_report": prod_report
    }