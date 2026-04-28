import lancedb
import os

db_path = "knowledge/lancedb_store"
db = lancedb.connect(db_path)
all_tables = db.table_names()
print(f"All tables: {all_tables}")

test_tables = ["infrastructure", "labs", "placements", "sports", "industry", "transport", "rankings"]
for t in test_tables:
    if t in all_tables:
        print(f"Table '{t}' exists.")
    else:
        print(f"Table '{t}' MISSING from table_names().")
        # Try to open it anyway
        try:
            db.open_table(t)
            print(f"Opened table '{t}' successfully despite missing from table_names()!")
        except Exception as e:
            print(f"Failed to open table '{t}': {e}")
