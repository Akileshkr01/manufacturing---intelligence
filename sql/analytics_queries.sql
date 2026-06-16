--  oee_by_production_line
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
        100.0 * SUM(rejected_units)
        / NULLIF(SUM(actual_output_units), 0), 2
    )                                         AS rejection_rate_pct
FROM production_log
GROUP BY production_line
ORDER BY avg_oee DESC;

--  worst_performing_line_by_month
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
ORDER BY year, month, rank_worst;

--  shift_productivity
SELECT
    shift,
    production_line,
    ROUND(AVG(availability_rate)::numeric, 4) AS avg_availability,
    ROUND(AVG(performance_rate)::numeric, 4)  AS avg_performance,
    ROUND(AVG(quality_rate)::numeric, 4)      AS avg_quality,
    ROUND(AVG(oee)::numeric, 4)               AS avg_oee,
    SUM(actual_output_units)                  AS total_output,
    ROUND(AVG(downtime_min)::numeric, 2)      AS avg_downtime_min
FROM production_log
GROUP BY shift, production_line
ORDER BY shift, avg_oee DESC;

--  monthly_oee_trend
SELECT
    year,
    month,
    TO_CHAR(TO_DATE(month::text, 'MM'), 'Month') AS month_name,
    ROUND(AVG(availability_rate)::numeric, 4)    AS avg_availability,
    ROUND(AVG(performance_rate)::numeric, 4)     AS avg_performance,
    ROUND(AVG(quality_rate)::numeric, 4)         AS avg_quality,
    ROUND(AVG(oee)::numeric, 4)                  AS avg_oee,
    SUM(actual_output_units)                     AS total_output,
    SUM(downtime_min)                            AS total_downtime_min
FROM production_log
GROUP BY year, month
ORDER BY year, month;

--  top_downtime_reasons
SELECT
    downtime_reason,
    COUNT(*)                                      AS occurrence_count,
    SUM(downtime_min)                             AS total_downtime_min,
    ROUND(AVG(downtime_min)::numeric, 2)          AS avg_downtime_min,
    ROUND(
        100.0 * SUM(downtime_min)
        / SUM(SUM(downtime_min)) OVER (), 2
    )                                             AS pct_of_total
FROM downtime_log
GROUP BY downtime_reason
ORDER BY total_downtime_min DESC;

--  downtime_by_line_and_reason
SELECT
    production_line,
    downtime_reason,
    COUNT(*)                             AS occurrence_count,
    SUM(downtime_min)                    AS total_downtime_min,
    ROUND(AVG(downtime_min)::numeric, 2) AS avg_downtime_min
FROM downtime_log
GROUP BY production_line, downtime_reason
ORDER BY production_line, total_downtime_min DESC;

--  defect_analysis_by_type_and_line
SELECT
    production_line,
    defect_type,
    COUNT(*)          AS occurrence_count,
    SUM(defect_count) AS total_defects,
    ROUND(
        100.0 * SUM(defect_count)
        / SUM(SUM(defect_count)) OVER (
            PARTITION BY production_line
        ), 2
    )                 AS pct_of_line_defects
FROM defect_log
GROUP BY production_line, defect_type
ORDER BY production_line, total_defects DESC;

--  machine_utilization
SELECT
    machine_id,
    COUNT(DISTINCT production_line)           AS lines_operated,
    ROUND(AVG(availability_rate)::numeric, 4) AS avg_availability,
    ROUND(AVG(oee)::numeric, 4)               AS avg_oee,
    SUM(downtime_min)                         AS total_downtime_min,
    SUM(actual_output_units)                  AS total_output,
    ROUND(
        100.0 * SUM(run_time_min)
        / NULLIF(SUM(planned_time_min), 0), 2
    )                                         AS utilization_pct
FROM production_log
GROUP BY machine_id
ORDER BY avg_oee DESC;

--  quarter_over_quarter_oee
SELECT
    year,
    quarter,
    production_line,
    ROUND(AVG(oee)::numeric, 4)              AS avg_oee,
    SUM(good_units)                          AS total_good_units,
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
ORDER BY production_line, year, quarter;

--  product_efficiency
SELECT
    product,
    COUNT(*)                                      AS total_records,
    SUM(actual_output_units)                      AS total_output,
    SUM(good_units)                               AS total_good_units,
    SUM(rejected_units)                           AS total_rejected,
    ROUND(AVG(oee)::numeric, 4)                   AS avg_oee,
    ROUND(AVG(quality_rate)::numeric, 4)          AS avg_quality_rate,
    ROUND(
        100.0 * SUM(rejected_units)
        / NULLIF(SUM(actual_output_units), 0), 2
    )                                             AS rejection_rate_pct
FROM production_log
GROUP BY product
ORDER BY avg_oee DESC;

--  shift_performance_gap
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
ORDER BY day_night_gap DESC;

--  rolling_3month_oee
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
ORDER BY production_line, year, month;