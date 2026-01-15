"""
LLM Suggestion Generator for Real-Time Sales Assistant.
Uses Claude API to generate response suggestions.
"""

import logging
import os
import re
from typing import Optional

import anthropic

from config import get_system_prompt

logger = logging.getLogger(__name__)


class SuggestionGenerator:
    """
    Generates sales response suggestions using Claude API.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 300,
        temperature: float = 0.7,
    ):
        """
        Initialize suggestion generator.

        Args:
            api_key: Anthropic API key (or from ANTHROPIC_API_KEY env var)
            model: Claude model to use
            max_tokens: Maximum response tokens
            temperature: Response creativity (0-1)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key required")

        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        self._client = anthropic.Anthropic(api_key=self.api_key)
        logger.info(f"Initialized suggestion generator with model: {model}")

    async def generate(
        self,
        conversation_context: str,
        last_statement: str,
    ) -> list[str]:
        """
        Generate response suggestions for the current conversation.

        Args:
            conversation_context: Recent conversation transcript
            last_statement: Most recent prospect statement

        Returns:
            List of 2-3 suggestion strings
        """
        if not last_statement or not last_statement.strip():
            logger.warning("Empty last statement, skipping suggestion generation")
            return []

        system_prompt = get_system_prompt(conversation_context, last_statement)

        try:
            logger.debug(f"Generating suggestions for: {last_statement[:50]}...")

            response = self._client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": "Generate response suggestions now."}
                ],
            )

            raw_response = response.content[0].text
            suggestions = self._parse_suggestions(raw_response)

            logger.info(f"Generated {len(suggestions)} suggestions")
            return suggestions

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return []

    def generate_sync(
        self,
        conversation_context: str,
        last_statement: str,
    ) -> list[str]:
        """
        Synchronous version of generate().

        Args:
            conversation_context: Recent conversation transcript
            last_statement: Most recent prospect statement

        Returns:
            List of 2-3 suggestion strings
        """
        if not last_statement or not last_statement.strip():
            logger.warning("Empty last statement, skipping suggestion generation")
            return []

        system_prompt = get_system_prompt(conversation_context, last_statement)

        try:
            logger.debug(f"Generating suggestions for: {last_statement[:50]}...")

            response = self._client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": "Generate response suggestions now."}
                ],
            )

            raw_response = response.content[0].text
            suggestions = self._parse_suggestions(raw_response)

            logger.info(f"Generated {len(suggestions)} suggestions")
            return suggestions

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return []

    def _parse_suggestions(self, response: str) -> list[str]:
        """
        Parse numbered suggestions from Claude response.

        Args:
            response: Raw response text from Claude

        Returns:
            List of cleaned suggestion strings
        """
        suggestions = []
        lines = response.strip().split("\n")

        # Pattern to match numbered items: "1.", "1)", "1 -", etc.
        pattern = r"^\s*(\d+)[.\):\-]\s*(.+)$"

        for line in lines:
            line = line.strip()
            if not line:
                continue

            match = re.match(pattern, line)
            if match:
                suggestion = match.group(2).strip()

                # Remove surrounding quotes if present
                if (
                    (suggestion.startswith('"') and suggestion.endswith('"'))
                    or (suggestion.startswith("'") and suggestion.endswith("'"))
                ):
                    suggestion = suggestion[1:-1]

                # Remove leading/trailing special chars
                suggestion = suggestion.strip("\"'")

                if suggestion and len(suggestion) > 5:
                    suggestions.append(suggestion)

        # Limit to 3 suggestions
        return suggestions[:3]

    def test_connection(self) -> bool:
        """
        Test API connection.

        Returns:
            True if connection successful
        """
        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}],
            )
            return True
        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            return False
