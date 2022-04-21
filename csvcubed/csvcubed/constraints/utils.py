from pathlib import Path

def get_csv_length(csv_path: Path) -> int:
    """
    Use a generator to get quick row count without
    readng the whole file into memory at once.
    """
    with open(csv_path) as f:
        row_count = sum(1 for _ in f)
    return row_count