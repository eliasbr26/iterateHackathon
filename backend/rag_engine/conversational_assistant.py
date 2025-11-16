"""
Conversational Assistant - PILLAR 7.3
RAG-powered Q&A engine for interviewer assistance
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import anthropic

from .vector_store import VectorStore
from .document_indexer import DocumentIndexer

logger = logging.getLogger(__name__)


class ConversationalAssistant:
    """
    RAG-powered conversational assistant for interviewers

    Features:
    - Answers questions using retrieved knowledge
    - Context-aware responses
    - Cites sources
    - Maintains conversation history
    """

    # Model configuration
    DEFAULT_MODEL = "claude-sonnet-4-5"
    MAX_TOKENS = 2000
    TEMPERATURE = 0.3  # Lower temperature for factual, consistent answers

    RAG_PROMPT = """You are an expert interview coach assistant helping an interviewer in real-time during a candidate interview.

CURRENT INTERVIEW CONTEXT:
- Position: {job_title}
- Candidate: {candidate_name}
- Interview Duration: {duration_minutes} minutes
- Questions Asked So Far: {questions_asked}
- Current Competencies Covered: {competencies_covered}
- Coverage Gaps: {coverage_gaps}

INTERVIEWER QUESTION:
{interviewer_question}

RELEVANT KNOWLEDGE (retrieved from past interviews and company knowledge):
{retrieved_context}

Provide a helpful, concise answer to the interviewer's question. Consider:
1. The current interview context and stage
2. Relevant information from past successful interviews
3. Best practices from the knowledge base
4. Specific guidance for this role and candidate

Respond in JSON format:
{{
    "answer": "Clear, actionable answer (2-3 sentences)",
    "suggestions": ["Specific action item 1", "Specific action item 2"],
    "sources": ["Source 1 reference", "Source 2 reference"],
    "related_questions": ["Optional follow-up question 1"],
    "confidence": 0.0-1.0
}}

Be specific, actionable, and cite your sources. Focus on what the interviewer should do RIGHT NOW."""

    def __init__(
        self,
        anthropic_api_key: str,
        openai_api_key: str,
        vector_store: VectorStore,
        model: str = DEFAULT_MODEL
    ):
        """
        Initialize conversational assistant

        Args:
            anthropic_api_key: Anthropic API key for Claude
            openai_api_key: OpenAI API key for embeddings
            vector_store: Vector store instance
            model: Claude model to use
        """
        self.claude_client = anthropic.Anthropic(api_key=anthropic_api_key)
        self.vector_store = vector_store
        self.document_indexer = DocumentIndexer(api_key=openai_api_key)
        self.model = model

        # Conversation history: interview_id -> list of messages
        self.conversation_history: Dict[int, List[Dict]] = {}

        logger.info(f"✅ ConversationalAssistant initialized with model: {model}")

    async def ask(
        self,
        question: str,
        interview_id: int,
        interview_context: Dict
    ) -> Dict:
        """
        Answer interviewer's question using RAG

        Args:
            question: Interviewer's question
            interview_id: Current interview ID
            interview_context: Current interview state (job_title, duration, coverage, etc.)

        Returns:
            Response with answer, suggestions, sources, confidence
        """
        try:
            logger.info(f"💬 Answering question for interview {interview_id}: {question[:50]}...")

            # 1. Create query embedding
            query_embedding = await self.document_indexer._create_embedding(question)

            # 2. Build metadata filters based on context
            filters = self._build_filters(interview_context)

            # 3. Retrieve relevant documents
            retrieved_docs = await self.vector_store.search(
                query_embedding=query_embedding,
                filters=filters,
                top_k=5
            )

            # 4. Format retrieved context
            context = self._format_retrieved_context(retrieved_docs)

            # 5. Build prompt
            prompt = self._build_prompt(
                question=question,
                interview_context=interview_context,
                retrieved_context=context
            )

            # 6. Get conversation messages
            messages = self._get_conversation_messages(interview_id, prompt)

            # 7. Call Claude
            response = self.claude_client.messages.create(
                model=self.model,
                max_tokens=self.MAX_TOKENS,
                temperature=self.TEMPERATURE,
                messages=messages
            )

            # 8. Parse response
            response_text = response.content[0].text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:].strip()
                if response_text.endswith("```"):
                    response_text = response_text[:-3].strip()

            result = json.loads(response_text)

            # 9. Add metadata
            result["retrieved_sources_count"] = len(retrieved_docs)
            result["timestamp"] = datetime.now().isoformat()

            # 10. Store in conversation history
            self._update_conversation_history(interview_id, question, result)

            logger.info(f"✅ Answer generated with confidence: {result.get('confidence', 0):.2f}")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text}")
            return self._fallback_response(question)

        except Exception as e:
            logger.error(f"❌ Failed to generate answer: {e}", exc_info=True)
            return self._fallback_response(question)

    def _build_filters(self, interview_context: Dict) -> Optional[Dict]:
        """
        Build metadata filters for retrieval

        Args:
            interview_context: Interview context data

        Returns:
            ChromaDB where clause or None
        """
        filters = {}

        # Filter by job title if available
        if interview_context.get("job_title"):
            filters["job_title"] = interview_context["job_title"]

        # Return None if no filters
        return filters if filters else None

    def _format_retrieved_context(self, retrieved_docs: List[Dict]) -> str:
        """
        Format retrieved documents into context string

        Args:
            retrieved_docs: List of retrieved documents

        Returns:
            Formatted context string
        """
        if not retrieved_docs:
            return "No relevant knowledge found in the database."

        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            metadata = doc.get("metadata", {})
            content = doc.get("content", "")

            # Build source reference
            source = metadata.get("doc_type", "unknown")
            if metadata.get("interview_id"):
                source += f" (Interview #{metadata['interview_id']})"
            if metadata.get("overall_score"):
                source += f" [Score: {metadata['overall_score']}/100]"

            context_parts.append(
                f"[Source {i}: {source}]\n{content}\n"
            )

        return "\n---\n".join(context_parts)

    def _build_prompt(
        self,
        question: str,
        interview_context: Dict,
        retrieved_context: str
    ) -> str:
        """
        Build prompt for Claude

        Args:
            question: Interviewer's question
            interview_context: Current interview context
            retrieved_context: Retrieved knowledge context

        Returns:
            Formatted prompt
        """
        return self.RAG_PROMPT.format(
            job_title=interview_context.get("job_title", "Unknown"),
            candidate_name=interview_context.get("candidate_name", "the candidate"),
            duration_minutes=interview_context.get("duration_minutes", 0),
            questions_asked=interview_context.get("questions_asked", 0),
            competencies_covered=", ".join(interview_context.get("competencies_covered", [])) or "None yet",
            coverage_gaps=", ".join(interview_context.get("coverage_gaps", [])) or "None identified",
            interviewer_question=question,
            retrieved_context=retrieved_context
        )

    def _get_conversation_messages(self, interview_id: int, prompt: str) -> List[Dict]:
        """
        Get conversation messages for Claude API

        Args:
            interview_id: Interview ID
            prompt: Current prompt

        Returns:
            List of messages for Claude
        """
        # Initialize conversation history if needed
        if interview_id not in self.conversation_history:
            self.conversation_history[interview_id] = []

        # Get recent history (last 5 exchanges)
        history = self.conversation_history[interview_id][-5:]

        # Build messages
        messages = []

        # Add history
        for entry in history:
            messages.append({
                "role": "user",
                "content": entry["question"]
            })
            messages.append({
                "role": "assistant",
                "content": json.dumps(entry["response"])
            })

        # Add current prompt
        messages.append({
            "role": "user",
            "content": prompt
        })

        return messages

    def _update_conversation_history(
        self,
        interview_id: int,
        question: str,
        response: Dict
    ):
        """
        Update conversation history

        Args:
            interview_id: Interview ID
            question: Question asked
            response: Response given
        """
        if interview_id not in self.conversation_history:
            self.conversation_history[interview_id] = []

        self.conversation_history[interview_id].append({
            "question": question,
            "response": response,
            "timestamp": datetime.now().isoformat()
        })

        # Keep only last 10 exchanges
        if len(self.conversation_history[interview_id]) > 10:
            self.conversation_history[interview_id] = self.conversation_history[interview_id][-10:]

    def _fallback_response(self, question: str) -> Dict:
        """
        Generate fallback response when AI fails

        Args:
            question: Original question

        Returns:
            Basic fallback response
        """
        logger.warning("⚠️ Using fallback response")

        return {
            "answer": "I encountered an issue generating a response. Please try rephrasing your question or consult the interview guidelines.",
            "suggestions": [
                "Review the competency evaluation criteria for this role",
                "Check the interview coverage to identify gaps"
            ],
            "sources": [],
            "related_questions": [],
            "confidence": 0.0,
            "fallback": True
        }

    def get_conversation_history(self, interview_id: int) -> List[Dict]:
        """
        Get conversation history for an interview

        Args:
            interview_id: Interview ID

        Returns:
            List of conversation entries
        """
        return self.conversation_history.get(interview_id, [])

    def clear_conversation_history(self, interview_id: int):
        """
        Clear conversation history for an interview

        Args:
            interview_id: Interview ID
        """
        if interview_id in self.conversation_history:
            del self.conversation_history[interview_id]
            logger.info(f"🗑️ Cleared conversation history for interview {interview_id}")
