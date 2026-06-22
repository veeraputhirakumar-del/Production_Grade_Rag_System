import os
import pickle
import re

from rank_bm25 import BM25Okapi

from config import BM25_DIR
from database import get_all_chunks


class BM25Store:
    def __init__(self):
        os.makedirs(BM25_DIR, exist_ok=True)
        self.index_path = os.path.join(BM25_DIR, "bm25_index.pkl")
        self.chunks_path = os.path.join(BM25_DIR, "bm25_chunks.pkl")
        self.bm25 = None
        self.chunks = []
        self.load()

    @staticmethod
    def tokenize(text):
        # "Centre?" and "Centre" must be the same search token.
        return re.findall(r"[a-z0-9]+", str(text).lower())

    def rebuild(self):
        self.chunks = get_all_chunks()
        tokenized_corpus = [
            self.tokenize(chunk["chunk_text"])
            for chunk in self.chunks
        ]
        self.bm25 = BM25Okapi(tokenized_corpus) if tokenized_corpus else None
        self.save()

    def save(self):
        with open(self.index_path, "wb") as file:
            pickle.dump(self.bm25, file)
        with open(self.chunks_path, "wb") as file:
            pickle.dump(self.chunks, file)

    def load(self):
        if os.path.exists(self.index_path) and os.path.exists(self.chunks_path):
            with open(self.index_path, "rb") as file:
                self.bm25 = pickle.load(file)
            with open(self.chunks_path, "rb") as file:
                self.chunks = pickle.load(file)

    def keyword_search(self, query, top_k=8):
        if self.bm25 is None or not self.chunks:
            return []

        scores = self.bm25.get_scores(self.tokenize(query))
        ranked_indexes = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True,
        )[:top_k]

        results = []
        for index in ranked_indexes:
            score = float(scores[index])
            if score <= 0:
                continue
            chunk = self.chunks[index]
            results.append({
                "chroma_id": chunk["chroma_id"],
                "text": chunk["chunk_text"],
                "metadata": {
                    "document_id": chunk["document_id"],
                    "chunk_id": chunk["id"],
                    "filename": chunk["filename"],
                    "page_number": chunk["page_number"],
                    "chunk_index": chunk["chunk_index"],
                },
                "score": score,
                "source_type": "bm25",
            })
        return results


bm25_store = BM25Store()
