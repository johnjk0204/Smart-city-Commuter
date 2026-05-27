import re
from dataclasses import dataclass

_BLOCKED_PATTERNS = [
    r"\b(?:bomb|explosive|weapon|attack|hack|malware|ransomware)\b",
    r"\b(?:kill|murder|assault|threat)\b",
    r"\b(?:scam|fraud|phishing|steal|rob)\b",
]

_OFF_TOPIC_PATTERNS = [
    r"\b(?:recipe|cooking|movie|sports score|stock price|lottery)\b",
    r"\b(?:dating|romance|relationship advice)\b",
]

_COMMUTE_KEYWORDS = [
    "route", "commute", "travel", "transit", "bus", "metro", "train", "subway",
    "bike", "walk", "drive", "traffic", "fastest", "cheapest", "directions",
    "how to get", "how do i get", "way to", "from", "to", "station", "stop",
    "schedule", "time", "duration", "distance", "airport", "work", "office",
    "weather", "delay", "congestion", "parking", "ride", "trip", "journey",
    "peak", "rush hour", "avoid", "alternative", "detour",
]


@dataclass
class FilterResult:
    is_blocked: bool
    is_relevant: bool
    reason: str
    confidence: float


class ContentFilter:
    """Guards against harmful, off-topic, or irrelevant queries."""

    def __init__(self):
        self._blocked = [re.compile(p, re.IGNORECASE) for p in _BLOCKED_PATTERNS]
        self._off_topic = [re.compile(p, re.IGNORECASE) for p in _OFF_TOPIC_PATTERNS]
        self._commute_kw = re.compile(
            "|".join(re.escape(k) for k in _COMMUTE_KEYWORDS), re.IGNORECASE
        )

    def check(self, text: str) -> FilterResult:
        # Block harmful content
        for pattern in self._blocked:
            if pattern.search(text):
                return FilterResult(True, False, "Harmful content detected", 0.95)

        # Check off-topic
        for pattern in self._off_topic:
            if pattern.search(text):
                return FilterResult(False, False, "Query appears off-topic for commute planning", 0.7)

        # Relevance check
        matches = self._commute_kw.findall(text)
        relevance_score = min(1.0, len(matches) / 3)

        if relevance_score == 0:
            return FilterResult(
                False, False,
                "Query does not appear related to commute planning. Please ask about routes, transit, or travel.",
                0.6
            )

        return FilterResult(False, True, "Query is relevant to commute planning", relevance_score)
