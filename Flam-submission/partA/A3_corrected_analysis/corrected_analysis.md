# Corrected analysis (A3)

I ran the corrected script from A2 (`fertility_fixed.py`) on the A1 corpus (1,012 parallel sentences), once with each tokenizer. The two commands and their full output are in `results.txt`.

- **Tokenizers:** `gpt2` (the report's) and Sarvam-1 (Indic-aware).
- **Denominators:** whitespace word, grapheme cluster, UTF-8 byte, parallel sentence.

## Results: how many times English

**`gpt2`**

| lang   | per word | per grapheme | per byte | per sentence |
|--------|----------|--------------|----------|--------------|
| Hindi  | 6.34     | 11.39        | 2.91     | **7.42**     |
| Tamil  | 20.28    | 20.56        | 4.87     | **15.54**    |
| Telugu | 16.77    | 22.35        | 4.84     | **12.97**    |

**Sarvam-1**

| lang   | per word | per grapheme | per byte | per sentence |
|--------|----------|--------------|----------|--------------|
| Hindi  | 0.97     | 1.74         | 0.44     | **1.13**     |
| Tamil  | 1.51     | 1.53         | 0.36     | **1.16**     |
| Telugu | 1.49     | 1.99         | 0.43     | **1.15**     |

What the tables show:
- **The denominator changes the answer.** For Hindi with `gpt2`, the same data says 2.9× or 11.4×, depending on what I divide by.
- **The tokenizer changes it far more.** The same Hindi sentences take 198 tokens each with `gpt2` and 35 with Sarvam-1. The report's "property of the script, not the tokenizer" is wrong.
- **The report's "6× for Hindi" does not hold.** It is 7.4× with `gpt2`, 13 to 16× for Tamil and Telugu, and about 1.15× for all three with an Indic-aware tokenizer.

## Which single number should drive routing and cost?

**Tokens per parallel sentence, relative to English, measured with the tokenizer of the model that serves the request.**

Why: we pay per token, and a user asks for a piece of content. So the fair comparison is tokens for the same content. A parallel sentence is the only unit where the content is the same in both languages.

Why not the others. Each holds the wrong thing constant, so the same sentence has a different size in each language (Hindi, `gpt2`):

| Denominator | Holds constant     | Same sentence: English / Hindi | Says  | True | Error        |
|-------------|--------------------|--------------------------------|-------|------|--------------|
| Word        | whitespace chunks  | 21.6 / 25.3 words              | 6.34  | 7.42 | 15% too low  |
| Grapheme    | visible characters | 130 / 85 characters            | 11.39 | 7.42 | 54% too high |
| Byte        | storage size       | 131 / 333 bytes                | 2.91  | 7.42 | 61% too low  |

For routing between models, use the same unit in absolute form: tokens per sentence with each model's tokenizer. Hindi goes from 198 to 35 tokens per sentence on Sarvam-1, so it should move. English goes from 26.7 to 31.0, so it should stay.
