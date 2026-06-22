from sentence_transformers import SentenceTransformer

from config import EMBEDDING_BATCH_SIZE, EMBEDDING_MODEL


class EmbeddingModel:
    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)

    def embed_text(self, text):
        embedding = self.model.encode(
            text,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return embedding.tolist()

    def embed_texts(self, texts):
        if not texts:
            return []
        embeddings = self.model.encode(
            texts,
            batch_size=EMBEDDING_BATCH_SIZE,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return embeddings.tolist()


embedding_model = EmbeddingModel()

