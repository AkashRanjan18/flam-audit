# A1 — Evaluation corpus

**Build it:** `python your-submission/partA/prepare_corpus.py` (log: `results/05_corpus_stats.txt`)

## What it is

| | |
|---|---|
| Source | FLORES-200, official release by Meta's NLLB team (`dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz`), CC-BY-SA 4.0 |
| Integrity | SHA-256 `b8b0b767…944011f6`, checked by the script on every run |
| Split used | `devtest`, **1,012 sentences**. `dev` (997 sentences) is held back as a replication set |
| Languages | 8: English, Hindi, Marathi, Bengali (Indo-Aryan) and Kannada, Tamil, Telugu, Malayalam (Dravidian) |
| Parallel? | Yes. Line *N* is the same sentence in every language, professionally translated from English |
| Domain | Wikinews 341, Wikibooks 351, Wikivoyage 320 sentences |
| Preprocessing | **None.** Only the trailing newline is removed. No lowercasing, no Unicode normalization, no punctuation changes |

I chose FLORES because the question is "what does the same content cost in each language", and that needs the same content in each language. The six Part C languages are all included, so Parts A and C use one corpus.

## Size

| lang | sentences | words | graphemes | code points | UTF-8 bytes | words / sentence | bytes / word |
|---|---|---|---|---|---|---|---|
| eng | 1,012 | 21,901 | 131,966 | 131,966 | 132,096 | 21.64 | 6.03 |
| hin | 1,012 | 25,643 | 85,978 | 131,079 | 337,094 | 25.34 | 13.15 |
| mar | 1,012 | 19,046 | 80,489 | 133,252 | 355,712 | 18.82 | 18.68 |
| ben | 1,012 | 19,506 | 81,693 | 129,042 | 344,682 | 19.27 | 17.67 |
| kan | 1,012 | 16,100 | 90,471 | 138,140 | 375,480 | 15.91 | 23.32 |
| tam | 1,012 | 16,775 | 99,724 | 154,133 | 421,641 | 16.58 | 25.14 |
| tel | 1,012 | 16,938 | 76,602 | 132,505 | 353,711 | 16.74 | 20.88 |
| mal | 1,012 | 14,930 | 79,428 | 149,336 | 411,753 | 14.75 | 27.58 |

The same 1,012 sentences take 25,643 words in Hindi and 14,930 in Malayalam. That one column is why "tokens per word" cannot compare languages (see A2, claim 5).

## Checks the script runs

- **Alignment:** every language has exactly 1,012 non-empty lines.
- **Parallel sanity:** per-line byte length correlates with English at r = 0.90–0.93 for every language. The intern's toy samples score r = 0.29 (A2, claim 6).
- **Why no normalization:** I measured what NFC would change rather than assuming it. It alters 609 Bengali lines and 93 Hindi lines. The effect on results is reported in A3, and it is not always zero.
- **Messiness left in on purpose:** double spaces appear in 213 Kannada lines and 136 Telugu lines; zero-width joiners in 289 Kannada lines. Real input has these, so the corpus keeps them.

## What this corpus cannot tell you

FLORES is edited, formal, encyclopedic prose, translated from English by professionals. Our users write chat messages. Four things follow.

1. **Register and domain.** Chat text is shorter, more colloquial, and full of names, slang and typos. The premium varies little across FLORES's three domains (Hindi with `gpt2`: 7.33–7.50), but all three are formal writing, so this says nothing about chat.
2. **Script.** Every Indic sentence here is in native script. Many Indian users type Hindi in Latin letters or mix English into it. A 10-sentence illustration (A2, E6) shows the tokenizer ranking can flip on romanized text. FLORES cannot measure this at all.
3. **Translationese.** The Indic sentences mirror English sentence structure. Text first written in Hindi or Tamil may be longer or shorter for the same idea.
4. **Inputs only.** The corpus measures the cost of reading text. Model replies are generated text and may tokenize differently from human text.

On sample size: 1,012 sentences gives a 95% interval of about ±1.5% on each premium (A3), which is tight enough for a budget. It is not enough to study rare cases such as long conjunct clusters or unusual names, and one corpus cannot show how much the numbers move between corpora. The `dev` split replicates every premium within 3%, but it comes from the same source and so shares all four limits above.
