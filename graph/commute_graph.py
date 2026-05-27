import logging
import uuid
import re
from typing import Literal

from langgraph.graph import StateGraph, END, START

from .state import CommuteState
from agents import (
    RoutePlannerAgent,
    TrafficAnalystAgent,
    WeatherAnalystAgent,
    TransitAdvisorAgent,
    RecommendationAgent,
)
from guardrails import PIIDetector, ContentFilter, MonitoringManager
from vectorstore import ChromaVectorStore
from evaluation import CommuteEvaluator
from utils import PromptCompressor
from config import CHROMA_PERSIST_DIR, COMPRESSION_RATIO

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Shared singletons (initialized once per build_commute_graph call)
# ──────────────────────────────────────────────────────────────

def _extract_locations(query: str) -> tuple[str, str]:
    """Best-effort extraction of origin/destination from free text."""
    query_lower = query.lower()

    # Patterns: "from X to Y", "X to Y", "between X and Y"
    patterns = [
        r"from\s+(.+?)\s+to\s+(.+?)(?:\s+by|\s+via|\s+using|\s+at|\?|$)",
        r"(?:get\s+from|travel\s+from)\s+(.+?)\s+to\s+(.+?)(?:\s+by|\?|$)",
        r"(.+?)\s+to\s+(.+?)(?:\s+by|\s+via|\?|$)",
    ]

    for pattern in patterns:
        m = re.search(pattern, query_lower)
        if m:
            origin = m.group(1).strip().title()
            dest = m.group(2).strip().title()
            if len(origin) > 2 and len(dest) > 2:
                return origin, dest

    # Fallback: look for known landmark names in the query
    known_places = [
        # Metro City (demo)
        "Central Station", "Tech Park", "City Hall", "University Campus",
        "Metro Medical Center", "Financial District", "Riverside Park",
        "Airport Terminal", "Shopping Mall", "Sports Arena",
        "North Suburbs Hub", "Industrial Zone", "Old Town Square",
        "Science Museum", "East Residential Area",
        # Bengaluru
        "KSR Bengaluru City Railway Station", "MG Road", "Electronic City",
        "Whitefield", "Koramangala", "Indiranagar", "Lalbagh",
        "Vidhana Soudha", "Kempegowda International Airport", "IISc Campus",
        "Majestic", "Hebbal", "Marathahalli", "JP Nagar", "Banashankari",
        "Silk Institute", "Nagasandra", "Baiyappanahalli",
        # Mumbai
        "CST Mumbai", "Chhatrapati Shivaji Maharaj Terminus",
        "Bandra Kurla Complex", "BKC", "Nariman Point", "Andheri",
        "Dadar", "Gateway of India", "Marine Drive", "IIT Bombay",
        "Lilavati Hospital", "CSIA Airport", "Colaba", "Thane",
        "Worli Sea Link", "Film City",
        # Delhi
        "New Delhi Railway Station", "Connaught Place", "India Gate",
        "Cyber Hub", "IGI Airport", "Lajpat Nagar", "AIIMS Delhi",
        "IIT Delhi", "Red Fort", "Qutub Minar", "Lotus Temple",
        "Hauz Khas", "Saket", "Dwarka", "Karol Bagh",
        "Rajiv Chowk", "HUDA City Centre",
    ]
    found = [p for p in known_places if p.lower() in query_lower]
    if len(found) >= 2:
        return found[0], found[1]
    if len(found) == 1:
        return found[0], "Central Station"

    return "Central Station", "Tech Park"


def build_commute_graph(
    use_mlflow: bool = False,
    use_langsmith: bool = False,
    use_deepeval: bool = False,
    use_compression: bool = False,
    compression_ratio: float | None = None,
) -> StateGraph:

    # Initialize shared components
    vector_store = ChromaVectorStore(persist_dir=CHROMA_PERSIST_DIR)
    pii_detector = PIIDetector()
    content_filter = ContentFilter()
    monitor = MonitoringManager(use_mlflow=use_mlflow, use_langsmith=use_langsmith)
    evaluator = CommuteEvaluator(use_deepeval_api=use_deepeval)

    compressor = PromptCompressor(compression_ratio=compression_ratio or COMPRESSION_RATIO) if use_compression else None

    route_agent   = RoutePlannerAgent(vector_store, compressor=compressor)
    traffic_agent = TrafficAnalystAgent(vector_store, compressor=compressor)
    weather_agent = WeatherAnalystAgent()
    transit_agent = TransitAdvisorAgent(vector_store, compressor=compressor)
    rec_agent     = RecommendationAgent(compressor=compressor)

    # ── Node definitions ──────────────────────────────────────

    def pii_guardian_node(state: CommuteState) -> dict:
        raw = state["raw_query"]
        result = pii_detector.detect_and_mask(raw)
        monitor.record_pii(result.risk_level, result.has_pii)
        blocked = not pii_detector.is_safe_to_process(result)
        updates: dict = {
            "masked_query": result.masked_text,
            "pii_entities": [{"type": e.entity_type, "redacted": e.redacted} for e in result.entities],
            "pii_risk_level": result.risk_level,
            "pii_blocked": blocked,
        }
        if blocked:
            updates["error"] = (
                "Input blocked: HIGH-risk PII detected (SSN, credit card, passport). "
                "Please remove sensitive information and try again."
            )
        return updates

    def content_filter_node(state: CommuteState) -> dict:
        if state.get("pii_blocked"):
            return {}
        query = state.get("masked_query", state["raw_query"])
        result = content_filter.check(query)
        updates: dict = {"content_blocked": result.is_blocked, "is_relevant": result.is_relevant}
        if result.is_blocked:
            updates["error"] = f"Query blocked: {result.reason}"
        elif not result.is_relevant:
            updates["error"] = result.reason
            updates["content_blocked"] = True
        return updates

    def intent_parser_node(state: CommuteState) -> dict:
        query = state.get("masked_query", state["raw_query"])
        origin, destination = _extract_locations(query)
        prefs = dict(state.get("user_preferences", {}))
        query_lower = query.lower()
        if any(w in query_lower for w in ["cheap", "cheapest", "low cost", "budget"]):
            prefs["priority"] = "cost"
        elif any(w in query_lower for w in ["fast", "fastest", "quick", "urgent"]):
            prefs["priority"] = "speed"
        elif any(w in query_lower for w in ["green", "eco", "environment", "sustainable"]):
            prefs["priority"] = "eco"
        else:
            prefs["priority"] = "balanced"
        return {"origin": origin, "destination": destination, "user_preferences": prefs}

    def route_planner_node(state: CommuteState) -> dict:
        with monitor.trace_agent("RoutePlannerAgent") as trace:
            result = route_agent.run(
                state.get("masked_query", ""),
                state.get("origin", "Central Station"),
                state.get("destination", "Tech Park"),
            )
            trace.output_tokens = 200
        return result  # keys: route_analysis, route_options

    def traffic_analyst_node(state: CommuteState) -> dict:
        with monitor.trace_agent("TrafficAnalystAgent") as trace:
            result = traffic_agent.run(
                state.get("masked_query", ""),
                state.get("origin", ""),
                state.get("destination", ""),
            )
            trace.output_tokens = 150
        return result  # keys: traffic_analysis, traffic_severity

    def weather_analyst_node(state: CommuteState) -> dict:
        with monitor.trace_agent("WeatherAnalystAgent") as trace:
            result = weather_agent.run(
                state.get("masked_query", ""),
                state.get("origin", ""),
                state.get("destination", ""),
            )
            trace.output_tokens = 120
        return result  # keys: weather_analysis, weather_impact

    def transit_advisor_node(state: CommuteState) -> dict:
        with monitor.trace_agent("TransitAdvisorAgent") as trace:
            result = transit_agent.run(
                state.get("masked_query", ""),
                state.get("origin", ""),
                state.get("destination", ""),
            )
            trace.output_tokens = 180
        return result  # keys: transit_analysis, transit_options

    def recommendation_node(state: CommuteState) -> dict:
        with monitor.trace_agent("RecommendationAgent") as trace:
            result = rec_agent.run(state)
            trace.output_tokens = 400
        return result  # keys: recommendation, recommended_mode, estimated_duration

    def evaluator_node(state: CommuteState) -> dict:
        with monitor.trace_agent("EvaluatorAgent") as trace:
            recommendation = state.get("recommendation", "")
            query = state.get("masked_query", state.get("raw_query", ""))
            route_docs  = [r.get("summary", "") for r in state.get("route_options", [])]
            transit_docs = [t.get("summary", "") for t in state.get("transit_options", [])]
            eval_result = evaluator.evaluate(query, recommendation, route_docs + transit_docs)
            monitor.record_evaluation({
                "answer_relevancy": eval_result.answer_relevancy,
                "faithfulness":     eval_result.faithfulness,
                "completeness":     eval_result.completeness,
                "safety_score":     eval_result.safety_score,
                "overall_score":    eval_result.overall_score,
            })
            trace.output_tokens = 50
        return {
            "evaluation_scores": {
                "answer_relevancy": eval_result.answer_relevancy,
                "faithfulness":     eval_result.faithfulness,
                "completeness":     eval_result.completeness,
                "safety_score":     eval_result.safety_score,
                "overall_score":    eval_result.overall_score,
            },
            "evaluation_summary": eval_result.feedback,
        }

    def error_node(state: CommuteState) -> dict:
        logger.warning("Pipeline terminated early: %s", state.get("error"))
        return {}

    # ── Routing conditions ────────────────────────────────────

    def after_pii(state: CommuteState) -> Literal["content_filter", "error"]:
        return "error" if state.get("pii_blocked") else "content_filter"

    def after_content_filter(state: CommuteState) -> Literal["intent_parser", "error"]:
        return "error" if state.get("content_blocked") else "intent_parser"

    # ── Build graph ───────────────────────────────────────────

    graph = StateGraph(CommuteState)

    graph.add_node("pii_guardian", pii_guardian_node)
    graph.add_node("content_filter", content_filter_node)
    graph.add_node("intent_parser", intent_parser_node)
    graph.add_node("route_planner", route_planner_node)
    graph.add_node("traffic_analyst", traffic_analyst_node)
    graph.add_node("weather_analyst", weather_analyst_node)
    graph.add_node("transit_advisor", transit_advisor_node)
    graph.add_node("recommendation", recommendation_node)
    graph.add_node("evaluator", evaluator_node)
    graph.add_node("error", error_node)

    graph.add_edge(START, "pii_guardian")
    graph.add_conditional_edges("pii_guardian", after_pii, {"content_filter": "content_filter", "error": "error"})
    graph.add_conditional_edges("content_filter", after_content_filter, {"intent_parser": "intent_parser", "error": "error"})
    graph.add_edge("intent_parser", "route_planner")
    graph.add_edge("intent_parser", "traffic_analyst")
    graph.add_edge("intent_parser", "weather_analyst")
    graph.add_edge("intent_parser", "transit_advisor")
    graph.add_edge("route_planner", "recommendation")
    graph.add_edge("traffic_analyst", "recommendation")
    graph.add_edge("weather_analyst", "recommendation")
    graph.add_edge("transit_advisor", "recommendation")
    graph.add_edge("recommendation", "evaluator")
    graph.add_edge("evaluator", END)
    graph.add_edge("error", END)

    return graph.compile()


def build_streaming_pipeline(
    use_mlflow: bool = False,
    use_langsmith: bool = False,
    use_deepeval: bool = False,
    use_compression: bool = False,
    compression_ratio: float | None = None,
) -> tuple:
    """
    Returns (analysis_graph, rec_agent, evaluator).

    analysis_graph runs: pii_guardian → content_filter → intent_parser →
        [route_planner, traffic_analyst, weather_analyst, transit_advisor] → END

    Call rec_agent.run_stream(state) to stream the recommendation, then
    evaluator.evaluate(...) for quality scores.
    """
    vector_store   = ChromaVectorStore(persist_dir=CHROMA_PERSIST_DIR)
    pii_detector   = PIIDetector()
    content_filter = ContentFilter()
    monitor        = MonitoringManager(use_mlflow=use_mlflow, use_langsmith=use_langsmith)
    evaluator      = CommuteEvaluator(use_deepeval_api=use_deepeval)

    compressor  = PromptCompressor(compression_ratio=compression_ratio or COMPRESSION_RATIO) if use_compression else None
    route_agent   = RoutePlannerAgent(vector_store, compressor=compressor)
    traffic_agent = TrafficAnalystAgent(vector_store, compressor=compressor)
    weather_agent = WeatherAnalystAgent()
    transit_agent = TransitAdvisorAgent(vector_store, compressor=compressor)
    rec_agent     = RecommendationAgent(compressor=compressor)

    def pii_guardian_node(state: CommuteState) -> dict:
        raw    = state["raw_query"]
        result = pii_detector.detect_and_mask(raw)
        monitor.record_pii(result.risk_level, result.has_pii)
        blocked = not pii_detector.is_safe_to_process(result)
        updates: dict = {
            "masked_query":  result.masked_text,
            "pii_entities":  [{"type": e.entity_type, "redacted": e.redacted} for e in result.entities],
            "pii_risk_level": result.risk_level,
            "pii_blocked":   blocked,
        }
        if blocked:
            updates["error"] = (
                "Input blocked: HIGH-risk PII detected (SSN, credit card, passport). "
                "Please remove sensitive information and try again."
            )
        return updates

    def content_filter_node(state: CommuteState) -> dict:
        if state.get("pii_blocked"):
            return {}
        query  = state.get("masked_query", state["raw_query"])
        result = content_filter.check(query)
        updates: dict = {"content_blocked": result.is_blocked, "is_relevant": result.is_relevant}
        if result.is_blocked:
            updates["error"] = f"Query blocked: {result.reason}"
        elif not result.is_relevant:
            updates["error"] = result.reason
            updates["content_blocked"] = True
        return updates

    def intent_parser_node(state: CommuteState) -> dict:
        query  = state.get("masked_query", state["raw_query"])
        origin, destination = _extract_locations(query)
        prefs  = dict(state.get("user_preferences", {}))
        ql     = query.lower()
        if any(w in ql for w in ["cheap", "cheapest", "low cost", "budget"]):
            prefs["priority"] = "cost"
        elif any(w in ql for w in ["fast", "fastest", "quick", "urgent"]):
            prefs["priority"] = "speed"
        elif any(w in ql for w in ["green", "eco", "environment", "sustainable"]):
            prefs["priority"] = "eco"
        else:
            prefs["priority"] = "balanced"
        return {"origin": origin, "destination": destination, "user_preferences": prefs}

    def route_planner_node(state: CommuteState) -> dict:
        with monitor.trace_agent("RoutePlannerAgent") as trace:
            result = route_agent.run(state.get("masked_query",""), state.get("origin","Central Station"), state.get("destination","Tech Park"))
            trace.output_tokens = 200
        return result

    def traffic_analyst_node(state: CommuteState) -> dict:
        with monitor.trace_agent("TrafficAnalystAgent") as trace:
            result = traffic_agent.run(state.get("masked_query",""), state.get("origin",""), state.get("destination",""))
            trace.output_tokens = 150
        return result

    def weather_analyst_node(state: CommuteState) -> dict:
        with monitor.trace_agent("WeatherAnalystAgent") as trace:
            result = weather_agent.run(state.get("masked_query",""), state.get("origin",""), state.get("destination",""))
            trace.output_tokens = 120
        return result

    def transit_advisor_node(state: CommuteState) -> dict:
        with monitor.trace_agent("TransitAdvisorAgent") as trace:
            result = transit_agent.run(state.get("masked_query",""), state.get("origin",""), state.get("destination",""))
            trace.output_tokens = 180
        return result

    def error_node(state: CommuteState) -> dict:
        logger.warning("Analysis pipeline terminated early: %s", state.get("error"))
        return {}

    def after_pii(state: CommuteState) -> Literal["content_filter", "error"]:
        return "error" if state.get("pii_blocked") else "content_filter"

    def after_content_filter(state: CommuteState) -> Literal["intent_parser", "error"]:
        return "error" if state.get("content_blocked") else "intent_parser"

    graph = StateGraph(CommuteState)
    graph.add_node("pii_guardian",    pii_guardian_node)
    graph.add_node("content_filter",  content_filter_node)
    graph.add_node("intent_parser",   intent_parser_node)
    graph.add_node("route_planner",   route_planner_node)
    graph.add_node("traffic_analyst", traffic_analyst_node)
    graph.add_node("weather_analyst", weather_analyst_node)
    graph.add_node("transit_advisor", transit_advisor_node)
    graph.add_node("error",           error_node)

    graph.add_edge(START, "pii_guardian")
    graph.add_conditional_edges("pii_guardian",    after_pii,            {"content_filter": "content_filter", "error": "error"})
    graph.add_conditional_edges("content_filter",  after_content_filter, {"intent_parser":  "intent_parser",  "error": "error"})
    graph.add_edge("intent_parser",   "route_planner")
    graph.add_edge("intent_parser",   "traffic_analyst")
    graph.add_edge("intent_parser",   "weather_analyst")
    graph.add_edge("intent_parser",   "transit_advisor")
    graph.add_edge("route_planner",   END)
    graph.add_edge("traffic_analyst", END)
    graph.add_edge("weather_analyst", END)
    graph.add_edge("transit_advisor", END)
    graph.add_edge("error",           END)

    return graph.compile(), rec_agent, evaluator


def run_commute_query(query: str, preferences: dict | None = None, **kwargs) -> CommuteState:
    """Convenience wrapper: builds graph and runs a single query."""
    graph = build_commute_graph(**kwargs)
    initial_state: CommuteState = {
        "raw_query": query,
        "session_id": str(uuid.uuid4())[:8],
        "user_preferences": preferences or {},
    }
    return graph.invoke(initial_state)
