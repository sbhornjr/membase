import unittest
from src.database import Database

class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.db = Database()

    def test_set_and_get(self):
        self.db.set("a", "1", "default")
        self.assertEqual(self.db.get("a", "default"), "1")

    def test_get_nonexistent(self):
        self.assertIsNone(self.db.get("nonexistent", "default"))

    def test_delete(self):
        self.db.set("a", "1", "default")
        self.db.delete("a", "default")
        self.assertIsNone(self.db.get("a", "default"))

    def test_count(self):
        self.db.set("a", "1", "default")
        self.db.set("b", "1", "default")
        self.db.set("c", "2", "default")
        self.assertEqual(self.db.count("1", "default"), 2)
        self.assertEqual(self.db.count("2", "default"), 1)
        self.assertEqual(self.db.count("3", "default"), 0)

    def test_overwrite_value(self):
        self.db.set("a", "1", "default")
        self.db.set("a", "2", "default")
        self.assertEqual(self.db.get("a", "default"), "2")
        self.assertEqual(self.db.count("1", "default"), 1)
        self.assertEqual(self.db.count("2", "default"), 1)

    def test_delete_updates_count(self):
        self.db.set("a", "1", "default")
        self.db.set("b", "1", "default")
        self.db.delete("a", "default")
        self.assertEqual(self.db.count("1", "default"), 1)

if __name__ == "__main__":
    unittest.main()
