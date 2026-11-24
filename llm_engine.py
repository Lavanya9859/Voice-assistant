"""LLM integration for natural language understanding."""

from __future__ import annotations

import logging
import os
from typing import Optional

LOGGER = logging.getLogger("llm_engine")


class LLMEngine:
    """Flexible LLM integration supporting multiple providers."""

    def __init__(self):
        """Initialize LLM engine with available providers."""
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.gemini_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        self.huggingface_key = os.getenv("HUGGINGFACE_API_KEY")

        self.use_openai = bool(self.openai_key)
        self.use_gemini = bool(self.gemini_key)
        self.use_huggingface = bool(self.huggingface_key)

    def query(self, prompt: str, context: str = "") -> Optional[str]:
        """Query the LLM with a prompt and optional context."""

        if not any([self.use_openai, self.use_gemini, self.use_huggingface]):
            LOGGER.warning("No LLM API keys configured. Using smart fallback.")
            return None

        # Try providers in order of preference
        if self.use_openai:
            return self._query_openai(prompt, context)
        elif self.use_gemini:
            return self._query_gemini(prompt, context)
        elif self.use_huggingface:
            return self._query_huggingface(prompt, context)

        return None

    def _query_openai(self, prompt: str, context: str) -> Optional[str]:
        """Query OpenAI GPT API."""
        try:
            import openai
            openai.api_key = self.openai_key

            system_msg = (
                "You are a helpful voice assistant. Keep responses concise and natural. "
                "You help with general questions, weather, time, dates, websites, and Wikipedia. "
                f"{context}"
            )

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7,
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            LOGGER.error(f"OpenAI query failed: {e}")
            return None

    def _query_gemini(self, prompt: str, context: str) -> Optional[str]:
        """Query Google Gemini API."""
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.gemini_key)
            model = genai.GenerativeModel("gemini-pro")

            full_prompt = f"{context}\n\nUser: {prompt}"

            response = model.generate_content(full_prompt)
            return response.text.strip()
        except Exception as e:
            LOGGER.error(f"Gemini query failed: {e}")
            return None

    def _query_huggingface(self, prompt: str, context: str) -> Optional[str]:
        """Query Hugging Face Inference API."""
        try:
            import requests

            api_url = "https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf"
            headers = {"Authorization": f"Bearer {self.huggingface_key}"}

            payload = {
                "inputs": f"{context}\n\nUser: {prompt}\nAssistant:",
                "parameters": {"max_length": 200}
            }

            response = requests.post(api_url, headers=headers, json=payload, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    text = result[0].get("generated_text", "")
                    # Extract only the assistant's response
                    if "Assistant:" in text:
                        return text.split("Assistant:")[-1].strip()
                    return text.strip()

            return None
        except Exception as e:
            LOGGER.error(f"Hugging Face query failed: {e}")
            return None

    def is_available(self) -> bool:
        """Check if any LLM provider is configured."""
        return any([self.use_openai, self.use_gemini, self.use_huggingface])


class SmartFallback:
    """Smart pattern matching fallback when no LLM is available."""

    def __init__(self):
        """Initialize smart fallback patterns."""
        self.patterns = {
            # Questions about capabilities
            "can you|what can you|what do you|help|assist":
                "I can help with time, date, weather, greetings, websites, Wikipedia searches, and answer general questions. Try asking me things like: What time is it? How's the weather? Open YouTube. Search Wikipedia for Python.",

            # Questions about the assistant
            "who are you|your name|what are you|introduce yourself":
                "I'm a personal voice assistant built with Python. I can help you with time, date, weather, opening websites, Wikipedia searches, and answering general questions using AI.",

            # General knowledge questions
            "what is|define|explain|tell me about":
                "I can help explain that! For detailed information, try searching Wikipedia or asking in a different way.",

            # How questions
            "how do i|how can i|how to|how does":
                "Great question! I can help guide you. Try asking me more specifically what you need help with.",

            # Questions about user
            "how are you|how's it going|what's up":
                "I'm ready to help you! How can I assist you today?",

            # Math and calculations
            "calculate|what is|math|plus|minus|times|divided":
                "I can help with that! Ask me something like: What is 10 plus 5? Or: Calculate 100 divided by 4.",

            # Time-related with variations
            "what.*time|current time|time now|tell.*time":
                "I'll check the current time for you.",

            # Date-related with variations
            "what.*date|today|current date|tell.*date|day is it":
                "I'll tell you today's date.",

            # Weather with variations
            "weather|temperature|rain|snow|hot|cold|forecast":
                "I can help with weather! Tell me a city name like: What's the weather in London?",

            # Website requests with variations
            "open|visit|go to|browse|access|website|site":
                "I can open many websites! Ask me to open: Google, YouTube, GitHub, Amazon, Netflix, or any website URL.",
        }

    def respond(self, text: str) -> Optional[str]:
        """Generate a smart fallback response based on pattern matching."""
        text_lower = text.lower()

        # Check patterns in order
        for pattern, response in self.patterns.items():
            if any(word in text_lower for word in pattern.split("|")):
                return response

        return None
