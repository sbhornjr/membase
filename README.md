# membase

## SERVER USAGE:

membase is an in-memory key-value database server

The project started as an opportunity to learn and practice basic concepts such as data storage, persistence 
and transactions. It turned into a way to learn how to set up an HTTP server and create API endpoints for 
CRUD and more complex operations such as transactions. It then evolved into a way to explore what changes 
when software is built for agents instead of only humans: explicit schemas, recoverable errors, tool-oriented 
documentation, MCP integration, and evals that grade final state after tool use.

It includes:
- Namespaces
- CRUD operations
- Nested transactions
- Write-ahead log persistence
- Snapshots
- Key history
- HTTP API
- MCP server
- Agent-oriented docs
- Eval suite

The FastAPI server creates one database object and persistence manager at startup. These objects
handle database storage, all CRUD and extra operations, snapshots and WAL operations and startup/teardown.

Membase supports a namespace system to emulate different databases. Each namespace is equipped with its
own database, history and transaction manager.

On startup, membase restores state from the latest snapshot and replays the
write-ahead log. During operation, successful modifying commands are appended to
the WAL. Snapshots can be triggered manually through the API or automatically on
shutdown.

The project includes an HTTP server, an MCP server layer built around the HTTP server for agent
tool use, agent-oriented documentation and an eval suite for measuring agent reliability. The evals
utilize Anthropic. The MCP server is a thin agent-facing adapter over the HTTP API. It exposes 
operations such as `set_key`, `get_key`, `begin_transaction`, and `commit_transaction` as tools 
that MCP-compatible clients can discover and call. The HTTP server remains the source of truth for database state.

## AGENT-FACING FEATURES:

membase includes several interfaces designed for AI agent use:

- Structured HTTP API with predictable JSON responses
- OpenAPI schema for machine-readable API discovery
- MCP server exposing database operations as model-callable tools
- Agent-oriented tool documentation
- Eval suite using Anthropic to test whether agents can complete database workflows

## QUICKSTART:

Start the HTTP server: uvicorn membase.api.server:app --reload

Start the MCP server: python -m mcp.server

Run Evals: python evals/run_evals.py

Run Unit Tests: bash test.sh

Start in Terminal Mode: python main.py

## EVALS

The eval suite tests whether an agent can use membase tools correctly across common workflows:

- Basic CRUD
- Namespace Isolation
- Transaction Commit
- Transaction Rollback
- Nested Transactions
- Destructive Operation Avoidance
- Error Recovery

Each eval records tool calls, recoverable errors, final database state, and pass/fail results.

## AVAILABLE APIs:

All API documentation is available via OpenAPI at `/openapi.json` or through Swagger UI at `/docs`, or in this project at `membase/docs/api_reference.md`.

## CLI USAGE:

membase is an in-memory key-value store

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