# membase

membase is an in-memory key-value store

It includes functions such as:
- get x (gets the value currently set to x)
- set x 1 (sets x to 1)
- delete x (deletes x)
- begin/commit/rollback for transactions (including nested transactions)
- a persistence layer with both a write-ahead log and a snapshot system
- a namespace system to emulate different databases/tables
- count 1 (gets the number of keys with 1 as their value)
- find 1 (returns the list of keys with 1 as their value)
- history x (returns a list of the history of modifying operations on x with timestamps)
- keys (returns the list of keys)
- exists x (true if the x key exists, false otherwise)
- snapshot (automatically creates a snapshot and saves it onto disk)
- size (returns the number of keys)
- stats (shows basic stats for the current session such as number of deletes and number of commits)
- undo (reverses the last modifying operation)
- clear (clears the database for the current namespace)
- dump (returns the whole database for the current namespace as a dict)
- help (prints all the above operations)
- also includes a client-server architecture setup with POST/GET/DELETE operations for all of the above