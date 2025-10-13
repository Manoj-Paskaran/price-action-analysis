from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
DATA_DIR: Path = PROJECT_ROOT / "data"
SECTOR_DIR: Path = DATA_DIR / "sector-analysis"
INDEX_DIR: Path = DATA_DIR / "index-analysis"

STOCK_METADATA = DATA_DIR / "combined.parquet"

INDEX_CSV = INDEX_DIR / "nifty_sectoral_indices.csv"

NIFTY_50_CSV = INDEX_DIR / "nifty_50.csv"

if __name__ == "__main__":
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"DATA_DIR: {DATA_DIR}")
    print(f"SECTOR_DIR: {SECTOR_DIR}")
    print(f"INDEX_DIR: {INDEX_DIR}")
    print(f"STOCK_METADATA: {STOCK_METADATA}")
    print(f"INDEX_CSV: {INDEX_CSV}")