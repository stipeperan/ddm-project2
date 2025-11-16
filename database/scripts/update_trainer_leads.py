#!/usr/bin/env python3
"""Update dataset/json/trainer.json "leads" values from dataset/csv/trainer_leads_gym.csv

Backups the original `trainer.json` to `trainer.json.bak.<ts>` before overwriting.
"""
import csv
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / 'dataset' / 'csv' / 'trainer_leads_gym.csv'
TRAINER_JSON = ROOT / 'dataset' / 'json' / 'trainer.json'


def load_mapping(csv_path):
    m = {}
    with open(csv_path, newline='') as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            t = r.get('trainer_id')
            g = r.get('gym_id')
            if t is None or g is None:
                continue
            m[str(t)] = str(g)
    return m


def main():
    if not CSV_PATH.exists():
        print('CSV mapping not found:', CSV_PATH)
        return 2
    if not TRAINER_JSON.exists():
        print('trainer.json not found:', TRAINER_JSON)
        return 2

    mapping = load_mapping(CSV_PATH)
    print(f'Loaded {len(mapping)} mappings from {CSV_PATH}')

    # Load trainers
    print('Loading trainer.json (this may take a moment)...')
    with open(TRAINER_JSON, 'r', encoding='utf-8') as fh:
        data = json.load(fh)

    # Backup original
    bak = TRAINER_JSON.with_suffix(TRAINER_JSON.suffix + f'.bak.{int(time.time())}')
    TRAINER_JSON.rename(bak)
    print('Backed up original to', bak)

    # Update
    updated = 0
    touched_ids = []
    for doc in data:
        # determine trainer id field
        tid = None
        if '_id' in doc:
            tid = str(doc.get('_id'))
        elif 'trainerID' in doc:
            tid = str(doc.get('trainerID'))
        elif 'id' in doc:
            tid = str(doc.get('id'))

        if tid and tid in mapping:
            new_leads = mapping[tid]
            # set leads to gym_id as string
            if doc.get('leads') != new_leads:
                doc['leads'] = new_leads
                updated += 1
                touched_ids.append(tid)

    # Write updated file
    with open(TRAINER_JSON, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)

    print(f'Updated {updated} trainer documents in {TRAINER_JSON}')
    if updated:
        print('Sample updated trainer ids:', touched_ids[:20])
    print('Original backup kept at', bak)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
