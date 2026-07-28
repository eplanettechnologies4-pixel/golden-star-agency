from sqlalchemy import text
from sqlalchemy.orm import Session
from ai_chatbot.embeddings import EmbeddingsService
from typing import List, Dict, Any

class VectorRetriever:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.embeddings_service = EmbeddingsService()

    def retrieve_similar_packages(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves matching travel packages from pgvector database based on user query similarity.
        """
        query_vector = self.embeddings_service.get_embedding(query)
        
        # SQL query using pgvector `<->` cosine distance operator
        sql = text("""
            SELECT id, title, description, price, category,
            (embedding <-> :vector) AS distance
            FROM packages_package
            ORDER BY distance ASC
            LIMIT :limit;
        """)
        
        try:
            # Format query_vector as a string vector for pgvector '[val1,val2,...]'
            vector_str = "[" + ",".join(map(str, query_vector)) + "]"
            results = self.db.execute(sql, {"vector": vector_str, "limit": limit}).fetchall()
            
            return [
                {
                    "id": row.id,
                    "title": row.title,
                    "description": row.description,
                    "price": row.price,
                    "category": row.category,
                    "score": 1 - float(row.distance)
                }
                for row in results
            ]
        except Exception as e:
            # Fallback or error print (e.g. if database doesn't have pgvector loaded yet)
            print(f"Vector search failed: {e}. Falling back to Python similarity search.")
            try:
                # Query all packages from the database
                all_packages = self.db.execute(text("SELECT id, title, description, price, category, embedding FROM packages_package")).fetchall()
                
                import json
                import numpy as np
                matches = []
                for p in all_packages:
                    if p.embedding:
                        emb = p.embedding
                        if isinstance(emb, str):
                            emb = json.loads(emb)
                        
                        # Calculate cosine similarity: dot(A, B) / (norm(A) * norm(B))
                        v1 = np.array(query_vector)
                        v2 = np.array(emb)
                        dot_product = np.dot(v1, v2)
                        norm_v1 = np.linalg.norm(v1)
                        norm_v2 = np.linalg.norm(v2)
                        similarity = dot_product / (norm_v1 * norm_v2) if (norm_v1 > 0 and norm_v2 > 0) else 0.0
                        
                        matches.append({
                            "id": p.id,
                            "title": p.title,
                            "description": p.description,
                            "price": float(p.price) if p.price is not None else 0.0,
                            "category": p.category,
                            "score": float(similarity)
                        })
                
                # Sort by similarity score descending and return top matches
                matches.sort(key=lambda x: x["score"], reverse=True)
                return matches[:limit]
            except Exception as ex:
                print(f"Python fallback similarity search failed: {ex}")
                return []

