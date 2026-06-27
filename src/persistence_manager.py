from src.config import Config
import os
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import asyncio

DATA_DIR = Path("data")
WAL_PATH = DATA_DIR / "wal.log"    
SNAPSHOT_PATH = DATA_DIR / "snapshot.json"

class PersistenceManager:
    def __init__(self, db, stats):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        config = Config()
        self.snapshot_threshold = config.snapshot_threshold
        self.flush_threshold = config.flush_threshold
        self.ops_since_snapshot = 0
        self.ops_since_flush = 0
        self.wal_file = open(WAL_PATH, "a")
        self.db = db
        self.stats = stats
        self.namespace = None
        self._snapshot_lock = asyncio.Lock()

    def set_namespace(self, namespace):
        self.namespace = namespace
        self.db.namespace = namespace

    def add_command(self, command, namespace = None):
        ns = namespace if namespace else self.namespace
        timestamp = datetime.now(ZoneInfo("America/New_York")).isoformat()
        self.wal_file.write(ns + " " + command + " " + timestamp + "\n")
        self.ops_since_flush += 1
        self.ops_since_snapshot += 1
        # Flush WAL and create snapshot if thresholds are reached
        self.stats.wal_size += 1
        if self.ops_since_flush >= self.flush_threshold:
            self._flush_wal()
            self.ops_since_flush = 0
        if self.ops_since_snapshot >= self.snapshot_threshold:
            self._create_snapshot(ns)
            self.ops_since_snapshot = 0

    def add_commands(self, commands, namespace = None):
        for command in commands:
            self.add_command(command, namespace if namespace else self.namespace)
        self._flush_wal()
        self.ops_since_flush = 0

    def close(self):
        self._flush_wal()
        self.wal_file.close()

    async def snapshot(self, namespace = None):
        await self._create_snapshot(namespace if namespace else self.namespace)
        self.ops_since_snapshot = 0

    def startup(self):
        try:
            with open(SNAPSHOT_PATH, "r") as f:
                content = f.read()
                if not content.strip():
                    self.db.db = {}
                else:
                    data = json.loads(content)
                    for k, v in data.items():
                        self.db.db[k] = v.get("db", {})
                        if self.db.config.enable_history:
                            self.db.db_history[k] = data.get("history", {})
                    for namespace, store in self.db.db.items():
                        for k, v in store.items():
                            if namespace in self.db.db_counts:
                                if value in self.db.db_counts[namespace]:
                                    self.db.db_counts[namespace][v] += 1
                                else:
                                    self.db.db_counts[namespace][v] = 1
                            else:
                                self.db.db_counts[namespace] = {}
                                self.db.db_counts[namespace][v] = 1
        except FileNotFoundError:
            print("Error: Could not find snapshot file. Starting with an empty database.")
        except json.JSONDecodeError as e:
            print(f"Error: Corrupted snapshot file: {e}. Starting with an empty database.")
            self.db.db = {}
        except Exception as e:
            print(f"Unexpected error: {e}. Starting with an empty database.")
            self.db.db = {}
        try:
            with open(WAL_PATH, "r") as f:
                for line in f:
                    command = line.strip()
                    if command.split(" ", 1)[1].startswith("set"):
                        namespace, _, key, value, timestamp = command.split()
                        self.db.set(key, value, namespace)
                        if self.db.config.enable_history:
                            self.db._track_history(key, value, namespace, timestamp)
                    elif command.split(" ", 1)[1].startswith("delete"):
                        namespace, _, key, timestamp = command.split()
                        self.db.delete(key, namespace)
                        if self.db.config.enable_history:
                            self.db._track_history(key, value, namespace, timestamp)
        except FileNotFoundError:
            pass

    def _flush_wal(self):
        self.wal_file.flush()
        os.fsync(self.wal_file.fileno())

    async def _create_snapshot(self, namespace, file=SNAPSHOT_PATH):
        async with self._snapshot_lock:
            snapshot_data = {"db": self.db.db.get(namespace, {})}
            if self.db.config.enable_history:
                snapshot_data["history"] = self.db.db_history.get(namespace, [])
            tmp_file = file.with_suffix(".tmp")
            old_snapshot_data = {}
            if not file.exists():
                with open(file, "w") as f:
                    json.dump({}, f)
            with open(file, "r") as f:
                try:
                    old_snapshot_data = json.load(f)
                except json.JSONDecodeError:
                    pass
            old_snapshot_data[self.namespace] = snapshot_data
            with open(tmp_file, "w") as f:
                json.dump(old_snapshot_data, f)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_file, file)
            self.stats.snapshots += 1
