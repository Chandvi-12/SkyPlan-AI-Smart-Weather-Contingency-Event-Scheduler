import os
import json
import logging
from datetime import datetime, date
from pathlib import Path
from bson import ObjectId
import pymongo
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

class JSONEncoderCustom(json.JSONEncoder):
    """Custom JSON encoder for BSON types like ObjectId and datetime"""
    def default(self, o):
        if isinstance(o, ObjectId):
            return {"$oid": str(o)}
        if isinstance(o, (datetime, date)):
            return {"$date": o.isoformat()}
        return super().default(o)

def json_decoder_object_hook(dct):
    """Hook to reconstruct ObjectId and datetime from JSON"""
    if "$oid" in dct:
        return ObjectId(dct["$oid"])
    if "$date" in dct:
        try:
            return datetime.fromisoformat(dct["$date"])
        except Exception:
            return dct["$date"]
    return dct

class DatabaseManager:
    _instance = None

    def __init__(self):
        self.client = None
        self.db = None
        self.is_mock = False
        self.connection_status = "uninitialized"
        self.collections_list = [
            "users", "events", "weather_data", 
            "predictions", "venues", "notifications", "alternatives"
        ]

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def initialize(self, app):
        mongo_uri = app.config.get("MONGO_URI", "mongodb://localhost:27017/skyplan_ai")
        db_name = app.config.get("DB_NAME", "skyplan_ai")
        data_dir = Path(app.config.get("DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
        data_dir.mkdir(parents=True, exist_ok=True)
        self.persistence_file = data_dir / "local_db.json"

        try:
            # Try connecting to real MongoDB with a fast timeout
            logger.info(f"Attempting to connect to MongoDB at: {mongo_uri}")
            client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
            client.server_info()  # Triggers server selection
            self.client = client
            self.db = client[db_name]
            self.is_mock = False
            self.connection_status = "Connected to MongoDB"
            logger.info("Successfully connected to real MongoDB instance.")
            self._create_indexes()
        except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as e:
            logger.warning(
                f"Could not connect to MongoDB server ({e}). "
                "Activating embedded mock MongoDB engine with persistent JSON storage. "
                "All features (Auth, CRUD, Weather, ML, Recommendations) will work completely!"
            )
            import mongomock
            self.client = mongomock.MongoClient()
            self.db = self.client[db_name]
            self.is_mock = True
            self.connection_status = "Running on Embedded MongoDB Engine (Persistent)"
            self._load_local_storage()
            self._create_indexes()

    def _create_indexes(self):
        try:
            self.db.users.create_index("email", unique=True)
            self.db.events.create_index([("user_id", pymongo.ASCENDING), ("event_date", pymongo.ASCENDING)])
            self.db.weather_data.create_index([("city", pymongo.ASCENDING), ("forecast_date", pymongo.ASCENDING)])
            self.db.predictions.create_index("event_id")
            self.db.venues.create_index([("city", pymongo.ASCENDING), ("capacity", pymongo.ASCENDING)])
            self.db.notifications.create_index([("user_id", pymongo.ASCENDING), ("is_read", pymongo.ASCENDING)])
            self.db.alternatives.create_index("event_id")
        except Exception as e:
            logger.debug(f"Index creation note: {e}")

    def _load_local_storage(self):
        """Restore saved collections when using embedded mongomock engine"""
        if self.persistence_file.exists():
            try:
                with open(self.persistence_file, "r", encoding="utf-8") as f:
                    data = json.load(f, object_hook=json_decoder_object_hook)
                for col_name, docs in data.items():
                    col = self.db[col_name]
                    col.delete_many({})
                    if docs:
                        col.insert_many(docs)
                logger.info(f"Restored {sum(len(d) for d in data.values())} documents from persistent store.")
            except Exception as ex:
                logger.error(f"Failed to load persistent storage: {ex}")

    def sync_storage(self):
        """Persist state to JSON if running embedded mock engine"""
        if not self.is_mock:
            return
        try:
            dump = {}
            for col_name in self.collections_list:
                docs = list(self.db[col_name].find({}))
                dump[col_name] = docs
            with open(self.persistence_file, "w", encoding="utf-8") as f:
                json.dump(dump, f, cls=JSONEncoderCustom, indent=2)
        except Exception as ex:
            logger.error(f"Failed syncing embedded storage: {ex}")

    def get_collection(self, name):
        return self.db[name]

    @property
    def users(self):
        return self.db.users

    @property
    def events(self):
        return self.db.events

    @property
    def weather_data(self):
        return self.db.weather_data

    @property
    def predictions(self):
        return self.db.predictions

    @property
    def venues(self):
        return self.db.venues

    @property
    def notifications(self):
        return self.db.notifications

    @property
    def alternatives(self):
        return self.db.alternatives

db_manager = DatabaseManager.get_instance()

def get_db():
    return db_manager.db

def get_db_manager():
    return db_manager

