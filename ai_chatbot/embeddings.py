from sentence_transformers import SentenceTransformer
from typing import List

class EmbeddingsService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # Load local lightweight sentence transformer model
        self.model = SentenceTransformer(model_name)

    def get_embedding(self, text: str) -> List[float]:
        """
        Generate vector embedding for a single text chunk.
        """
        embedding = self.model.encode(text)
        return embedding.tolist()

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate vector embeddings for a list of text chunks.
        """
        embeddings = self.model.encode(texts)
        return embeddings.tolist()
