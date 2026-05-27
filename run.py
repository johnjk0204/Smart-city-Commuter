#!/usr/bin/env python3
"""
CLI entry point for quick testing without the Streamlit UI.
Usage:  python run.py "How do I get from Central Station to Tech Park?"
"""
import sys
import logging
import json

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")

def main():
    from vectorstore import ChromaVectorStore, seed_all_collections
    from graph.commute_graph import run_commute_query
    from config import CHROMA_PERSIST_DIR

    # Seed knowledge base on first run
    store = ChromaVectorStore(persist_dir=CHROMA_PERSIST_DIR)
    seed_all_collections(store)

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else (
        "What is the fastest way to get from Central Station to Tech Park during morning rush hour?"
    )

    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}\n")

    result = run_commute_query(query)

    if result.get("error"):
        print(f"❌ Error: {result['error']}")
        return

    print(f"🏁 Route: {result.get('origin')} → {result.get('destination')}")
    print(f"🚇 Mode: {result.get('recommended_mode')}")
    print(f"⏱️  Est. Time: {result.get('estimated_duration')}")
    print(f"🚦 Traffic: {result.get('traffic_severity')}")
    print(f"⛅ Weather: {result.get('weather_impact')}")
    print(f"\n{'─'*60}")
    print("RECOMMENDATION:")
    print(result.get("recommendation", ""))

    scores = result.get("evaluation_scores", {})
    if scores:
        print(f"\n{'─'*60}")
        print("EVALUATION SCORES:")
        for k, v in scores.items():
            print(f"  {k}: {v*100:.1f}%")

    pii = result.get("pii_entities", [])
    if pii:
        print(f"\n{'─'*60}")
        print(f"PII DETECTED ({result.get('pii_risk_level')}):")
        for e in pii:
            print(f"  {e['type']} → {e['redacted']}")


if __name__ == "__main__":
    main()
