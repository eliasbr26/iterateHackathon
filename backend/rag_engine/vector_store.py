"""
Vector Store - PILLAR 7.2
Vector storage and retrieval using ChromaDB
"""

import logging
from typing import Dict, List, Optional
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Vector storage and retrieval using ChromaDB

    Features:
    - Fast similarity search
    - Metadata filtering
    - Persistent storage
    - Cosine similarity scoring
    """

    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize vector store

        Args:
            persist_directory: Directory to persist vector database
        """
        try:
            # Initialize ChromaDB client with persistence
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="interview_knowledge",
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )

            logger.info(f"✅ VectorStore initialized with {self.collection.count()} documents")

        except Exception as e:
            logger.error(f"❌ Failed to initialize VectorStore: {e}")
            raise

    async def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadata: List[Dict],
        ids: List[str]
    ):
        """
        Add documents to vector store

        Args:
            documents: List of document texts
            embeddings: List of embedding vectors
            metadata: List of metadata dicts
            ids: List of unique document IDs
        """
        try:
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadata,
                ids=ids
            )

            logger.info(f"✅ Added {len(documents)} documents to vector store")

        except Exception as e:
            logger.error(f"❌ Failed to add documents: {e}")
            raise

    async def search(
        self,
        query_embedding: List[float],
        filters: Optional[Dict] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Search for similar documents

        Args:
            query_embedding: Query vector
            filters: Metadata filters (ChromaDB where clause)
            top_k: Number of results to return

        Returns:
            List of matching documents with metadata and scores
        """
        try:
            # Build query parameters
            query_params = {
                "query_embeddings": [query_embedding],
                "n_results": top_k
            }

            # Add filters if provided
            if filters:
                query_params["where"] = filters

            # Execute search
            results = self.collection.query(**query_params)

            # Format results
            formatted_results = []
            if results and results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        "content": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "distance": results['distances'][0][i] if results['distances'] else 0.0,
                        "id": results['ids'][0][i] if results['ids'] else None
                    })

            logger.info(f"🔍 Found {len(formatted_results)} results for query")
            return formatted_results

        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []

    async def delete_documents(self, ids: List[str]):
        """
        Delete documents by IDs

        Args:
            ids: List of document IDs to delete
        """
        try:
            self.collection.delete(ids=ids)
            logger.info(f"🗑️ Deleted {len(ids)} documents")

        except Exception as e:
            logger.error(f"❌ Failed to delete documents: {e}")
            raise

    async def update_document(
        self,
        doc_id: str,
        document: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Update a single document

        Args:
            doc_id: Document ID
            document: New document text (optional)
            embedding: New embedding (optional)
            metadata: New metadata (optional)
        """
        try:
            update_params = {"ids": [doc_id]}

            if document:
                update_params["documents"] = [document]
            if embedding:
                update_params["embeddings"] = [embedding]
            if metadata:
                update_params["metadatas"] = [metadata]

            self.collection.update(**update_params)
            logger.info(f"✅ Updated document: {doc_id}")

        except Exception as e:
            logger.error(f"❌ Failed to update document: {e}")
            raise

    def get_document_count(self) -> int:
        """Get total number of documents in store"""
        return self.collection.count()

    def reset(self):
        """Reset the vector store (delete all documents)"""
        try:
            self.client.reset()
            logger.warning("⚠️ Vector store reset - all documents deleted")
        except Exception as e:
            logger.error(f"❌ Failed to reset vector store: {e}")
            raise

    def get_collection_info(self) -> Dict:
        """Get information about the collection"""
        return {
            "name": self.collection.name,
            "count": self.collection.count(),
            "metadata": self.collection.metadata
        }
