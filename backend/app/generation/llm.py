"""LLM client abstraction supporting Ollama, Anthropic, and OpenAI."""

import logging

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def generate(
        self,
        system: str,
        messages: list[dict],
        provider: str = "ollama",
    ) -> str:
        """Generate a response from the specified LLM provider."""
        if provider == "ollama":
            return await self._ollama(system, messages)
        elif provider == "anthropic":
            return await self._anthropic(system, messages)
        elif provider == "openai":
            return await self._openai(system, messages)
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")

    async def _ollama(self, system: str, messages: list[dict]) -> str:
        """Call Ollama's chat API."""
        ollama_messages = [{"role": "system", "content": system}]
        ollama_messages.extend(messages)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.settings.ollama_base_url}/api/chat",
                json={
                    "model": self.settings.ollama_model,
                    "messages": ollama_messages,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]

    async def _anthropic(self, system: str, messages: list[dict]) -> str:
        """Call Anthropic's Messages API."""
        if not self.settings.anthropic_api_key:
            raise ValueError("Anthropic API key not configured")

        import anthropic

        client = anthropic.AsyncAnthropic(api_key=self.settings.anthropic_api_key)
        response = await client.messages.create(
            model=self.settings.anthropic_model,
            max_tokens=2048,
            system=system,
            messages=messages,
        )
        return response.content[0].text

    async def _openai(self, system: str, messages: list[dict]) -> str:
        """Call OpenAI's Chat Completions API."""
        if not self.settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")

        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        openai_messages = [{"role": "system", "content": system}]
        openai_messages.extend(messages)

        response = await client.chat.completions.create(
            model=self.settings.openai_model,
            messages=openai_messages,
            max_tokens=2048,
        )
        return response.choices[0].message.content
