import os
import json
import shutil
import tempfile
import unittest
from src.persistence_manager import PersistenceManager
from src.stats import StatsTracker
from src.database import Database  # Adjust import to match your structure

class TestPersistenceManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        os.mkdir("data")

        # Mock database object
        stats = StatsTracker()
        self.db = Database()
        self.pm = PersistenceManager(self.db, stats)
        self.pm.namespace = "default"

    def tearDown(self):
        # Clean up temporary files and restore working directory
        self.pm.close()
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_add_command_writes_to_wal(self):
        self.pm.add_command("set a 1", "default")
        self.pm._flush_wal()
        with open("data/wal.log") as f:
            content = f.read()
        self.assertIn("default set a 1", content)

    async def test_snapshot_creation(self):
        self.db.db = {"default": {"a": "1", "b": "2"}}
        await self.pm._create_snapshot("default")
        with open("data/snapshot.json") as f:
            data = json.load(f)
        self.assertEqual(data, {"default": {"db": {"a": "1", "b": "2"}, "history": []}})

    def test_add_commands_flushes_correctly(self):
        commands = [f"set k{i} {i}" for i in range(5)]
        self.pm.add_commands(commands, "default")
        with open("data/wal.log") as f:
            content = f.read()
        for cmd in commands:
            self.assertIn(f"default {cmd}", content)

if __name__ == "__main__":
    unittest.main()
