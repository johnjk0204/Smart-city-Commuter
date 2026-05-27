import logging
from langchain_core.messages import HumanMessage, SystemMessage
from vectorstore import ChromaVectorStore
from config import build_llm
from utils import PromptCompressor

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are the Transit Advisor Agent for Metro City's Smart Commute Planner.

Your role is to:
- Provide detailed public transit schedules and service information
- Identify the best transit connections for a journey
- Highlight service disruptions, delays, or reduced frequency
- Compare transit options (metro vs bus vs bike share)
- Give platform/stop-level details where available

Be specific about line names, stop names, frequency, and operating hours.
Format transit options clearly with times and costs."""


class TransitAdvisorAgent:
    def __init__(self, vector_store: ChromaVectorStore, compressor: PromptCompressor | None = None):
        self._store = vector_store
        self._compressor = compressor
        self._llm = build_llm()

    def run(self, query: str, origin: str, destination: str) -> dict:
        transit_docs = self._store.search_transit(f"{origin} {destination} transit", n=4)
        route_docs = self._store.search_routes(f"from {origin} to {destination}", n=2)

        raw_transit = "\n".join(f"- {d['document']}" for d in transit_docs) or "General transit information applies."
        raw_route   = "\n".join(f"- {r['document']}" for r in route_docs) or ""
        transit_context = self._compressor.compress(query, raw_transit, agent="TransitAdvisor")[0] if self._compressor else raw_transit
        route_context   = self._compressor.compress(query, raw_route,   agent="TransitAdvisor")[0] if (self._compressor and raw_route) else raw_route

        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=f"""Query: {query}
Origin: {origin}
Destination: {destination}

Transit System Information:
{transit_context}

Route Information:
{route_context}

Provide specific transit options with line names, frequencies, estimated times, and costs."""),
        ]

        response = self._llm.invoke(messages)

        transit_options = [
            {
                "type": d["metadata"].get("type", "transit"),
                "frequency_min": d["metadata"].get("frequency_min", "N/A"),
                "summary": d["document"][:150],
            }
            for d in transit_docs
        ]

        logger.info("Transit advisor completed for %s → %s", origin, destination)
        return {
            "transit_analysis": response.content,
            "transit_options": transit_options,
        }
