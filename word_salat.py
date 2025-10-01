#!/usr/bin/env python3
"""Word salat generator.

This module scrambles the interior letters of each word while keeping the
first and last characters intact. It can be used as a library or executed as a
command-line utility.
"""
from __future__ import annotations

import argparse
import os
import random
import re
import sys
from difflib import SequenceMatcher
from typing import Iterable, Iterator, Optional

# Matches words made of alphabetic characters. Accented Latin letters are
# included to support a broader set of natural languages. Hyphenated and
# apostrophized compounds are handled by scrambling each alphabetic segment
# independently, which keeps punctuation in place.
_WORD_PATTERN = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+")


def _attempt_shuffle(
    chars: list[str],
    indices: list[int],
    rng: random.Random,
    max_attempts: int = 8,
) -> list[str]:
    """Shuffle *chars* at the provided indices, keeping the rest fixed.

    Returns the updated list. If all shuffle attempts yield the original
    configuration (for example because the characters are identical), the
    original ordering is preserved.
    """

    if len(indices) <= 1:
        return chars

    original_chars = chars.copy()
    subset = [chars[i] for i in indices]

    if len(set(subset)) <= 1:
        return chars

    for _ in range(max_attempts):
        randomized = subset.copy()
        rng.shuffle(randomized)
        candidate = original_chars.copy()
        for idx, value in zip(indices, randomized):
            candidate[idx] = value
        if candidate != original_chars:
            chars[:] = candidate
            return chars

    chars[:] = original_chars
    return chars


def scramble_word(word: str, rng: Optional[random.Random] = None) -> str:
    """Scramble the *word* while keeping its first and last characters.

    Words of length three or fewer are returned unchanged. If *rng* is provided
    it will be used for shuffling; otherwise, :class:`random.Random` is used.
    """
    if len(word) <= 3:
        return word

    if rng is None:
        rng = random.Random()

    chars = list(word)
    indices = list(range(1, len(word) - 1))

    if len(word) % 2 == 1:
        middle_index = len(word) // 2
        if middle_index in indices:
            indices.remove(middle_index)

    shuffled_chars = _attempt_shuffle(chars, indices, rng)
    return ''.join(shuffled_chars)


def _scramble_segments(text: str, rng: random.Random) -> Iterator[str]:
    """Yield the scrambled text segments, preserving non-word characters."""
    last_index = 0
    for match in _WORD_PATTERN.finditer(text):
        start, end = match.span()
        if start > last_index:
            yield text[last_index:start]
        yield scramble_word(match.group(), rng)
        last_index = end

    if last_index < len(text):
        yield text[last_index:]


def scramble_text(text: str, seed: Optional[int] = None) -> str:
    """Return *text* with each word scrambled.

    :param text: Input text to transform.
    :param seed: Optional seed for deterministic output.
    """
    rng = random.Random(seed)
    return ''.join(_scramble_segments(text, rng))


def score_decoded_text(
    original: str,
    decoded: str,
    *,
    ignore_case: bool = True,
    collapse_whitespace: bool = True,
    method: str = "hybrid",
    name: Optional[str] = None,
    source_label: str = "custom",
    results_file: str = "results/decoded_scores.md",
) -> float:
    """Score how well *decoded* matches *original*.

    The score is a similarity ratio between 0 and 1, where 1 represents an
    exact match. By default the comparison is case-insensitive and treats any
    run of whitespace as a single space; disable these normalizations by
    setting the corresponding keyword arguments to ``False``.

        ``method`` selects the similarity heuristic:

    * ``"char"`` — character-level comparison using :class:`difflib.SequenceMatcher`.
    * ``"word"`` — order-aware word-level comparison.
    * ``"token_set"`` — Jaccard similarity on unique words (order ignored).
        * ``"hybrid"`` (default) — average of the available metrics, providing a
            balanced view that is resilient to whitespace and minor ordering issues.

        If *name* is provided, the score is automatically appended to
        ``results/decoded_scores.md`` (or the path supplied via *results_file*),
        using *source_label* to identify the evaluated text.
    """

    def normalize(text: str) -> str:
        processed = text
        if collapse_whitespace:
            processed = ' '.join(processed.split())
        if ignore_case:
            processed = processed.lower()
        return processed

    original_norm = normalize(original)
    decoded_norm = normalize(decoded)
    char_ratio = SequenceMatcher(None, original_norm, decoded_norm).ratio()

    words_original = _WORD_PATTERN.findall(original_norm)
    words_decoded = _WORD_PATTERN.findall(decoded_norm)

    word_ratio: Optional[float]
    if not words_original and not words_decoded:
        word_ratio = 1.0
    elif not words_original or not words_decoded:
        word_ratio = 0.0
    else:
        word_ratio = SequenceMatcher(None, words_original, words_decoded).ratio()

    if words_original or words_decoded:
        union = set(words_original) | set(words_decoded)
        if union:
            intersection = set(words_original) & set(words_decoded)
            token_set_ratio = len(intersection) / len(union)
        else:
            token_set_ratio = 1.0
    else:
        token_set_ratio = 1.0

    method_normalized = method.lower()
    if method_normalized == "char":
        score = char_ratio
    elif method_normalized == "word":
        score = word_ratio if word_ratio is not None else char_ratio
    elif method_normalized == "token_set":
        score = token_set_ratio
    elif method_normalized == "hybrid":
        components = [char_ratio]
        if word_ratio is not None:
            components.append(word_ratio)
        components.append(token_set_ratio)
        score = sum(components) / len(components)
    else:
        raise ValueError(f"Unsupported scoring method: {method}")

    if name:
        _log_decoding_score(
            model_name=name,
            source_label=source_label,
            method=method_normalized,
            score=score,
            results_file=results_file,
        )

    return score


def _log_decoding_score(
    *,
    model_name: str,
    source_label: str,
    method: str,
    score: float,
    results_file: str,
) -> None:
    """Append the score to the results markdown table, creating it if needed."""

    header = (
        "# Decoding Evaluations\n\n"
        "| Model             | Source Text | Method      | Score  | Notes |\n"
        "|-------------------|-------------|-------------|--------|-------|\n"
    )
    row = (
        f"| {model_name} | `{source_label}` | `{method}` | {score:.4f} | Auto-logged via score_decoded_text. |\n"
    )

    results_path = os.path.abspath(results_file)
    os.makedirs(os.path.dirname(results_path), exist_ok=True)

    if not os.path.exists(results_path):
        with open(results_path, "w", encoding="utf-8") as fh:
            fh.write(header)
            fh.write(row)
        return

    with open(results_path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    insertion_index = None
    for idx, line in enumerate(lines):
        if line.startswith("- "):
            insertion_index = idx
            break

    if insertion_index is None:
        lines.append(row)
    else:
        lines.insert(insertion_index, row)

    with open(results_path, "w", encoding="utf-8") as fh:
        fh.writelines(lines)


def parse_arguments(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Scramble the interior characters of each word while keeping the borders intact."
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Text to scramble. If omitted, the program reads from standard input.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for reproducible output.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> None:
    """CLI entry point."""
    args = parse_arguments(argv)

    if args.text is None:
        text = sys.stdin.read()
        if not text:
            raise SystemExit("Provide text as an argument or via standard input.")
    else:
        text = args.text

    scrambled = scramble_text(text, seed=args.seed)
    print(scrambled)


if __name__ == "__main__":
    main()
