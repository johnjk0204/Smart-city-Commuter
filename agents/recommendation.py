import logging
from langchain_core.messages import HumanMessage, SystemMessage
from config import build_llm
from utils import PromptCompressor

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are the Chief Recommendation Agent for Metro City's Smart Commute Planner.

You synthesize inputs from four specialized agents:
1. Route Planner — route options and distances
2. Traffic Analyst — congestion levels and delays
3. Weather Analyst — weather impact on modes
4. Transit Advisor — public transit details and schedules

Your job is to produce ONE clear, final commute recommendation that:
- Selects the single best mode/route for this specific situation
- Explains WHY this is the best choice given all factors
- Provides step-by-step journey instructions
- Gives an estimated total journey time
- Lists 1-2 backup alternatives

Format your response as:

## Recommended Route
[Main recommendation]

## Why This Route?
[Reasoning combining all agent insights]

## Step-by-Step Instructions
[Numbered steps]

## Estimated Journey Time
[Time estimate with any caveats]

## Backup Options
[1-2 alternatives]

Be decisive and practical — the commuter needs to act on your advice."""


class RecommendationAgent:
    def __init__(self, compressor: PromptCompressor | None = None):
        self._compressor = compressor
        self._llm = build_llm()

    def _build_messages(self, state: dict) -> list:
        origin = state.get("origin", "Unknown")
        destination = state.get("destination", "Unknown")
        query = state.get("masked_query", state.get("raw_query", ""))

        def _maybe_compress(text: str, label: str) -> str:
            if self._compressor and text and "No " not in text[:10]:
                return self._compressor.compress(query, text, agent=f"Recommendation/{label}")[0]
            return text

        route_analysis   = _maybe_compress(state.get("route_analysis",   "No route data available."),   "Route")
        traffic_analysis = _maybe_compress(state.get("traffic_analysis", "No traffic data available."), "Traffic")
        weather_analysis = _maybe_compress(state.get("weather_analysis", "No weather data available."), "Weather")
        transit_analysis = _maybe_compress(state.get("transit_analysis", "No transit data available."), "Transit")

        traffic_severity = state.get("traffic_severity", "UNKNOWN")
        weather_impact   = state.get("weather_impact",   "UNKNOWN")

        return [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=f"""Original Query: {query}
Journey: {origin} → {destination}

=== ROUTE PLANNER REPORT ===
{route_analysis}

=== TRAFFIC ANALYST REPORT ===
Severity: {traffic_severity}
{traffic_analysis}

=== WEATHER ANALYST REPORT ===
Impact Level: {weather_impact}
{weather_analysis}

=== TRANSIT ADVISOR REPORT ===
{transit_analysis}

Based on all the above, provide the final commute recommendation."""),
        ]

    def run(self, state: dict) -> dict:
        import re
        messages = self._build_messages(state)
        response = self._llm.invoke(messages)
        recommendation = response.content

        duration_match = re.search(r"(\d+)\s*(?:to\s*\d+\s*)?(?:minutes?|mins?)", recommendation, re.IGNORECASE)
        estimated_duration = duration_match.group(0) if duration_match else "See recommendation"

        recommended_mode = "transit"
        for kw in ["metro", "bus", "bike", "walk", "taxi", "cycling", "transit"]:
            if kw.lower() in recommendation[:300].lower():
                recommended_mode = kw
                break

        logger.info("Recommendation agent completed | mode=%s", recommended_mode)
        return {
            "recommendation": recommendation,
            "recommended_mode": recommended_mode,
            "estimated_duration": estimated_duration,
        }

    def run_stream(self, state: dict):
        """Yield recommendation text chunks for real-time streaming."""
        messages = self._build_messages(state)
        for chunk in self._llm.stream(messages):
            if chunk.content:
                yield chunk.content
