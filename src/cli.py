"""Command-line interface for word-salat.

This module provides a comprehensive CLI with subcommands for scrambling text,
scoring decoded attempts, and running batch evaluations.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

from src.core import scramble_text
from src.scoring import (
    ScoreResult,
    batch_evaluate,
    compute_detailed_score,
    generate_leaderboard,
)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="word-salat",
        description="Scramble text while keeping first and last letters intact.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  word-salat scramble "Hello World"
  word-salat scramble -i input.txt -o output.txt --seed 42
  word-salat score -o original.txt -d decoded.txt
  word-salat evaluate -o original.txt -d decoded_dir/ --format json
        """,
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 2.0.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scramble subcommand
    scramble_parser = subparsers.add_parser(
        "scramble",
        help="Scramble text",
        description="Scramble the interior letters of each word.",
    )
    scramble_parser.add_argument(
        "text",
        nargs="?",
        help="Text to scramble. If omitted, reads from --input or stdin.",
    )
    scramble_parser.add_argument(
        "-i",
        "--input",
        type=Path,
        help="Input file to read text from.",
    )
    scramble_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file to write scrambled text to.",
    )
    scramble_parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducible output.",
    )
    scramble_parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress output (useful with --output).",
    )

    # Score subcommand
    score_parser = subparsers.add_parser(
        "score",
        help="Score a decoded text",
        description="Calculate similarity between original and decoded text.",
    )
    score_parser.add_argument(
        "-o",
        "--original",
        type=Path,
        required=True,
        help="Path to the original unscrambled text file.",
    )
    score_parser.add_argument(
        "-d",
        "--decoded",
        type=Path,
        required=True,
        help="Path to the decoded text file.",
    )
    score_parser.add_argument(
        "-m",
        "--method",
        choices=["char", "word", "token_set", "hybrid"],
        default="hybrid",
        help="Scoring method (default: hybrid).",
    )
    score_parser.add_argument(
        "-n",
        "--name",
        help="Model name (logs result if provided).",
    )
    score_parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text).",
    )
    score_parser.add_argument(
        "--results-file",
        type=Path,
        default=Path("results/decoded_scores.md"),
        help="Results file for logging.",
    )

    # Evaluate subcommand (batch)
    eval_parser = subparsers.add_parser(
        "evaluate",
        help="Batch evaluate decoded files",
        description="Evaluate all decoded files in a directory.",
    )
    eval_parser.add_argument(
        "-o",
        "--original",
        type=Path,
        required=True,
        help="Path to the original unscrambled text file.",
    )
    eval_parser.add_argument(
        "-d",
        "--decoded-dir",
        type=Path,
        required=True,
        help="Directory containing decoded text files.",
    )
    eval_parser.add_argument(
        "-m",
        "--method",
        choices=["char", "word", "token_set", "hybrid"],
        default="hybrid",
        help="Scoring method (default: hybrid).",
    )
    eval_parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="markdown",
        help="Output format (default: markdown).",
    )
    eval_parser.add_argument(
        "--no-log",
        action="store_true",
        help="Don't log results to file.",
    )
    eval_parser.add_argument(
        "--results-file",
        type=Path,
        default=Path("results/decoded_scores.md"),
        help="Results file for logging.",
    )

    return parser


def cmd_scramble(args: argparse.Namespace) -> int:
    """Handle the scramble subcommand."""
    # Determine input source
    if args.text:
        text = args.text
    elif args.input:
        if not args.input.exists():
            print(f"Error: Input file not found: {args.input}", file=sys.stderr)
            return 1
        text = args.input.read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()
        if not text:
            print("Error: No input provided.", file=sys.stderr)
            return 1

    # Scramble
    scrambled = scramble_text(text, seed=args.seed)

    # Output
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(scrambled, encoding="utf-8")

    if not args.quiet:
        print(scrambled)

    return 0


def cmd_score(args: argparse.Namespace) -> int:
    """Handle the score subcommand."""
    if not args.original.exists():
        print(f"Error: Original file not found: {args.original}", file=sys.stderr)
        return 1
    if not args.decoded.exists():
        print(f"Error: Decoded file not found: {args.decoded}", file=sys.stderr)
        return 1

    original_text = args.original.read_text(encoding="utf-8")
    decoded_text = args.decoded.read_text(encoding="utf-8")

    result = compute_detailed_score(
        original_text,
        decoded_text,
        method=args.method,
        name=args.name or args.decoded.stem,
        source_label=args.decoded.name,
    )

    # Log if name provided
    if args.name:
        from src.scoring import _log_decoding_score

        _log_decoding_score(result, results_file=str(args.results_file))

    # Format output
    output = format_score_result(result, args.format)
    print(output)
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    """Handle the evaluate subcommand."""
    try:
        results = batch_evaluate(
            args.original,
            args.decoded_dir,
            method=args.method,
            results_file=str(args.results_file),
            log_results=not args.no_log,
        )
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except NotADirectoryError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if not results:
        print("No decoded files found.", file=sys.stderr)
        return 1

    # Generate leaderboard
    output = generate_leaderboard(results, output_format=args.format)
    print(output)
    return 0


def format_score_result(result: ScoreResult, fmt: str) -> str:
    """Format a single score result."""
    if fmt == "json":
        return json.dumps(result.to_dict(), indent=2)
    if fmt == "markdown":
        lines = [
            "| Model | Source | Method | Score | Char | Word | Token |",
            "|-------|--------|--------|-------|------|------|-------|",
            result.to_markdown_row(),
        ]
        return "\n".join(lines)
    # text format
    return (
        f"Model: {result.model_name}\n"
        f"Source: {result.source_label}\n"
        f"Method: {result.method}\n"
        f"Score: {result.score:.4f} ({result.score:.2%})\n"
        f"  Char:      {result.char_score:.4f}\n"
        f"  Word:      {result.word_score:.4f}\n"
        f"  Token Set: {result.token_set_score:.4f}"
    )


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        # Legacy mode: direct text scrambling for backwards compatibility
        if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
            # Treat first arg as text to scramble
            text = " ".join(sys.argv[1:])
            print(scramble_text(text))
            return
        parser.print_help()
        sys.exit(0)

    handlers = {
        "scramble": cmd_scramble,
        "score": cmd_score,
        "evaluate": cmd_evaluate,
    }

    handler = handlers.get(args.command)
    if handler:
        sys.exit(handler(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
