import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "manufacturing_intelligence"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "your_password")
}

DATA_RAW_DIR = "data/raw"
DATA_PROCESSED_DIR = "data/processed"
RANDOM_STATE = 42

PRODUCTION_LINES = ["Line_A", "Line_B", "Line_C", "Line_D", "Line_E"]
SHIFTS = ["Morning", "Afternoon", "Night"]
PRODUCTS = ["Product_X1", "Product_X2", "Product_Y1", "Product_Y2", "Product_Z1"]
MACHINES = ["Machine_01", "Machine_02", "Machine_03", "Machine_04", "Machine_05",
            "Machine_06", "Machine_07", "Machine_08", "Machine_09", "Machine_10"]
DOWNTIME_REASONS = [
    "Mechanical Failure", "Electrical Fault", "Material Shortage",
    "Operator Absence", "Planned Maintenance", "Tool Changeover",
    "Quality Inspection", "Line Changeover", "Power Outage", "Sensor Error"
]
DEFECT_TYPES = [
    "Surface Scratch", "Dimensional Error", "Assembly Defect",
    "Paint Defect", "Weld Defect", "Material Crack"
]

PLANNED_PRODUCTION_TIME_HOURS = 8
IDEAL_CYCLE_TIME_SECONDS = 30
START_DATE = "2023-01-01"
END_DATE = "2024-12-31"