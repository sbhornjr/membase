import unittest
from src.database import Database

class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.db = Database()

    def test_set_and_get(self):
        self.db.set("a", "1")
        self.assertEqual(self.db.get("a"), "1")

    def test_get_nonexistent(self):
        self.assertIsNone(self.db.get("nonexistent"))

    def test_delete(self):
        self.db.set("a", "1")
        self.db.delete("a")
        self.assertIsNone(self.db.get("a"))

    def test_count(self):
        self.db.set("a", "1")
        self.db.set("b", "1")
        self.db.set("c", "2")
        self.assertEqual(self.db.count("1"), 2)
        self.assertEqual(self.db.count("2"), 1)
        self.assertEqual(self.db.count("3"), 0)

    def test_overwrite_value(self):
        self.db.set("a", "1")
        self.db.set("a", "2")
        self.assertEqual(self.db.get("a"), "2")
        self.assertEqual(self.db.count("1"), 1)
        self.assertEqual(self.db.count("2"), 1)

    def test_delete_updates_count(self):
        self.db.set("a", "1")
        self.db.set("b", "1")
        self.db.delete("a")
        self.assertEqual(self.db.count("1"), 1)

if __name__ == "__main__":
    unittest.main()
