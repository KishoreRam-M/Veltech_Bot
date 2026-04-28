import lancedb
import os

db_path = "knowledge/lancedb_store"
if os.path.exists(db_path):
    db = lancedb.connect(db_path)
    print(f"Tables: {db.table_names()}")
else:
    print("DB path not found")
