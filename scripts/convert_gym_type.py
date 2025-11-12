#!/usr/bin/env python3
"""
Convert specialty_type in gym.csv to its corresponding id from type.csv.

- Reads dataset/csv/gym.csv and dataset/csv/type.csv
- For each gym, replaces specialty_type with its id (from type.csv)
- If specialty_type contains multiple types (separated by /), replaces with comma-separated ids
- Writes output to dataset/csv/gym_converted.csv
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSV_DIR = ROOT / "dataset" / "csv"
GYM_CSV = CSV_DIR / "gym.csv"
TYPE_CSV = CSV_DIR / "type.csv"
OUTPUT_CSV = CSV_DIR / "gym_converted.csv"


def load_type_map(type_csv: Path) -> dict[str, str]:
    """Return mapping from type name (case-insensitive, stripped) to id (as string)."""
    type_map = {}
    with type_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"].strip().lower()
            type_map[name] = row["id"].strip()
    return type_map


def convert_specialty_type(specialty: str, type_map: dict[str, str]) -> str:
    """Convert specialty_type string to comma-separated type ids."""
    types = [t.strip().lower() for t in specialty.split("/")]
    ids = [type_map.get(t, "") for t in types]
    # If any type not found, leave blank
    return ",".join([i for i in ids if i])


def main():
    type_map = load_type_map(TYPE_CSV)
    with GYM_CSV.open(newline="", encoding="utf-8") as f_in, OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in)
        fieldnames = list(reader.fieldnames) if reader.fieldnames else []
        # Replace specialty_type with specialty_type_id
        if "specialty_type" in fieldnames:
            idx = fieldnames.index("specialty_type")
            fieldnames[idx] = "specialty_type_id"
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            specialty = row["specialty_type"]
            specialty_id = convert_specialty_type(specialty, type_map)
            row["specialty_type_id"] = specialty_id
            del row["specialty_type"]
            writer.writerow(row)
    print(f"Converted specialty_type to id for all gyms. Output: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
