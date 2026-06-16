import os
import pandas as pd
from src.db_utils import (
    create_indexes,
    load_dataframe_to_db,
    run_query,
    test_connection,
)


def load_all_tables(cleaned_data: dict):
    test_connection()

    load_dataframe_to_db(
        cleaned_data["production"], "production_log", if_exists="replace"
    )
    load_dataframe_to_db(
        cleaned_data["defects"], "defect_log", if_exists="replace"
    )
    load_dataframe_to_db(
        cleaned_data["downtime"], "downtime_log", if_exists="replace"
    )

    create_indexes()

    for table in ["production_log", "defect_log", "downtime_log"]:
        run_query(f"SELECT COUNT(*) AS total_rows FROM {table}")


def run_analytics_queries() -> dict:
    queries = {
        "1. Overall OEE by Production Line": """
            SELECT
                production_line,
                ROUND(AVG(availability_rate)::numeric, 4) AS avg_availability,
                ROUND(AVG(performance_rate)::numeric, 4)  AS avg_performance,
                ROUND(AVG(quality_rate)::numeric, 4)      AS avg_quality,
                ROUND(AVG(oee)::numeric, 4)               AS avg_oee,
                SUM(actual_output_units)                  AS total_output,
                SUM(good_units)                           AS total_good_units,
                SUM(rejected_units)                       AS total_rejected,
                ROUND(
                    (100.0 * SUM(rejected_units)
                    / NULLIF(SUM(actual_output_units), 0))::numeric, 2
                )                                         AS rejection_rate_pct
            FROM production_log
            GROUP BY production_line
            ORDER BY avg_oee DESC
        """,
        "2. Worst Performing Production Line by Month": """
            SELECT
                year,
                month,
                production_line,
                ROUND(AVG(oee)::numeric, 4) AS avg_oee,
                RANK() OVER (
                    PARTITION BY year, month
                    ORDER BY AVG(oee) ASC
                ) AS rank_worst
            FROM production_log
            GROUP BY year, month, production_line
            ORDER BY year, month, rank_worst
        """,
        "3. Shift-wise Productivity Analysis": """
            SELECT
                shift,
                production_line,
                ROUND(AVG(availability_rate)::numeric, 4) AS avg_availability,
                ROUND(AVG(performance_rate)::numeric, 4)  AS avg_performance,
                ROUND(AVG(quality_rate)::numeric, 4)      AS avg_quality,
                ROUND(AVG(oee)::numeric, 4)               AS avg_oee,
                SUM(actual_output_units)                  AS total_output,
                SUM(good_units)                           AS total_good_units,
                ROUND(AVG(downtime_min)::numeric, 2)      AS avg_downtime_min
            FROM production_log
            GROUP BY shift, production_line
            ORDER BY shift, avg_oee DESC
        """,
        "4. Monthly OEE Trend (All Lines Combined)": """
            SELECT
                year,
                month,
                TO_CHAR(TO_DATE(month::text, 'MM'), 'Month') AS month_name,
                ROUND(AVG(availability_rate)::numeric, 4)    AS avg_availability,
                ROUND(AVG(performance_rate)::numeric, 4)     AS avg_performance,
                ROUND(AVG(quality_rate)::numeric, 4)         AS avg_quality,
                ROUND(AVG(oee)::numeric, 4)                  AS avg_oee,
                SUM(actual_output_units)                     AS total_output,
                SUM(good_units)                              AS total_good_units,
                SUM(downtime_min)                            AS total_downtime_min
            FROM production_log
            GROUP BY year, month
            ORDER BY year, month
        """,
        "5. Top Downtime Reasons by Total Minutes": """
            SELECT
                downtime_reason,
                COUNT(*)                                      AS occurrence_count,
                SUM(downtime_min)                             AS total_downtime_min,
                ROUND(AVG(downtime_min)::numeric, 2)          AS avg_downtime_min,
                ROUND(
                    (100.0 * SUM(downtime_min)
                    / SUM(SUM(downtime_min)) OVER ())::numeric, 2
                )                                             AS pct_of_total
            FROM downtime_log
            GROUP BY downtime_reason
            ORDER BY total_downtime_min DESC
        """,
        "6. Downtime by Production Line and Reason": """
            SELECT
                production_line,
                downtime_reason,
                COUNT(*)                             AS occurrence_count,
                SUM(downtime_min)                    AS total_downtime_min,
                ROUND(AVG(downtime_min)::numeric, 2) AS avg_downtime_min
            FROM downtime_log
            GROUP BY production_line, downtime_reason
            ORDER BY production_line, total_downtime_min DESC
        """,
        "7. Defect Analysis by Type and Line": """
            SELECT
                production_line,
                defect_type,
                COUNT(*)              AS occurrence_count,
                SUM(defect_count)     AS total_defects,
                ROUND(
                    (100.0 * SUM(defect_count)
                    / SUM(SUM(defect_count)) OVER (
                        PARTITION BY production_line
                    ))::numeric, 2
                )                     AS pct_of_line_defects
            FROM defect_log
            GROUP BY production_line, defect_type
            ORDER BY production_line, total_defects DESC
        """,
        "8. Machine Utilization Analysis": """
            SELECT
                machine_id,
                COUNT(DISTINCT production_line)           AS lines_operated,
                ROUND(AVG(availability_rate)::numeric, 4) AS avg_availability,
                ROUND(AVG(oee)::numeric, 4)               AS avg_oee,
                SUM(downtime_min)                         AS total_downtime_min,
                SUM(actual_output_units)                  AS total_output,
                ROUND(
                    (100.0 * SUM(run_time_min)
                    / NULLIF(SUM(planned_time_min), 0))::numeric, 2
                )                                         AS utilization_pct
            FROM production_log
            GROUP BY machine_id
            ORDER BY avg_oee DESC
        """,
        "9. Quarter-over-Quarter OEE Comparison": """
            SELECT
                year,
                quarter,
                production_line,
                ROUND(AVG(oee)::numeric, 4)              AS avg_oee,
                SUM(good_units)                          AS total_good_units,
                SUM(actual_output_units)                 AS total_output,
                SUM(downtime_min)                        AS total_downtime_min,
                LAG(ROUND(AVG(oee)::numeric, 4)) OVER (
                    PARTITION BY production_line
                    ORDER BY year, quarter
                )                                        AS prev_quarter_oee,
                ROUND(
                    (
                        AVG(oee)
                        - LAG(AVG(oee)) OVER (
                            PARTITION BY production_line
                            ORDER BY year, quarter
                        )
                    )::numeric * 100, 2
                )                                        AS oee_change_pct_points
            FROM production_log
            GROUP BY year, quarter, production_line
            ORDER BY production_line, year, quarter
        """,
        "10. Production Efficiency Summary by Product": """
            SELECT
                product,
                COUNT(*)                                      AS total_records,
                SUM(actual_output_units)                      AS total_output,
                SUM(good_units)                               AS total_good_units,
                SUM(rejected_units)                           AS total_rejected,
                ROUND(AVG(oee)::numeric, 4)                   AS avg_oee,
                ROUND(AVG(quality_rate)::numeric, 4)          AS avg_quality_rate,
                ROUND(
                    (100.0 * SUM(rejected_units)
                    / NULLIF(SUM(actual_output_units), 0))::numeric, 2
                )                                             AS rejection_rate_pct
            FROM production_log
            GROUP BY product
            ORDER BY avg_oee DESC
        """,
        "11. Night Shift vs Day Shift Performance Gap": """
            SELECT
                production_line,
                ROUND(AVG(CASE WHEN shift = 'Morning'
                    THEN oee END)::numeric, 4)   AS morning_oee,
                ROUND(AVG(CASE WHEN shift = 'Afternoon'
                    THEN oee END)::numeric, 4)   AS afternoon_oee,
                ROUND(AVG(CASE WHEN shift = 'Night'
                    THEN oee END)::numeric, 4)   AS night_oee,
                ROUND((
                    AVG(CASE WHEN shift = 'Morning' THEN oee END)
                    - AVG(CASE WHEN shift = 'Night' THEN oee END)
                )::numeric, 4)                   AS day_night_gap
            FROM production_log
            GROUP BY production_line
            ORDER BY day_night_gap DESC
        """,
        "12. Rolling 3-Month Average OEE per Line": """
            SELECT
                year,
                month,
                production_line,
                ROUND(AVG(oee)::numeric, 4) AS monthly_avg_oee,
                ROUND(AVG(AVG(oee)) OVER (
                    PARTITION BY production_line
                    ORDER BY year, month
                    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
                )::numeric, 4)              AS rolling_3m_oee
            FROM production_log
            GROUP BY year, month, production_line
            ORDER BY production_line, year, month
        """
    }

    results = {}
    for name, sql in queries.items():
        df_result = run_query(sql)
        results[name] = df_result

    return results


def export_query_results(results: dict,
                         save_dir: str = "data/processed"):
    export_map = {
        "1. Overall OEE by Production Line":
            "sql_oee_by_line.csv",
        "2. Worst Performing Production Line by Month":
            "sql_worst_line_by_month.csv",
        "3. Shift-wise Productivity Analysis":
            "sql_shift_productivity.csv",
        "4. Monthly OEE Trend (All Lines Combined)":
            "sql_monthly_oee_trend.csv",
        "5. Top Downtime Reasons by Total Minutes":
            "sql_downtime_reasons.csv",
        "6. Downtime by Production Line and Reason":
            "sql_downtime_by_line_reason.csv",
        "7. Defect Analysis by Type and Line":
            "sql_defect_by_type_line.csv",
        "8. Machine Utilization Analysis":
            "sql_machine_utilization.csv",
        "9. Quarter-over-Quarter OEE Comparison":
            "sql_qoq_oee.csv",
        "10. Production Efficiency Summary by Product":
            "sql_product_efficiency.csv",
        "11. Night Shift vs Day Shift Performance Gap":
            "sql_shift_gap.csv",
        "12. Rolling 3-Month Average OEE per Line":
            "sql_rolling_oee.csv",
    }

    for query_name, filename in export_map.items():
        if query_name in results:
            path = os.path.join(save_dir, filename)
            results[query_name].to_csv(path, index=False)