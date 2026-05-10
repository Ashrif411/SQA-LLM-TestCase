from __future__ import annotations

import argparse
import json
import logging
import sys

from llm_sqa.config import ensure_project_directories
from llm_sqa.doctor import run_doctor
from llm_sqa.logging_config import configure_logging
from llm_sqa.pipeline import (
    enrich_cases,
    extract_all_metadata,
    generate_cases,
    review_cases,
    run_full_pipeline,
    seed_deterministic_final_cases,
)

logger = logging.getLogger(__name__)


def _print_json(data: object) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="llm-sqa",
        description="LLM-assisted reviewed test case generation and risk-based execution for web forms.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "doctor", help="Check Python imports, browser session, Ollama, and target reachability."
    )
    subparsers.add_parser("extract", help="Extract form metadata with Selenium and BeautifulSoup.")

    generate_parser = subparsers.add_parser("generate", help="Generate test cases.")
    generate_parser.add_argument(
        "--no-llm", action="store_true", help="Use deterministic fallback instead of Ollama."
    )

    review_parser = subparsers.add_parser("review", help="Review generated test cases.")
    review_parser.add_argument(
        "--no-llm", action="store_true", help="Use deterministic fallback instead of Ollama."
    )

    enrich_parser = subparsers.add_parser("enrich", help="Add severity and expected results.")
    enrich_parser.add_argument(
        "--no-llm", action="store_true", help="Use deterministic fallback instead of Ollama."
    )

    all_parser = subparsers.add_parser("all", help="Run the full pipeline.")
    all_parser.add_argument(
        "--no-llm", action="store_true", help="Use deterministic fallback instead of Ollama."
    )

    subparsers.add_parser(
        "seed", help="Create deterministic final test cases without browser or Ollama."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    ensure_project_directories()
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "doctor":
            _print_json(run_doctor())
        elif args.command == "extract":
            items = extract_all_metadata(use_browser=True)
            _print_json({"metadata_files_created": len(items)})
        elif args.command == "generate":
            cases = generate_cases(use_llm=not args.no_llm)
            _print_json({"generated_count": len(cases)})
        elif args.command == "review":
            accepted, rejected = review_cases(use_llm=not args.no_llm)
            _print_json({"accepted_count": len(accepted), "rejected_count": len(rejected)})
        elif args.command == "enrich":
            final_cases = enrich_cases(use_llm=not args.no_llm)
            _print_json({"final_count": len(final_cases)})
        elif args.command == "all":
            _print_json(run_full_pipeline(use_llm=not args.no_llm))
        elif args.command == "seed":
            seeded_cases = seed_deterministic_final_cases()
            _print_json({"final_count": len(seeded_cases)})
        else:
            parser.print_help()
            return 2
        return 0
    except Exception as exc:  # noqa: BLE001
        logger.exception("Command failed: %s", exc)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
