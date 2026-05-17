"""
Translation service — LLM-powered translation between English, Hindi, and Gujarati.

Uses the existing LLMService for translations. No new API keys needed.
"""

import logging
from typing import Any

from app.services.llmService import LLMService

logger = logging.getLogger("crimegpt.translation")

_LANG_NAMES = {
    "en": "English",
    "hi": "Hindi (Devanagari script)",
    "gu": "Gujarati (Gujarati script)",
}

_TRANSLATION_SYSTEM_PROMPT = """You are an expert legal translator specializing in Indian criminal law documents.

Rules:
1. Translate accurately while preserving legal terminology
2. Keep proper nouns (names, places, case numbers) untranslated
3. Use formal, official language appropriate for police/court documents
4. For Hindi, use Devanagari script
5. For Gujarati, use Gujarati script
6. Output ONLY the translated text, no explanations or notes
7. Maintain the original formatting and structure
"""


class TranslationService:
    """LLM-powered translation between en/hi/gu."""

    def __init__(self):
        self._llm = LLMService()

    async def translate(
        self,
        text: str,
        source_lang: str = "en",
        target_lang: str = "hi",
    ) -> dict[str, Any]:
        """
        Translate text between supported languages.

        Args:
            text: Text to translate
            source_lang: Source language code (en/hi/gu)
            target_lang: Target language code (en/hi/gu)

        Returns:
            Dict with translated text and metadata
        """
        if source_lang == target_lang:
            return {
                "original": text,
                "translated": text,
                "source_language": source_lang,
                "target_language": target_lang,
                "note": "Source and target languages are the same",
            }

        source_name = _LANG_NAMES.get(source_lang, source_lang)
        target_name = _LANG_NAMES.get(target_lang, target_lang)

        user_prompt = (
            f"Translate the following text from {source_name} to {target_name}.\n\n"
            f"Text to translate:\n{text}"
        )

        try:
            translated = await self._llm.generate(
                system_prompt=_TRANSLATION_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.1,
                max_tokens=2000,
                model_tier="primary",
            )
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return {
                "original": text,
                "translated": f"[Translation to {target_name} failed — {e}]",
                "source_language": source_lang,
                "target_language": target_lang,
                "error": str(e),
            }

        logger.info(f"Translated {len(text)} chars from {source_lang} to {target_lang}")

        return {
            "original": text,
            "translated": translated.strip(),
            "source_language": source_lang,
            "target_language": target_lang,
        }
