"""
LLM Service — unified abstraction over Groq (cloud) and Ollama (local).

Provides a single `generate()` method that routes to the configured provider.
All other services (FIR, Legal, Case Linkage) call this — never Groq/Ollama directly.

Usage:
    from app.services.llmService import LLMService
    llm = LLMService()
    response = await llm.generate(
        system_prompt="You are a legal assistant...",
        user_prompt="Draft a FIR for theft...",
    )
"""

import logging
from typing import Any

from app.config import get_settings

logger = logging.getLogger("crimegpt.llm")


class LLMService:
    """Unified LLM interface — cloud (Groq) or local (Ollama)."""

    def __init__(self):
        self._settings = get_settings()
        self._mode = self._settings.llm.mode

    def _resolve_model(self, tier: str) -> str:
        """Resolve model name from tier: primary, fast, or fallback."""
        tier_map = {
            "primary": self._settings.llm.groq_model_primary,
            "fast": self._settings.llm.groq_model_fast,
            "fallback": self._settings.llm.groq_model_fallback,
        }
        return tier_map.get(tier, self._settings.llm.groq_model_primary)

    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        json_mode: bool = False,
        model_tier: str = "primary",
    ) -> str:
        """
        Generate text completion from the configured LLM provider.

        Args:
            system_prompt: System-level instructions
            user_prompt: User query / context
            temperature: Creativity level (0.0 = deterministic, 1.0 = creative)
            max_tokens: Maximum response length
            json_mode: If True, instruct the LLM to respond in JSON
            model_tier: Which model to use — 'primary' (Scout 17B), 'fast' (8B), 'fallback' (70B)

        Returns:
            Generated text response
        """
        if self._mode == "cloud":
            return await self._generate_groq(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=json_mode,
                model_tier=model_tier,
            )
        else:
            return await self._generate_ollama(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

    async def _generate_groq(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        json_mode: bool,
        model_tier: str = "primary",
    ) -> str:
        """Generate via Groq cloud API with automatic fallback."""
        api_key = self._settings.llm.groq_api_key
        model = self._resolve_model(model_tier)

        if not api_key:
            logger.warning("No GROQ_API_KEY configured — returning mock response")
            return self._mock_response(user_prompt)

        try:
            from groq import AsyncGroq

            client = AsyncGroq(api_key=api_key)

            kwargs: dict[str, Any] = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = await client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content or ""

            logger.info(
                f"Groq [{model}] generated {len(content)} chars "
                f"(tokens: {response.usage.total_tokens if response.usage else '?'})"
            )
            return content

        except ImportError:
            logger.error("groq package not installed — pip install groq")
            return self._mock_response(user_prompt)
        except Exception as e:
            logger.error(f"Groq API error with {model}: {e}")
            # Auto-fallback: try fallback model before returning mock
            if model_tier != "fallback":
                logger.info(f"Retrying with fallback model...")
                return await self._generate_groq(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    json_mode=json_mode,
                    model_tier="fallback",
                )
            return self._mock_response(user_prompt)

    async def _generate_ollama(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate via local Ollama instance."""
        base_url = self._settings.llm.ollama_base_url
        model = self._settings.llm.ollama_model

        try:
            import httpx

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{base_url}/api/generate",
                    json={
                        "model": model,
                        "system": system_prompt,
                        "prompt": user_prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        },
                    },
                )
                response.raise_for_status()
                data = response.json()
                content = data.get("response", "")
                logger.info(f"Ollama [{model}] generated {len(content)} chars")
                return content

        except ImportError:
            logger.error("httpx package not installed — pip install httpx")
            return self._mock_response(user_prompt)
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return self._mock_response(user_prompt)

    def _mock_response(self, user_prompt: str) -> str:
        """Fallback mock response when LLM is unavailable."""
        return (
            "[MOCK LLM RESPONSE — Configure GROQ_API_KEY or start Ollama for real AI]\n\n"
            f"Based on the provided input, here is a placeholder analysis:\n\n"
            f"Input received: {user_prompt[:200]}...\n\n"
            f"This response will be replaced with real AI-generated content "
            f"once an LLM provider is configured."
        )

    async def health_check(self) -> dict[str, Any]:
        """Check LLM provider health."""
        result: dict[str, Any] = {"mode": self._mode, "healthy": False}

        if self._mode == "cloud":
            result["provider"] = "Groq"
            result["models"] = {
                "primary": self._settings.llm.groq_model_primary,
                "fast": self._settings.llm.groq_model_fast,
                "fallback": self._settings.llm.groq_model_fallback,
                "whisper": self._settings.llm.groq_model_whisper,
            }
            result["healthy"] = bool(self._settings.llm.groq_api_key)
            if not result["healthy"]:
                result["error"] = "GROQ_API_KEY not configured"
        else:
            result["provider"] = "Ollama"
            result["model"] = self._settings.llm.ollama_model
            try:
                import httpx
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(f"{self._settings.llm.ollama_base_url}/api/tags")
                    result["healthy"] = resp.status_code == 200
            except Exception as e:
                result["error"] = str(e)

        return result
