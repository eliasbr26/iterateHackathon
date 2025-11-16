# PILLAR 7: LLM + RAG Conversational Q&A Engine
## Implementation Plan

**Status**: In Development
**Priority**: High
**Integration**: Real-time interviewer assistance with knowledge retrieval

---

## Overview

Provides a conversational AI assistant for interviewers with RAG (Retrieval-Augmented Generation) capabilities. Allows interviewers to ask questions during interviews and get intelligent answers based on company knowledge, past interviews, and best practices.

## Architecture

```
rag_engine/
├── __init__.py                      # Module exports
├── document_indexer.py              # Indexes knowledge sources
├── vector_store.py                  # Vector storage and retrieval
├── conversational_assistant.py      # Main Q&A engine
└── knowledge_sources.py             # Manages different knowledge types
```

---

## Module 1: Document Indexer

**Purpose**: Index various knowledge sources for RAG retrieval

**Key Features**:
- Index company documents (hiring guides, role requirements, etc.)
- Index past interview transcripts and evaluations
- Index question bank with performance data
- Automatic re-indexing on updates

**Data Sources**:
- Company knowledge base (PDFs, markdown files)
- Historical interview transcripts
- Competency evaluation results
- Question bank with effectiveness metrics
- Best practices documentation

**Implementation**:
```python
class DocumentIndexer:
    """
    Indexes documents and creates embeddings for RAG

    Uses Claude embeddings API or similar
    Supports multiple document types
    """

    def __init__(self, embedding_model: str = "text-embedding-3-small"):
        self.embedding_model = embedding_model
        self.documents = []

    async def index_document(
        self,
        doc_type: str,  # "company_doc", "interview", "question", "best_practice"
        content: str,
        metadata: Dict
    ) -> str:
        """Index a single document"""
        # Create embeddings
        # Store in vector database
        # Return document ID

    async def index_past_interviews(
        self,
        interview_ids: List[int],
        db: Session
    ):
        """Index historical interviews for learning"""
        # Get transcripts and evaluations
        # Create searchable chunks
        # Index with metadata (competency scores, outcomes)

    async def index_question_bank(self, db: Session):
        """Index question bank with effectiveness data"""
        # Get all questions
        # Include usage stats and success rates
        # Make searchable by competency/topic
```

**Document Structure**:
```python
{
    "doc_id": "uuid",
    "doc_type": "interview" | "company_doc" | "question" | "best_practice",
    "content": "chunked text content",
    "embedding": [0.1, 0.2, ...],  # Vector
    "metadata": {
        "interview_id": 123,
        "competency": "leadership",
        "success_score": 85,
        "timestamp": "2024-01-15T10:00:00Z",
        # ... other relevant metadata
    }
}
```

---

## Module 2: Vector Store

**Purpose**: Store and retrieve document embeddings efficiently

**Key Features**:
- Fast similarity search
- Metadata filtering
- Hybrid search (semantic + keyword)
- Relevance scoring

**Implementation Options**:
1. **In-Memory** (for MVP): Use numpy/faiss for quick prototyping
2. **Pinecone** (production): Managed vector database
3. **ChromaDB** (self-hosted): Open-source vector database
4. **pgvector** (PostgreSQL): Use existing database with vector extension

**For MVP, we'll use ChromaDB** (simple, Python-native, self-hosted):

```python
class VectorStore:
    """
    Vector storage and retrieval using ChromaDB
    """

    def __init__(self, persist_directory: str = "./chroma_db"):
        import chromadb
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="interview_knowledge",
            metadata={"hnsw:space": "cosine"}
        )

    async def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadata: List[Dict],
        ids: List[str]
    ):
        """Add documents to vector store"""
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadata,
            ids=ids
        )

    async def search(
        self,
        query_embedding: List[float],
        filters: Optional[Dict] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """Search for similar documents"""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filters  # Metadata filtering
        )

        return [
            {
                "content": doc,
                "metadata": meta,
                "distance": dist
            }
            for doc, meta, dist in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )
        ]
```

---

## Module 3: Conversational Assistant

**Purpose**: Main Q&A engine that answers interviewer questions using RAG

**Key Features**:
- Context-aware responses
- Cites sources from retrieved documents
- Maintains conversation history
- Adapts to interview stage and context

**Claude Prompt Template**:
```python
RAG_PROMPT = """You are an expert interview coach assistant helping an interviewer in real-time.

CURRENT INTERVIEW CONTEXT:
- Position: {job_title}
- Candidate: {candidate_name}
- Interview Duration: {duration_minutes} minutes
- Questions Asked So Far: {questions_asked}
- Current Competencies Covered: {competencies_covered}
- Coverage Gaps: {coverage_gaps}

INTERVIEWER QUESTION:
{interviewer_question}

RELEVANT KNOWLEDGE (retrieved from company docs and past interviews):
{retrieved_context}

Provide a helpful, concise answer to the interviewer's question. Consider:
1. The current interview context and stage
2. Relevant information from past successful interviews
3. Best practices from company knowledge base
4. Specific guidance for this role and candidate

Format your response as:
{{
    "answer": "Clear, actionable answer (2-3 sentences)",
    "suggestions": ["Specific action item 1", "Specific action item 2"],
    "sources": ["Source 1 reference", "Source 2 reference"],
    "related_questions": ["Optional follow-up question 1", "Optional follow-up question 2"]
}}

Be specific and immediately actionable. Cite your sources.
"""
```

**Implementation**:
```python
class ConversationalAssistant:
    """
    RAG-powered conversational assistant for interviewers
    """

    def __init__(
        self,
        api_key: str,
        vector_store: VectorStore,
        model: str = "claude-sonnet-4-5"
    ):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.vector_store = vector_store
        self.model = model
        self.conversation_history: Dict[int, List[Dict]] = {}  # interview_id -> messages

    async def ask(
        self,
        question: str,
        interview_id: int,
        interview_context: Dict,
        db: Session
    ) -> Dict:
        """
        Answer interviewer's question using RAG

        Args:
            question: Interviewer's question
            interview_id: Current interview ID
            interview_context: Current interview state
            db: Database session

        Returns:
            Response with answer, suggestions, sources
        """
        # 1. Create query embedding
        query_embedding = await self._embed_query(question)

        # 2. Retrieve relevant documents
        filters = self._build_filters(interview_context)
        retrieved_docs = await self.vector_store.search(
            query_embedding=query_embedding,
            filters=filters,
            top_k=5
        )

        # 3. Build context from retrieved docs
        context = self._format_retrieved_context(retrieved_docs)

        # 4. Build prompt with interview context
        prompt = self._build_prompt(
            question=question,
            interview_context=interview_context,
            retrieved_context=context
        )

        # 5. Call Claude
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=self._get_conversation_messages(interview_id, prompt)
        )

        # 6. Parse response
        result = json.loads(response.content[0].text)

        # 7. Store in conversation history
        self._update_conversation_history(interview_id, question, result)

        return result

    async def _embed_query(self, query: str) -> List[float]:
        """Create embedding for query"""
        # Use Claude embeddings or OpenAI embeddings API
        # For now, placeholder
        return [0.0] * 1536

    def _build_filters(self, interview_context: Dict) -> Dict:
        """Build metadata filters for retrieval"""
        filters = {}

        # Filter by job role if available
        if interview_context.get("job_title"):
            filters["job_title"] = interview_context["job_title"]

        # Filter by relevant competencies
        if interview_context.get("target_competencies"):
            filters["competency"] = {"$in": interview_context["target_competencies"]}

        return filters
```

---

## Module 4: Knowledge Sources

**Purpose**: Manage different types of knowledge and their indexing

**Knowledge Types**:

### 1. Company Knowledge Base
- Hiring guides
- Role requirements
- Interview best practices
- Company values documentation

### 2. Historical Interviews
- Past successful interviews (high scores)
- Past unsuccessful interviews (learn what to avoid)
- Competency-specific examples
- STAR method examples

### 3. Question Bank Analytics
- Most effective questions by competency
- Questions that led to good insights
- Questions with high STAR completion rates

### 4. Best Practices Database
- Interview techniques
- Follow-up question strategies
- Bias avoidance tips
- Cultural fit assessment guidance

**Implementation**:
```python
class KnowledgeSourceManager:
    """
    Manages different knowledge sources and their indexing
    """

    def __init__(
        self,
        indexer: DocumentIndexer,
        db: Session
    ):
        self.indexer = indexer
        self.db = db

    async def index_all_sources(self):
        """Index all available knowledge sources"""
        await self.index_company_docs()
        await self.index_historical_interviews()
        await self.index_question_analytics()
        await self.index_best_practices()

    async def index_historical_interviews(self, min_score: float = 75.0):
        """Index successful past interviews"""
        # Get high-scoring interviews
        interviews = self.db.query(Interview).join(InterviewSummary).filter(
            InterviewSummary.overall_score >= min_score
        ).all()

        for interview in interviews:
            # Get transcript
            transcripts = get_interview_transcripts(self.db, interview.id)

            # Get competency scores
            competency_scores = get_interview_competency_scores(self.db, interview.id)

            # Create document
            doc_content = self._format_interview_for_indexing(
                interview, transcripts, competency_scores
            )

            # Index
            await self.indexer.index_document(
                doc_type="interview",
                content=doc_content,
                metadata={
                    "interview_id": interview.id,
                    "job_title": interview.job_title,
                    "overall_score": interview.summaries[0].overall_score,
                    "competencies": [s.competency.value for s in competency_scores]
                }
            )
```

---

## Database Schema Updates

No new tables needed! We'll use existing data for RAG:
- `interviews` + `transcripts` → Historical interview knowledge
- `question_bank` + `interview_questions` → Question effectiveness data
- `competency_scores` + `star_analyses` → Success patterns

**ChromaDB** will handle vector storage externally.

---

## API Endpoints

### 1. Ask Question (Real-Time Assistance)
```
POST /interviews/{interview_id}/ask

Request:
{
    "question": "How should I probe deeper on their leadership example?",
    "context": {
        "current_topic": "leadership",
        "question_just_asked": "Tell me about a time you led a team..."
    }
}

Response:
{
    "answer": "Based on successful past interviews, probe for specific metrics and team size. Ask about challenges faced and how they overcame resistance.",
    "suggestions": [
        "Ask: 'What was the team size and composition?'",
        "Ask: 'What specific metrics improved after your intervention?'",
        "Look for quantified results in their answer"
    ],
    "sources": [
        "Interview #45 (Leadership score: 92/100)",
        "Best Practice: STAR Method Deep-Dive Guide"
    ],
    "related_questions": [
        "How did you handle disagreements within the team?",
        "What would you do differently next time?"
    ],
    "confidence": 0.89
}
```

### 2. Get Conversation History
```
GET /interviews/{interview_id}/assistant-history

Response:
{
    "interview_id": 123,
    "conversation_count": 5,
    "messages": [
        {
            "timestamp": "2024-01-15T10:15:00Z",
            "question": "What should I ask about technical depth?",
            "answer": "..."
        }
    ]
}
```

### 3. Index Knowledge Source
```
POST /knowledge/index

Request:
{
    "source_type": "company_doc",  # or "interview", "question", "best_practice"
    "content": "...",
    "metadata": {...}
}

Response:
{
    "status": "indexed",
    "doc_id": "uuid",
    "chunks_created": 3
}
```

### 4. Search Knowledge Base
```
POST /knowledge/search

Request:
{
    "query": "effective leadership questions",
    "filters": {
        "competency": "leadership",
        "min_success_score": 80
    },
    "top_k": 10
}

Response:
{
    "results": [
        {
            "content": "Question: 'Describe a situation where...'",
            "metadata": {
                "success_score": 92,
                "interview_id": 45
            },
            "relevance_score": 0.87
        }
    ]
}
```

### 5. Get Interview Suggestions (Proactive)
```
GET /interviews/{interview_id}/suggestions

Response:
{
    "coverage_suggestions": [
        "You haven't covered 'Problem Solving' yet - consider asking about debugging or optimization"
    ],
    "pacing_suggestions": [
        "You're 15 minutes in with only 2 questions - consider picking up the pace"
    ],
    "quality_suggestions": [
        "Last 2 questions were yes/no - try open-ended behavioral questions"
    ]
}
```

---

## Implementation Order

1. ✅ Create implementation plan
2. Install ChromaDB dependency
3. Build VectorStore module
4. Build DocumentIndexer module
5. Build KnowledgeSourceManager module
6. Build ConversationalAssistant module
7. Create API endpoints
8. Index sample knowledge sources
9. Test real-time Q&A
10. Integration testing

---

## Technical Considerations

**Embeddings**:
- Use OpenAI `text-embedding-3-small` (1536 dimensions, cheap, fast)
- Alternative: Cohere embeddings or open-source models

**Vector Database**:
- **ChromaDB** for MVP (Python-native, easy setup)
- Can migrate to Pinecone/Weaviate for production scale

**Response Time**:
- Target: <2 seconds for Q&A response
- Embedding: ~100ms
- Vector search: ~50-200ms
- Claude generation: ~1-2 seconds

**Chunking Strategy**:
- Interview transcripts: Chunk by Q&A pairs (keep question + answer together)
- Documents: 500-word chunks with 50-word overlap
- Questions: Keep entire question + metadata as single chunk

**Privacy & Security**:
- Don't index sensitive personal information
- Option to exclude specific interviews from indexing
- Anonymize candidate names in indexed content

---

## Success Metrics

1. **Response Quality**
   - Target: 90%+ interviewer satisfaction with answers
   - Measure: Post-interview survey

2. **Response Time**
   - Target: <2 seconds average response time
   - Measure: Server-side timing

3. **Usage Rate**
   - Target: 3+ questions per interview
   - Measure: API call tracking

4. **Source Relevance**
   - Target: 80%+ of retrieved sources rated as relevant
   - Measure: Implicit feedback (did they use the suggestion?)

---

## Future Enhancements

1. **Multi-Modal RAG**: Include video interview clips as context
2. **Automatic Indexing**: Auto-index all completed interviews
3. **Personalized Learning**: Learn interviewer preferences over time
4. **Proactive Suggestions**: Push suggestions without being asked
5. **Voice Interface**: Voice-to-text for hands-free assistance
6. **Custom Knowledge Bases**: Per-company or per-role knowledge sources

---

## File Structure Summary

```
backend/
├── rag_engine/
│   ├── __init__.py
│   ├── document_indexer.py       (~300 lines)
│   ├── vector_store.py           (~200 lines)
│   ├── conversational_assistant.py (~400 lines)
│   └── knowledge_sources.py      (~250 lines)
└── server.py                      (add 4 new endpoints)
```

**Estimated Total**: ~1,200 lines of new code

**External Dependencies**:
- `chromadb` - Vector database
- `openai` - For embeddings (or use anthropic if they add embeddings API)
