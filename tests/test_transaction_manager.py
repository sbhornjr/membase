import unittest
from src.transaction_manager import TransactionManager
from src.database import Database
from src.persistence_manager import PersistenceManager

class TestTransactionManager(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        self.pm = PersistenceManager(self.db)
        self.tm = TransactionManager(self.db, self.pm)

    def test_single_transaction_commit(self):
        self.tm.begin()
        self.db.set("a", "1")
        self.tm.commit()
        self.assertEqual(self.db.get("a"), "1")

    def test_single_transaction_rollback(self):
        self.db.set("a", "1")
        self.tm.begin()
        self.tm.add_command("a")
        self.db.set("a", "2")
        self.tm.rollback()
        self.assertEqual(self.db.get("a"), "1")

    def test_nested_transactions_commit(self):
        self.tm.begin()
        self.tm.add_command("a")
        self.db.set("a", "1")
        self.tm.begin()
        self.tm.add_command("a")
        self.db.set("a", "2")
        self.tm.commit()  # commit nested
        self.tm.rollback()  # rollback outer
        self.assertIsNone(self.db.get("a"))

    def test_nested_commit_behavior(self):
        self.tm.begin()
        self.tm.add_command("a")
        self.db.set("a", "1")
        self.tm.begin()
        self.tm.add_command("a")
        self.db.set("a", "2")
        self.tm.commit()
        self.tm.add_command("b")
        self.db.set("b", "3")
        self.tm.rollback()
        self.assertIsNone(self.db.get("a"))
        self.assertIsNone(self.db.get("b"))

if __name__ == '__main__':
    unittest.main()
