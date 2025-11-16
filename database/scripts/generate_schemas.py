import json
import os
from typing import List


def generate_schema_files(model_file: str, output_folder: str, wrap: bool = True, do_write: bool = True) -> List[str]:
    """
    Parses a MongoDB visual model JSON file and generates separate
    JSON Schema validation files for each collection.

    Returns a list of written schema file paths.
    """
    # Load the model JSON file
    try:
        with open(model_file, 'r', encoding='utf-8') as f:
            model_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in model file: {model_file}") from e
    except (FileNotFoundError, OSError) as e:
        raise RuntimeError(f"Failed to open model file: {model_file}") from e

    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    written_files: List[str] = []

    # Determine how collections are represented in the model file.
    # Common shapes: {"collections": {...}} or top-level collection objects.
    if isinstance(model_data, dict) and "collections" in model_data:
        items = model_data["collections"].items()
    elif isinstance(model_data, dict) and "entities" in model_data:
        items = model_data["entities"].items()
    else:
        # Fallback: treat top-level dict entries that map to dicts as collections
        items = [(k, v) for k, v in model_data.items() if isinstance(v, dict)]

    for collection_name, coll_def in items:
        validation_schema = None

        if isinstance(coll_def, dict):
            # Look for common keys that hold a JSON Schema
            for key in ("validation", "schema", "jsonSchema", "json_schema"):
                if key in coll_def:
                    validation_schema = coll_def[key]
                    break

            # If the collection definition itself *looks like* a JSON Schema, use it
            if validation_schema is None and any(k in coll_def for k in ("properties", "$schema", "type")):
                validation_schema = coll_def

        if not validation_schema:
            # Nothing sensible to write for this collection; skip it
            continue

        # Prepare output document according to `wrap` flag.
        if wrap:
            # If the schema is already wrapped with `$jsonSchema`, keep as-is.
            if isinstance(validation_schema, dict) and "$jsonSchema" in validation_schema:
                out_doc = validation_schema
            else:
                out_doc = {"$jsonSchema": validation_schema}
        else:
            # Output the raw inner schema (or the dict as-is)
            out_doc = validation_schema

        output_file = os.path.join(output_folder, f"{collection_name}.schema.json")
        if do_write:
            with open(output_file, 'w', encoding='utf-8') as schema_file:
                json.dump(out_doc, schema_file, indent=2, ensure_ascii=False)
            written_files.append(output_file)
        else:
            # When not writing to files, print the output document to stdout
            print(f"--- {collection_name} ---")
            print(json.dumps(out_doc, indent=2, ensure_ascii=False))

    return written_files


if __name__ == '__main__':
    import argparse

    base_dir = os.path.dirname(__file__)
    # scripts/ sits under database/, so model and schemas folders are one level up
    default_model = os.path.join(base_dir, '..', 'model', 'pokemon_model.json')
    default_output = os.path.join(base_dir, '..', 'schemas')

    parser = argparse.ArgumentParser(description='Generate JSON Schema files from a visual model JSON file')
    parser.add_argument('--model-file', '-m', default=default_model, help='Path to the model JSON file')
    parser.add_argument('--output-folder', '-o', default=default_output, help='Folder to write schema files')
    parser.add_argument('--no-wrap', dest='wrap', action='store_false', help='Do not wrap schemas under $jsonSchema')
    parser.add_argument('--stdout', dest='stdout', action='store_true', help='Print schemas to stdout instead of writing files')

    args = parser.parse_args()

    written = generate_schema_files(args.model_file, args.output_folder, wrap=args.wrap, do_write=not args.stdout)
    if args.stdout:
        # generate_schema_files already printed documents when do_write=False
        pass
    else:
        if written:
            print(f"Wrote {len(written)} schema file(s) to {args.output_folder}")
        else:
            print("No schema files were generated. Check the model file format.")