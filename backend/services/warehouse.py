import sqlite3
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from backend.config import settings

WAREHOUSE_PATH = settings.BASE_DIR / "data" / "warehouse.db"
WAREHOUSE_URL = f"sqlite:///{WAREHOUSE_PATH.as_posix()}"

warehouse_engine = create_engine(WAREHOUSE_URL, connect_args={"check_same_thread": False})

def get_warehouse_connection():
    return sqlite3.connect(str(WAREHOUSE_PATH))

def load_df_to_warehouse(df: pd.DataFrame, table_name: str, if_exists: str = "replace"):
    # Normalize column names: lowercase, strip, replace spaces/special chars with underscores
    df_clean = df.copy()
    cleaned_cols = []
    for col in df_clean.columns:
        c_str = str(col).strip().lower().replace(" ", "_").replace("-", "_").replace(".", "_")
        cleaned_cols.append(c_str)
    df_clean.columns = cleaned_cols
    
    # Store into SQLite warehouse
    df_clean.to_sql(table_name, warehouse_engine, if_exists=if_exists, index=False)
    return df_clean

def get_warehouse_tables():
    with warehouse_engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
        return [row[0] for row in result.fetchall()]

def query_warehouse(sql: str, params: dict = None) -> pd.DataFrame:
    with warehouse_engine.connect() as conn:
        return pd.read_sql_query(text(sql), conn, params=params)
