import pandas as pd
import numpy as np
import os
from config import (
    PRODUCTION_LINES, SHIFTS, PRODUCTS, MACHINES,
    DOWNTIME_REASONS, DEFECT_TYPES,
    PLANNED_PRODUCTION_TIME_HOURS, IDEAL_CYCLE_TIME_SECONDS,
    START_DATE, END_DATE, RANDOM_STATE, DATA_RAW_DIR
)

rng = np.random.default_rng(RANDOM_STATE)


def generate_production_log() -> pd.DataFrame:
    dates = pd.date_range(start=START_DATE, end=END_DATE, freq="D")

    records = []
    record_id = 1

    line_performance_base = {
        "Line_A": {"avail": 0.91, "perf": 0.89, "qual": 0.97},
        "Line_B": {"avail": 0.83, "perf": 0.81, "qual": 0.94},
        "Line_C": {"avail": 0.87, "perf": 0.85, "qual": 0.96},
        "Line_D": {"avail": 0.78, "perf": 0.76, "qual": 0.92},
        "Line_E": {"avail": 0.93, "perf": 0.91, "qual": 0.98},
    }

    shift_multipliers = {
        "Morning":   {"avail": 1.00, "perf": 1.00, "qual": 1.00},
        "Afternoon": {"avail": 0.97, "perf": 0.96, "qual": 0.98},
        "Night":     {"avail": 0.92, "perf": 0.90, "qual": 0.95},
    }

    for date in dates:
        month = date.month
        seasonal_factor = 1.0 - 0.04 * abs(month - 6.5) / 6.5

        for line in PRODUCTION_LINES:
            base = line_performance_base[line]
            machine = rng.choice(MACHINES)
            product = rng.choice(PRODUCTS)

            for shift in SHIFTS:
                smult = shift_multipliers[shift]

                avail_rate = float(np.clip(
                    base["avail"] * smult["avail"] * seasonal_factor
                    + rng.normal(0, 0.03), 0.55, 1.0
                ))
                perf_rate = float(np.clip(
                    base["perf"] * smult["perf"] * seasonal_factor
                    + rng.normal(0, 0.03), 0.50, 1.0
                ))
                qual_rate = float(np.clip(
                    base["qual"] * smult["qual"]
                    + rng.normal(0, 0.015), 0.80, 1.0
                ))

                planned_time_min = PLANNED_PRODUCTION_TIME_HOURS * 60
                downtime_min = round(float(
                    planned_time_min * (1 - avail_rate)
                    * rng.uniform(0.8, 1.2)
                ), 1)
                downtime_min = min(downtime_min, planned_time_min * 0.45)
                run_time_min = planned_time_min - downtime_min

                ideal_output = int(
                    (run_time_min * 60) / IDEAL_CYCLE_TIME_SECONDS
                )
                actual_output = int(ideal_output * perf_rate)
                good_units = int(actual_output * qual_rate)
                rejected_units = actual_output - good_units

                oee = round(avail_rate * perf_rate * qual_rate, 4)

                downtime_reason = (
                    rng.choice(DOWNTIME_REASONS)
                    if downtime_min > 10
                    else "No Downtime"
                )

                records.append({
                    "record_id": record_id,
                    "date": date.date(),
                    "year": date.year,
                    "month": date.month,
                    "month_name": date.strftime("%B"),
                    "week_number": int(date.strftime("%W")),
                    "day_of_week": date.strftime("%A"),
                    "quarter": f"Q{((date.month - 1) // 3) + 1}",
                    "production_line": line,
                    "machine_id": machine,
                    "shift": shift,
                    "product": product,
                    "planned_time_min": planned_time_min,
                    "downtime_min": downtime_min,
                    "run_time_min": round(run_time_min, 1),
                    "ideal_output_units": ideal_output,
                    "actual_output_units": actual_output,
                    "good_units": good_units,
                    "rejected_units": rejected_units,
                    "availability_rate": round(avail_rate, 4),
                    "performance_rate": round(perf_rate, 4),
                    "quality_rate": round(qual_rate, 4),
                    "oee": oee,
                    "downtime_reason": downtime_reason,
                })
                record_id += 1

    df = pd.DataFrame(records)
    return df


def generate_defect_log(production_df: pd.DataFrame) -> pd.DataFrame:
    defect_records = []
    defect_id = 1

    sampled = production_df[production_df["rejected_units"] > 0].copy()

    for _, row in sampled.iterrows():
        n_defect_entries = max(1, int(row["rejected_units"] / 20))
        n_defect_entries = min(n_defect_entries, 6)

        for _ in range(n_defect_entries):
            defect_count = max(1, int(
                row["rejected_units"] / n_defect_entries
                * rng.uniform(0.7, 1.3)
            ))
            defect_records.append({
                "defect_id": defect_id,
                "record_id": row["record_id"],
                "date": row["date"],
                "production_line": row["production_line"],
                "machine_id": row["machine_id"],
                "shift": row["shift"],
                "product": row["product"],
                "defect_type": rng.choice(DEFECT_TYPES),
                "defect_count": defect_count,
                "year": row["year"],
                "month": row["month"],
                "month_name": row["month_name"],
                "quarter": row["quarter"],
            })
            defect_id += 1

    df = pd.DataFrame(defect_records)
    return df


def generate_downtime_log(production_df: pd.DataFrame) -> pd.DataFrame:
    downtime_df = production_df[
        production_df["downtime_reason"] != "No Downtime"
    ][[
        "record_id", "date", "production_line", "machine_id",
        "shift", "downtime_min", "downtime_reason",
        "year", "month", "month_name", "quarter"
    ]].copy()

    downtime_df = downtime_df.reset_index(drop=True)
    downtime_df.insert(0, "downtime_id", range(1, len(downtime_df) + 1))
    return downtime_df


def run_data_generation(save_dir: str = "data/raw") -> dict:
    os.makedirs(save_dir, exist_ok=True)

    production_df = generate_production_log()
    prod_path = os.path.join(save_dir, "production_log.csv")
    production_df.to_csv(prod_path, index=False)

    defect_df = generate_defect_log(production_df)
    defect_path = os.path.join(save_dir, "defect_log.csv")
    defect_df.to_csv(defect_path, index=False)

    downtime_df = generate_downtime_log(production_df)
    downtime_path = os.path.join(save_dir, "downtime_log.csv")
    downtime_df.to_csv(downtime_path, index=False)

    return {
        "production": production_df,
        "defects": defect_df,
        "downtime": downtime_df
    }