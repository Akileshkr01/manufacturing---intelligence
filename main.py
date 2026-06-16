import os

os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)

from src.data_generator import run_data_generation
from src.data_cleaner import run_data_cleaning
from src.oee_calculator import run_oee_analysis
from src.db_loader import load_all_tables, run_analytics_queries, export_query_results
from src.dashboard_exporter import run_dashboard_export

print("=" * 60)
print("PHASE 1: DATA GENERATION")
print("=" * 60)
datasets = run_data_generation(save_dir="data/raw")

print("\n" + "=" * 60)
print("PHASE 2: DATA CLEANING & OEE ANALYSIS")
print("=" * 60)
cleaned_data = run_data_cleaning(
    data_dir="data/raw",
    save_dir="data/processed"
)
oee_results = run_oee_analysis(
    cleaned_data,
    save_dir="data/processed"
)

print("\n" + "=" * 60)
print("PHASE 3: POSTGRESQL INTEGRATION")
print("=" * 60)
load_all_tables(cleaned_data)
query_results = run_analytics_queries()
export_query_results(query_results, save_dir="data/processed")

print("\n" + "=" * 60)
print("PHASE 4: DASHBOARD EXPORT")
print("=" * 60)
run_dashboard_export(cleaned_data, save_dir="data/processed")

print("\nFull pipeline complete.")