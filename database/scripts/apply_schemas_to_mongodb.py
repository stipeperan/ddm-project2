import os
import json
import argparse
import sys
from pymongo import MongoClient, errors
from typing import Optional

# Ensure parent `database` directory is on sys.path so `setup` package can be imported
BASE_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.normpath(os.path.join(BASE_DIR, '..'))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from setup import config


def _derive_collection_name(filename: str) -> str:
    """Derive a collection name from a schema filename.

    If filename is like 'pokemon.battles.schema.json' this returns 'battles'.
    Otherwise returns the base name without '.schema.json'.
    """
    base = filename.rsplit('.schema.json', 1)[0]
    # If there's a dot namespace (e.g. prefix.object), take the last token as collection name
    if '.' in base:
        return base.split('.')[-1]
    return base


def apply_schemas_to_mongodb(db_client: MongoClient, db_name: str, schema_folder: str,
                             validation_level: str = 'strict', validation_action: str = 'error', dry_run: bool = False):
    db = db_client[db_name]

    if not os.path.isdir(schema_folder):
        raise FileNotFoundError(f"Schema folder not found: {schema_folder}")

    applied = []
    errors_list = []

    for filename in sorted(os.listdir(schema_folder)):
        if not filename.endswith('.schema.json'):
            continue

        schema_path = os.path.join(schema_folder, filename)
        collection_name = _derive_collection_name(filename)

        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_doc = json.load(f)

        # Ensure schema_doc is a validator document. If it's already wrapped under $jsonSchema, keep it.
        validator = schema_doc if ('$jsonSchema' in schema_doc) else {'$jsonSchema': schema_doc}

        if dry_run:
            print(f"[dry-run] Would apply validator to collection '{collection_name}': {schema_path}")
            continue

        try:
            # Try to create the collection with validator
            db.create_collection(collection_name, validator=validator)
            # Set validation options if provided (create_collection accepts validator but not validationAction/Level)
            try:
                db.command({'collMod': collection_name, 'validator': validator,
                            'validationLevel': validation_level, 'validationAction': validation_action})
            except Exception:
                # collMod may fail on creation; ignore secondary failure if collection created
                pass
            print(f"✅ Created collection '{collection_name}' with validator from '{filename}'")
            applied.append(collection_name)
        except errors.CollectionInvalid:
            # Collection exists; update validator using collMod
            try:
                db.command({'collMod': collection_name, 'validator': validator,
                            'validationLevel': validation_level, 'validationAction': validation_action})
                print(f"🔁 Updated validator for existing collection '{collection_name}' from '{filename}'")
                applied.append(collection_name)
            except Exception as e:
                print(f"❌ Failed to update validator for '{collection_name}': {e}")
                errors_list.append((collection_name, str(e)))
        except Exception as e:
            print(f"❌ Failed to create collection '{collection_name}': {e}")
            errors_list.append((collection_name, str(e)))

    return applied, errors_list


def main():
    base_dir = os.path.dirname(__file__)
    # scripts/ sits under database/, so default schemas folder is one level up
    default_folder = os.path.join(base_dir, '..', 'schemas')

    parser = argparse.ArgumentParser(description='Apply generated JSON Schema validators to a MongoDB database')
    parser.add_argument('--schema-folder', '-s', default=default_folder, help='Folder containing .schema.json files')
    parser.add_argument('--mongo-uri', '-u', default=None, help='MongoDB connection URI (overrides config)')
    parser.add_argument('--db-name', '-d', default=None, help='Database name (overrides config)')
    parser.add_argument('--validation-level', default='strict', choices=['off', 'moderate', 'strict'], help='Validation level')
    parser.add_argument('--validation-action', default='error', choices=['warn', 'error'], help='Validation action')
    parser.add_argument('--dry-run', action='store_true', help='Do not modify DB, just print actions')

    args = parser.parse_args()

    mongo_uri = args.mongo_uri or config.MONGO_URI
    db_name = args.db_name or config.DB_NAME

    client = config.get_client(mongo_uri)
    try:
        applied, errors_list = apply_schemas_to_mongodb(client, db_name, args.schema_folder,
                                                       validation_level=args.validation_level,
                                                       validation_action=args.validation_action,
                                                       dry_run=args.dry_run)

        print('\nSummary:')
        print(f'  Applied validators to {len(applied)} collection(s)')
        if errors_list:
            print(f'  Errors for {len(errors_list)} collection(s):')
            for coll, err in errors_list:
                print(f'    - {coll}: {err}')
    finally:
        client.close()


if __name__ == '__main__':
    main()