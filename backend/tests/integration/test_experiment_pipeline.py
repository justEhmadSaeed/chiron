"""
Experiment Pipeline — Manual Test Runner
=========================================
Usage:
    PYTHONPATH=src python tests/integration/test_experiment_pipeline.py
"""

import os
import sys
import json
import logging
import warnings

warnings.filterwarnings("ignore")

# Suppress noisy third-party loggers
for noisy in ["httpx", "httpcore", "pinecone", "google", "langchain", "urllib3"]:
    logging.getLogger(noisy).setLevel(logging.ERROR)

# Clean, minimal logger for this test
logging.basicConfig(
    level=logging.INFO,
    format="\033[90m%(asctime)s\033[0m  %(message)s",
    datefmt="%H:%M:%S",
)

# Patch the research_agent logger to use colours
research_logger = logging.getLogger("research_agent")
research_logger.propagate = False
_handler = logging.StreamHandler()
_handler.setFormatter(
    logging.Formatter("\033[90m%(asctime)s\033[0m  %(message)s", datefmt="%H:%M:%S")
)
research_logger.addHandler(_handler)
research_logger.setLevel(logging.INFO)

# Monkey-patch the RAG store_and_retrieve so we can surface confirmation to the user
import chiron_backend.agents.research.experiment_rag as _rag_module

_original_store_and_retrieve = _rag_module.store_and_retrieve

def _patched_store_and_retrieve(namespace, query_text, raw_search_results, top_k=3):
    chunks = _original_store_and_retrieve(namespace, query_text, raw_search_results, top_k)
    _sep = "\033[90m" + "─" * 60 + "\033[0m"
    print(f"\n{_sep}")
    print(f"  \033[96m[RAG]\033[0m Namespace : \033[1m{namespace}\033[0m")
    print(f"  \033[96m[RAG]\033[0m Indexed   : {len(raw_search_results)} Tavily results → {sum(1 for r in raw_search_results if r.get('content'))} with content")
    print(f"  \033[96m[RAG]\033[0m Retrieved : {len(chunks)} chunks")
    if chunks:
        preview = chunks[0][:120].replace("\n", " ")
        print(f"  \033[96m[RAG]\033[0m Top chunk : \033[93m{preview}…\033[0m")
    print(_sep)
    return chunks

_rag_module.store_and_retrieve = _patched_store_and_retrieve


def _section(title: str) -> None:
    bar = "═" * 60
    print(f"\n\033[1;92m{bar}\033[0m")
    print(f"  \033[1;92m{title}\033[0m")
    print(f"\033[1;92m{bar}\033[0m")


def _field(label: str, value) -> None:
    print(f"  \033[94m{label:<18}\033[0m {value}")


def main() -> None:
    _section("Experiment Design Pipeline — Test Runner")

    hypothesis = input("\n  Enter your hypothesis: ").strip()
    if not hypothesis:
        print("\033[91m[ERROR] Hypothesis cannot be empty.\033[0m")
        sys.exit(1)

    print(f"\n  Running pipeline for:\n  \033[93m{hypothesis}\033[0m\n")

    from chiron_backend.agents.research.experiment_pipeline import run_experiment_pipeline

    try:
        result = run_experiment_pipeline(hypothesis)
    except Exception as e:
        print(f"\n\033[91m[PIPELINE ERROR]\033[0m {e}")
        raise

    # ── Summary ────────────────────────────────────────────────────────────
    _section("Pipeline Result Summary")
    _field("Title",       result.get("title", "—"))
    _field("Question",    result.get("question", "—")[:80] + "…" if len(result.get("question","")) > 80 else result.get("question","—"))
    _field("Complexity",  result.get("complexity", "—"))
    _field("Team Size",   result.get("teamSize", "—"))
    _field("Total Weeks", result.get("totalWeeks", "—"))
    _field("Created At",  result.get("createdAt", "—"))

    protocol = result.get("protocol", [])
    materials = result.get("materials", [])
    timeline  = result.get("timeline", [])
    validation = result.get("validation", [])

    print()
    _field("Protocol phases",  len(protocol))
    _field("Materials (BOM)",  len(materials))
    _field("Timeline phases",  len(timeline))
    _field("Validation items", len(validation))

    budget = result.get("budget")
    if budget:
        _field("Budget total",  f"${budget.get('total', 0):,.2f}")

    # ── Full JSON dump ──────────────────────────────────────────────────────
    _section("Full JSON Output")
    print(json.dumps(result, indent=2))

    _section("Done")


if __name__ == "__main__":
    main()
