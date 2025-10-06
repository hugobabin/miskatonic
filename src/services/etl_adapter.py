from pathlib import Path
from datetime import datetime
from src.services.etl_quiz import process_and_export_csv

DATA_IN = Path("data/in")

def _ts_name(name: str) -> str:
    base = Path(name).stem
    return f"{base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

def save_file_to_data_in(filename: str, data: bytes) -> Path:
    DATA_IN.mkdir(parents=True, exist_ok=True)
    dst = DATA_IN / _ts_name(filename)
    dst.write_bytes(data)  # writes the file for the ETL
    return dst

def run_etl_from_upload(filename: str, data: bytes, author: str | None):
    csv_path = save_file_to_data_in(filename, data)
    stats, log_path = process_and_export_csv(csv_path, author=author)

    return stats,log_path
