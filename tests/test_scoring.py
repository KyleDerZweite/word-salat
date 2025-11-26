"""Tests for word_salat scoring functionality."""

import json
import tempfile
import unittest
from pathlib import Path

from src import score_decoded_text
from src.scoring import (
    ScoreResult,
    batch_evaluate,
    compute_detailed_score,
    generate_leaderboard,
)


class ScoreDecodedTextTests(unittest.TestCase):
    """Tests for score_decoded_text function."""

    def test_score_decoded_text_perfect_match(self) -> None:
        original = "Dies ist ein Test."
        decoded = "Dies ist ein Test."
        self.assertAlmostEqual(score_decoded_text(original, decoded), 1.0)

    def test_score_decoded_text_ignores_case_and_whitespace(self) -> None:
        original = "Vertraue dem Prozess"
        decoded = "vertraue   dem\nprozeSS"
        self.assertAlmostEqual(score_decoded_text(original, decoded), 1.0)

    def test_score_decoded_text_penalizes_mismatches(self) -> None:
        original = "Künstliche Intelligenz"
        decoded = "Natürliche Intelligenz"
        score = score_decoded_text(original, decoded)
        self.assertLess(score, 1.0)

    def test_score_decoded_text_word_method(self) -> None:
        original = "Alpha Beta Gamma"
        decoded = "Alpha Beta Gamma"
        self.assertAlmostEqual(
            score_decoded_text(original, decoded, method="word"),
            1.0,
        )

    def test_score_decoded_text_token_set_handles_reordered_words(self) -> None:
        original = "Eins Zwei Drei Vier"
        decoded = "Vier Drei Zwei Eins"
        word_score = score_decoded_text(original, decoded, method="word")
        char_score = score_decoded_text(original, decoded, method="char")
        token_score = score_decoded_text(original, decoded, method="token_set")
        hybrid_score = score_decoded_text(original, decoded)

        self.assertLess(word_score, 1.0)
        self.assertLess(char_score, 1.0)
        self.assertAlmostEqual(token_score, 1.0)
        self.assertGreater(hybrid_score, char_score)

    def test_score_decoded_text_logs_when_name_supplied(self) -> None:
        original = "Alpha Beta"
        decoded = "Alpha Beta"

        with tempfile.TemporaryDirectory() as tmpdir:
            results_path = Path(tmpdir) / "scores.md"
            score = score_decoded_text(
                original,
                decoded,
                name="UnitTestModel",
                source_label="snippet.txt",
                results_file=str(results_path),
            )

            self.assertAlmostEqual(score, 1.0)
            contents = results_path.read_text(encoding="utf-8")

        self.assertIn("UnitTestModel", contents)
        self.assertIn("`snippet.txt`", contents)

    def test_score_decoded_text_rejects_unknown_method(self) -> None:
        with self.assertRaises(ValueError):
            score_decoded_text("a", "a", method="unknown")  # type: ignore[arg-type]

    def test_score_decoded_text_empty_strings(self) -> None:
        """Empty strings should give perfect score."""
        self.assertAlmostEqual(score_decoded_text("", ""), 1.0)

    def test_score_decoded_text_case_sensitive_option(self) -> None:
        """With ignore_case=False, case matters."""
        original = "Hello World"
        decoded = "hello world"
        score = score_decoded_text(original, decoded, ignore_case=False)
        self.assertLess(score, 1.0)

    def test_score_decoded_text_whitespace_sensitive_option(self) -> None:
        """With collapse_whitespace=False, whitespace matters."""
        original = "Hello World"
        decoded = "Hello  World"
        score = score_decoded_text(original, decoded, collapse_whitespace=False)
        self.assertLess(score, 1.0)


class ComputeDetailedScoreTests(unittest.TestCase):
    """Tests for compute_detailed_score function."""

    def test_returns_score_result(self) -> None:
        result = compute_detailed_score("Hello", "Hello", name="test")
        self.assertIsInstance(result, ScoreResult)
        self.assertEqual(result.model_name, "test")
        self.assertAlmostEqual(result.score, 1.0)

    def test_all_metrics_calculated(self) -> None:
        result = compute_detailed_score("Hello World", "Hello World")
        self.assertAlmostEqual(result.char_score, 1.0)
        self.assertAlmostEqual(result.word_score, 1.0)
        self.assertAlmostEqual(result.token_set_score, 1.0)

    def test_partial_match_metrics(self) -> None:
        result = compute_detailed_score("Hello World", "Hello Earth")
        self.assertLess(result.char_score, 1.0)
        self.assertLess(result.word_score, 1.0)
        self.assertLess(result.token_set_score, 1.0)


class ScoreResultTests(unittest.TestCase):
    """Tests for ScoreResult dataclass."""

    def test_to_dict(self) -> None:
        result = ScoreResult(
            model_name="test",
            source_label="test.txt",
            method="hybrid",
            score=0.95,
            char_score=0.90,
            word_score=0.95,
            token_set_score=1.0,
        )
        d = result.to_dict()
        self.assertEqual(d["model_name"], "test")
        self.assertEqual(d["score"], 0.95)

    def test_to_markdown_row(self) -> None:
        result = ScoreResult(
            model_name="test",
            source_label="test.txt",
            method="hybrid",
            score=0.95,
            char_score=0.90,
            word_score=0.95,
            token_set_score=1.0,
        )
        row = result.to_markdown_row()
        self.assertIn("test", row)
        self.assertIn("0.9500", row)
        self.assertIn("|", row)


class BatchEvaluateTests(unittest.TestCase):
    """Tests for batch_evaluate function."""

    def test_batch_evaluate_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create original file
            original = Path(tmpdir) / "original.txt"
            original.write_text("Hello World", encoding="utf-8")

            # Create decoded directory with files
            decoded_dir = Path(tmpdir) / "decoded"
            decoded_dir.mkdir()
            (decoded_dir / "model1.txt").write_text("Hello World", encoding="utf-8")
            (decoded_dir / "model2.txt").write_text("Hello Earth", encoding="utf-8")

            results = batch_evaluate(
                original,
                decoded_dir,
                log_results=False,
            )

            self.assertEqual(len(results), 2)
            # Results should be sorted by score descending
            self.assertGreaterEqual(results[0].score, results[1].score)

    def test_batch_evaluate_missing_original(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            decoded_dir = Path(tmpdir) / "decoded"
            decoded_dir.mkdir()

            with self.assertRaises(FileNotFoundError):
                batch_evaluate(
                    Path(tmpdir) / "nonexistent.txt",
                    decoded_dir,
                    log_results=False,
                )

    def test_batch_evaluate_missing_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            original = Path(tmpdir) / "original.txt"
            original.write_text("Hello", encoding="utf-8")

            with self.assertRaises(NotADirectoryError):
                batch_evaluate(
                    original,
                    Path(tmpdir) / "nonexistent",
                    log_results=False,
                )


class GenerateLeaderboardTests(unittest.TestCase):
    """Tests for generate_leaderboard function."""

    def setUp(self) -> None:
        self.results = [
            ScoreResult("model1", "f1.txt", "hybrid", 0.95, 0.9, 0.95, 1.0),
            ScoreResult("model2", "f2.txt", "hybrid", 0.85, 0.8, 0.85, 0.9),
            ScoreResult("model3", "f3.txt", "hybrid", 0.75, 0.7, 0.75, 0.8),
        ]

    def test_markdown_format(self) -> None:
        output = generate_leaderboard(self.results, output_format="markdown")
        self.assertIn("# Decoding Leaderboard", output)
        self.assertIn("model1", output)
        self.assertIn("🥇", output)
        self.assertIn("🥈", output)
        self.assertIn("🥉", output)

    def test_json_format(self) -> None:
        output = generate_leaderboard(self.results, output_format="json")
        data = json.loads(output)
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]["model_name"], "model1")

    def test_text_format(self) -> None:
        output = generate_leaderboard(self.results, output_format="text")
        self.assertIn("Decoding Leaderboard", output)
        self.assertIn("1. model1", output)

    def test_sorts_by_score(self) -> None:
        reversed_results = list(reversed(self.results))
        output = generate_leaderboard(reversed_results, output_format="text")
        lines = output.split("\n")
        # model1 should be first
        self.assertIn("model1", lines[2])


if __name__ == "__main__":
    unittest.main()
