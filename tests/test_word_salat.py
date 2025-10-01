import os
import random
import tempfile
import unittest

from word_salat import scramble_text, scramble_word, score_decoded_text


class ScrambleWordTests(unittest.TestCase):
    def test_scramble_word_keeps_first_and_last_characters(self) -> None:
        rng = random.Random(7)
        word = "scramble"
        scrambled = scramble_word(word, rng)
        self.assertEqual(scrambled[0], word[0])
        self.assertEqual(scrambled[-1], word[-1])
        self.assertCountEqual(scrambled[1:-1], word[1:-1])

    def test_scramble_word_preserves_middle_for_odd_length(self) -> None:
        rng = random.Random(5)
        word = "World"
        scrambled = scramble_word(word, rng)
        self.assertEqual(scrambled[len(word) // 2], word[len(word) // 2])

    def test_scramble_word_returns_original_for_short_words(self) -> None:
        rng = random.Random(12)
        for word in ("a", "at", "the"):
            with self.subTest(word=word):
                self.assertEqual(scramble_word(word, rng), word)


class ScrambleTextTests(unittest.TestCase):
    def test_scramble_text_is_deterministic_with_seed(self) -> None:
        text = "The quick brown fox jumps over the lazy dog."
        scrambled = scramble_text(text, seed=123)
        self.assertEqual(
            scrambled,
            "The qciuk bworn fox jpmus oevr the lzay dog.",
        )

    def test_scramble_text_handles_german_sentence(self) -> None:
        text = (
            "Obwohl verschlungene Worte verblüffen, bleibt der Sinn für Menschen "
            "erstaunlich klar."
        )
        scrambled = scramble_text(text, seed=2025)
        self.assertEqual(
            scrambled,
            "Ohwobl vnugrhlcneese Wtroe vbüfflreen, bebilt der Snin für Mhcseenn esailurntch kalr.",
        )

    def test_scramble_text_preserves_punctuation(self) -> None:
        text = "Hello, world! This test... works?"
        scrambled = scramble_text(text, seed=7)
        self.assertEqual(scrambled.count(","), 1)
        self.assertEqual(scrambled.count("!"), 1)
        self.assertEqual(scrambled.count("."), 3)
        self.assertTrue(scrambled.startswith("H"))
        self.assertTrue(scrambled.endswith("?"))
        # Ensure words are scrambled but boundaries stay put.
        first_word = scrambled.split()[0]
        self.assertTrue(first_word.startswith("H"))
        self.assertTrue(first_word.endswith(","))


class ScoreDecodedTextTests(unittest.TestCase):
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
            results_path = os.path.join(tmpdir, "scores.md")
            score = score_decoded_text(
                original,
                decoded,
                name="UnitTestModel",
                source_label="snippet.txt",
                results_file=results_path,
            )

            self.assertAlmostEqual(score, 1.0)
            with open(results_path, "r", encoding="utf-8") as fh:
                contents = fh.read()

        self.assertIn("UnitTestModel", contents)
        self.assertIn("`snippet.txt`", contents)

    def test_score_decoded_text_rejects_unknown_method(self) -> None:
        with self.assertRaises(ValueError):
            score_decoded_text("a", "a", method="unknown")


if __name__ == "__main__":
    unittest.main()
