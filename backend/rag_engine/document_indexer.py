"""
Document Indexer - PILLAR 7.1
Indexes documents and creates embeddings for RAG
"""

import logging
import hashlib
import uuid
from typing import Dict, List, Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class DocumentIndexer:
    """
    Indexes documents and creates embeddings

    Uses OpenAI embeddings API for vector generation
    Handles document chunking and metadata
    """

    # Embedding configuration
    DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"  # 1536 dimensions, cheap, fast
    CHUNK_SIZE = 500  # words per chunk
    CHUNK_OVERLAP = 50  # words overlap between chunks

    def __init__(self, api_key: str, embedding_model: str = DEFAULT_EMBEDDING_MODEL):
        """
        Initialize document indexer

        Args:
            api_key: OpenAI API key
            embedding_model: Embedding model to use
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.embedding_model = embedding_model
        self.indexed_documents = []

        logger.info(f"✅ DocumentIndexer initialized with model: {embedding_model}")

    async def index_document(
        self,
        doc_type: str,
        content: str,
        metadata: Dict,
        chunk: bool = True
    ) -> List[Dict]:
        """
        Index a single document

        Args:
            doc_type: Type of document ("interview", "company_doc", "question", "best_practice")
            content: Document text content
            metadata: Document metadata
            chunk: Whether to chunk long documents

        Returns:
            List of indexed document chunks with IDs
        """
        try:
            logger.info(f"📄 Indexing {doc_type} document")

            # Chunk document if needed
            if chunk and len(content.split()) > self.CHUNK_SIZE:
                chunks = self._chunk_text(content)
            else:
                chunks = [content]

            # Create embeddings for all chunks
            indexed_chunks = []
            for i, chunk_text in enumerate(chunks):
                # Generate unique ID
                doc_id = self._generate_doc_id(content, metadata, i)

                # Create embedding
                embedding = await self._create_embedding(chunk_text)

                # Combine metadata with chunk info
                chunk_metadata = {
                    **metadata,
                    "doc_type": doc_type,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "indexed_at": str(uuid.uuid4())  # Timestamp placeholder
                }

                indexed_chunks.append({
                    "id": doc_id,
                    "content": chunk_text,
                    "embedding": embedding,
                    "metadata": chunk_metadata
                })

            logger.info(f"✅ Indexed document into {len(indexed_chunks)} chunks")
            return indexed_chunks

        except Exception as e:
            logger.error(f"❌ Failed to index document: {e}")
            raise

    async def index_interview_transcript(
        self,
        interview_id: int,
        transcripts: List[Dict],
        interview_metadata: Dict
    ) -> List[Dict]:
        """
        Index interview transcript with Q&A structure

        Args:
            interview_id: Interview ID
            transcripts: List of transcript entries
            interview_metadata: Interview metadata (job_title, scores, etc.)

        Returns:
            List of indexed Q&A pairs
        """
        try:
            logger.info(f"📝 Indexing interview {interview_id} transcript")

            # Extract Q&A pairs
            qa_pairs = self._extract_qa_pairs(transcripts)

            # Index each Q&A pair
            indexed_pairs = []
            for i, qa in enumerate(qa_pairs):
                content = f"Q: {qa['question']}\nA: {qa['answer']}"

                metadata = {
                    **interview_metadata,
                    "interview_id": interview_id,
                    "question": qa['question'],
                    "qa_pair_index": i
                }

                chunks = await self.index_document(
                    doc_type="interview",
                    content=content,
                    metadata=metadata,
                    chunk=False  # Keep Q&A pairs together
                )

                indexed_pairs.extend(chunks)

            logger.info(f"✅ Indexed {len(indexed_pairs)} Q&A pairs from interview {interview_id}")
            return indexed_pairs

        except Exception as e:
            logger.error(f"❌ Failed to index interview transcript: {e}")
            raise

    async def index_question_bank_entry(
        self,
        question_text: str,
        question_metadata: Dict
    ) -> List[Dict]:
        """
        Index question bank entry

        Args:
            question_text: Question text
            question_metadata: Question metadata (competency, difficulty, success rate, etc.)

        Returns:
            List of indexed documents
        """
        try:
            # Create enriched content
            content = f"Question: {question_text}\n"

            if question_metadata.get("competency"):
                content += f"Competency: {question_metadata['competency']}\n"

            if question_metadata.get("difficulty"):
                content += f"Difficulty: {question_metadata['difficulty']}\n"

            if question_metadata.get("success_rate"):
                content += f"Success Rate: {question_metadata['success_rate']}%\n"

            return await self.index_document(
                doc_type="question",
                content=content,
                metadata=question_metadata,
                chunk=False
            )

        except Exception as e:
            logger.error(f"❌ Failed to index question: {e}")
            raise

    async def _create_embedding(self, text: str) -> List[float]:
        """
        Create embedding vector for text

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )

            return response.data[0].embedding

        except Exception as e:
            logger.error(f"❌ Failed to create embedding: {e}")
            raise

    def _chunk_text(self, text: str) -> List[str]:
        """
        Chunk text into smaller pieces with overlap

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []

        for i in range(0, len(words), self.CHUNK_SIZE - self.CHUNK_OVERLAP):
            chunk = ' '.join(words[i:i + self.CHUNK_SIZE])
            chunks.append(chunk)

        return chunks

    def _extract_qa_pairs(self, transcripts: List[Dict]) -> List[Dict]:
        """
        Extract question-answer pairs from transcript

        Args:
            transcripts: List of transcript entries with speaker and text

        Returns:
            List of Q&A pairs
        """
        qa_pairs = []
        current_question = None

        for entry in transcripts:
            speaker = entry.get("speaker", "").lower()
            text = entry.get("text", "")

            if speaker == "interviewer":
                # This is a question
                current_question = text
            elif speaker == "candidate" and current_question:
                # This is an answer to the previous question
                qa_pairs.append({
                    "question": current_question,
                    "answer": text
                })
                current_question = None  # Reset

        return qa_pairs

    def _generate_doc_id(self, content: str, metadata: Dict, chunk_index: int) -> str:
        """
        Generate unique document ID

        Args:
            content: Document content
            metadata: Document metadata
            chunk_index: Index of chunk

        Returns:
            Unique document ID
        """
        # Create hash from content and metadata for uniqueness
        hash_input = f"{content}_{metadata.get('interview_id', '')}_{chunk_index}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()

        return f"doc_{hash_value[:16]}"

    async def batch_create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for multiple texts in batch

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )

            return [item.embedding for item in response.data]

        except Exception as e:
            logger.error(f"❌ Failed to create batch embeddings: {e}")
            raise
