import os
import lancedb
import numpy as np
from server.config import TOP_K_RETRIEVAL, KNOWLEDGE_DIR

class VectorStore:
    def __init__(self):
        self._db_path = os.path.join(KNOWLEDGE_DIR, "lancedb_store")
        self._db = None
        self._domains = []

    def init_db(self):
        if not self._db:
            if os.path.exists(self._db_path):
                self._db = lancedb.connect(self._db_path)
                tables = self._db.list_tables()
                self._domains = tables.tables if hasattr(tables, "tables") else tables
            else:
                print(f"[LanceDB] Warning: DB path {self._db_path} does not exist. Run indexer.py.")

    def get_chunks_for_domain(self, domain: str) -> list[dict]:
        self.init_db()
        if not self._db or domain not in self._domains:
            return []
        
        table = self._db.open_table(domain)
        # return all rows as dicts
        df = table.to_arrow().to_pylist()
        for row in df:
            row.pop("vector", None)
        return df

    def search(self, domain: str, query_embedding: np.ndarray, top_k: int = TOP_K_RETRIEVAL) -> list[tuple[dict, float]]:
        self.init_db()
        if not self._db or domain not in self._domains:
            return []
        
        table = self._db.open_table(domain)
        # Search returns a PyArrow table, convert to pylist
        results = table.search(query_embedding.tolist()).metric("cosine").limit(top_k).to_arrow().to_pylist()
        
        out = []
        for row_dict in results:
            # LanceDB returns _distance (cosine distance)
            # cosine similarity = 1 - cosine distance
            distance = row_dict.get("_distance", 1.0)
            score = 1.0 - distance
            
            # Remove internal columns
            row_dict.pop("vector", None)
            row_dict.pop("_distance", None)
            out.append((row_dict, score))
            
        return out

    def has_domain(self, domain: str) -> bool:
        self.init_db()
        return domain in self._domains

    @property
    def domains(self) -> list[str]:
        self.init_db()
        return self._domains

vector_store = VectorStore()
