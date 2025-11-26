"""Tests for word_salat core functionality."""

import random
import unittest

from src import scramble_text, scramble_word
from src.core import WORD_PATTERN, _attempt_shuffle


class AttemptShuffleTests(unittest.TestCase):
    """Tests for the _attempt_shuffle helper function."""

    def test_shuffle_single_index_returns_unchanged(self) -> None:
        """Single index should return unchanged list."""
        chars = list("abc")
        rng = random.Random(42)
        result = _attempt_shuffle(chars, [1], rng)
        self.assertEqual(result, list("abc"))

    def test_shuffle_empty_indices_returns_unchanged(self) -> None:
        """Empty indices should return unchanged list."""
        chars = list("test")
        rng = random.Random(42)
        result = _attempt_shuffle(chars, [], rng)
        self.assertEqual(result, list("test"))

    def test_shuffle_identical_chars_returns_unchanged(self) -> None:
        """All identical characters at indices should return unchanged."""
        chars = list("aaaa")
        rng = random.Random(42)
        result = _attempt_shuffle(chars, [1, 2], rng)
        self.assertEqual(result, list("aaaa"))

    def test_shuffle_produces_different_order(self) -> None:
        """Shuffling should eventually produce different order."""
        chars = list("abcdef")
        rng = random.Random(42)
        indices = [1, 2, 3, 4]
        result = _attempt_shuffle(chars, indices, rng)
        # Should be different (with high probability)
        self.assertNotEqual(result, list("abcdef"))
        # But first and last should be same
        self.assertEqual(result[0], "a")
        self.assertEqual(result[-1], "f")


class ScrambleWordTests(unittest.TestCase):
    """Tests for scramble_word function."""

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

    def test_scramble_word_empty_string(self) -> None:
        """Empty string should return empty."""
        self.assertEqual(scramble_word(""), "")

    def test_scramble_word_single_char(self) -> None:
        """Single character should return unchanged."""
        self.assertEqual(scramble_word("a"), "a")

    def test_scramble_word_two_chars(self) -> None:
        """Two characters should return unchanged."""
        self.assertEqual(scramble_word("ab"), "ab")

    def test_scramble_word_three_chars(self) -> None:
        """Three characters should return unchanged."""
        self.assertEqual(scramble_word("abc"), "abc")

    def test_scramble_word_four_chars(self) -> None:
        """Four character word has one interior char to shuffle."""
        rng = random.Random(42)
        word = "test"
        scrambled = scramble_word(word, rng)
        self.assertEqual(scrambled[0], "t")
        self.assertEqual(scrambled[-1], "t")

    def test_scramble_word_with_accents(self) -> None:
        """Accented characters should be handled correctly."""
        rng = random.Random(42)
        word = "übung"
        scrambled = scramble_word(word, rng)
        self.assertEqual(scrambled[0], "ü")
        self.assertEqual(scrambled[-1], "g")

    def test_scramble_word_without_rng(self) -> None:
        """Without RNG, should still work (non-deterministic)."""
        word = "testing"
        scrambled = scramble_word(word)
        self.assertEqual(scrambled[0], "t")
        self.assertEqual(scrambled[-1], "g")
        self.assertEqual(len(scrambled), len(word))

    def test_scramble_word_long_word(self) -> None:
        """Long words should scramble properly."""
        rng = random.Random(42)
        word = "internationalization"
        scrambled = scramble_word(word, rng)
        self.assertEqual(scrambled[0], word[0])
        self.assertEqual(scrambled[-1], word[-1])
        self.assertCountEqual(scrambled, word)


class ScrambleTextTests(unittest.TestCase):
    """Tests for scramble_text function."""

    def test_scramble_text_is_deterministic_with_seed(self) -> None:
        text = "The quick brown fox jumps over the lazy dog."
        scrambled = scramble_text(text, seed=123)
        self.assertEqual(
            scrambled,
            "The qciuk bworn fox jpmus oevr the lzay dog.",
        )

    def test_scramble_text_handles_german_sentence(self) -> None:
        text = (
            "Obwohl verschlungene Worte verblüffen, bleibt der Sinn für Menschen erstaunlich klar."
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
        first_word = scrambled.split()[0]
        self.assertTrue(first_word.startswith("H"))
        self.assertTrue(first_word.endswith(","))

    def test_scramble_text_empty_string(self) -> None:
        """Empty string should return empty."""
        self.assertEqual(scramble_text(""), "")

    def test_scramble_text_whitespace_only(self) -> None:
        """Whitespace only should be preserved."""
        self.assertEqual(scramble_text("   \n\t  "), "   \n\t  ")

    def test_scramble_text_numbers_preserved(self) -> None:
        """Numbers should be preserved."""
        text = "I have 42 apples and 123 oranges."
        scrambled = scramble_text(text, seed=42)
        self.assertIn("42", scrambled)
        self.assertIn("123", scrambled)

    def test_scramble_text_mixed_content(self) -> None:
        """Mixed content with numbers, symbols, words."""
        text = "Test@123 <html> 'quoted' (parens)"
        scrambled = scramble_text(text, seed=42)
        self.assertIn("@", scrambled)
        self.assertIn("123", scrambled)
        self.assertIn("<", scrambled)
        self.assertIn(">", scrambled)

    def test_scramble_text_unicode_emoji(self) -> None:
        """Emoji should be preserved."""
        text = "Hello 🌍 World!"
        scrambled = scramble_text(text, seed=42)
        self.assertIn("🌍", scrambled)

    def test_scramble_text_newlines_preserved(self) -> None:
        """Newlines should be preserved."""
        text = "Line one\nLine two\n\nLine four"
        scrambled = scramble_text(text, seed=42)
        self.assertEqual(scrambled.count("\n"), 3)


class WordPatternTests(unittest.TestCase):
    """Tests for the WORD_PATTERN regex."""

    def test_matches_basic_words(self) -> None:
        matches = WORD_PATTERN.findall("Hello World")
        self.assertEqual(matches, ["Hello", "World"])

    def test_matches_accented_words(self) -> None:
        matches = WORD_PATTERN.findall("café naïve résumé")
        self.assertEqual(matches, ["café", "naïve", "résumé"])

    def test_matches_german_umlauts(self) -> None:
        matches = WORD_PATTERN.findall("Größe Übung ähnlich")
        self.assertEqual(matches, ["Größe", "Übung", "ähnlich"])

    def test_splits_on_punctuation(self) -> None:
        matches = WORD_PATTERN.findall("don't won't")
        self.assertEqual(matches, ["don", "t", "won", "t"])

    def test_splits_on_hyphen(self) -> None:
        matches = WORD_PATTERN.findall("well-known self-aware")
        self.assertEqual(matches, ["well", "known", "self", "aware"])


if __name__ == "__main__":
    unittest.main()
