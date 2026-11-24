# Data123
Internal read-only MES dashboard prototype. Run on an authorized Windows PC on the plant network. Install Python 3.11+ and run `run.bat`, or install requirements and run `python -m streamlit run app.py --server.address 127.0.0.1`.

Enter database credentials locally, select the table and production date. Use a database role restricted to SELECT. TLS require is the default; verify-full is preferred with a trusted certificate. Confirm IT policy before relaxing TLS. No credentials or data are committed.

First event per unique module within the selected production day is counted for each stage. Lamination uses entry time, not completion. EL rejection codes must be selected after confirming MES definitions. Timestamp columns must be native PostgreSQL timestamps; confirm plant timezone and timestamp semantics. Production day is 06:00 to 06:00. Queries have a 20-second timeout and a 100,000-row display limit. Prototype is not validated against live MES; do not use for official reporting until reconciled. Module explorer covers selected day only. Local-only binding by default; authentication required before shared deployment.
