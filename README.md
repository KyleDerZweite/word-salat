# Word Salat 🥗

[![CI](https://github.com/KyleDerZweite/word-salat/actions/workflows/ci.yml/badge.svg)](https://github.com/KyleDerZweite/word-salat/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Generate word salad text by shuffling the interior letters of each word while keeping the first and last characters intact. This reproduces the classic "Cambridge University" effect, making text readable to humans yet challenging for automated systems.

## Features

- 🔀 **Scramble text** while preserving readability
- 🎯 **Deterministic output** with optional `--seed` for reproducible experiments
- 📚 **Library functions** for programmatic use
- 🖥️ **Rich CLI** with subcommands for scrambling, scoring, and batch evaluation
- 📊 **Multiple scoring methods** to grade AI decoding attempts
- 🏆 **Leaderboard generation** for comparing model performance
- ✅ **Fully typed** with `py.typed` marker for IDE support

## Installation

### From source

The project uses only the Python standard library. Python 3.9 or later is required.

```bash
git clone https://github.com/KyleDerZweite/word-salat.git
cd word-salat
pip install -e .
```

### Development installation

```bash
pip install -e ".[dev]"
pre-commit install
```

## Usage

### Command Line Interface

The CLI provides three main commands: `scramble`, `score`, and `evaluate`.

#### Scramble text

```bash
# Inline text
word-salat scramble "The quick brown fox jumps over the lazy dog."

# From file
word-salat scramble -i input.txt -o output.txt

# With reproducible seed
word-salat scramble "Testing deterministic scramble" --seed 42

# From stdin
echo "Artificial intelligence loves jumbled words" | word-salat scramble
```

#### Score a decoded attempt

```bash
# Basic scoring
word-salat score -o original.txt -d decoded.txt

# With specific method and JSON output
word-salat score -o original.txt -d decoded.txt -m hybrid --format json

# Log result with model name
word-salat score -o original.txt -d decoded.txt -n "gpt-4" --results-file results/scores.md
```

#### Batch evaluate decoded files

```bash
# Evaluate all .txt files in a directory
word-salat evaluate -o text.txt -d text_decoded/

# Generate JSON leaderboard
word-salat evaluate -o text.txt -d text_decoded/ --format json

# Skip logging to file
word-salat evaluate -o text.txt -d text_decoded/ --no-log
```

### Library API

```python
from word_salat import scramble_text, scramble_word, score_decoded_text
from word_salat import batch_evaluate, generate_leaderboard

# Scramble text
original = "A longish sentence to scramble"
scrambled = scramble_text(original, seed=123)
print(scrambled)

# Score a decoded attempt
decoded_attempt = "A lgosnih scnteene to sracmble"
score = score_decoded_text(original, decoded_attempt)
print(f"Score: {score:.2%}")

# Get detailed metrics
from word_salat.scoring import compute_detailed_score
result = compute_detailed_score(original, decoded_attempt, name="my-model")
print(f"Char: {result.char_score:.2%}, Word: {result.word_score:.2%}")

# Batch evaluate a directory
results = batch_evaluate("text.txt", "text_decoded/", log_results=False)
leaderboard = generate_leaderboard(results)
print(leaderboard)
```

### Scoring Methods

`score_decoded_text` and the CLI accept a `method` argument:

| Method | Description |
|--------|-------------|
| `char` | Character-level comparison using SequenceMatcher |
| `word` | Order-sensitive word-level comparison |
| `token_set` | Jaccard similarity on unique words (order ignored) |
| `hybrid` | Average of all metrics (default, most balanced) |

### Standard Prompts for Decoding

#### English

```
Please decode the following text. The interior letters of each word have been
shuffled, but the first and last letters remain correct. Return only the
reconstructed plain text, without any additional comments or explanations.

<TEXT>
```

#### Deutsch

```
Bitte dekodiere den folgenden Text. Die inneren Buchstaben jedes Wortes wurden
vertauscht, der erste und letzte Buchstabe stimmt noch. Gib nur den
rekonstruierten Klartext zurück, ohne weitere Kommentare oder Erklärungen.

<TEXT>
```

## Project Structure

```
word-salat/
├── src/
│   ├── __init__.py      # Package exports
│   ├── core.py          # Scrambling logic
│   ├── scoring.py       # Scoring and evaluation
│   ├── cli.py           # Command-line interface
│   └── py.typed         # Type checking marker
├── tests/
│   ├── test_core.py         # Core functionality tests
│   ├── test_scoring.py      # Scoring tests
│   └── test_cli.py          # CLI tests
├── results/
│   └── decoded_scores.md    # Logged evaluation results
├── text_decoded/            # AI model decoding attempts
├── pyproject.toml           # Project configuration
└── README.md
```

## Development

### Running tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_core.py -v
```

### Code quality

```bash
# Lint and format
ruff check src tests
ruff format src tests

# Type checking
mypy src tests
```

### Pre-commit hooks

```bash
pre-commit install
pre-commit run --all-files
```

## Migration from v1

Version 2.0 introduces a new package structure. To migrate:

1. **Import changes**: Update imports to use the new module structure:
   ```python
   # Old (v1)
   from word_salat import scramble_text, score_decoded_text

   # New (v2) - same imports still work!
   from word_salat import scramble_text, score_decoded_text

   # New detailed imports
   from word_salat.core import scramble_text, scramble_word
   from word_salat.scoring import score_decoded_text, batch_evaluate
   ```

2. **CLI changes**: The CLI now uses subcommands:
   ```bash
   # Old (v1)
   python word_salat.py "text to scramble"

   # New (v2)
   word-salat scramble "text to scramble"
   ```

3. **New features**: Take advantage of `batch_evaluate`, `generate_leaderboard`, and JSON output.

## License

This project is released under the MIT License. See [LICENSE.md](LICENSE.md) for details.
