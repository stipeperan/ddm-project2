#!/usr/bin/env python3
"""Update dataset/json/trainer.json `owns` values from dataset/csv/trainer_owns_pokemon.csv

Backs up the original `trainer.json` to `trainer.json.bak.<ts>` before overwriting.
If trainers already have an `owns` array, this script will merge unique pokename values.
"""
import csv
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / 'dataset' / 'csv' / 'trainer_owns_pokemon.csv'
TRAINER_JSON = ROOT / 'dataset' / 'json' / 'trainer.json'


def load_mapping(csv_path):
    mapping = {}
    with open(csv_path, newline='') as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            t = r.get('trainerID') or r.get('trainer_id')
            p = r.get('pokename') or r.get('pokemon') or r.get('pokename')
            if t is None or p is None:
                continue
            t = str(t)
            p = str(p)
            mapping.setdefault(t, []).append(p)
    return mapping


def main():
    if not CSV_PATH.exists():
        print('CSV mapping not found:', CSV_PATH)
        return 2
    if not TRAINER_JSON.exists():
        print('trainer.json not found:', TRAINER_JSON)
        return 2

    mapping = load_mapping(CSV_PATH)
    print(f'Loaded mappings for {len(mapping)} trainers from {CSV_PATH}')

    print('Loading trainer.json (this may take a moment)...')
    with open(TRAINER_JSON, 'r', encoding='utf-8') as fh:
        data = json.load(fh)

    # Backup original
    bak = TRAINER_JSON.with_suffix(TRAINER_JSON.suffix + f'.bak.{int(time.time())}')
    TRAINER_JSON.rename(bak)
    print('Backed up original to', bak)

    updated = 0
    touched = []
    for doc in data:
        # determine trainer id
        tid = None
        if '_id' in doc:
            tid = str(doc.get('_id'))
        elif 'trainerID' in doc:
            tid = str(doc.get('trainerID'))
        elif 'id' in doc:
            tid = str(doc.get('id'))

        if not tid:
            continue

        new_owns = mapping.get(tid)
        if not new_owns:
            continue

        # Normalize existing owns to list of strings
        existing = doc.get('owns')
        if existing is None:
            merged = list(dict.fromkeys(new_owns))
        else:
            # ensure list
            if isinstance(existing, list):
                existing_list = [str(x) for x in existing]
            else:
                existing_list = [str(existing)]
            # merge preserving order and uniqueness
            merged = existing_list[:]
            for p in new_owns:
                if p not in merged:
                    merged.append(p)

        # Only replace if changed
        if doc.get('owns') != merged:
            doc['owns'] = merged
            updated += 1
            touched.append(tid)

    # Write updated file
    with open(TRAINER_JSON, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)

    print(f'Updated owns for {updated} trainer documents in {TRAINER_JSON}')
    if updated:
        print('Sample trainer ids updated:', touched[:20])
    print('Original backup kept at', bak)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
