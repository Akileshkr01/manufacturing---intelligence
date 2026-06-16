import pandas as pd
from sqlalchemy import create_engine, text
from config import DB_CONFIG


def get_engine():
    url = (
        f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )
    engine = create_engine(url)
    return engine


def test_connection():
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        result.fetchone()
    return engine


def load_dataframe_to_db(df: pd.DataFrame, table_name: str,
                        if_exists: str = "replace"):
    engine = get_engine()
    df.to_sql(table_name, engine, if_exists=if_exists,
              index=False, chunksize=5000)


def run_query(sql: str) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql(text(sql), conn)
    return df


def create_indexes():
    engine = get_engine()
    statements = [
        "CREATE INDEX IF NOT EXISTS idx_prod_line ON production_log(production_line);",
        "CREATE INDEX IF NOT EXISTS idx_prod_date ON production_log(date);",
        "CREATE INDEX IF NOT EXISTS idx_prod_shift ON production_log(shift);",
        "CREATE INDEX IF NOT EXISTS idx_prod_machine ON production_log(machine_id);",
        "CREATE INDEX IF NOT EXISTS idx_prod_year_month ON production_log(year, month);",
        "CREATE INDEX IF NOT EXISTS idx_defect_line ON defect_log(production_line);",
        "CREATE INDEX IF NOT EXISTS idx_defect_type ON defect_log(defect_type);",
        "CREATE INDEX IF NOT EXISTS idx_defect_date ON defect_log(date);",
        "CREATE INDEX IF NOT EXISTS idx_downtime_line ON downtime_log(production_line);",
        "CREATE INDEX IF NOT EXISTS idx_downtime_reason ON downtime_log(downtime_reason);",
        "CREATE INDEX IF NOT EXISTS idx_downtime_date ON downtime_log(date);",
    ]
    with engine.connect() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
        conn.commit()