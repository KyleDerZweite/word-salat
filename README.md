# Word Salat

Generate word salad text by shuffling the interior letters of each word while keeping the first and last characters intact. This reproduces the classic "Cambridge University" effect, making text readable to humans yet challenging for automated systems.

## Features

- Deterministic output with an optional `--seed` for reproducible experiments.
- Library functions (`scramble_text` and `scramble_word`) for programmatic use.
- Command-line interface for quick text scrambling.
- Preserves punctuation, whitespace, short words, and the central letter of odd-length words.
- Includes a similarity validator (`score_decoded_text`) to grade AI decoding attempts.

## Installation

The project uses only the Python standard library. Python 3.9 or later is recommended.

Clone or download the repository and (optionally) create a virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate
```

## Usage

Scramble inline text:

```bash
python word_salat.py "The quick brown fox jumps over the lazy dog."
```

Read text from standard input:

```bash
echo "Artificial intelligence loves jumbled words" | python word_salat.py
```

Make the output reproducible:

```bash
python word_salat.py "Testing deterministic scramble" --seed 42
```

### Library Example

```python
from word_salat import scramble_text, score_decoded_text

original = "A longish sentence to scramble"
scrambled = scramble_text(original, seed=123)
decoded_attempt = "A lgosnih scnteene to sracmble"
score = score_decoded_text(original, decoded_attempt)
print(scrambled)
print(f"Decoded score: {score:.2%}")

# Log the score for a specific model (optional)
score_decoded_text(
	original,
	decoded_attempt,
	name="example-model",
	source_label="demo.txt",
)
```

### Decoding evaluation modes

`score_decoded_text` accepts a `method` argument to choose how similarity is
calculated:

- `"char"`: character-level comparison (original behaviour).
- `"word"`: order-sensitive token comparison.
- `"token_set"`: bag-of-words overlap, ignoring order.
- `"hybrid"`: averages the available metrics for a more resilient score (default).

Provide the optional `name` argument to automatically append the result to
`results/decoded_scores.md`. Use `source_label` to indicate which text or file
was evaluated, and `results_file` to override the output location if needed.

### Standardprompt für Decodierung (Deutsch)

```
Bitte dekodiere den folgenden Text. Die inneren Buchstaben jedes Wortes wurden vertauscht, der erste und letzte Buchstabe stimmt noch. Gib nur den rekonstruierten Klartext zurück, ohne weitere Kommentare oder Erklärungen.

<TEXT>
```

## Testing

Run the unit tests with:

```bash
python -m unittest discover
```

## License

This project is released under the MIT License.
