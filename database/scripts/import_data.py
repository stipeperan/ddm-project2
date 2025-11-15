import os
import sys
import json
import argparse
from typing import Iterable

from pymongo import MongoClient, errors

# Ensure parent `database` directory is on sys.path so `setup` package can be imported
BASE_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.normpath(os.path.join(BASE_DIR, '..'))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from setup import config


def chunked_iterable(seq: Iterable, size: int):
    seq = list(seq)
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def import_json_file(db, collection_name: str, path: str, batch_size: int = 1000, dry_run: bool = False):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    inserted = 0
    errors_list = []

    if isinstance(data, list):
        for batch in chunked_iterable(data, batch_size):
            if dry_run:
                print(f"[dry-run] Would insert {len(batch)} documents into '{collection_name}' (from {os.path.basename(path)})")
                inserted += len(batch)
                continue

            try:
                res = db[collection_name].insert_many(batch, ordered=False)
                inserted += len(res.inserted_ids)
            except errors.BulkWriteError as bwe:
                # Some writes may fail (duplicate keys, etc.)
                details = bwe.details.get('writeErrors', []) if bwe.details else []
                errors_list.append((collection_name, len(details), str(bwe)))
                # count successful inserts if available
                if 'nInserted' in bwe.details:
                    inserted += bwe.details.get('nInserted', 0)
            except Exception as e:
                errors_list.append((collection_name, 0, str(e)))
    elif isinstance(data, dict):
        # single document
        if dry_run:
            print(f"[dry-run] Would insert 1 document into '{collection_name}' (from {os.path.basename(path)})")
            inserted = 1
        else:
            try:
                db[collection_name].insert_one(data)
                inserted = 1
            except Exception as e:
                errors_list.append((collection_name, 0, str(e)))
    else:
        # unsupported structure
        errors_list.append((collection_name, 0, f"Unsupported JSON root type: {type(data)}"))

    return inserted, errors_list


def main():
    base_dir = os.path.dirname(__file__)
    # default data folder: project-root/dataset/json
    default_data = os.path.normpath(os.path.join(base_dir, '..', '..', 'dataset', 'json'))

    parser = argparse.ArgumentParser(description='Import JSON dataset files into MongoDB')
    parser.add_argument('--data-folder', '-i', default=default_data, help='Folder containing JSON files to import')
    parser.add_argument('--mongo-uri', '-u', default=None, help='MongoDB connection URI (overrides config)')
    parser.add_argument('--db-name', '-d', default=None, help='Database name (overrides config)')
    parser.add_argument('--drop', action='store_true', help='Drop collection before importing')
    parser.add_argument('--dry-run', action='store_true', help='Do not write to DB, only print actions')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for bulk inserts')
    parser.add_argument('--files', nargs='*', help='Optional list of specific JSON files (filenames) to import')

    args = parser.parse_args()

    data_folder = args.data_folder
    mongo_uri = args.mongo_uri or config.MONGO_URI
    db_name = args.db_name or config.DB_NAME

    if not os.path.isdir(data_folder):
        print(f"Data folder not found: {data_folder}")
        raise SystemExit(1)

    client = config.get_client(mongo_uri)
    try:
        db = client[db_name]

        files = sorted([f for f in os.listdir(data_folder) if f.endswith('.json')])
        if args.files:
            # filter to provided filenames
            files = [f for f in files if f in args.files]

        total_inserted = 0
        total_errors = []

        for filename in files:
            path = os.path.join(data_folder, filename)
            # collection name: use filename without extension
            collection_name = filename.rsplit('.json', 1)[0]

            if args.drop and not args.dry_run:
                try:
                    db.drop_collection(collection_name)
                    print(f"Dropped existing collection '{collection_name}'")
                except Exception as e:
                    print(f"Failed to drop collection '{collection_name}': {e}")

            inserted, errors = import_json_file(db, collection_name, path, batch_size=args.batch_size, dry_run=args.dry_run)
            total_inserted += inserted
            total_errors.extend(errors)
            print(f"File: {filename} -> inserted: {inserted}, errors: {len(errors)}")

        print('\nImport summary:')
        print(f'  Total documents inserted: {total_inserted}')
        if total_errors:
            print(f'  Files with errors: {len(total_errors)}')
            for coll, count, err in total_errors:
                print(f'    - {coll}: {count} errors; example: {err}')
    finally:
        client.close()


if __name__ == '__main__':
    main()
