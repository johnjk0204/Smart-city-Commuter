import json
import logging
from pathlib import Path
from .chroma_client import ChromaVectorStore, COLLECTION_ROUTES, COLLECTION_LANDMARKS, COLLECTION_TRANSIT, COLLECTION_TRAFFIC

logger = logging.getLogger(__name__)
DATA_DIR = Path(__file__).parent.parent / "data"

_TRAFFIC_PATTERNS = [
    {
        "id": "TP001",
        "pattern": "Morning peak hour rush (07:00-09:00): Major congestion on Central Station routes. Expect 30-50% longer journey times. Red Line and Blue Line at capacity. City Express 101 bus running 10-15 min delays.",
        "meta": {"period": "morning_peak", "severity": "HIGH", "hours": "07:00-09:00"},
    },
    {
        "id": "TP002",
        "pattern": "Evening peak hour rush (17:00-19:00): Heavy outbound traffic from Financial District and Tech Park. Metro lines crowded. Recommend bike or walk for short distances under 2km.",
        "meta": {"period": "evening_peak", "severity": "HIGH", "hours": "17:00-19:00"},
    },
    {
        "id": "TP003",
        "pattern": "Off-peak midday (10:00-16:00): Normal traffic conditions. Metro frequency unchanged. Bus routes running on schedule. Ideal time for non-urgent commutes.",
        "meta": {"period": "off_peak", "severity": "LOW", "hours": "10:00-16:00"},
    },
    {
        "id": "TP004",
        "pattern": "Weekend morning (09:00-12:00): Light traffic overall. Metro running reduced frequency (every 10-12 min). Shopping Mall and Sports Arena routes busier from 11:00.",
        "meta": {"period": "weekend_morning", "severity": "LOW", "hours": "09:00-12:00"},
    },
    {
        "id": "TP005",
        "pattern": "Post-event congestion at Sports Arena: After major events (concerts, basketball games), Green Line experiences 2x normal load. Surge pricing for taxis. Plan for 45+ min delays if using transit.",
        "meta": {"period": "post_event", "severity": "VERY_HIGH", "hours": "variable"},
    },
    {
        "id": "TP006",
        "pattern": "Airport route peak: Early morning (04:00-07:00) and late evening (20:00-23:00) see peak airport travel. Red Line Airport Shuttle fully booked. Book airport shuttle in advance.",
        "meta": {"period": "airport_peak", "severity": "MEDIUM", "hours": "04:00-07:00, 20:00-23:00"},
    },
    {
        "id": "TP007",
        "pattern": "Industrial Zone early shift (05:00-06:30): Red Line sees unusual early morning demand. Workers from North Suburbs commuting to Industrial Zone. Trains may be standing-room only.",
        "meta": {"period": "early_industrial", "severity": "MEDIUM", "hours": "05:00-06:30"},
    },
    {
        "id": "TP008",
        "pattern": "Rainy day impact: During heavy rain, bike share usage drops 80%. Bus delays increase by 15-25%. Metro is the most weather-resilient option. Riverside Park bike path becomes slippery and unsafe.",
        "meta": {"period": "rainy_day", "severity": "MEDIUM", "hours": "all day"},
    },
]


def seed_routes(store: ChromaVectorStore):
    with open(DATA_DIR / "city_routes.json") as f:
        routes = json.load(f)

    docs, ids, metas = [], [], []
    for r in routes:
        modes_str = ", ".join(r["modes"])
        options_str = " | ".join(
            f"{o['mode']} ({o['duration_min']}min, ${o['cost']})" for o in r["transit_options"]
        )
        doc = (
            f"Route from {r['from']} to {r['to']}. Distance: {r['distance_km']}km. "
            f"Available modes: {modes_str}. "
            f"Options: {options_str}. "
            f"Peak delay factor: {r['peak_delay_factor']}x. "
            f"{r['description']}"
        )
        docs.append(doc)
        ids.append(r["id"])
        metas.append({"from": r["from"], "to": r["to"], "recommended_mode": r["recommended_mode"]})

    store.upsert(COLLECTION_ROUTES, docs, ids, metas)
    logger.info("Seeded %d routes", len(docs))


def seed_landmarks(store: ChromaVectorStore):
    with open(DATA_DIR / "landmarks.json") as f:
        landmarks = json.load(f)

    docs = [f"{l['name']} ({l['type']}): {l['description']}" for l in landmarks]
    ids = [l["id"] for l in landmarks]
    metas = [{"name": l["name"], "type": l["type"], "lat": l["lat"], "lng": l["lng"]} for l in landmarks]
    store.upsert(COLLECTION_LANDMARKS, docs, ids, metas)
    logger.info("Seeded %d landmarks", len(docs))


def seed_transit(store: ChromaVectorStore):
    with open(DATA_DIR / "transit_stops.json") as f:
        transit = json.load(f)

    docs, ids, metas = [], [], []

    for line in transit["metro_lines"]:
        stops = ", ".join(s["name"] for s in line["stops"])
        doc = (
            f"{line['name']} Metro Line ({line['id']}): Runs every {line['frequency_minutes']} minutes. "
            f"Operating hours: {line['operating_hours']}. Stops: {stops}."
        )
        docs.append(doc)
        ids.append(line["id"])
        metas.append({"type": "metro", "frequency_min": line["frequency_minutes"]})

    for bus in transit["bus_routes"]:
        stops = " → ".join(bus["stops"])
        doc = (
            f"{bus['name']} ({bus['id']}, {bus['type']}): Runs every {bus['frequency_minutes']} minutes. "
            f"Operating hours: {bus['operating_hours']}. Route: {stops}."
        )
        docs.append(doc)
        ids.append(bus["id"])
        metas.append({"type": bus["type"], "frequency_min": bus["frequency_minutes"]})

    for bs in transit["bike_share_stations"]:
        doc = f"Bike share station at {bs['name']} with {bs['docks']} docks."
        docs.append(doc)
        ids.append(bs["id"])
        metas.append({"type": "bike_share", "docks": bs["docks"]})

    store.upsert(COLLECTION_TRANSIT, docs, ids, metas)
    logger.info("Seeded %d transit entries", len(docs))


def seed_traffic(store: ChromaVectorStore):
    docs = [p["pattern"] for p in _TRAFFIC_PATTERNS]
    ids = [p["id"] for p in _TRAFFIC_PATTERNS]
    metas = [p["meta"] for p in _TRAFFIC_PATTERNS]
    store.upsert(COLLECTION_TRAFFIC, docs, ids, metas)
    logger.info("Seeded %d traffic patterns", len(docs))


def seed_all_collections(store: ChromaVectorStore):
    if store.is_seeded():
        logger.info("ChromaDB already seeded — skipping")
        return
    logger.info("Seeding ChromaDB collections...")
    seed_routes(store)
    seed_landmarks(store)
    seed_transit(store)
    seed_traffic(store)
    logger.info("ChromaDB seeding complete")
