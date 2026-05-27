import logging
import random
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage
from vectorstore import ChromaVectorStore
from config import build_llm
from utils import PromptCompressor

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are the Traffic Analysis Agent for Metro City's Smart Commute Planner.

Your role is to:
- Assess current and predicted traffic conditions
- Identify congestion hotspots and bottlenecks
- Estimate delays and their impact on journey times
- Suggest traffic-avoidance strategies

Base your analysis on the retrieved traffic pattern data and current time of day.
Give a clear severity rating: LOW / MEDIUM / HIGH / VERY HIGH.
Always suggest at least one congestion-avoidance tip."""


def _get_simulated_conditions() -> dict:
    """Simulate real-time traffic conditions based on time of day."""
    hour = datetime.now().hour
    conditions = {
        "current_time": datetime.now().strftime("%H:%M"),
        "is_peak": hour in range(7, 10) or hour in range(17, 20),
        "is_weekend": datetime.now().weekday() >= 5,
    }

    if conditions["is_peak"]:
        conditions["congestion_level"] = random.choice(["HIGH", "VERY HIGH"])
        conditions["avg_delay_min"] = random.randint(10, 30)
        conditions["incidents"] = random.randint(0, 3)
    elif 10 <= hour <= 16:
        conditions["congestion_level"] = random.choice(["LOW", "MEDIUM"])
        conditions["avg_delay_min"] = random.randint(0, 8)
        conditions["incidents"] = random.randint(0, 1)
    else:
        conditions["congestion_level"] = "LOW"
        conditions["avg_delay_min"] = random.randint(0, 5)
        conditions["incidents"] = 0

    if conditions["is_weekend"]:
        conditions["congestion_level"] = "LOW"
        conditions["avg_delay_min"] = max(0, conditions["avg_delay_min"] - 5)

    return conditions


class TrafficAnalystAgent:
    def __init__(self, vector_store: ChromaVectorStore, compressor: PromptCompressor | None = None):
        self._store = vector_store
        self._compressor = compressor
        self._llm = build_llm()

    def run(self, query: str, origin: str, destination: str) -> dict:
        conditions = _get_simulated_conditions()
        traffic_docs = self._store.search_traffic(f"{origin} {destination} traffic", n=3)

        raw_context = "\n".join(f"- {d['document']}" for d in traffic_docs) or "General traffic patterns apply."
        context = self._compressor.compress(query, raw_context, agent="TrafficAnalyst")[0] if self._compressor else raw_context

        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=f"""Query: {query}
Route: {origin} → {destination}

Current Conditions:
- Time: {conditions['current_time']}
- Peak Hour: {conditions['is_peak']}
- Weekend: {conditions['is_weekend']}
- Congestion Level: {conditions['congestion_level']}
- Average Delay: {conditions['avg_delay_min']} minutes
- Active Incidents: {conditions['incidents']}

Traffic Pattern Knowledge:
{context}

Provide traffic analysis with severity rating and avoidance tips."""),
        ]

        response = self._llm.invoke(messages)
        logger.info("Traffic analyst completed | congestion=%s", conditions["congestion_level"])
        return {
            "traffic_analysis": response.content,
            "traffic_severity": conditions["congestion_level"],
        }
