# PostgreSQL

PostgreSQL is the source of truth for metadata and workflow state.
Only creates the database service and Alembic migration baseline.

Use `make migrate` to apply migrations through the API project.
