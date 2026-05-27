from typing import Any, Optional
from typing_extensions import TypedDict


class CommuteState(TypedDict, total=False):
    # Input
    raw_query: str
    session_id: str
    user_preferences: dict[str, Any]

    # PII Guardian outputs
    masked_query: str
    pii_entities: list[dict]
    pii_risk_level: str
    pii_blocked: bool

    # Content filter
    content_blocked: bool
    content_block_reason: str
    is_relevant: bool

    # Parsed intent
    origin: str
    destination: str
    travel_time: str
    travel_mode_preference: str

    # Agent outputs
    route_analysis: str
    route_options: list[dict]
    traffic_analysis: str
    traffic_severity: str
    weather_analysis: str
    weather_impact: str
    transit_analysis: str
    transit_options: list[dict]

    # Final output
    recommendation: str
    recommended_mode: str
    estimated_duration: str

    # Evaluation
    evaluation_scores: dict[str, float]
    evaluation_summary: str

    # Monitoring
    agent_traces: list[dict]
    error: Optional[str]

    # Prompt compression
    compression_stats: list[dict]
