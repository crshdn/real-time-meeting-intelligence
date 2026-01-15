# Conversation Context Manager Snippet
# Manages rolling conversation buffer and trigger detection

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from typing import Optional, List

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
    Maintains configurable duration of history.
    """

    # Phrases that trigger AI suggestions
    TRIGGER_PHRASES = [
        "too expensive", "over budget", "can't afford", "too much",
        "not sure", "don't know", "maybe",
        "think about it", "get back to you", "discuss internally",
        "already using", "have a solution", "competitor",
        "not the right time", "too busy", "next quarter",
        "not interested", "don't need", "don't see the value"
    ]

    def __init__(self, max_duration_seconds: int = 180):
        """
        Initialize conversation buffer.

        Args:
            max_duration_seconds: How long to keep utterances (default 3 minutes)
        """
        self.utterances: deque[Utterance] = deque()
        self.max_duration = max_duration_seconds
        self.last_suggestion_time: Optional[datetime] = None
        self.suggestion_cooldown = 5  # seconds between suggestions

    def add(self, utterance: Utterance) -> None:
        """Add an utterance to the buffer."""
        self.utterances.append(utterance)
        self._prune_old()

    def add_transcript(self, text: str, speaker: str, is_final: bool = True) -> None:
        """Convenience method to add transcript text."""
        utterance = Utterance(
            speaker=speaker,
            text=text,
            is_final=is_final
        )
        self.add(utterance)

    def _prune_old(self) -> None:
        """Remove utterances older than max_duration."""
        cutoff = datetime.now() - timedelta(seconds=self.max_duration)
        while self.utterances and self.utterances[0].timestamp < cutoff:
            self.utterances.popleft()

    def get_context_string(self, last_n: Optional[int] = None) -> str:
        """
        Get conversation as formatted string.

        Args:
            last_n: Only include last N utterances (None for all)
        """
        utterances = list(self.utterances)
        if last_n:
            utterances = utterances[-last_n:]

        return "\n".join([
            f"{u.speaker.title()}: {u.text}"
            for u in utterances
            if u.is_final
        ])

    def get_last_prospect_statement(self) -> Optional[str]:
        """Get the most recent prospect utterance."""
        for utterance in reversed(self.utterances):
            if utterance.speaker == "prospect" and utterance.is_final:
                return utterance.text
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

        # Always trigger on prospect speech (they might need a response)
        # Could add more sophisticated logic here
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

        for phrase in self.TRIGGER_PHRASES:
            if phrase in recent_text:
                return phrase

        return None

    def mark_suggestion_sent(self) -> None:
        """Mark that a suggestion was just sent (for cooldown)."""
        self.last_suggestion_time = datetime.now()

    def clear(self) -> None:
        """Clear all utterances."""
        self.utterances.clear()
        self.last_suggestion_time = None

    @property
    def utterance_count(self) -> int:
        """Number of utterances in buffer."""
        return len(self.utterances)

    @property
    def duration_seconds(self) -> float:
        """Duration of conversation in buffer."""
        if len(self.utterances) < 2:
            return 0
        first = self.utterances[0].timestamp
        last = self.utterances[-1].timestamp
        return (last - first).total_seconds()


# Usage example:
if __name__ == "__main__":
    buffer = ConversationBuffer(max_duration_seconds=180)

    # Simulate conversation
    buffer.add_transcript("Hi, thanks for taking my call today.", "salesperson")
    buffer.add_transcript("Sure, what can I help you with?", "prospect")
    buffer.add_transcript(
        "I wanted to show you how our CRM can help your team close more deals.",
        "salesperson"
    )
    buffer.add_transcript(
        "That sounds interesting, but honestly it seems too expensive for our budget.",
        "prospect"
    )

    print("Conversation context:")
    print(buffer.get_context_string())
    print()

    print(f"Should trigger AI: {buffer.should_trigger_ai()}")
    print(f"Last prospect statement: {buffer.get_last_prospect_statement()}")
    print(f"Detected objection: {buffer.check_for_objection()}")
