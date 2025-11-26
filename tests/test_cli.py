"""Tests for word_salat CLI functionality."""

import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.cli import cmd_evaluate, cmd_score, cmd_scramble, create_parser, main


class CreateParserTests(unittest.TestCase):
    """Tests for argument parser creation."""

    def test_parser_has_subcommands(self) -> None:
        parser = create_parser()
        # Just check it doesn't raise
        args = parser.parse_args(["scramble", "test"])
        self.assertEqual(args.command, "scramble")

    def test_scramble_subcommand_args(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["scramble", "hello", "--seed", "42"])
        self.assertEqual(args.text, "hello")
        self.assertEqual(args.seed, 42)

    def test_score_subcommand_args(self) -> None:
        parser = create_parser()
        args = parser.parse_args(
            [
                "score",
                "-o",
                "original.txt",
                "-d",
                "decoded.txt",
                "-m",
                "hybrid",
            ]
        )
        self.assertEqual(args.command, "score")
        self.assertEqual(args.method, "hybrid")

    def test_evaluate_subcommand_args(self) -> None:
        parser = create_parser()
        args = parser.parse_args(
            [
                "evaluate",
                "-o",
                "original.txt",
                "-d",
                "decoded_dir/",
                "--format",
                "json",
            ]
        )
        self.assertEqual(args.command, "evaluate")
        self.assertEqual(args.format, "json")


class CmdScrambleTests(unittest.TestCase):
    """Tests for scramble command."""

    def test_scramble_inline_text(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["scramble", "Hello World", "--seed", "42"])

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            result = cmd_scramble(args)

        self.assertEqual(result, 0)
        output = mock_stdout.getvalue()
        self.assertIn("H", output)

    def test_scramble_from_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.txt"
            input_file.write_text("Test input text", encoding="utf-8")

            parser = create_parser()
            args = parser.parse_args(
                [
                    "scramble",
                    "-i",
                    str(input_file),
                    "--seed",
                    "42",
                ]
            )

            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                result = cmd_scramble(args)

            self.assertEqual(result, 0)
            self.assertIn("T", mock_stdout.getvalue())

    def test_scramble_to_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "output.txt"

            parser = create_parser()
            args = parser.parse_args(
                [
                    "scramble",
                    "Hello World",
                    "-o",
                    str(output_file),
                    "--seed",
                    "42",
                    "-q",
                ]
            )

            result = cmd_scramble(args)

            self.assertEqual(result, 0)
            self.assertTrue(output_file.exists())
            content = output_file.read_text(encoding="utf-8")
            self.assertIn("H", content)

    def test_scramble_missing_input_file(self) -> None:
        parser = create_parser()
        args = parser.parse_args(
            [
                "scramble",
                "-i",
                "/nonexistent/file.txt",
            ]
        )

        with patch("sys.stderr", new_callable=io.StringIO):
            result = cmd_scramble(args)

        self.assertEqual(result, 1)


class CmdScoreTests(unittest.TestCase):
    """Tests for score command."""

    def test_score_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            original = Path(tmpdir) / "original.txt"
            decoded = Path(tmpdir) / "decoded.txt"
            original.write_text("Hello World", encoding="utf-8")
            decoded.write_text("Hello World", encoding="utf-8")

            parser = create_parser()
            args = parser.parse_args(
                [
                    "score",
                    "-o",
                    str(original),
                    "-d",
                    str(decoded),
                ]
            )

            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                result = cmd_score(args)

            self.assertEqual(result, 0)
            output = mock_stdout.getvalue()
            self.assertIn("Score:", output)
            self.assertIn("1.0", output)

    def test_score_json_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            original = Path(tmpdir) / "original.txt"
            decoded = Path(tmpdir) / "decoded.txt"
            original.write_text("Hello", encoding="utf-8")
            decoded.write_text("Hello", encoding="utf-8")

            parser = create_parser()
            args = parser.parse_args(
                [
                    "score",
                    "-o",
                    str(original),
                    "-d",
                    str(decoded),
                    "--format",
                    "json",
                ]
            )

            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                result = cmd_score(args)

            self.assertEqual(result, 0)
            import json

            data = json.loads(mock_stdout.getvalue())
            self.assertIn("score", data)

    def test_score_missing_original(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            decoded = Path(tmpdir) / "decoded.txt"
            decoded.write_text("Hello", encoding="utf-8")

            parser = create_parser()
            args = parser.parse_args(
                [
                    "score",
                    "-o",
                    "/nonexistent.txt",
                    "-d",
                    str(decoded),
                ]
            )

            with patch("sys.stderr", new_callable=io.StringIO):
                result = cmd_score(args)

            self.assertEqual(result, 1)


class CmdEvaluateTests(unittest.TestCase):
    """Tests for evaluate command."""

    def test_evaluate_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            original = Path(tmpdir) / "original.txt"
            original.write_text("Hello World", encoding="utf-8")

            decoded_dir = Path(tmpdir) / "decoded"
            decoded_dir.mkdir()
            (decoded_dir / "model1.txt").write_text("Hello World", encoding="utf-8")
            (decoded_dir / "model2.txt").write_text("Hello Earth", encoding="utf-8")

            parser = create_parser()
            args = parser.parse_args(
                [
                    "evaluate",
                    "-o",
                    str(original),
                    "-d",
                    str(decoded_dir),
                    "--no-log",
                ]
            )

            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                result = cmd_evaluate(args)

            self.assertEqual(result, 0)
            output = mock_stdout.getvalue()
            self.assertIn("model1", output)
            self.assertIn("model2", output)

    def test_evaluate_empty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            original = Path(tmpdir) / "original.txt"
            original.write_text("Hello", encoding="utf-8")

            decoded_dir = Path(tmpdir) / "decoded"
            decoded_dir.mkdir()

            parser = create_parser()
            args = parser.parse_args(
                [
                    "evaluate",
                    "-o",
                    str(original),
                    "-d",
                    str(decoded_dir),
                    "--no-log",
                ]
            )

            with patch("sys.stderr", new_callable=io.StringIO):
                result = cmd_evaluate(args)

            self.assertEqual(result, 1)


class MainTests(unittest.TestCase):
    """Tests for main entry point."""

    def test_main_no_args_shows_help(self) -> None:
        with (
            patch("sys.stdout", new_callable=io.StringIO),
            patch.object(sys, "argv", ["word-salat"]),
            self.assertRaises(SystemExit) as cm,
        ):
            main([])
        # Should exit with 0 (help shown)
        self.assertEqual(cm.exception.code, 0)

    def test_main_scramble_command(self) -> None:
        with (
            patch("sys.stdout", new_callable=io.StringIO),
            self.assertRaises(SystemExit) as cm,
        ):
            main(["scramble", "Hello", "--seed", "42"])
        self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
