# Fertility audit (A2)

The report's headline is that Hindi needs **5.89×** as many tokens per word as English. That is what `fertility.py` prints. `fertility_fixed.py` is the same script with the bugs corrected, and it prints **6.11×**.

`results.txt` has the evidence for every line below.

## 1. Bugs

| # | `fertility.py`               | `fertility_fixed.py`       | Hindi ÷ English with the bug | Fixed |
|---|------------------------------|----------------------------|------------------------------|-------|
| 1 | `line = line.lower()`        | line removed               | 5.93                         | 6.11  |
| 2 | `line.split(" ")`            | `line.split()`             | 6.09                         | 6.11  |
| 3 | average of each line's ratio | total tokens ÷ total words | 6.09                         | 6.11  |

What each bug did:
1. **Lowercasing** changed English tokens but not Hindi, which has no capitals. English looked 3.1% worse than it is.
2. **Split on one space** made an empty "word" from a double space. "Please keep the books  in the cupboard." counted as 8 words; it has 7.
3. **Averaging** let a 4-word line count as much as a 12-word line.

Each bug was measured alone: one old line put back into the fixed script, nothing else changed. All three together are the gap between the two scripts, 5.89 → 6.11 (3.8%). The bugs are real but small.

## 2. Conceptual problem

The script computes tokens per word correctly. The problem is that a word does not carry the same amount of meaning in every language. The same sentence averages 21.6 words in English, 25.3 in Hindi and 16.6 in Tamil.

What should be computed is tokens for the **same sentence**, compared with English. `fertility_fixed.py` prints both. On the A1 corpus:

| lang   | × English, per word | × English, per sentence | per word is  |
|--------|---------------------|-------------------------|--------------|
| Hindi  | 6.34                | 7.42                    | 15% too low  |
| Tamil  | 20.28               | 15.54                   | 31% too high |
| Telugu | 16.77               | 12.97                   | 29% too high |

Same text and same tokenizer; only what I divide by changed.

## 3. Looks suspicious, is fine

| Item                | Why it looks suspicious                        | What I measured                       |
|---------------------|------------------------------------------------|---------------------------------------|
| NFC normalization   | rewrites the text before measuring it          | 6.11 with it, 6.11 without it         |
| `random.seed(1337)` | suggests the numbers depend on random sampling | `random` is never used after the seed |
