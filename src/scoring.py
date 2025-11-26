"""Scoring and evaluation functionality for word-salat.

This module provides tools to score decoded text attempts, run batch evaluations,
and generate leaderboards for AI model comparisons.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Literal

from src.core import WORD_PATTERN

# Type aliases
ScoringMethod = Literal["char", "word", "token_set", "hybrid"]


@dataclass
class ScoreResult:
    """Result of a text scoring operation."""

    model_name: str
    source_label: str
    method: ScoringMethod
    score: float
    char_score: float
    word_score: float
    token_set_score: float

    def to_dict(self) -> dict[str, str | float]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_markdown_row(self) -> str:
        """Format as a markdown table row."""
        return (
            f"| {self.model_name} | `{self.source_label}` | `{self.method}` | "
            f"{self.score:.4f} | {self.char_score:.4f} | {self.word_score:.4f} | "
            f"{self.token_set_score:.4f} |"
        )


def score_decoded_text(
    original: str,
    decoded: str,
    *,
    ignore_case: bool = True,
    collapse_whitespace: bool = True,
    method: ScoringMethod = "hybrid",
    name: str | None = None,
    source_label: str = "custom",
    results_file: str = "results/decoded_scores.md",
) -> float:
    """Score how well *decoded* matches *original*.

    The score is a similarity ratio between 0 and 1, where 1 represents an
    exact match. By default the comparison is case-insensitive and treats any
    run of whitespace as a single space.

    Args:
        original: The original unscrambled text.
        decoded: The decoded attempt to score.
        ignore_case: Whether to ignore case differences.
        collapse_whitespace: Whether to normalize whitespace.
        method: Scoring method to use:
            - "char": Character-level comparison
            - "word": Order-aware word-level comparison
            - "token_set": Jaccard similarity on unique words (order ignored)
            - "hybrid": Average of all metrics (default)
        name: If provided, logs the score to results_file.
        source_label: Label identifying the source text.
        results_file: Path to the results markdown file.

    Returns:
        Similarity score between 0 and 1.

    Raises:
        ValueError: If an unknown scoring method is specified.

    Examples:
        >>> score_decoded_text("Hello World", "Hello World")
        1.0
        >>> score_decoded_text("Hello World", "hello world")
        1.0
    """
    result = compute_detailed_score(
        original,
        decoded,
        ignore_case=ignore_case,
        collapse_whitespace=collapse_whitespace,
        method=method,
        name=name or "unnamed",
        source_label=source_label,
    )

    if name:
        _log_decoding_score(result, results_file=results_file)

    return result.score


def compute_detailed_score(
    original: str,
    decoded: str,
    *,
    ignore_case: bool = True,
    collapse_whitespace: bool = True,
    method: ScoringMethod = "hybrid",
    name: str = "unnamed",
    source_label: str = "custom",
) -> ScoreResult:
    """Compute detailed scoring metrics for decoded text.

    Unlike `score_decoded_text`, this function returns a `ScoreResult` object
    containing all individual metrics.

    Args:
        original: The original unscrambled text.
        decoded: The decoded attempt to score.
        ignore_case: Whether to ignore case differences.
        collapse_whitespace: Whether to normalize whitespace.
        method: Scoring method for the primary score.
        name: Model or attempt name.
        source_label: Label identifying the source text.

    Returns:
        ScoreResult with all metrics.
    """

    def normalize(text: str) -> str:
        processed = text
        if collapse_whitespace:
            processed = " ".join(processed.split())
        if ignore_case:
            processed = processed.lower()
        return processed

    original_norm = normalize(original)
    decoded_norm = normalize(decoded)

    # Character-level score
    char_score = SequenceMatcher(None, original_norm, decoded_norm).ratio()

    # Word-level score
    words_original = WORD_PATTERN.findall(original_norm)
    words_decoded = WORD_PATTERN.findall(decoded_norm)

    if not words_original and not words_decoded:
        word_score = 1.0
    elif not words_original or not words_decoded:
        word_score = 0.0
    else:
        word_score = SequenceMatcher(None, words_original, words_decoded).ratio()

    # Token set score (Jaccard similarity)
    if words_original or words_decoded:
        union = set(words_original) | set(words_decoded)
        if union:
            intersection = set(words_original) & set(words_decoded)
            token_set_score = len(intersection) / len(union)
        else:
            token_set_score = 1.0
    else:
        token_set_score = 1.0

    # Calculate final score based on method
    method_lower = method.lower()
    if method_lower == "char":
        final_score = char_score
    elif method_lower == "word":
        final_score = word_score
    elif method_lower == "token_set":
        final_score = token_set_score
    elif method_lower == "hybrid":
        final_score = (char_score + word_score + token_set_score) / 3
    else:
        raise ValueError(f"Unsupported scoring method: {method}")

    return ScoreResult(
        model_name=name,
        source_label=source_label,
        method=method_lower,  # type: ignore[arg-type]
        score=final_score,
        char_score=char_score,
        word_score=word_score,
        token_set_score=token_set_score,
    )


def _log_decoding_score(
    result: ScoreResult,
    *,
    results_file: str,
) -> None:
    """Append the score to the results markdown table, creating it if needed."""
    header = (
        "# Decoding Evaluations\n\n"
        "| Model | Source | Method | Score | Char | Word | Token |\n"
        "|-------|--------|--------|-------|------|------|-------|\n"
    )
    row = result.to_markdown_row() + "\n"

    results_path = Path(results_file).resolve()
    results_path.parent.mkdir(parents=True, exist_ok=True)

    if not results_path.exists():
        results_path.write_text(header + row, encoding="utf-8")
        return

    lines = results_path.read_text(encoding="utf-8").splitlines(keepends=True)

    # Find insertion point (before any notes/comments starting with "- ")
    insertion_index = None
    for idx, line in enumerate(lines):
        if line.startswith("- "):
            insertion_index = idx
            break

    if insertion_index is None:
        lines.append(row)
    else:
        lines.insert(insertion_index, row)

    results_path.write_text("".join(lines), encoding="utf-8")


def batch_evaluate(
    original_file: str | Path,
    decoded_dir: str | Path,
    *,
    method: ScoringMethod = "hybrid",
    results_file: str = "results/decoded_scores.md",
    log_results: bool = True,
) -> list[ScoreResult]:
    """Evaluate all decoded files in a directory against the original.

    Args:
        original_file: Path to the original unscrambled text file.
        decoded_dir: Directory containing decoded attempt files.
        method: Scoring method to use.
        results_file: Path to save results (if log_results is True).
        log_results: Whether to log results to the markdown file.

    Returns:
        List of ScoreResult objects, sorted by score (descending).

    Examples:
        >>> results = batch_evaluate("text.txt", "text_decoded/")
        >>> for r in results:
        ...     print(f"{r.model_name}: {r.score:.2%}")
    """
    original_path = Path(original_file)
    decoded_path = Path(decoded_dir)

    if not original_path.exists():
        raise FileNotFoundError(f"Original file not found: {original_path}")
    if not decoded_path.is_dir():
        raise NotADirectoryError(f"Decoded directory not found: {decoded_path}")

    original_text = original_path.read_text(encoding="utf-8")
    results: list[ScoreResult] = []

    for decoded_file in sorted(decoded_path.glob("*.txt")):
        decoded_text = decoded_file.read_text(encoding="utf-8")
        model_name = decoded_file.stem

        result = compute_detailed_score(
            original_text,
            decoded_text,
            method=method,
            name=model_name,
            source_label=decoded_file.name,
        )
        results.append(result)

        if log_results:
            _log_decoding_score(result, results_file=results_file)

    # Sort by score descending
    results.sort(key=lambda r: r.score, reverse=True)
    return results


def generate_leaderboard(
    results: list[ScoreResult],
    *,
    output_format: Literal["markdown", "json", "text"] = "markdown",
) -> str:
    """Generate a formatted leaderboard from scoring results.

    Args:
        results: List of ScoreResult objects.
        output_format: Output format ("markdown", "json", or "text").

    Returns:
        Formatted leaderboard string.

    Examples:
        >>> results = batch_evaluate("text.txt", "text_decoded/", log_results=False)
        >>> print(generate_leaderboard(results))
    """
    # Sort by score descending
    sorted_results = sorted(results, key=lambda r: r.score, reverse=True)

    if output_format == "json":
        return json.dumps([r.to_dict() for r in sorted_results], indent=2)

    if output_format == "text":
        lines = ["Decoding Leaderboard", "=" * 40]
        for i, r in enumerate(sorted_results, 1):
            lines.append(f"{i}. {r.model_name}: {r.score:.2%}")
        return "\n".join(lines)

    # markdown format
    lines = [
        "# Decoding Leaderboard",
        "",
        "| Rank | Model | Score | Char | Word | Token |",
        "|------|-------|-------|------|------|-------|",
    ]
    for i, r in enumerate(sorted_results, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, str(i))
        lines.append(
            f"| {medal} | {r.model_name} | {r.score:.2%} | "
            f"{r.char_score:.2%} | {r.word_score:.2%} | {r.token_set_score:.2%} |"
        )
    return "\n".join(lines)
