"""
Legal Intelligence service (LexBot) — RAG-powered legal Q&A.

Provides:
    - ask_question() — natural language legal query → cited answer
    - search_sections() — keyword search over legal corpus
"""

import logging
from typing import Any

from app.services.llmService import LLMService
from app.services.ragService import RAGService

logger = logging.getLogger("crimegpt.legal")

_LEGAL_SYSTEM_PROMPT = """You are LexBot, an AI legal assistant for Indian Law Enforcement Agencies.
You specialize in the Bharatiya Nyaya Sanhita (BNS) 2023, IT Act 2000, POCSO Act, and related Indian criminal law.

Rules:
1. Always cite specific sections and sub-sections
2. Provide clear, actionable legal guidance
3. If unsure, say so — never fabricate legal references
4. Use simple language understandable by police officers
5. When multiple sections apply, list them in order of relevance
6. Include maximum imprisonment/fine details when available
"""


class LegalService:
    """Legal intelligence — RAG-powered Q&A over Indian criminal law."""

    def __init__(self):
        self._llm = LLMService()
        self._rag = RAGService()

    async def ask_question(
        self,
        question: str,
        *,
        language: str = "en",
    ) -> dict[str, Any]:
        """
        Answer a legal question using RAG + LLM.

        Flow: embed question → retrieve relevant chunks → LLM generates cited answer
        """
        logger.info(f"Legal query: {question[:100]}...")

        # 1. Retrieve relevant legal chunks via RAG
        chunks = await self._rag.query(question, n_results=5)

        # 2. Build context from retrieved chunks
        context_parts = []
        sources = []
        for i, chunk in enumerate(chunks):
            context_parts.append(f"[Source {i+1}] {chunk['text']}")
            sources.append({
                "text": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                "source": chunk.get("metadata", {}).get("source", "unknown"),
                "act": chunk.get("metadata", {}).get("act", "unknown"),
                "similarity": chunk.get("similarity", 0),
            })

        context = "\n\n".join(context_parts) if context_parts else "No relevant legal documents found in corpus."

        # 3. Generate answer with LLM
        user_prompt = (
            f"Legal Question: {question}\n\n"
            f"Relevant Legal Context:\n{context}\n\n"
            f"Instructions: Answer the question using the provided legal context. "
            f"Cite specific sections. If the context doesn't cover the question, "
            f"provide general guidance and note the limitation."
        )

        answer = await self._llm.generate(
            system_prompt=_LEGAL_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.2,
            max_tokens=1500,
        )

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "language": language,
            "chunks_retrieved": len(chunks),
        }

    async def search_sections(
        self,
        keyword: str,
        *,
        act: str | None = None,
        n_results: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search legal sections by keyword.

        Optionally filter by act name (e.g., 'BNS 2023', 'IT Act').
        """
        where = {"act": act} if act else None
        chunks = await self._rag.query(keyword, n_results=n_results, where=where)

        return [
            {
                "text": c["text"],
                "source": c.get("metadata", {}).get("source", "unknown"),
                "act": c.get("metadata", {}).get("act", "unknown"),
                "relevance": c.get("similarity", 0),
            }
            for c in chunks
        ]

    async def recommend_sections(
        self,
        incident_description: str,
    ) -> list[dict[str, Any]]:
        """
        Recommend applicable BNS/IPC sections for an incident description.

        Used by FIR service during draft generation.
        """
        prompt = (
            f"Incident: {incident_description}\n\n"
            f"List the most applicable BNS 2023 / IPC sections for this incident. "
            f"For each section, provide: section number, title, and why it applies. "
            f"Respond in JSON format: [{{'section': '...', 'title': '...', 'reason': '...'}}]"
        )

        response = await self._llm.generate(
            system_prompt=_LEGAL_SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0.1,
            max_tokens=1000,
            json_mode=True,
        )

        # Parse JSON response (with fallback)
        try:
            import json
            sections = json.loads(response)
            if isinstance(sections, dict) and "sections" in sections:
                sections = sections["sections"]
            return sections if isinstance(sections, list) else []
        except (json.JSONDecodeError, TypeError):
            logger.warning("Failed to parse LLM section recommendations as JSON")
            return [{"section": "Unable to parse", "raw_response": response[:500]}]
