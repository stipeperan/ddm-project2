#!/usr/bin/env python3
"""
Generate battle.csv by creating 3 random battles for each Pokémon entry in pokemon.csv.

Rules:
- For every Pokémon in dataset/csv/pokemon.csv, generate 3 battles.
- Each battle links two distinct Pokémon IDs (pok1_id, pok2_id) chosen from dataset/csv/pokemon.csv.
- Each of the 3 battles must have a different opponent Pokémon.
- The opponent must NOT be owned by the same trainer as pok1 (see dataset/csv/trainer_owns_pokemon.csv).
- Winner is the Pokémon with the higher 'total' stat (from pokemon.csv). If equal, choose randomly.
- Each battle is hosted by a random gym; pick a gym_id from dataset/csv/gym.csv.
- Each battle has a unique incremental battle_id and a random date between 2025-01-01 and 2025-12-31 (ISO YYYY-MM-DD).
- Also store the trainer_winner_id (owner of the winning Pokémon).

Output:
- Writes dataset/csv/battle.csv with columns: battle_id, date, pok1_id, pok2_id, pokemon_winner_id, trainer_winner_id, gym_id
"""

from __future__ import annotations

import csv
import random
import sys
from pathlib import Path
from datetime import date, timedelta


ROOT = Path(__file__).resolve().parent
DATASET_DIR = ROOT / "dataset"
CSV_DIR = DATASET_DIR / "csv"

POKEMON_CSV = CSV_DIR / "pokemon.csv"
GYM_CSV = CSV_DIR / "gym.csv"
TRAINER_OWNS_POKEMON_CSV = CSV_DIR / "trainer_owns_pokemon.csv"
OUTPUT_CSV = CSV_DIR / "battle.csv"


def load_pokemon_stats(csv_path: Path) -> tuple[list[int], dict[int, int]]:
    """Return list of Pokémon IDs and mapping id->total from pokemon.csv.

    The CSV is expected to have headers including 'id' and 'total' (case-insensitive).
    """
    ids: list[int] = []
    totals: dict[int, int] = {}
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Normalize fieldnames to lowercase for robust access
        # but DictReader already uses header row; we'll access case-insensitively.
        for row in reader:
            try:
                # Handle potential case differences
                rid = row.get("id") if "id" in row else row.get("ID")
                rtotal = row.get("total") if "total" in row else row.get("TOTAL")
                if rid is None or rtotal is None:
                    continue
                pid = int(str(rid).strip())
                total_val = int(str(rtotal).strip())
            except (ValueError, TypeError):
                # Skip malformed rows
                continue
            ids.append(pid)
            totals[pid] = total_val
    if not ids:
        raise RuntimeError(f"No Pokémon IDs loaded from {csv_path}")
    return ids, totals


def load_gyms(csv_path: Path) -> list[int]:
    """Return list of gym_id values from gym.csv."""
    gym_ids: list[int] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            val = row.get("gym_id") or row.get("GYM_ID") or row.get("id")
            if val is None:
                continue
            try:
                gym_ids.append(int(str(val).strip()))
            except ValueError:
                continue
    if not gym_ids:
        raise RuntimeError(f"No gym IDs loaded from {csv_path}")
    return gym_ids


def load_trainer_ownership(csv_path: Path) -> dict[int, int]:
    """Load mapping from pokemon_id -> trainerID from trainer_owns_pokemon.csv.

    Expected headers: trainerID, pokename (where pokename holds the Pokémon 'id').
    If multiple trainers own the same Pokémon id, the last one wins (arbitrary).
    """
    mapping: dict[int, int] = {}
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                trainer = int(str(row.get("trainerID", "")).strip())
                pid = int(str(row.get("pokename", "")).strip())
            except (ValueError, TypeError):
                continue
            mapping[pid] = trainer
    return mapping


def pick_random_opponent(
    all_ids: list[int],
    exclude_id: int,
    ownership: dict[int, int] | None = None,
) -> int | None:
    """Pick a random Pokémon ID different from exclude_id and, if ownership is provided,
    not owned by the same trainer as exclude_id. If no suitable candidate exists,
    fall back to any other Pokémon ID different from exclude_id.
    """
    if len(all_ids) < 2:
        raise RuntimeError("Need at least 2 Pokémon to form battles")

    base_trainer = ownership.get(exclude_id) if ownership else None

    candidates = [
        pid
        for pid in all_ids
        if pid != exclude_id
        and (ownership is None or ownership.get(pid) is not None)
        and (base_trainer is None or ownership.get(pid) != base_trainer)
    ] if ownership is not None else [pid for pid in all_ids if pid != exclude_id]

    if candidates:
        return random.choice(candidates)

    # Fallback: pick any different Pokémon
    # For stricter requirement (both must be owned and different trainer),
    # if no candidates exist, return None to skip this battle.
    return None


def random_date(start: date, end: date) -> date:
    """Pick a random date between start and end (inclusive)."""
    delta_days = (end - start).days
    if delta_days < 0:
        raise ValueError("Start date must be before end date")
    return start + timedelta(days=random.randint(0, delta_days))


def main() -> int:
    # Optional: seed for reproducibility if provided
    seed_env = sys.argv[1] if len(sys.argv) > 1 else None
    if seed_env is not None:
        try:
            random.seed(int(seed_env))
        except ValueError:
            random.seed(seed_env)

    # Load inputs
    pokemon_ids, pokemon_totals = load_pokemon_stats(POKEMON_CSV)
    gym_ids = load_gyms(GYM_CSV)
    ownership = load_trainer_ownership(TRAINER_OWNS_POKEMON_CSV)
    rows: list[dict[str, int | str]] = []

    # Iterate over every Pokémon from pokemon.csv and generate 3 battles each
    start_day = date(2025, 1, 1)
    end_day = date(2025, 12, 31)
    battle_id = 1
    # Consider only Pokémon that are actually owned by a trainer
    owned_pokemon_ids = [pid for pid in pokemon_ids if ownership.get(pid) is not None]
    for base_id in owned_pokemon_ids:
        used_opponents: set[int] = set()
        
        for _ in range(3):
            # Pick opponent that hasn't been used yet for this base_id
            opp_id = pick_random_opponent(owned_pokemon_ids, exclude_id=base_id, ownership=ownership)
            
            # Ensure opponent is different from previously picked opponents
            attempts = 0
            while opp_id is not None and opp_id in used_opponents and attempts < 100:
                opp_id = pick_random_opponent(owned_pokemon_ids, exclude_id=base_id, ownership=ownership)
                attempts += 1
            
            if opp_id is None or opp_id in used_opponents:
                # No valid unique opponent found under constraints; skip this battle
                continue
            
            used_opponents.add(opp_id)

            # Determine winner by higher total (from CSV). If equal, choose randomly.
            base_total = pokemon_totals.get(base_id, 0)
            opp_total = pokemon_totals.get(opp_id, 0)
            if base_total > opp_total:
                pokemon_winner_id = base_id
            elif opp_total > base_total:
                pokemon_winner_id = opp_id
            else:
                pokemon_winner_id = random.choice([base_id, opp_id])

            gym_id = random.choice(gym_ids)
            battle_day = random_date(start_day, end_day).isoformat()
            trainer_winner_id = ownership.get(pokemon_winner_id, "")

            rows.append(
                {
                    "battle_id": battle_id,
                    "date": battle_day,
                    "pok1_id": base_id,
                    "pok2_id": opp_id,
                    "pokemon_winner_id": pokemon_winner_id,
                    "trainer_winner_id": trainer_winner_id,
                    "gym_id": gym_id,
                }
            )
            battle_id += 1

    # Ensure output directory exists
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "battle_id",
        "date",
        "pok1_id",
        "pok2_id",
        "pokemon_winner_id",
        "trainer_winner_id",
        "gym_id",
    ]
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} battles -> {OUTPUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
