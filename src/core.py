"""Core scrambling functionality for word-salat.

This module contains the main text scrambling logic, preserving first and last
characters of each word while shuffling the interior letters.
"""

from __future__ import annotations

import random
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

# Constants
MAX_SHUFFLE_ATTEMPTS = 8
"""Maximum number of attempts to generate a different shuffle."""

# Matches words made of alphabetic characters. Accented Latin letters are
# included to support a broader set of natural languages. Hyphenated and
# apostrophized compounds are handled by scrambling each alphabetic segment
# independently, which keeps punctuation in place.
WORD_PATTERN = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+")


def _attempt_shuffle(
    chars: list[str],
    indices: list[int],
    rng: random.Random,
    max_attempts: int = MAX_SHUFFLE_ATTEMPTS,
) -> list[str]:
    """Shuffle *chars* at the provided indices, keeping the rest fixed.

    Returns the updated list. If all shuffle attempts yield the original
    configuration (for example because the characters are identical), the
    original ordering is preserved.

    Args:
        chars: List of characters to shuffle.
        indices: Indices of characters to shuffle.
        rng: Random number generator instance.
        max_attempts: Maximum shuffle attempts before giving up.

    Returns:
        The shuffled character list.
    """
    if len(indices) <= 1:
        return chars

    original_chars = chars.copy()
    subset = [chars[i] for i in indices]

    # If all characters are identical, no shuffle is possible
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


def scramble_word(word: str, rng: random.Random | None = None) -> str:
    """Scramble the *word* while keeping its first and last characters.

    Words of length three or fewer are returned unchanged. For odd-length words,
    the middle character is also preserved.

    Args:
        word: The word to scramble.
        rng: Optional random number generator for reproducible results.

    Returns:
        The scrambled word.

    Examples:
        >>> scramble_word("testing", random.Random(42))
        'tniestg'
        >>> scramble_word("the")
        'the'
    """
    if len(word) <= 3:
        return word

    if rng is None:
        rng = random.Random()

    chars = list(word)
    indices = list(range(1, len(word) - 1))

    # Preserve middle character for odd-length words
    if len(word) % 2 == 1:
        middle_index = len(word) // 2
        if middle_index in indices:
            indices.remove(middle_index)

    shuffled_chars = _attempt_shuffle(chars, indices, rng)
    return "".join(shuffled_chars)


def _scramble_segments(text: str, rng: random.Random) -> Iterator[str]:
    """Yield the scrambled text segments, preserving non-word characters.

    Args:
        text: The text to process.
        rng: Random number generator instance.

    Yields:
        Text segments (scrambled words and preserved non-word characters).
    """
    last_index = 0
    for match in WORD_PATTERN.finditer(text):
        start, end = match.span()
        if start > last_index:
            yield text[last_index:start]
        yield scramble_word(match.group(), rng)
        last_index = end

    if last_index < len(text):
        yield text[last_index:]


def scramble_text(text: str, seed: int | None = None) -> str:
    """Return *text* with each word scrambled.

    The first and last characters of each word are preserved, while the
    interior letters are shuffled. For odd-length words, the middle character
    is also preserved.

    Args:
        text: Input text to transform.
        seed: Optional seed for deterministic output.

    Returns:
        The scrambled text.

    Examples:
        >>> scramble_text("Hello World", seed=42)
        'Hlelo Wlrod'
    """
    rng = random.Random(seed)
    return "".join(_scramble_segments(text, rng))
