import chromadb
import math

from config import CHROMA_BATCH_SIZE, CHROMA_DIR
from embedding_model import embedding_model


class ChromaVectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_DIR)
        self.collection = self.client.get_or_create_collection(
            name="rag_chunks",
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks):
        """Embed and upsert chunks in bounded batches."""
        for start in range(0, len(chunks), CHROMA_BATCH_SIZE):
            batch = chunks[start:start + CHROMA_BATCH_SIZE]
            texts = [chunk["text"] for chunk in batch]
            ids = [chunk["chroma_id"] for chunk in batch]
            metadatas = [chunk["metadata"] for chunk in batch]
            embeddings = embedding_model.embed_texts(texts)

            self.collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
            )

    def delete_document(self, document_id):
        self.collection.delete(where={"document_id": document_id})

    def get_embedding_details(self, chroma_ids, preview_size=12):
        """Return compact vector diagnostics keyed by Chroma ID."""
        if not chroma_ids:
            return {}

        results = self.collection.get(
            ids=chroma_ids,
            include=["embeddings", "metadatas"],
        )
        result_ids = results.get("ids") or []
        embeddings = results.get("embeddings")
        embeddings = [] if embeddings is None else embeddings
        details = {}

        for index, chroma_id in enumerate(result_ids):
            raw_embedding = embeddings[index] if index < len(embeddings) else []
            vector = (
                raw_embedding.tolist()
                if hasattr(raw_embedding, "tolist")
                else list(raw_embedding or [])
            )
            details[chroma_id] = {
                "embedding_dimension": len(vector),
                "embedding_norm": round(
                    math.sqrt(sum(float(value) ** 2 for value in vector)),
                    6,
                ) if vector else 0,
                "embedding_preview": [
                    round(float(value), 6)
                    for value in vector[:preview_size]
                ],
            }
        return details

    def semantic_search(self, query, top_k=5):
        query_embedding = embedding_model.embed_text(query)
        available = self.collection.count()
        if available == 0:
            return []

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, available),
            include=["documents", "metadatas", "distances"],
        )

        output = []
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for index, chroma_id in enumerate(ids):
            output.append({
                "chroma_id": chroma_id,
                "text": documents[index],
                "metadata": metadatas[index],
                "score": 1 - distances[index],
                "source_type": "semantic",
            })
        return output


chroma_store = ChromaVectorStore()
