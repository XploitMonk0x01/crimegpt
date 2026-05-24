"""
Legal Intelligence service (LexBot) — RAG-powered legal Q&A.

Provides:
    - ask_question() — natural language legal query → cited answer
    - search_sections() — keyword search over legal corpus
    - recommend_sections() — RAG-grounded section recommendations for FIRs
"""

import json
import logging
import re
from typing import Any

from app.config import get_settings
from app.services.llmService import LLMService
from app.services.ragSafety import analyze_text, redact_pii, strip_prompt_injection
from app.services.ragService import RAGService
from app.services.ragCache import RAGCache

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
        self._settings = get_settings()
        self._llm = LLMService()
        self._rag = RAGService()

    async def ask_question(self, question: str, *, language: str = "en") -> dict[str, Any]:
        """Answer a legal question using RAG + LLM, with Redis answer cache."""
        logger.info("Legal query: %s...", question[:100])

        where = self._infer_act_filter(question)
        act_filter = (where or {}).get("act", "")

        # ── Layer 1: Full answer cache check ──
        cache = RAGCache()
        cached_answer = await cache.get_answer(question, act_filter, language)
        if cached_answer is not None:
            cached_answer["cached"] = True
            return cached_answer

        search_query = await self._expand_query(question)

        # Over-fetch with a low threshold — hybrid reranker in RAGService will
        # re-score and apply the final min_similarity cutoff (0.12) after BM25 fusion.
        chunks = await self._rag.query(
            search_query, n_results=8, where=where, min_similarity=0.12, rerank=True
        )

        context_parts = []
        sources = []
        safety_summary = {
            "prompt_injection": 0,
            "prompt_injection_stripped": 0,
            "pii_matches": {"email": 0, "phone": 0, "aadhaar": 0},
        }
        source_types: dict[str, int] = {}
        for i, chunk in enumerate(chunks):
            metadata = chunk.get("metadata", {})
            section = metadata.get("section", "unknown")

            raw_text = chunk["text"]
            signals = analyze_text(raw_text)
            safety_summary["prompt_injection"] += int(signals.prompt_injection)
            for key in safety_summary["pii_matches"]:
                safety_summary["pii_matches"][key] += signals.pii_matches.get(key, 0)

            sanitized_text = raw_text
            stripped_lines = 0
            if self._settings.rag.redact_pii:
                sanitized_text = redact_pii(sanitized_text)
            if self._settings.rag.strip_prompt_injection:
                sanitized_text, stripped_lines = strip_prompt_injection(sanitized_text)
                safety_summary["prompt_injection_stripped"] += stripped_lines

            context_parts.append(f"[Source {i + 1} | Section: {section}] {sanitized_text}")
            source_type = metadata.get("source_type", "corpus")
            source_types[source_type] = source_types.get(source_type, 0) + 1
            sources.append({
                "text": sanitized_text[:200] + "..." if len(sanitized_text) > 200 else sanitized_text,
                "source": metadata.get("source", "unknown"),
                "source_type": source_type,
                "act": metadata.get("act", "unknown"),
                "section": section,
                "similarity": chunk.get("similarity", 0),
            })

        context = "\n\n".join(context_parts) if context_parts else "No relevant legal documents found in corpus."
        user_prompt = (
            f"Legal Question: {question}\n\n"
            f"Relevant Legal Context:\n{context}\n\n"
            f"Instructions: Answer using the provided legal context first. "
            f"Cite source numbers and specific sections. If the context does not cover the question, "
            f"state the limitation clearly before providing general guidance. "
            f"Respond in language code: {language}."
        )

        answer = await self._llm.generate(
            system_prompt=_LEGAL_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.2,
            max_tokens=1500,
        )

        result = {
            "question": question,
            "answer": answer,
            "sources": sources,
            "language": language,
            "chunks_retrieved": len(chunks),
            "retrieval": {
                "query": search_query,
                "act_filter": where,
                "source_types": source_types,
            },
            "safety": safety_summary,
            "cached": False,
        }

        # ── Store in answer cache ──
        await cache.set_answer(question, act_filter, language, result)
        return result

    async def search_sections(
        self,
        keyword: str,
        *,
        act: str | None = None,
        n_results: int = 10,
    ) -> list[dict[str, Any]]:
        """Search legal sections by keyword, optionally filtered by act."""
        where = {"act": act} if act else None
        chunks = await self._rag.query(
            keyword, n_results=n_results, where=where, min_similarity=0.10, rerank=True
        )

        return [
            {
                "text": c["text"],
                "source": c.get("metadata", {}).get("source", "unknown"),
                "act": c.get("metadata", {}).get("act", "unknown"),
                "section": c.get("metadata", {}).get("section", "unknown"),
                "relevance": c.get("similarity", 0),
            }
            for c in chunks
        ]

    async def recommend_sections(self, incident_description: str) -> list[dict[str, Any]]:
        """
        Recommend applicable BNS/IPC sections for an incident description.

        The LLM is grounded with RAG candidates first. If Groq/Ollama cannot return
        valid JSON, deterministic RAG candidates are returned instead of a broken
        placeholder so FIR draft generation remains usable.
        """
        candidate_chunks = await self._rag.query(
            incident_description,
            n_results=8,
            where={"act": "bns_2023"},
            min_similarity=0.10,
            rerank=True,
        )
        context = "\n\n".join(
            f"[Candidate {i + 1} | Section: {chunk.get('metadata', {}).get('section', 'unknown')}] {chunk['text']}"
            for i, chunk in enumerate(candidate_chunks)
        )

        prompt = (
            f"Incident: {incident_description}\n\n"
            f"Candidate BNS context from the legal corpus:\n{context}\n\n"
            f"Return the most applicable sections as a JSON object with exactly this shape: "
            f"{{\"sections\": [{{\"section\": \"...\", \"title\": \"...\", "
            f"\"reason\": \"...\", \"confidence\": 0.0}}]}}. "
            f"Use only sections supported by the candidate context where possible."
        )

        response = await self._llm.generate(
            system_prompt=_LEGAL_SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0.1,
            max_tokens=1000,
            json_mode=True,
        )

        sections = self._parse_section_recommendations(response)
        if sections:
            return sections

        return [
            {
                "section": str(chunk.get("metadata", {}).get("section", "unknown")),
                "title": self._infer_section_title(chunk["text"]),
                "reason": "Matched incident description against the legal corpus.",
                "confidence": chunk.get("similarity", 0),
            }
            for chunk in candidate_chunks[:5]
        ]

    def _infer_act_filter(self, question: str) -> dict[str, str] | None:
        q_lower = question.lower()
        if "bns" in q_lower or "nyaya sanhita" in q_lower:
            return {"act": "bns_2023"}
        if "pocso" in q_lower:
            return {"act": "pocso"}
        if "it act" in q_lower:
            return {"act": "it_act"}
        return None

    async def _expand_query(self, question: str) -> str:
        expansion_prompt = (
            "Rewrite the following legal question into a concise, keyword-rich search query "
            "optimized for a semantic vector database. Output ONLY the search query.\n"
            f"Question: {question}"
        )
        try:
            expanded = await self._llm.generate(
                system_prompt="You are an expert legal search engineer. Output only the query.",
                user_prompt=expansion_prompt,
                temperature=0.1,
                max_tokens=80,
                model_tier="fast",
            )
            expanded = expanded.strip('"\' \n')
            if expanded and "MOCK LLM RESPONSE" not in expanded and len(expanded) < 300:
                logger.info("Expanded query for vector search: %s", expanded)
                return expanded
        except Exception as exc:
            logger.warning("Query expansion failed; using original question: %s", exc)
        return question

    def _parse_section_recommendations(self, response: str) -> list[dict[str, Any]]:
        """Parse LLM JSON, tolerating fenced JSON or extra prose."""
        if not response or "MOCK LLM RESPONSE" in response:
            return []

        candidates = [response]
        match = re.search(r"```(?:json)?\s*(.*?)```", response, flags=re.DOTALL | re.IGNORECASE)
        if match:
            candidates.insert(0, match.group(1))
        brace_match = re.search(r"(\{.*\})", response, flags=re.DOTALL)
        if brace_match:
            candidates.append(brace_match.group(1))

        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
            except (json.JSONDecodeError, TypeError):
                continue
            sections = parsed.get("sections") if isinstance(parsed, dict) else parsed
            if isinstance(sections, list):
                return [section for section in sections if isinstance(section, dict)]
        logger.warning("Failed to parse LLM section recommendations as JSON")
        return []

    def _infer_section_title(self, text: str) -> str:
        """Extract a short section title from corpus text."""
        first_line = text.splitlines()[0] if text else ""
        match = re.match(r"Section\s+[0-9A-Za-z-]+\.\s*([^—.–-]{3,80})", first_line)
        if match:
            return match.group(1).strip()
        return first_line[:80].strip() or "Relevant BNS section"
