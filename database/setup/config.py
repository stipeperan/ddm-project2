import os
from typing import Optional
from pymongo import MongoClient


def _load_dotenv(path: Optional[str] = None) -> None:
	"""Simple .env loader: reads KEY=VALUE lines and sets environment variables if not already set."""
	if path is None:
		path = os.path.join(os.path.dirname(__file__), '..', '.env')
	try:
		with open(path, 'r', encoding='utf-8') as f:
			for raw in f:
				line = raw.strip()
				if not line or line.startswith('#'):
					continue
				if '=' not in line:
					continue
				key, val = line.split('=', 1)
				key = key.strip()
				val = val.strip().strip('"').strip("'")
				os.environ.setdefault(key, val)
	except FileNotFoundError:
		# It's fine if .env is not present
		return


# Load .env from repository root (one level up from this module)
_load_dotenv()


MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
DB_NAME = os.getenv('DB_NAME', 'pokemon')


def get_client(uri: Optional[str] = None) -> MongoClient:
	"""Return a new MongoClient. Caller is responsible for closing it."""
	return MongoClient(uri or MONGO_URI)


def get_db(client: Optional[MongoClient] = None, db_name: Optional[str] = None):
	"""Return a database instance. If client not provided, a new client is created."""
	if client is None:
		client = get_client()
	return client[db_name or DB_NAME]


__all__ = [
	'MONGO_URI',
	'DB_NAME',
	'get_client',
	'get_db',
]