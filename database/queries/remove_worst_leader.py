#!/usr/bin/env python3
import argparse
import os
import sys
from pymongo import MongoClient

# Ensure `database` (the parent of this file's directory) is on sys.path so
# `from setup import config` works regardless of current working directory.
_THIS_DIR = os.path.dirname(__file__)
_DATABASE_DIR = os.path.dirname(_THIS_DIR)
if _DATABASE_DIR not in sys.path:
    sys.path.insert(0, _DATABASE_DIR)

from setup import config

def find_worst_leader(db):
    pipeline = [
        {"$match": {"leads": {"$exists": True, "$ne": None}}},
        {"$lookup": {
            "from": "battles",
            "let": {"gymId": "$leads"},
            "pipeline": [{"$match": {"$expr": {"$eq": ["$gym_id", "$$gymId"]}}}],
            "as": "battles"
        }},
        {"$addFields": {
            "total": {"$size": "$battles"},
            "wins": {"$size": {"$filter": {"input": "$battles", "as": "b", "cond": {"$eq": ["$$b.participants.winner.trainer_id", "$_id"]}}}}
        }},
        {"$addFields": {"ratio": {"$cond": [{"$eq": ["$total", 0]}, 0, {"$divide": ["$wins", "$total"]}]}}},
        {"$sort": {"ratio": 1, "total": 1}},
        {"$limit": 1}
    ]
    res = list(db.trainer.aggregate(pipeline))
    return res[0] if res else None

def main(dry_run=True, mongo_uri=None, db_name=None):
    client = MongoClient(mongo_uri or config.MONGO_URI)
    db = client[db_name or config.DB_NAME]
    try:
        worst = find_worst_leader(db)
        if not worst:
            print("No leader found.")
            return 0
        print("Candidate to remove:", {k: worst[k] for k in ("_id","name","leads","wins","total","ratio") if k in worst})
        trainerId = worst["_id"]
        gymId = worst.get("leads")

        if dry_run:
            print("[dry-run] would remove trainer", trainerId)
            print("[dry-run] would pull trainer from trainer.owns arrays and unset gym leader fields")
            return 0

        # cleanup references
        db.trainer.update_many({"owns": trainerId}, {"$pull": {"owns": trainerId}})
        # unset gym leader fields if present
        db.gym.update_many({"leader": trainerId}, {"$unset": {"leader": ""}})
        # delete trainer doc
        db.trainer.delete_one({"_id": trainerId})
        print("Deleted trainer", trainerId)
        return 0
    finally:
        client.close()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mongo-uri", "-u", help="MongoDB URI")
    ap.add_argument("--db-name", "-d", help="DB name")
    ap.add_argument("--apply", action="store_true", help="Actually apply deletions (omit for dry-run)")
    args = ap.parse_args()
    main(dry_run=not args.apply, mongo_uri=args.mongo_uri, db_name=args.db_name)