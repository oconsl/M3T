import csv
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from m3t.config import BACKUPS_DIR, MESSAGES_CSV, RECIPIENTS_CSV, TEMPLATES_DIR


def merge_columns(base: list[str], discovered: list[str]) -> list[str]:
    columns = []
    for column in [*base, *discovered]:
        if column and column not in columns:
            columns.append(column)
    return columns


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        return list(reader.fieldnames or []), list(reader)


def write_csv_rows(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({column: row.get(column, "") for column in columns})
            file.flush()
            os.fsync(file.fileno())
        Path(temp_name).replace(path)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise


def make_backup() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = BACKUPS_DIR / timestamp
    counter = 2
    while backup_dir.exists():
        backup_dir = BACKUPS_DIR / f"{timestamp}-{counter}"
        counter += 1

    backup_dir.mkdir(parents=True, exist_ok=True)
    for source in (MESSAGES_CSV, RECIPIENTS_CSV):
        if source.exists():
            shutil.copy2(source, backup_dir / source.name)
    if TEMPLATES_DIR.exists():
        shutil.copytree(TEMPLATES_DIR, backup_dir / "templates")
    return backup_dir
