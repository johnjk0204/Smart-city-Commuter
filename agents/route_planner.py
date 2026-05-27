import logging
from langchain_core.messages import HumanMessage, SystemMessage
from vectorstore import ChromaVectorStore
from config import build_llm
from utils import PromptCompressor

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are the Route Planning Agent for Metro City's Smart Commute Planner.

Your job is to analyze available routes between locations and recommend the best options based on:
- Distance and travel time
- Available transportation modes (metro, bus, bike, walk, taxi)
- Cost effectiveness
- Number of transfers/changes required

Use the retrieved route data to give specific, actionable route recommendations.
Always mention the top 2-3 options with estimated times and costs.
Be concise and structured in your response."""


class RoutePlannerAgent:
    def __init__(self, vector_store: ChromaVectorStore, compressor: PromptCompressor | None = None):
        self._store = vector_store
        self._compressor = compressor
        self._llm = build_llm()

    def run(self, query: str, origin: str, destination: str) -> dict:
        route_docs = self._store.search_routes(f"from {origin} to {destination}", n=3)
        landmark_docs = self._store.search_landmarks(f"{origin} {destination}", n=2)

        context = self._build_context(query, route_docs, landmark_docs)

        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=f"""Query: {query}

Origin: {origin}
Destination: {destination}

Retrieved Route Data:
{context}

Provide a structured route analysis with the best 2-3 options."""),
        ]

        response = self._llm.invoke(messages)
        analysis = response.content
        route_options = [
            {"source": r["metadata"].get("from", ""), "dest": r["metadata"].get("to", ""),
             "mode": r["metadata"].get("recommended_mode", ""), "summary": r["document"][:200]}
            for r in route_docs
        ]

        logger.info("Route planner completed for %s → %s", origin, destination)
        return {
            "route_analysis": analysis,
            "route_options": route_options,
        }

    def _build_context(self, query: str, route_docs: list, landmark_docs: list) -> str:
        parts = []
        if route_docs:
            raw = "\n".join(f"- {r['document']}" for r in route_docs)
            parts.append("Routes:\n" + (self._compressor.compress(query, raw, agent="RoutePlanner")[0] if self._compressor else raw))
        if landmark_docs:
            raw = "\n".join(f"- {l['document']}" for l in landmark_docs)
            parts.append("Landmarks:\n" + (self._compressor.compress(query, raw, agent="RoutePlanner")[0] if self._compressor else raw))
        return "\n\n".join(parts) if parts else "No specific route data found — providing general guidance."
