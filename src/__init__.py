"""Word Salat - Text scrambling with preserved word boundaries.

This package provides tools to scramble the interior letters of words while
keeping the first and last characters intact, reproducing the classic
"Cambridge University" effect.
"""

from __future__ import annotations

from src.core import scramble_text, scramble_word
from src.scoring import batch_evaluate, generate_leaderboard, score_decoded_text

__version__ = "2.0.0"
__all__ = [
    "__version__",
    "batch_evaluate",
    "generate_leaderboard",
    "score_decoded_text",
    "scramble_text",
    "scramble_word",
]


def main() -> None:
    """CLI entry point."""
    from src.cli import main as cli_main

    cli_main()
