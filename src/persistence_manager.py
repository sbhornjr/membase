from src.config import Config
import os
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

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

    def add_command(self, command):
        timestamp = datetime.now(ZoneInfo("America/New_York")).isoformat()
        self.wal_file.write(command + " " + timestamp + "\n")
        self.ops_since_flush += 1
        self.ops_since_snapshot += 1
        # Flush WAL and create snapshot if thresholds are reached
        self.stats.wal_size += 1
        if self.ops_since_flush >= self.flush_threshold:
            self._flush_wal()
            self.ops_since_flush = 0
        if self.ops_since_snapshot >= self.snapshot_threshold:
            self._create_snapshot()
            self.ops_since_snapshot = 0

    def add_commands(self, commands):
        for command in commands:
            self.add_command(command)
        self._flush_wal()
        self.ops_since_flush = 0

    def close(self):
        self._flush_wal()
        self.wal_file.close()

    def snapshot(self):
        if self.namespace:
            self._create_snapshot()
            self.ops_since_snapshot = 0

    def startup(self):
        try:
            with open(SNAPSHOT_PATH, "r") as f:
                content = f.read()
                if not content.strip():
                    self.db.db = {}
                else:
                    data = json.loads(content)
                    self.db.db = data.get(self.namespace, {}).get("db", {})
                    if self.db.config.enable_history:
                        self.db.db_history = data.get(self.namespace, {}).get("history", {})
                    for key, value in self.db.db.items():
                        if value in self.db.db_counts:
                            self.db.db_counts[value] += 1
                        else:
                            self.db.db_counts[value] = 1
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
                    if command.startswith("set"):
                        _, key, value, timestamp = command.split()
                        self.db.set(key, value)
                        if self.db.config.enable_history:
                            self.db._track_history(key, value, timestamp)
                    elif command.startswith("delete"):
                        _, key, timestamp = command.split()
                        self.db.delete(key)
                        if self.db.config.enable_history:
                            self.db._track_history(key, value, timestamp)
        except FileNotFoundError:
            pass

    def _flush_wal(self):
        self.wal_file.flush()
        os.fsync(self.wal_file.fileno())

    def _create_snapshot(self, file=SNAPSHOT_PATH):
        snapshot_data = {"db": self.db.db}
        if self.db.config.enable_history:
            snapshot_data["history"] = self.db.db_history
        tmp_file = file.with_suffix(".tmp")
        old_snapshot_data = {}
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
        self.wal_file.close()
        with open(WAL_PATH, "w") as f:
                pass  # Truncates the file
        self.wal_file = open(WAL_PATH, "a")
        self.stats.wal_size = 0
        self.stats.snapshots += 1
