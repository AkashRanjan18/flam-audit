# Tokenizer Findings (v1): corrected

*Replaces Section 1 of REPORT_v0. Evidence: `A3_corrected_analysis/results.txt`.*

## 1. Corrected numbers

Ran `fertility_fixed.py` on 1,012 parallel sentences (FLORES-200) with two tokenizers. Ratio to English = that language's tokens ÷ English tokens, for the same sentences:

| lang | `gpt2` tokens / sentence | ratio to English | Sarvam-1 tokens / sentence | ratio to English |
|------|--------------------------|------------------|----------------------------|------------------|
| eng  | 26.7                     | 1.00             | 31.0                       | 1.00             |
| hin  | 198.3                    | 7.42             | 35.1                       | 1.13             |
| tam  | 415.2                    | 15.54            | 36.0                       | 1.16             |
| tel  | 346.6                    | 12.97            | 35.8                       | 1.15             |

**Findings:**

1. With `gpt2`, Hindi costs **7.4×** English for the same content, not 6×. Tamil and Telugu cost 13 to 16×.
2. With an Indic-aware tokenizer, all three cost about **1.15×** English. The cost is a property of the tokenizer, not the script.


## 2. Routing recommendation

Between the two tokenizers measured:

| Traffic | Route to | Tokens / sentence: `gpt2` → Sarvam-1 | Effect                   |
|---------|----------|--------------------------------------|--------------------------|
| Hindi   | Sarvam-1 | 198.3 → 35.1                         | 5.6× fewer tokens        |
| Tamil   | Sarvam-1 | 415.2 → 36.0                         | 11.5× fewer tokens       |
| Telugu  | Sarvam-1 | 346.6 → 35.8                         | 9.7× fewer tokens        |
| English | `gpt2`   | 26.7 → 31.0                          | Sarvam-1 would cost +16% |

- **Route Hindi, Tamil and Telugu to the model that uses the Sarvam-1 tokenizer. Keep English on `gpt2`.**
- **Budget Indic traffic at about 1.3× English, not 6×.** On this routing a sentence costs 35 to 36 tokens in the Indic languages against 26.7 in English, at equal price per token.
- **If another tokenizer is a candidate,** run the same command with it (`--tokenizer hf:<repo>`). For each language, pick whichever gives the fewest tokens per sentence × price per token.

## 3. Biggest caveat

**The numbers above were measured on text that may not look like what our users send.**

- **What I tested on:** news and encyclopedia sentences, translated from English, written in each language's own script.
- **What users may send:** short chat messages, possibly Hindi typed in English letters ("kal milte hain") or mixed with English words. The kit has no sample of real requests, so this is my assumption, not something I measured.
- **Why it matters:** a tokenizer splits those kinds of text differently. The 7.4× and 1.13× above could be higher or lower for real messages.
- **What to do:** treat these numbers as estimates. Measure a sample of real requests before fixing a budget, and route by script (Devanagari against Latin letters), not by language.

## 4. Metric to monitor

**Tokens per UTF-8 byte, per language and script, on live traffic.** The multiplier itself cannot be measured in production, because live requests have no parallel English version. Tokens per byte needs only the request, and within one language and script it should stay near the corpus value (Devanagari Hindi: 0.105 with Sarvam-1). If it drifts, the corpus no longer represents our users and this analysis must be rerun.
