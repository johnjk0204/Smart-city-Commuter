import re
from dataclasses import dataclass, field
from typing import Optional

# PII patterns
_PATTERNS = {
    "EMAIL":       (r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b", "[EMAIL REDACTED]"),
    "PHONE":       (r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE REDACTED]"),
    "SSN":         (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN REDACTED]"),
    "CREDIT_CARD": (r"\b(?:\d{4}[-\s]?){3}\d{4}\b", "[CARD REDACTED]"),
    "ZIP_CODE":    (r"\b\d{5}(?:-\d{4})?\b", "[ZIP REDACTED]"),
    "IP_ADDRESS":  (r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[IP REDACTED]"),
    "DATE_OF_BIRTH": (r"\b(?:dob|date of birth|born)[:\s]+\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b", "[DOB REDACTED]"),
    "PASSPORT":    (r"\b[A-Z]{1,2}\d{6,9}\b", "[PASSPORT REDACTED]"),
    "PERSON_NAME": (
        r"\b(?:my name is|i am|i'm|this is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
        "[NAME REDACTED]"
    ),
    "HOME_ADDRESS": (
        r"\b\d{1,5}\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:St|Street|Ave|Avenue|Blvd|Boulevard|Dr|Drive|Rd|Road|Ln|Lane|Ct|Court|Way|Pl|Place)\b",
        "[ADDRESS REDACTED]"
    ),
}

# Sensitive context keywords that indicate location is personal
_PERSONAL_LOCATION_PREFIXES = re.compile(
    r"\b(?:my home|my house|my apartment|my flat|i live at|i'm at|pick me up|drop me off at|from my|to my)\b",
    re.IGNORECASE,
)


@dataclass
class PIIEntity:
    entity_type: str
    original: str
    redacted: str
    start: int
    end: int


@dataclass
class PIIDetectionResult:
    original_text: str
    masked_text: str
    entities: list[PIIEntity] = field(default_factory=list)
    has_pii: bool = False
    risk_level: str = "LOW"  # LOW | MEDIUM | HIGH

    @property
    def pii_summary(self) -> str:
        if not self.entities:
            return "No PII detected"
        types = list({e.entity_type for e in self.entities})
        return f"Detected: {', '.join(types)}"


class PIIDetector:
    """Regex-based PII detector and anonymizer for commute query inputs."""

    def __init__(self):
        self._compiled = {
            name: (re.compile(pattern, re.IGNORECASE), replacement)
            for name, (pattern, replacement) in _PATTERNS.items()
        }

    def detect_and_mask(self, text: str) -> PIIDetectionResult:
        masked = text
        entities: list[PIIEntity] = []
        offset = 0

        for entity_type, (regex, replacement) in self._compiled.items():
            for match in regex.finditer(text):
                start, end = match.start() + offset, match.end() + offset
                original = match.group()
                # For PERSON_NAME we mask the captured group only
                if entity_type == "PERSON_NAME" and match.lastindex:
                    original = match.group(1)
                    start = match.start(1) + offset
                    end = match.end(1) + offset

                entities.append(PIIEntity(entity_type, original, replacement, start, end))

        # Re-apply replacements on text (simpler pass)
        masked = text
        for entity_type, (regex, replacement) in self._compiled.items():
            if entity_type == "PERSON_NAME":
                masked = regex.sub(
                    lambda m: m.group(0).replace(m.group(1), replacement) if m.lastindex else m.group(0),
                    masked,
                )
            else:
                masked = regex.sub(replacement, masked)

        # Flag personal location context but don't redact — just note it
        has_personal_location = bool(_PERSONAL_LOCATION_PREFIXES.search(text))
        if has_personal_location:
            entities.append(
                PIIEntity("PERSONAL_LOCATION_CONTEXT", "personal location reference", "(noted)", 0, 0)
            )

        risk = self._assess_risk(entities)
        return PIIDetectionResult(
            original_text=text,
            masked_text=masked,
            entities=entities,
            has_pii=len(entities) > 0,
            risk_level=risk,
        )

    def _assess_risk(self, entities: list[PIIEntity]) -> str:
        high_risk_types = {"SSN", "CREDIT_CARD", "PASSPORT", "DATE_OF_BIRTH"}
        medium_risk_types = {"EMAIL", "PHONE", "HOME_ADDRESS"}

        types = {e.entity_type for e in entities}
        if types & high_risk_types:
            return "HIGH"
        if types & medium_risk_types:
            return "MEDIUM"
        if entities:
            return "LOW"
        return "NONE"

    def is_safe_to_process(self, result: PIIDetectionResult) -> bool:
        return result.risk_level != "HIGH"
