#!/usr/bin/env python3
"""
Generate battles.json by creating 3 random battles for each owned Pokémon.

Rules (ported from the old CSV/Neo4j script):

- For every Pokémon (from pokemon.json) that is owned by at least one trainer:
    - Generate up to 3 battles.
- Each battle links two distinct Pokémon IDs (base vs opponent).
- Each of the 3 battles for a given base Pokémon must have a different opponent.
- The opponent must NOT be owned by the same trainer as the base Pokémon.
- Winner is the Pokémon with the higher 'tot' stat (from pokemon.json). If equal, choose randomly.
- Each battle is hosted by a random gym (from gym.json).
- Each battle has:
    - a unique incremental battle id: "b1", "b2", ...
    - a random date between 2025-01-01 and 2025-12-31 (as ISO 8601 with time & Z).
- Trainer ownership is deduced from trainer.json:
    "owns": ["290", "1052", ...]
- IDs written to battles.json are taken directly from the JSON files:
    - pokemon_id: pokemon._id (e.g. "2")
    - trainer_id: trainer._id (e.g. "17")
    - gym_id: gym._id (e.g. "3")
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from datetime import date, timedelta, datetime


# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------

# This script is at: PROJROOT/scripts/create_battles_json.py
SCRIPTS_DIR = Path(__file__).resolve().parent
PROJROOT = SCRIPTS_DIR.parent
DATASET_DIR = PROJROOT / "dataset"
JSON_DIR = DATASET_DIR / "json"

POKEMON_JSON = JSON_DIR / "pokemon.json"
GYM_JSON = JSON_DIR / "gym.json"
TRAINER_JSON = JSON_DIR / "trainer.json"
TYPE_JSON = JSON_DIR / "type.json"  # currently unused, but left as hook

OUTPUT_JSON = JSON_DIR / "battles.json"


# ---------------------------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------------------------

def load_pokemon(json_path: Path):
    """
    Load Pokémon from pokemon.json.

    Expected shape (as in your snippet):

    {
        "_id": "1",
        "pokedex": "0001",
        "name": "Bulbasaur",
        "stats": {
            "hp": "45",
            "atk": "49",
            "def": "49",
            "sp_atk": "65",
            "sp_def": "65",
            "tot": "318"
        },
        ...
    }

    Returns:
        pokemon_ids: list[str]         # Pokémon ids as strings (e.g. "1", "2", "290")
        totals: dict[str, int]         # id -> total stat (int)
    """
    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)

    pokemon_ids: list[str] = []
    totals: dict[str, int] = {}

    for entry in data:
        pid = entry.get("_id")
        stats = entry.get("stats", {})
        tot = stats.get("tot")

        if pid is None or tot is None:
            continue

        pid_str = str(pid).strip()
        try:
            tot_int = int(str(tot))
        except (ValueError, TypeError):
            continue

        pokemon_ids.append(pid_str)
        totals[pid_str] = tot_int

    if not pokemon_ids:
        raise RuntimeError(f"No Pokémon loaded from {json_path}")

    return pokemon_ids, totals


def load_gyms(json_path: Path):
    """
    Load gyms from gym.json.

    Expected shape:

    {
        "_id": "1",
        "name": "Pewter Gym",
        ...
    }

    Returns:
        gym_ids: list[str]             # e.g. ["1", "2", "3", ...]
    """
    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)

    gym_ids: list[str] = []

    for entry in data:
        gid = entry.get("_id")
        if gid is None:
            continue
        gym_ids.append(str(gid).strip())

    if not gym_ids:
        raise RuntimeError(f"No gyms loaded from {json_path}")

    return gym_ids


def load_trainers_and_ownership(json_path: Path):
    """
    Load trainers and build ownership mapping from trainer.json.

    Expected trainer.json snippet:

    {
        "_id": "1",
        "name": "A-list Actor Alonso",
        "owns": [
            "290",
            "1052"
        ],
        "leads": "1"
    }

    Returns:
        trainer_ids: list[str]                 # trainer ids as strings
        ownership: dict[str, str]              # pokemon_id -> trainer_id
    """
    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)

    trainer_ids: list[str] = []
    ownership: dict[str, str] = {}

    for entry in data:
        tid = entry.get("_id")
        if tid is None:
            continue

        tid_str = str(tid).strip()
        trainer_ids.append(tid_str)

        owns = entry.get("owns")
        if not owns:
            continue

        for p in owns:
            pid_str = str(p).strip()
            # If multiple trainers list the same Pokémon, last one wins
            ownership[pid_str] = tid_str

    if not trainer_ids:
        raise RuntimeError(f"No trainers loaded from {json_path}")

    return trainer_ids, ownership


def load_types(json_path: Path):
    """Currently unused; present as an extension hook."""
    try:
        with json_path.open(encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


# ---------------------------------------------------------------------------
# BATTLE UTILITIES (from old script, adapted to string IDs)
# ---------------------------------------------------------------------------

def pick_random_opponent(
    all_ids: list[str],
    exclude_id: str,
    ownership: dict[str, str] | None = None,
) -> str | None:
    """
    Pick a random Pokémon ID different from exclude_id and, if ownership is provided,
    not owned by the same trainer as exclude_id.

    If no suitable candidate exists, return None.
    """
    if len(all_ids) < 2:
        raise RuntimeError("Need at least 2 Pokémon to form battles")

    base_trainer = ownership.get(exclude_id) if ownership else None

    if ownership is not None:
        candidates = [
            pid
            for pid in all_ids
            if pid != exclude_id
            and ownership.get(pid) is not None
            and (base_trainer is None or ownership.get(pid) != base_trainer)
        ]
    else:
        candidates = [pid for pid in all_ids if pid != exclude_id]

    if candidates:
        return random.choice(candidates)

    return None


def random_date(start: date, end: date) -> date:
    """Pick a random date between start and end (inclusive)."""
    delta_days = (end - start).days
    if delta_days < 0:
        raise ValueError("Start date must be before end date")
    return start + timedelta(days=random.randint(0, delta_days))


def date_to_iso_z(dt: date) -> str:
    """
    Convert a date object to ISO 8601 with a fixed time and 'Z' suffix.

    Example: 2025-11-27 -> "2025-11-27T10:00:00Z"
    """
    t = datetime(dt.year, dt.month, dt.day, 10, 0, 0)  # 10:00:00 is arbitrary
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# BATTLE GENERATION
# ---------------------------------------------------------------------------

def generate_battles(
    pokemon_ids: list[str],
    pokemon_totals: dict[str, int],
    gym_ids: list[str],
    ownership: dict[str, str],
) -> list[dict]:
    """
    Generate battles as a list of Mongo-like documents.

    IDs used are exactly the _id values from your JSONs, no prefixing.
    """
    start_day = date(2025, 1, 1)
    end_day = date(2025, 12, 31)

    battle_id = 1
    documents: list[dict] = []

    # Only consider Pokémon that are actually owned by some trainer
    owned_pokemon_ids = [pid for pid in pokemon_ids if ownership.get(pid) is not None]

    for base_id in owned_pokemon_ids:
        used_opponents: set[str] = set()

        for _ in range(3):
            opp_id = pick_random_opponent(
                owned_pokemon_ids, exclude_id=base_id, ownership=ownership
            )

            # Ensure unique opponent per base Pokémon
            attempts = 0
            while opp_id is not None and opp_id in used_opponents and attempts < 100:
                opp_id = pick_random_opponent(
                    owned_pokemon_ids, exclude_id=base_id, ownership=ownership
                )
                attempts += 1

            if opp_id is None or opp_id in used_opponents:
                # No valid fresh opponent found for this base Pokémon under constraints
                continue

            used_opponents.add(opp_id)

            # Determine winner / loser by total stat
            base_total = pokemon_totals.get(base_id, 0)
            opp_total = pokemon_totals.get(opp_id, 0)

            if base_total > opp_total:
                winner_id, loser_id = base_id, opp_id
            elif opp_total > base_total:
                winner_id, loser_id = opp_id, base_id
            else:
                # Equal stats: random winner
                winner_id, loser_id = random.sample([base_id, opp_id], 2)

            # Pick a random gym
            gym_id = random.choice(gym_ids)

            # Random date
            battle_day = random_date(start_day, end_day)
            battle_date_iso = date_to_iso_z(battle_day)

            # Trainers from ownership mapping
            winner_trainer_id = ownership.get(winner_id)
            loser_trainer_id = ownership.get(loser_id)

            if winner_trainer_id is None or loser_trainer_id is None:
                # Ownership inconsistent with Pokémon used
                raise KeyError(
                    f"Missing trainer for Pokémon winner={winner_id} or loser={loser_id}"
                )

            battle_doc = {
                "_id": f"b{battle_id}",
                "date": battle_date_iso,
                "gym_id": gym_id,
                "participants": {
                    "hasWon": [
                        {
                            "trainer_id": winner_trainer_id,
                            "pokemon_id": winner_id,
                        }
                    ],
                    "hasLost": [
                        {
                            "trainer_id": loser_trainer_id,
                            "pokemon_id": loser_id,
                        }
                    ],
                },
            }

            documents.append(battle_doc)
            battle_id += 1

    return documents


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> int:
    # Optional seed for reproducibility:
    #   python create_battles_json.py 42
    seed_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if seed_arg is not None:
        try:
            random.seed(int(seed_arg))
        except ValueError:
            random.seed(seed_arg)

    # Load base data
    pokemon_ids, pokemon_totals = load_pokemon(POKEMON_JSON)
    gym_ids = load_gyms(GYM_JSON)
    trainer_ids, ownership = load_trainers_and_ownership(TRAINER_JSON)
    _types = load_types(TYPE_JSON)  # currently unused

    # Generate battles
    battle_docs = generate_battles(
        pokemon_ids=pokemon_ids,
        pokemon_totals=pokemon_totals,
        gym_ids=gym_ids,
        ownership=ownership,
    )

    # Ensure output directory exists
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(battle_docs, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(battle_docs)} battles -> {OUTPUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())