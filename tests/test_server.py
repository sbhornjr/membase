from fastapi.testclient import TestClient
from server.server import app
import unittest

client = TestClient(app)

class TestServer(unittest.TestCase):

    def setUp(self):
        # Reset the server state before each test
        client.get("/v1/namespaces/default/clear")

    def tearDown(self):
        # Clear the server state after each test
        client.get("/v1/namespaces/default/clear")

    def test_set_key(self):
        response = client.put("/v1/namespaces/default/keys/x", json={"value": 1})
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["operation"], "set")
        self.assertEqual(data["namespace"], "default")
        self.assertEqual(data["key"], "x")
        self.assertEqual(data["value"], 1)
        self.assertEqual(data["transaction_depth"], 0)

    def test_get_key(self):
        # First set a key
        client.put("/v1/namespaces/default/keys/x", json={"value": 1})
        
        # Now get the key
        response = client.get("/v1/namespaces/default/keys/x")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["exists"], True)
        self.assertEqual(data["namespace"], "default")
        self.assertEqual(data["key"], "x")
        self.assertEqual(data["value"], 1)

    def test_get_nonexistent_key(self):
        response = client.get("/v1/namespaces/default/keys/nonexistent")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data["ok"], False)
        self.assertEqual(data["error"]["code"], "key_not_found")
        self.assertEqual(data["error"]["recoverable"], True)

    def test_delete_key(self):
        # First set a key
        client.put("/v1/namespaces/default/keys/x", json={"value": 1})
        
        # Now delete the key
        response = client.delete("/v1/namespaces/default/keys/x")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["operation"], "delete")
        self.assertEqual(data["namespace"], "default")
        self.assertEqual(data["key"], "x")
        self.assertEqual(data["existed"], True)
        self.assertEqual(data["old_value"], 1)
        self.assertEqual(data["value"], None)
        self.assertEqual(data["transaction_depth"], 0)

    def test_delete_nonexistent_key(self):
        # Try to delete a non-existent key
        response = client.delete("/v1/namespaces/default/keys/nonexistent")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data["ok"], False)
        self.assertEqual(data["error"]["code"], "key_not_found")
        self.assertEqual(data["error"]["recoverable"], True)

    def test_begin_transaction(self):
        response = client.get("/v1/namespaces/default/transactions/begin")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["operation"], "begin_transaction")
        self.assertEqual(data["transaction_depth"], 1)

    def test_commit_transaction(self):
        # Begin a transaction first
        client.get("/v1/namespaces/default/transactions/begin")
        
        # Now commit the transaction
        response = client.get("/v1/namespaces/default/transactions/commit")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["operation"], "commit_transaction")
        self.assertEqual(data["transaction_depth"], 0)

    def test_rollback_transaction(self):
        # Begin a transaction first
        client.get("/v1/namespaces/default/transactions/begin")
        
        # Now rollback the transaction
        response = client.get("/v1/namespaces/default/transactions/rollback")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["operation"], "rollback_transaction")
        self.assertEqual(data["transaction_depth"], 0)

    def test_commit_without_active_transaction(self):
        response = client.get("/v1/namespaces/default/transactions/commit")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["ok"], False)
        self.assertEqual(data["error"]["code"], "no_active_transaction")
        self.assertEqual(data["error"]["recoverable"], True)

    def test_rollback_without_active_transaction(self):
        response = client.get("/v1/namespaces/default/transactions/rollback")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["ok"], False)
        self.assertEqual(data["error"]["code"], "no_active_transaction")
        self.assertEqual(data["error"]["recoverable"], True)

    def test_transaction_1(self):
        # Begin a transaction
        client.get("/v1/namespaces/default/transactions/begin")
        
        # Set a key within the transaction
        client.put("/v1/namespaces/default/keys/x", json={"value": 1})
        
        # Get the key within the transaction
        response = client.get("/v1/namespaces/default/keys/x")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["exists"], True)
        self.assertEqual(data["namespace"], "default")
        self.assertEqual(data["key"], "x")
        self.assertEqual(data["value"], 1)
        
        # Rollback the transaction
        client.get("/v1/namespaces/default/transactions/rollback")
        
        # Get the key after rollback
        response = client.get("/v1/namespaces/default/keys/x")
        self.assertEqual(response.status_code, 404)

    def test_transaction_2(self):
        # Begin a transaction
        client.get("/v1/namespaces/default/transactions/begin")
        
        # Set a key within the transaction
        client.put("/v1/namespaces/default/keys/x", json={"value": 1})
        
        # Get the key within the transaction
        response = client.get("/v1/namespaces/default/keys/x")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["exists"], True)
        self.assertEqual(data["namespace"], "default")
        self.assertEqual(data["key"], "x")
        self.assertEqual(data["value"], 1)
        
        # Commit the transaction
        client.get("/v1/namespaces/default/transactions/commit")
        
        # Get the key after commit
        response = client.get("/v1/namespaces/default/keys/x")
        self.assertEqual(response.status_code, 200)

    def test_transaction_3(self):
        # Begin a transaction
        client.get("/v1/namespaces/default/transactions/begin")
        
        # Set a key within the transaction
        client.put("/v1/namespaces/default/keys/x", json={"value": 1})
        
        # Begin a nested transaction
        client.get("/v1/namespaces/default/transactions/begin")
        
        # Set another key within the nested transaction
        client.put("/v1/namespaces/default/keys/y", json={"value": 2})
        
        # Rollback the nested transaction
        client.get("/v1/namespaces/default/transactions/rollback")
        
        # Get the first key (should still exist)
        response = client.get("/v1/namespaces/default/keys/x")
        self.assertEqual(response.status_code, 200)
        
        # Get the second key (should not exist)
        response = client.get("/v1/namespaces/default/keys/y")
        self.assertEqual(response.status_code, 404)

    def test_transaction_4(self):
        # Begin a transaction
        client.get("/v1/namespaces/default/transactions/begin")
        
        # Set a key within the transaction
        client.put("/v1/namespaces/default/keys/x", json={"value": 1})
        
        # Begin a nested transaction
        client.get("/v1/namespaces/default/transactions/begin")
        
        # Set another key within the nested transaction
        client.put("/v1/namespaces/default/keys/y", json={"value": 2})
        
        # Commit the nested transaction
        client.get("/v1/namespaces/default/transactions/commit")
        
        # Get the first key (should still exist)
        response = client.get("/v1/namespaces/default/keys/x")
        self.assertEqual(response.status_code, 200)
        
        # Get the second key (should still exist)
        response = client.get("/v1/namespaces/default/keys/y")
        self.assertEqual(response.status_code, 200)

    def test_transaction_5(self):
        # Begin a transaction
        client.get("/v1/namespaces/default/transactions/begin")
        
        # Set a key within the transaction
        client.put("/v1/namespaces/default/keys/x", json={"value": 1})
        
        # Begin a nested transaction
        client.get("/v1/namespaces/default/transactions/begin")
        
        # Set another key within the nested transaction
        client.put("/v1/namespaces/default/keys/y", json={"value": 2})
        
        # Commit nested transaction
        client.get("/v1/namespaces/default/transactions/commit")

        # Rollback outer transaction
        client.get("/v1/namespaces/default/transactions/rollback")
        
        # Get the first key (should not exist)
        response = client.get("/v1/namespaces/default/keys/x")
        self.assertEqual(response.status_code, 404)

        # Get the second key (should not exist)
        response = client.get("/v1/namespaces/default/keys/y")
        self.assertEqual(response.status_code, 404)

    def test_transaction_6(self):
        # Set a key outside of any transaction
        client.put("/v1/namespaces/default/keys/x", json={"value": 1})

        # Begin a transaction
        client.get("/v1/namespaces/default/transactions/begin")

        # Delete the key within the transaction
        client.delete("/v1/namespaces/default/keys/x")

        # Get the key within the transaction (should not exist)
        response = client.get("/v1/namespaces/default/keys/x")
        self.assertEqual(response.status_code, 404)

        # Rollback the transaction
        client.get("/v1/namespaces/default/transactions/rollback")  

        # Get the key after rollback (should exist again)
        response = client.get("/v1/namespaces/default/keys/x")
        self.assertEqual(response.status_code, 200)

    def test_clear_namespace(self):
        # Set some keys
        client.put("/v1/namespaces/default/keys/x", json={"value": 1})
        client.put("/v1/namespaces/default/keys/y", json={"value": 2})

        # Clear the namespace
        response = client.get("/v1/namespaces/default/clear")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["message"], "Namespace cleared")

        # Get the first key (should not exist)
        response = client.get("/v1/namespaces/default/keys/x")
        self.assertEqual(response.status_code, 404)

        # Get the second key (should not exist)
        response = client.get("/v1/namespaces/default/keys/y")
        self.assertEqual(response.status_code, 404)

    def test_clear_database_with_active_transaction(self):
        # Set a key
        client.put("/v1/namespaces/default/keys/x", json={"value": 1})

        # Begin a transaction
        client.get("/v1/namespaces/default/transactions/begin")

        # Set another key within the transaction
        client.put("/v1/namespaces/default/keys/y", json={"value": 2})

        # Clear the database
        response = client.get("/v1/namespaces/default/clear")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["message"], "Namespace cleared")

        # Get the first key (should not exist)
        response = client.get("/v1/namespaces/default/keys/x")
        self.assertEqual(response.status_code, 404)

        # Get the second key (should not exist)
        response = client.get("/v1/namespaces/default/keys/y")
        self.assertEqual(response.status_code, 404)

    def test_clear_database_with_nested_transactions(self):
        # Set a key
        client.put("/v1/namespaces/default/keys/x", json={"value": 1})

        # Begin a transaction
        client.get("/v1/namespaces/default/transactions/begin")

        # Set another key within the transaction
        client.put("/v1/namespaces/default/keys/y", json={"value": 2})

        # Begin a nested transaction
        client.get("/v1/namespaces/default/transactions/begin")

        # Set another key within the nested transaction
        client.put("/v1/namespaces/default/keys/z", json={"value": 3})

        # Clear the database
        response = client.get("/v1/namespaces/default/clear")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["message"], "Namespace cleared")

        # Get the first key (should not exist)
        response = client.get("/v1/namespaces/default/keys/x")
        self.assertEqual(response.status_code, 404)

        # Get the second key (should not exist)
        response = client.get("/v1/namespaces/default/keys/y")
        self.assertEqual(response.status_code, 404)

        # Get the third key (should not exist)
        response = client.get("/v1/namespaces/default/keys/z")
        self.assertEqual(response.status_code, 404)

    def test_count_value(self):
        # Set some keys
        client.put("/v1/namespaces/default/keys/x", json={"value": 1})
        client.put("/v1/namespaces/default/keys/y", json={"value": 1})
        client.put("/v1/namespaces/default/keys/z", json={"value": 2})

        # Count the value 1
        response = client.post("/v1/namespaces/default/count", json={"value": 1})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["value"], 1)
        self.assertEqual(data["count"], 2)
        self.assertEqual(data["namespace"], "default")

    def test_count_nonexistent_value(self):
        # Count a value that doesn't exist
        response = client.post("/v1/namespaces/default/count", json={"value": 999})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["value"], 999)
        self.assertEqual(data["count"], 0)
        self.assertEqual(data["namespace"], "default")

    def test_get_keys(self):
        # Set some keys
        client.put("/v1/namespaces/default/keys/x", json={"value": 1})
        client.put("/v1/namespaces/default/keys/y", json={"value": 2})

        # Get the keys
        response = client.get("/v1/namespaces/default/keys")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(set(data["keys"]), {"x", "y"})
        self.assertEqual(data["namespace"], "default")

    def test_keys_empty(self):
        # Get keys from an empty namespace
        response = client.get("/v1/namespaces/default/keys")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["keys"], [])
        self.assertEqual(data["namespace"], "default")
    
    def test_exists(self):
        # Set a key
        client.put("/v1/namespaces/default/keys/x", json={"value": 1})

        # Check if the key exists
        response = client.get("/v1/namespaces/default/keys/x/exists")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["exists"], True)
        self.assertEqual(data["key"], "x")
        self.assertEqual(data["namespace"], "default")

    def test_exists_nonexistent_key(self):
        # Check if a non-existent key exists
        response = client.get("/v1/namespaces/default/keys/nonexistent/exists")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["exists"], False)
        self.assertEqual(data["key"], "nonexistent")
        self.assertEqual(data["namespace"], "default")

    def test_find_value(self):
        # Set some keys
        client.put("/v1/namespaces/default/keys/x", json={"value": 1})
        client.put("/v1/namespaces/default/keys/y", json={"value": 1})
        client.put("/v1/namespaces/default/keys/z", json={"value": 2})

        # Find keys with value 1
        response = client.post("/v1/namespaces/default/find", json={"value": 1})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(set(data["keys"]), {"x", "y"})
        self.assertEqual(data["namespace"], "default")

    def test_find_nonexistent_value(self):
        # Find keys with a value that doesn't exist
        response = client.post("/v1/namespaces/default/find", json={"value": 999})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["keys"], [])
        self.assertEqual(data["namespace"], "default")

    def test_dump_database(self):
        # Set some keys
        client.put("/v1/namespaces/default/keys/x", json={"value": 1})
        client.put("/v1/namespaces/default/keys/y", json={"value": 2})

        # Dump the database
        response = client.get("/v1/namespaces/default/dump")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["data"], {"x": 1, "y": 2})
        self.assertEqual(data["namespace"], "default")

    def test_dump_empty_database(self):
        # Dump an empty database
        response = client.get("/v1/namespaces/default/dump")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["data"], {})
        self.assertEqual(data["namespace"], "default")

    def test_snapshot(self):
        # Set some keys
        client.put("/v1/namespaces/default/keys/x", json={"value": 1})
        client.put("/v1/namespaces/default/keys/y", json={"value": 2})
        # Create a snapshot
        response = client.get("/v1/namespaces/default/snapshot")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["operation"], "create_snapshot")
        self.assertEqual(data["message"], "Snapshot created")
        self.assertEqual(data["namespace"], "default")

    def test_get_stats(self):
        # Set some keys
        client.put("/v1/namespaces/default/keys/x", json={"value": 1})
        client.put("/v1/namespaces/default/keys/y", json={"value": 2})
        # Get stats
        response = client.get("/v1/stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["operation"], "get_stats")
        self.assertIn("set_ops", data["stats"])
        self.assertIn("get_ops", data["stats"])
        self.assertIn("delete_ops", data["stats"])
        self.assertIn("commits", data["stats"])
        self.assertIn("rollbacks", data["stats"])
        self.assertIn("snapshots", data["stats"])
        self.assertIn("wal_size", data["stats"])

    def test_get_history(self):
        # Set some keys
        client.put("/v1/namespaces/default/keys/x", json={"value": 1})
        client.put("/v1/namespaces/default/keys/x", json={"value": 2})
        client.delete("/v1/namespaces/default/keys/x")
        # Get history
        response = client.get("/v1/namespaces/default/keys/x/history")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["namespace"], "default")
        self.assertEqual(data["key"], "x")
        self.assertEqual(len(data["history"]), 3)
        self.assertEqual(data["history"][0][1], 1)
        self.assertEqual(data["history"][1][1], 2)
        self.assertEqual(data["history"][2][1], None)

    def test_get_history_nonexistent_key(self):
        # Get history for a non-existent key
        response = client.get("/v1/namespaces/default/keys/nonexistent/history")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data["ok"], False)
        self.assertEqual(data["error"]["code"], "key_not_found")
        self.assertEqual(data["error"]["recoverable"], True)

    def test_get_size(self):
        # Set some keys
        client.put("/v1/namespaces/default/keys/x", json={"value": 1})
        client.put("/v1/namespaces/default/keys/y", json={"value": 2})
        # Get size
        response = client.get("/v1/namespaces/default/size")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["namespace"], "default")
        self.assertEqual(data["size"], 2)

    def test_get_size_empty(self):
        # Get size of an empty namespace
        response = client.get("/v1/namespaces/default/size")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ok"], True)
        self.assertEqual(data["namespace"], "default")
        self.assertEqual(data["size"], 0)

    