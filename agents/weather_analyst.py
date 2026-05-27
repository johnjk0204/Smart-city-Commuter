import logging
import random
from langchain_core.messages import HumanMessage, SystemMessage
from config import build_llm

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are the Weather Analysis Agent for Metro City's Smart Commute Planner.

Your role is to:
- Assess how current weather conditions affect commute choices
- Flag weather-related safety concerns (heavy rain, storms, extreme heat/cold)
- Recommend mode adjustments based on weather (e.g., avoid cycling in rain)
- Estimate weather-related journey time impacts

Be practical and safety-focused. Give a weather impact rating: NONE / LOW / MEDIUM / HIGH."""

_WEATHER_SCENARIOS = [
    {"condition": "Clear skies", "temp_c": 22, "humidity_pct": 45, "wind_kmh": 10, "rain": False, "impact": "NONE"},
    {"condition": "Partly cloudy", "temp_c": 18, "humidity_pct": 60, "wind_kmh": 15, "rain": False, "impact": "NONE"},
    {"condition": "Light rain", "temp_c": 15, "humidity_pct": 80, "wind_kmh": 20, "rain": True, "impact": "LOW"},
    {"condition": "Heavy rain", "temp_c": 13, "humidity_pct": 92, "wind_kmh": 35, "rain": True, "impact": "HIGH"},
    {"condition": "Thunderstorm", "temp_c": 17, "humidity_pct": 95, "wind_kmh": 55, "rain": True, "impact": "HIGH"},
    {"condition": "Fog", "temp_c": 10, "humidity_pct": 98, "wind_kmh": 5, "rain": False, "impact": "MEDIUM"},
    {"condition": "Hot and sunny", "temp_c": 36, "humidity_pct": 35, "wind_kmh": 8, "rain": False, "impact": "LOW"},
    {"condition": "Cold and windy", "temp_c": 4, "humidity_pct": 55, "wind_kmh": 45, "rain": False, "impact": "MEDIUM"},
    {"condition": "Snowing", "temp_c": -2, "humidity_pct": 85, "wind_kmh": 25, "rain": False, "impact": "HIGH"},
]


def _get_simulated_weather() -> dict:
    return random.choice(_WEATHER_SCENARIOS)


class WeatherAnalystAgent:
    def __init__(self):
        self._llm = build_llm()

    def run(self, query: str, origin: str, destination: str) -> dict:
        weather = _get_simulated_weather()

        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=f"""Query: {query}
Route: {origin} → {destination}

Current Weather in Metro City:
- Condition: {weather['condition']}
- Temperature: {weather['temp_c']}°C
- Humidity: {weather['humidity_pct']}%
- Wind Speed: {weather['wind_kmh']} km/h
- Precipitation: {'Yes' if weather['rain'] else 'No'}

Analyze how this weather affects the commute and recommend mode adjustments if needed."""),
        ]

        response = self._llm.invoke(messages)
        logger.info("Weather analyst completed | condition=%s, impact=%s", weather["condition"], weather["impact"])
        return {
            "weather_analysis": response.content,
            "weather_impact": weather["impact"],
        }
