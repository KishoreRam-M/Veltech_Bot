import lancedb
import os

db_path = "knowledge/lancedb_store"
db = lancedb.connect(db_path)
tables = db.list_tables()
print(f"Type: {type(tables)}")
print(f"Content: {tables}")
