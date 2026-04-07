#!/usr/bin/env python3
"""
Provider Stats Generator

Aggregates real-world performance metrics from the benchmark leaderboard
and compares them against theoretical latency (Cold Start/TTFB pings).
"""

import sys
import csv
import time
from pathlib import Path
from collections import defaultdict
from statistics import median

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

def map_model_to_provider(model_name: str, type_str: str) -> str:
    """Very simple heuristic to map a model name to its provider."""
    model_name = model_name.lower()
    if type_str == "Local":
        return "Ollama (Local)"
    if "claude" in model_name:
        return "Anthropic"
    if "gpt" in model_name or "o1" in model_name or "o3" in model_name:
        return "OpenAI"
    if "gemini" in model_name:
        return "Google"
    if "grok" in model_name:
        return "x.AI"
    if "mistral" in model_name or "ministral" in model_name or "pixtral" in model_name:
        if type_str == "Commercial":
            return "Mistral AI"

    # Models often on Groq in our config
    if model_name in ["llama-3.3-70b-versatile", "llama-4-scout-17b-16e-instruct", "deepseek-r1-distill-llama-70b", "llama3-70b-8192"]:
        return "Groq"

    # Cloud models (often proxy via Ollama, DeepSeek API, MiniMax API, etc.)
    if "deepseek" in model_name and "cloud" in type_str.lower():
        return "DeepSeek API"
    if "minimax" in model_name:
        return "MiniMax API"
    if "qwen" in model_name and "cloud" in type_str.lower():
        return "Alibaba Cloud / DeepInv"

    if "cloud" in type_str.lower():
        return "Ollama Cloud"

    return "Other / Unknown"

def gather_historical_data():
    csv_file = Path("benchmark_scores/benchmark_leaderboard.csv")
    if not csv_file.exists():
        print("Leaderboard CSV not found.")
        return {}

    provider_stats = defaultdict(lambda: {
        "models": 0,
        "speeds_ts": [],
        "avg_times": [],
        "costs": []
    })

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            model = row.get("Model Name", "")
            mod_type = row.get("Type", "")
            provider = map_model_to_provider(model, mod_type)

            provider_stats[provider]["models"] += 1

            try:
                perf = float(row.get("Performance/s", 0) or 0)
                if perf > 0:
                    provider_stats[provider]["speeds_ts"].append(perf)
            except ValueError: pass

            try:
                avg_t = float(row.get("Avg Time (s)", 0) or 0)
                if avg_t > 0:
                    provider_stats[provider]["avg_times"].append(avg_t)
            except ValueError: pass

            try:
                cost = float(row.get("Cost per 1K (USD)", 0) or 0)
                if cost > 0:
                    provider_stats[provider]["costs"].append(cost)
            except ValueError: pass

    # Compute averages/medians
    results = {}
    for p, stats in provider_stats.items():
        results[p] = {
            "Models Tracked": stats["models"],
            "Median t/s": round(median(stats["speeds_ts"]), 2) if stats["speeds_ts"] else 0.0,
            "Median Avg Time (s)": round(median(stats["avg_times"]), 2) if stats["avg_times"] else 0.0,
            "Cost per 1K (median $)": round(median(stats["costs"]), 4) if stats["costs"] else 0.0
        }
    return results

class PingHandler:
    def __init__(self):
        self.first_token_time: float | None = None
        self.start_time: float | None = None
    def __call__(self, chunk: str):
        if self.first_token_time is None and self.start_time is not None:
            self.first_token_time = time.time() - self.start_time

def ping_providers():
    from utils.llm_client import LLMClient

    # We define a standard model for each provider to ping
    # Using small/fast models where possible
    models_to_ping = {
        "Anthropic": ("anthropic", "claude-3-haiku-20240307"),
        "OpenAI": ("openai", "gpt-4o-mini"),
        "Google": ("google", "gemini-2.5-flash"),
        "x.AI": ("xai", "grok-3-mini"),
        "Groq": ("groq", "meta-llama/llama-4-scout-17b-16e-instruct"),
        "Mistral AI": ("mistral", "mistral-large-latest"),
        "Ollama Cloud": ("ollama", "gemma3:27b-cloud")
    }

    print("\n--- Starting Active Provider Pings (Cold Start TTFB) ---\n")
    pings = {}
    client = LLMClient()

    for provider_name, (provider_id, model_id) in models_to_ping.items():
        print(f"Pinging {provider_name} ({model_id})...")
        results = []
        for _ in range(3):
            handler = PingHandler()
            handler.start_time = time.time()
            try:
                # We hide stdout for ping if possible, but stream_handler won't print by default
                # unless LLMClient enforces it. We can provide a clean stream_handler.
                res = client.query(
                    model=model_id,
                    prompt="Ping. Reply exactly with one word: 'Pong'.",
                    provider=provider_id,
                    temperature=0.1,
                    stream_handler=handler
                )
                if handler.first_token_time:
                    results.append(handler.first_token_time)
                elif handler.start_time is not None:
                    results.append(time.time() - handler.start_time)
            except Exception as e:
                print(f"  Error pinging {provider_name}: {e}")

        if results:
            avg_ping = sum(results) / len(results)
            pings[provider_name] = round(avg_ping * 1000) # in ms
            print(f"  -> Avg TTFB: {pings[provider_name]} ms")
        else:
            pings[provider_name] = None
            print(f"  -> Failed to ping {provider_name}")

    return pings

if __name__ == "__main__":
    print("Gathering Historical Data...")
    hist = gather_historical_data()

    pings = ping_providers()

    # Merge
    combined = []
    for prov, stats in hist.items():
        if stats["Models Tracked"] == 0:
            continue
        row = {
            "Provider": prov,
            "Models Tracked": stats["Models Tracked"],
            "Median t/s": stats["Median t/s"],
            "Median Avg Time (s)": stats["Median Avg Time (s)"],
            "Cost per 1K (median $)": stats["Cost per 1K (median $)"],
            "Active Ping TTFB (ms)": pings.get(prov, "N/A")
        }
        combined.append(row)

    # Sort by Ping TTFB if available, else by Time
    combined.sort(key=lambda x: (x["Active Ping TTFB (ms)"] if isinstance(x["Active Ping TTFB (ms)"], int) else 99999, x["Median Avg Time (s)"]))

    out_csv = Path("benchmark_scores/provider_leaderboard.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Provider", "Models Tracked", "Median t/s", "Median Avg Time (s)", "Cost per 1K (median $)", "Active Ping TTFB (ms)"])
        writer.writeheader()
        writer.writerows(combined)

    print(f"\nWritten provider stats to {out_csv}")
    print("\nPreview:")
    for c in combined:
        print(f" - {c['Provider']:<20}: Ping={c['Active Ping TTFB (ms)']}ms, t/s={c['Median t/s']}, Avg Time={c['Median Avg Time (s)']}s")
