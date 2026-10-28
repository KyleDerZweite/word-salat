# Word Salat 🥗

[![CI](https://github.com/KyleDerZweite/word-salat/actions/workflows/ci.yml/badge.svg)](https://github.com/KyleDerZweite/word-salat/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> IMPORTANT: This project is under development and is not a stable, released product. It is provided "as-is", without warranty or guarantee. It works to some extent, but may be incomplete, unstable, or contain bugs. Mentions of a version such as "v2" do not imply an official release.

Generate word salad text by shuffling the interior letters of each word while keeping the first and last characters intact. This reproduces the classic "Cambridge University" effect, making text readable to humans yet challenging for automated systems.

## Features

- **Scramble text** while preserving readability
- **Deterministic output** with optional `--seed` for reproducible experiments
- **Library functions** for programmatic use
- **Rich CLI** with subcommands for scrambling, scoring, and batch evaluation
- **Multiple scoring methods** to grade AI decoding attempts
- **Leaderboard generation** for comparing model performance
- **Fully typed** with `py.typed` marker for IDE support

## Installation

### From source

The project uses only the Python standard library. Python 3.9 or later is required.

```bash
git clone https://github.com/KyleDerZweite/word-salat.git
cd word-salat
pip install -e .
```

### Development installation

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) 0.11.16.
The required uv version is declared in `pyproject.toml` and read by CI.
Python 3.9 or later remains supported. Use `--python 3.12` with `uv sync`
to select the Python version used by the CI quality checks.

```bash
uv sync --locked --extra dev
uv run --locked --extra dev pre-commit install
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
from src import scramble_text, scramble_word, score_decoded_text
from src import batch_evaluate, generate_leaderboard

# Scramble text
original = "A longish sentence to scramble"
scrambled = scramble_text(original, seed=123)
print(scrambled)

# Score a decoded attempt
decoded_attempt = "A lgosnih scnteene to sracmble"
score = score_decoded_text(original, decoded_attempt)
print(f"Score: {score:.2%}")

# Get detailed metrics
from src.scoring import compute_detailed_score
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
uv run --locked --extra dev pytest

# With coverage
uv run --locked --extra dev pytest --cov=src --cov-report=html

# Run specific test file
uv run --locked --extra dev pytest tests/test_core.py -v
```

### Code quality

```bash
# Lint and format
uv run --locked --extra dev ruff check src tests
uv run --locked --extra dev ruff format src tests

# Type checking
uv run --locked --extra dev mypy src tests
```

### Pre-commit hooks

```bash
uv run --locked --extra dev pre-commit install
uv run --locked --extra dev pre-commit run --all-files
```

### Tooling and dependency updates

`pyproject.toml` owns development requirements. Commit `uv.lock` whenever
requirements change. CI and local hooks use `uv run --locked --extra dev`,
so a stale lockfile fails instead of silently resolving new versions.
Ruff, mypy and the file checks share this environment. Mypy stays on the 1.19
series to run on Python 3.9 as well as check the Python 3.9 target. There are no runtime
dependencies. The `dev` extra remains available to consumers, while contributor
workflows use uv rather than a separate requirements file. Whitespace-fixing
hooks exclude the benchmark inputs and decoded text captures so their contents
remain unchanged.

```bash
# Refresh the development lockfile after a dependency change
uv lock
uv sync --locked --extra dev

# Build with the locked build dependencies and validate metadata
uv run --locked --extra dev python -m build --no-isolation
uv run --locked --extra dev twine check dist/*
```

Dependabot checks the uv lockfile and GitHub Actions monthly. Dependency updates
must keep Python 3.9 support and pass the existing Python 3.9 through 3.13 matrix.

## Migration from v1

Version 2.0 introduces a new package structure. To migrate:

1. **Import changes**: Update imports to use the new module structure:
   ```python
   # Old (v1)
   from word_salat import scramble_text, score_decoded_text

   # New (v2)
   from src import scramble_text, score_decoded_text

   # Detailed imports
   from src.core import scramble_text, scramble_word
   from src.scoring import score_decoded_text, batch_evaluate
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
