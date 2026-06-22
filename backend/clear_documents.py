from database import init_db, get_connection
from chroma_store import chroma_store
from bm25_store import bm25_store

init_db()

# Clear ChromaDB vectors
ids = chroma_store.collection.get()["ids"]
for start in range(0, len(ids), 1000):
    chroma_store.collection.delete(ids=ids[start:start + 1000])

# Clear document-related SQLite data
connection = get_connection()
try:
    connection.execute("DELETE FROM retrieval_logs")
    connection.execute("DELETE FROM chunks")
    connection.execute("DELETE FROM documents")
    connection.execute(
        "DELETE FROM sqlite_sequence "
        "WHERE name IN ('documents', 'chunks', 'retrieval_logs')"
    )
    connection.commit()
finally:
    connection.close()

# Replace BM25 with an empty index
bm25_store.rebuild()

print("All indexed documents, chunks, vectors, and BM25 data deleted.")