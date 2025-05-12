import os
import json
import shutil
import tempfile
import unittest
from src.persistence_manager import PersistenceManager
from src.database import Database  # Adjust import to match your structure

class TestPersistenceManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        os.mkdir("data")

        # Mock database object
        self.db = Database()
        self.pm = PersistenceManager(self.db)

    def tearDown(self):
        # Clean up temporary files and restore working directory
        self.pm.close()
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_add_command_writes_to_wal(self):
        self.pm.add_command("SET a 1")
        self.pm._flush_wal()
        with open("data/wal.log") as f:
            content = f.read()
        self.assertIn("SET a 1", content)

    def test_snapshot_creation(self):
        self.db.db = {"a": "1", "b": "2"}
        self.pm._create_snapshot()
        with open("data/snapshot.json") as f:
            data = json.load(f)
        self.assertEqual(data, {"a": "1", "b": "2"})

    def test_add_commands_flushes_correctly(self):
        commands = [f"SET k{i} {i}" for i in range(5)]
        self.pm.add_commands(commands)
        with open("data/wal.log") as f:
            content = f.read()
        for cmd in commands:
            self.assertIn(cmd, content)

if __name__ == "__main__":
    unittest.main()
