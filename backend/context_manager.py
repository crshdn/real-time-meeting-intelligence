"""
Conversation Context Manager for Real-Time Sales Assistant.
Maintains rolling conversation buffer and detects when to trigger AI suggestions.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from typing import Optional, List
import logging

from config import OBJECTION_TRIGGERS

logger = logging.getLogger(__name__)


@dataclass
class Utterance:
    """Single utterance in conversation."""

    speaker: str  # "salesperson" or "prospect"
    text: str
    timestamp: datetime = field(default_factory=datetime.now)
    is_final: bool = True


class ConversationBuffer:
    """
    Rolling buffer of conversation utterances.
    Maintains configurable duration of history and detects trigger phrases.
    """

    def __init__(
        self,
        max_duration_seconds: int = 180,
        suggestion_cooldown: float = 5.0,
    ):
        """
        Initialize conversation buffer.

        Args:
            max_duration_seconds: How long to keep utterances (default 3 minutes)
            suggestion_cooldown: Minimum seconds between suggestion triggers
        """
        self.utterances: deque[Utterance] = deque()
        self.max_duration = max_duration_seconds
        self.suggestion_cooldown = suggestion_cooldown
        self.last_suggestion_time: Optional[datetime] = None
        self._pending_interim: Optional[Utterance] = None

    def add(self, utterance: Utterance) -> None:
        """Add an utterance to the buffer."""
        # If this is a final utterance, clear any pending interim
        if utterance.is_final:
            self._pending_interim = None
            self.utterances.append(utterance)
            self._prune_old()
            logger.debug(
                f"Added final utterance from {utterance.speaker}: {utterance.text[:50]}..."
            )
        else:
            # Store interim result (overwrite previous interim)
            self._pending_interim = utterance

    def add_transcript(
        self, text: str, speaker: int, is_final: bool = True
    ) -> None:
        """
        Convenience method to add transcript text.

        Args:
            text: The transcribed text
            speaker: Speaker ID from diarization (0 or 1)
            is_final: Whether this is a final or interim result
        """
        # Map speaker ID to label (0 = first speaker detected, usually prospect on calls)
        # This is a simplification - in production would need calibration
        speaker_label = "prospect" if speaker == 0 else "salesperson"

        utterance = Utterance(
            speaker=speaker_label,
            text=text.strip(),
            is_final=is_final,
        )
        self.add(utterance)

    def _prune_old(self) -> None:
        """Remove utterances older than max_duration."""
        cutoff = datetime.now() - timedelta(seconds=self.max_duration)
        while self.utterances and self.utterances[0].timestamp < cutoff:
            self.utterances.popleft()

    def get_context_string(self, last_n: Optional[int] = None) -> str:
        """
        Get conversation as formatted string for LLM context.

        Args:
            last_n: Only include last N utterances (None for all)

        Returns:
            Formatted conversation transcript
        """
        utterances = [u for u in self.utterances if u.is_final]
        if last_n:
            utterances = utterances[-last_n:]

        return "\n".join(
            [f"{u.speaker.title()}: {u.text}" for u in utterances]
        )

    def get_last_prospect_statement(self) -> Optional[str]:
        """Get the most recent prospect utterance."""
        for utterance in reversed(self.utterances):
            if utterance.speaker == "prospect" and utterance.is_final:
                return utterance.text
        return None

    def get_current_text(self) -> Optional[str]:
        """Get current text including any pending interim result."""
        if self._pending_interim:
            return self._pending_interim.text
        if self.utterances:
            return self.utterances[-1].text
        return None

    def get_current_speaker(self) -> Optional[str]:
        """Get current speaker including any pending interim result."""
        if self._pending_interim:
            return self._pending_interim.speaker
        if self.utterances:
            return self.utterances[-1].speaker
        return None

    def should_trigger_ai(self) -> bool:
        """
        Determine if we should generate AI suggestions.

        Returns:
            True if conditions are met for generating suggestions
        """
        if not self.utterances:
            return False

        # Check cooldown
        if self.last_suggestion_time:
            elapsed = (datetime.now() - self.last_suggestion_time).total_seconds()
            if elapsed < self.suggestion_cooldown:
                return False

        last = self.utterances[-1]

        # Only trigger on final prospect utterances
        if last.speaker != "prospect" or not last.is_final:
            return False

        # Require minimum text length
        if len(last.text) < 10:
            return False

        return True

    def check_for_objection(self) -> Optional[str]:
        """
        Check if recent conversation contains objection triggers.

        Returns:
            Matched trigger phrase or None
        """
        # Get last 3 utterances as text
        recent = list(self.utterances)[-3:]
        recent_text = " ".join([u.text.lower() for u in recent])

        for phrase in OBJECTION_TRIGGERS:
            if phrase in recent_text:
                logger.info(f"Detected objection trigger: '{phrase}'")
                return phrase

        return None

    def mark_suggestion_sent(self) -> None:
        """Mark that a suggestion was just sent (for cooldown)."""
        self.last_suggestion_time = datetime.now()

    def clear(self) -> None:
        """Clear all utterances."""
        self.utterances.clear()
        self.last_suggestion_time = None
        self._pending_interim = None
        logger.info("Conversation buffer cleared")

    @property
    def utterance_count(self) -> int:
        """Number of final utterances in buffer."""
        return len(self.utterances)

    @property
    def duration_seconds(self) -> float:
        """Duration of conversation in buffer."""
        if len(self.utterances) < 2:
            return 0
        first = self.utterances[0].timestamp
        last = self.utterances[-1].timestamp
        return (last - first).total_seconds()

    def to_dict(self) -> dict:
        """Export buffer state for debugging."""
        return {
            "utterance_count": self.utterance_count,
            "duration_seconds": self.duration_seconds,
            "last_prospect": self.get_last_prospect_statement(),
            "has_pending_interim": self._pending_interim is not None,
        }
