# A3 — Corrected cross-language analysis

**Run it:** `python your-submission/partA/a3_analysis.py` (log: `results/06_a3_devtest.txt`, data: `results/a3_devtest.csv`)

**Setup.** 1,012 parallel FLORES-200 sentences × 8 languages × 6 tokenizers. Text is tokenized raw, without special tokens. Hugging Face tokenizers are pinned to a commit hash in the script.

| tokenizer | what it is | vocabulary |
|---|---|---|
| `gpt2` | English byte-level BPE; the intern's choice | 50k |
| `Qwen2.5` | byte-level BPE of a current open LLM | 152k |
| `o200k_base` | byte-level BPE of a current general LLM, trained with more multilingual text | 200k |
| `XLM-R` | multilingual SentencePiece | 250k |
| `Sarvam-1` | Indic-focused LLM tokenizer (SentencePiece) | 68k |
| `MuRIL` | Indic-focused WordPiece from an encoder model | 197k |

## 1. The answer changes with the denominator

Hindi against English with `gpt2`, same text:

| denominator | "× English" |
|---|---|
| per UTF-8 byte | 2.91 |
| per whitespace word | 6.33 |
| per parallel sentence | **7.41** |
| per code point | 7.46 |
| per grapheme cluster | 11.38 |

Each unit holds something different constant:

| denominator | what it holds constant | why it fails for cost |
|---|---|---|
| UTF-8 byte | storage size | Indic letters are 3 bytes and Latin letters 1, so it flatters Indic text |
| code point | Unicode units | a Hindi syllable is often 2–3 code points |
| grapheme | visible characters | one Indic character carries a whole syllable, about 2–3 Latin letters of content |
| word | whitespace-separated units | Hindi needs 25.3 words per sentence, Kannada 15.9, for the same content |
| **parallel sentence** | **the meaning** | — |

## 2. The number that should drive routing and cost

**Token premium = total tokens for language L ÷ total tokens for English, on the same parallel sentences, measured with the tokenizer of the model that will serve the request.**

The reasoning:

1. We are billed, and we use GPU memory, per token.
2. A user wants a piece of content handled. The fair question is how many tokens that content costs in their language.
3. A parallel corpus is the only place where the content is identical across languages, so the sentence is the only denominator that holds meaning fixed.
4. Every other unit mixes tokenizer efficiency with how a language spells or spaces its words.

The premium compares languages under one tokenizer. To choose between models, use the absolute form, **tokens per parallel sentence × that model's price per token** (section 4).

## 3. Headline: token premium over English

95% intervals from a paired bootstrap, 2,000 resamples of sentences. Every interval is within ±1.5% of its estimate.

| lang | gpt2 | Qwen2.5 | o200k_base | XLM-R | MuRIL | Sarvam-1 |
|---|---|---|---|---|---|---|
| hin | 7.41 (7.32–7.50) | 4.42 | 1.57 | 1.25 | 1.16 | 1.14 (1.13–1.16) |
| mar | 7.86 | 4.62 | 1.82 | 1.22 | 1.06 | 1.08 |
| ben | 9.56 | 5.03 | 1.70 | 1.38 | 1.01 | 1.28 |
| kan | 13.59 (13.43–13.75) | 6.92 | 1.97 | 1.35 | 1.07 | 1.22 (1.20–1.23) |
| tam | 15.54 | 6.11 | 1.98 | 1.35 | 1.06 | 1.16 |
| tel | 12.97 | 6.99 | 1.93 | 1.32 | 1.20 | 1.15 |
| mal | 15.16 | 7.23 | 1.96 | 1.38 | 1.18 | 1.36 |

- **The report's "6× for Hindi" is wrong in both directions.** With `gpt2` the true premium is 7.4× for Hindi and 13–16× for Dravidian languages. With an Indic-aware tokenizer it is 1.1–1.4× for every language.
- **Dravidian languages cost about twice what Hindi costs under byte-level BPE** (13.6× against 7.4× with `gpt2`), and about the same as Hindi under Indic-aware tokenizers. The report tested Hindi only and generalized to "all Indic traffic".
- **The spread is across tokenizers.** Within one tokenizer the seven Indic languages differ by at most 2.1×; across tokenizers the same language differs by 6.5× (Hindi) to 14.7× (Tamil).

## 4. Absolute tokens per sentence

| lang | gpt2 | Qwen2.5 | o200k_base | XLM-R | MuRIL | Sarvam-1 |
|---|---|---|---|---|---|---|
| eng | 26.7 | 27.3 | 26.6 | 30.3 | 27.3 | 31.0 |
| hin | 198.1 | 120.5 | 41.8 | 37.8 | 31.6 | 35.5 |
| kan | 363.1 | 188.9 | 52.3 | 41.0 | 29.1 | 37.8 |
| tam | 415.2 | 166.8 | 52.6 | 40.9 | 28.9 | 36.0 |

Indic-aware tokenizers spend more tokens on English (Sarvam-1: 31.0 against `gpt2`'s 26.7, +16%). Routing English to an Indic model would cost more.

## 5. Robustness

| check | command | result |
|---|---|---|
| Replication on held-out split | `a3_analysis.py --split dev` | all 42 premiums within 3% of `devtest` |
| NFC normalization first | `a3_analysis.py --nfc` | 41 of 42 premiums move under 1.5%; Sarvam-1 Bengali moves 1.28 → 1.12 |
| Domain | `a2_extra.py --only E5` | Hindi/`gpt2` 7.33–7.50 across the three FLORES domains |
| Special tokens | `a2_extra.py --only E4` | including them lowers premiums by about 1% |

## 6. Caveats on the tokenizers

- **MuRIL's numbers are a lower bound.** It is a WordPiece tokenizer from an encoder model. It maps unknown pieces to `[UNK]` (0.40% of Telugu tokens) and discards whitespace, so it does not carry all the information a generative model needs. Sarvam-1 is the fair Indic comparison for an LLM.
- **None of these six is our served tokenizer.** The model spec says 128k vocabulary and no tokenizer was shipped with the kit. The script takes any tokenizer, so the real number is one command away.
- **Romanized Hindi reverses the ranking** on a 10-sentence illustration (`a2_extra.py --only E6`): `gpt2` 143 tokens, MuRIL 84, Sarvam-1 166. Ten hand-romanized sentences prove nothing about size; they show the direction of the risk.
