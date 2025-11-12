#!/usr/bin/env python3
"""
Generate trainer_owns_pokemon.csv ensuring each Pokémon is owned by exactly ONE trainer.

Rules:
- Read all Pokémon IDs from dataset/csv/pokemon.csv.
- Read all trainer IDs from dataset/csv/trainer.csv.
- Assign each Pokémon to exactly one random trainer.
- Some trainers may end up with no Pokémon (random distribution).
- Write dataset/csv/trainer_owns_pokemon.csv with columns: trainerID, pokename (where pokename=pokemon_id).

Usage:
    python3 generate_trainer_owns_pokemon.py [seed]
    
Optional seed argument for reproducible output.
"""

from __future__ import annotations

import csv
import random
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATASET_DIR = ROOT / "dataset"
CSV_DIR = DATASET_DIR / "csv"

POKEMON_CSV = CSV_DIR / "pokemon.csv"
TRAINER_CSV = CSV_DIR / "trainer.csv"
OUTPUT_CSV = CSV_DIR / "trainer_owns_pokemon.csv"


def load_pokemon_ids(csv_path: Path) -> list[int]:
    """Load all unique Pokémon IDs from pokemon.csv (using 'id' column for uniqueness)."""
    ids_set: set[int] = set()
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rid = row.get("id") if "id" in row else row.get("ID")
                if rid is None:
                    continue
                pid = int(str(rid).strip())
                ids_set.add(pid)
            except (ValueError, TypeError):
                continue
    if not ids_set:
        raise RuntimeError(f"No Pokémon IDs loaded from {csv_path}")
    return sorted(ids_set)


def load_trainer_ids(csv_path: Path) -> list[int]:
    """Load all unique trainer IDs from trainer.csv (using 'trainerID' column for uniqueness)."""
    ids_set: set[int] = set()
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                tid = row.get("trainerID") if "trainerID" in row else row.get("TRAINERID")
                if tid is None:
                    continue
                trainer_id = int(str(tid).strip())
                ids_set.add(trainer_id)
            except (ValueError, TypeError):
                continue
    if not ids_set:
        raise RuntimeError(f"No trainer IDs loaded from {csv_path}")
    return sorted(ids_set)


def main() -> int:
    # Optional: seed for reproducibility if provided
    seed_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if seed_arg is not None:
        try:
            random.seed(int(seed_arg))
        except ValueError:
            random.seed(seed_arg)

    # Load inputs
    pokemon_ids = load_pokemon_ids(POKEMON_CSV)
    trainer_ids = load_trainer_ids(TRAINER_CSV)

    if not trainer_ids:
        raise RuntimeError("No trainers available to assign Pokémon")

    # Assign each Pokémon to a random trainer
    # Note: Some trainers may end up with no Pokémon (random distribution)
    rows: list[dict[str, int]] = []
    for pid in pokemon_ids:
        assigned_trainer = random.choice(trainer_ids)
        rows.append({
            "trainerID": assigned_trainer,
            "pokename": pid,
        })

    # Ensure output directory exists
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    fieldnames = ["trainerID", "pokename"]
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} ownership records -> {OUTPUT_CSV}")
    print(f"  - {len(pokemon_ids)} unique Pokémon")
    print(f"  - {len(trainer_ids)} unique trainers")
    print(f"  - Each Pokémon is owned by exactly 1 trainer")
    print(f"  - Some trainers may have no Pokémon (random distribution)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
