# A4 — Recommendation memo: Indic tokenizer cost and routing

**To:** leadership · **Re:** REPORT_v0 Section 1 · **Status:** replaces the "budget 6× for Hindi" recommendation

## Recommendation

1. **Do not budget 6× for Hindi, and do not route on "Indic or not".** The 6× figure describes `gpt2`, a 50k-vocabulary English tokenizer. Our served model has a 128k vocabulary, so the report did not measure our system.
2. **Measure our own tokenizer before deciding.** One command produces its token premium for all seven Indic languages: `a3_analysis.py` with our tokenizer added.
3. **Then decide by this rule,** using the premium over English on parallel text:
   - **Under 2×:** keep one model for all traffic and budget that premium.
   - **Over 4×:** route native-script Indic traffic to a model with an Indic-aware tokenizer. Keep English on the current model, because Indic tokenizers cost about 16% more on English.

## Corrected numbers

Token premium over English: tokens for the same 1,012 parallel sentences (FLORES-200), 95% intervals within ±1.5%.

| tokenizer class | Hindi | Kannada | Tamil | Malayalam |
|---|---|---|---|---|
| English byte-level BPE (`gpt2`, what v0 measured) | 7.4× | 13.6× | 15.5× | 15.2× |
| Current open LLM, byte-level BPE (Qwen2.5) | 4.4× | 6.9× | 6.1× | 7.2× |
| Current general LLM (`o200k_base`) | 1.6× | 2.0× | 2.0× | 2.0× |
| Indic-focused LLM (Sarvam-1) | 1.14× | 1.22× | 1.16× | 1.36× |

- If our tokenizer behaves like the last two rows, Indic traffic costs **1.1–2.0×** English.
- If it behaves like Qwen2.5, routing Hindi to an Indic tokenizer cuts tokens per sentence from 120.5 to 35.5, a **3.4× saving**.
- The v0 report's three findings do not hold:
  - Its 5.89× came from 10 non-parallel sentences; the same metric on parallel text ranges from 5.5 to 6.8 on ten-sentence samples.
  - Its two metrics do not agree. The same data gives 2.8× to 11.4× depending on the unit.
  - Its root cause is false. Hindi has fewer characters per word than English (4.75 against 5.74); the cost comes from the tokenizer's vocabulary.

## Why this number

Cost and GPU memory are paid per token, and a user asks for a piece of content. The premium on parallel sentences is the only measure that holds the content fixed across languages. Tokens per word understates Hindi by 15% and overstates Kannada by 36%, because the same sentence is 25 words in Hindi and 16 in Kannada.

## Biggest caveat

The corpus is formal, native-script, translated text. Real traffic includes Hindi typed in Latin letters and mixed with English. On ten romanized sentences the ranking reversed: `gpt2` needed 143 tokens and Sarvam-1 needed 166. Routing "all Hindi" to an Indic tokenizer could raise cost for romanized users. Route on **script**, not on language, until this is measured on real traffic.

## The one metric to monitor

**Tokens per UTF-8 byte, by language and script bucket, on live traffic, compared with the corpus value.**

- The premium itself cannot be measured in production, because live traffic has no parallel English version.
- Tokens per byte needs only the request, and within one language and script it should stay near the corpus figure. For example, 0.107 for Devanagari Hindi with Sarvam-1.
- A bucket that drifts more than 20% from its corpus value, or a growing share of Latin-script Hindi, means the corpus no longer represents our users and this analysis should be rerun on sampled traffic.
