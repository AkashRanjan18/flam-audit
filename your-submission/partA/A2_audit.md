# A2 — Audit of `fertility.py` and its metric

**Method.** `audit_a2.py` re-implements the intern's calculation with one switch per design choice. With every switch in the intern's position it must return the intern's numbers exactly; the script imports `fertility.analyze` and asserts this. Each row then flips one switch, so any movement has one cause.

**Baseline reproduced** (`results/00_baseline_reproduction.txt`): eng 1.27, hin 7.45, ratio 5.89×, tok/char 0.226 and 1.579. The report's arithmetic is correct. Everything below is about whether those numbers mean what the report says.

All commands run from the repo root. "Sample" is the intern's 10+10 lines; "FLORES" is the A1 corpus.

## Summary

| # | Claim | Type | Effect on the Hindi/English ratio |
|---|---|---|---|
| 1 | `split(" ")` counts empty strings as words | code bug | sample 5.887 → 5.922 (+0.6%) |
| 2 | Mean of per-line ratios, not ratio of totals | code bug (minor) | sample 5.887 → 5.908 (+0.3%) |
| 3 | Lowercasing changes English only | code bug | sample 5.887 → 6.059 (+2.9%) |
| 4 | "tok/char" counts code points, and the two metrics do not agree | conceptual | 2.8× to 11.4× depending on the unit |
| 5 | Tokens per word is the wrong unit across languages | **conceptual, the main one** | understates Hindi by 15%, overstates Kannada by 36% |
| 6 | The samples are not parallel | design flaw | the ratio compares different content |
| 7 | Ten sentences is too few | design flaw | ±10% from sampling alone |
| 8 | The tokenizer measured is not the one we serve, and the result is not "a property of the script" | wrong conclusion | Hindi premium 7.41× → 1.14× by changing tokenizer |
| H1–H3 | NFC, `random.seed`, `add_special_tokens=False` | **look suspicious, are fine** | 0.000 on the intern's setup |

Fixing bugs 1–3 together moves the ratio from 5.89 to 6.11. **The code bugs are real but small. The report's errors come from claims 4–8.**

---

## Code bugs

### 1. `line.split(" ")` counts empty strings as words

`"books  in".split(" ")` returns `["books", "", "in"]`. Each double space adds a phantom word, which inflates the word count and lowers fertility.

```
python your-submission/partA/audit_a2.py
```

| | eng fertility | hin fertility | hin/eng |
|---|---|---|---|
| `split(" ")` (intern) | 1.2652 | 7.4485 | 5.8871 |
| `split()` | 1.2831 | 7.5985 | 5.9221 |

- Affected lines: eng line 7 (8 words counted, 7 real) and hin line 10 (6 counted, 5 real).
- **Direction:** fertility is understated in both languages. **Magnitude:** ratio +0.035.
- **Why it proves the claim:** only the split call changed, and only the two lines with a double space changed their word count.
- On real data it is larger and one-sided. 213 of 1,012 Kannada FLORES lines contain a double space and 0 English lines do. Kannada fertility moves 22.57 → 23.02 (+2.0%) while English does not move (`results/03_a2_switches_flores_kan.txt`).

### 2. Mean of per-line ratios instead of ratio of totals

`analyze()` averages `tokens/words` per line, so a 4-word line counts as much as a 12-word line. The quantity that matters for cost is total tokens ÷ total words.

| | eng | hin | hin/eng |
|---|---|---|---|
| mean of ratios (intern) | 1.2652 | 7.4485 | 5.8871 |
| ratio of sums | 1.2532 | 7.4032 | 5.9076 |

- **Direction:** both fertilities are overstated slightly. **Magnitude:** ratio +0.02 on the sample, +0.01 for Hindi and −0.09 for Kannada on FLORES. The sign is not stable.
- I rate this minor. It matters more on short, uneven lines, which is what chat traffic looks like.

### 3. `line.lower()` biases one language

The comment says lowercasing removes noise. Devanagari has no case, so it changes English only, and it changes it in one direction.

| | eng | hin | hin/eng |
|---|---|---|---|
| lowercased (intern) | 1.2652 | 7.4485 | 5.8871 |
| original casing | 1.2293 | 7.4485 | 6.0590 |

- Three English lines gain one token each when lowercased (lines 2, 6, 10: "Quarterly Review", "NASA and ISRO", "GPU"). Zero Hindi lines change.
- **Direction:** English fertility is inflated by 2.9%, so the ratio is understated. **Magnitude:** ratio +0.17 when fixed.
- On FLORES, 469 of 1,012 English lines change against 14 Hindi lines, and the ratio moves 6.11 → 6.32 (+3.4%).
- It is also the wrong thing to measure: production does not lowercase user text before tokenizing.

---

## Conceptual problems

### 4. "tok/char" counts code points, and the two metrics do not agree

`len(line)` counts Unicode code points. In Devanagari a vowel sign or a virama is its own code point, so one visible character is often two or three. The sample has 290 Hindi code points but 188 grapheme clusters.

The report says the per-character number "confirms" the per-word number. `DETAIL 5b` of `audit_a2.py` computes the same Hindi/English comparison under every unit:

| unit | sample | FLORES |
|---|---|---|
| per UTF-8 byte | 2.80× | 2.90× |
| per word | 6.11× | 6.34× |
| per code point (the intern's "char") | 7.39× | 7.47× |
| per grapheme (a reader's "character") | 11.39× | 11.39× |

- Switching the character definition alone moves the "per character" ratio from 7.0 to 10.9 (row 5 of the switch table).
- **Why it proves the claim:** same text, same tokenizer, and the answer spans 2.8× to 11.4×. Two of four units landing near each other is not confirmation. Both ratios also share one numerator (the `gpt2` token count), so they could not be independent checks anyway.

The report's root cause, "Hindi simply has more Unicode characters per word", is also false on its own data: Hindi has **4.75** code points per word and English **5.74** (`DETAIL 5`). What Hindi has more of is **bytes** per word, 12.5 against 5.7, and `gpt2` is a byte-level tokenizer. That points at the tokenizer, which claim 8 tests directly.

### 5. Tokens per word is the wrong unit across languages (the main conceptual flaw)

The code computes tokens per whitespace word correctly. The problem is that a "word" is not the same amount of meaning in each language. Hindi writes postpositions as separate words; Kannada and Malayalam attach them to the noun.

```
python your-submission/partA/a3_analysis.py
```

On FLORES the same 1,012 sentences use 21.6 words per sentence in English, 25.3 in Hindi, 15.9 in Kannada and 14.8 in Malayalam. With `gpt2`:

| lang | "× English" per word | "× English" per parallel sentence | per-word error |
|---|---|---|---|
| hin | 6.33 | 7.41 | understates by 15% |
| kan | 18.49 | 13.59 | overstates by 36% |
| tam | 20.28 | 15.54 | overstates by 31% |
| mal | 22.24 | 15.16 | overstates by 47% |

- **Direction:** depends on the language's grammar, so per-word numbers cannot even rank languages reliably.
- **Why it proves the claim:** cost is paid per token for a given piece of content. Per-sentence on a parallel corpus holds content fixed; per-word does not, and the gap between the two columns is exactly the words-per-sentence ratio.

### 6. The samples are not parallel

The task description calls the samples parallel line-by-line. They are not. Line 1 is "Bengaluru International Airport handled record traffic in March." in English and "मुझे सुबह की चाय बहुत पसंद है।" (I really like morning tea) in Hindi.

```
python your-submission/partA/a2_extra.py --only E1
```

- Line-length correlation between the two samples: **r = 0.285**.
- The same statistic on FLORES: r = 0.922.
- For 5,000 random 10-line subsets of truly parallel FLORES text, r falls in [0.71, 0.99], and only 0.02% of subsets score as low as the sample.
- **Consequence:** the 5.89× compares the tokenizer on different sentences. On the sample, Hindi costs 4.78× per line; on parallel text it costs 7.42× per line.

### 7. Ten sentences cannot support "numbers final"

```
python your-submission/partA/a2_extra.py --only E2
```

- The intern's exact metric on all 1,012 FLORES sentences gives 6.11.
- On 5,000 random 10-sentence subsets it ranges from 5.03 to 7.36, with 95% of draws in **[5.48, 6.75]**. That band is 21% of the value.
- A bootstrap of the toy sample itself gives [5.36, 6.44] around its 5.89.
- **Consequence:** the report's "5.89" is one draw from a wide distribution. "Roughly 5 to 7" is all ten sentences can support.

### 8. Wrong tokenizer, and the result is not "a property of the script"

```
python your-submission/partA/a2_extra.py --only E3
python your-submission/partA/a3_analysis.py
```

- `bench/model_spec.md` gives the served model a **128k** vocabulary. `tiktoken`'s `gpt2` has **50,257**. The report measured a tokenizer we do not serve.
- The report says any tokenizer will struggle. Same 1,012 Hindi sentences, six tokenizers:

| tokenizer | Hindi tokens / sentence | premium over English |
|---|---|---|
| gpt2 | 198.1 | 7.41× |
| Qwen2.5 | 120.5 | 4.42× |
| o200k_base | 41.8 | 1.57× |
| XLM-R | 37.8 | 1.25× |
| Sarvam-1 | 35.5 | 1.14× |
| MuRIL | 31.6 | 1.16× |

- **Why it proves the claim:** the text and script are fixed and only the tokenizer changes, and the premium falls from 7.41× to 1.14×. The cost is a property of the tokenizer's vocabulary.

---

## Things that look suspicious and are fine

### H1. `unicodedata.normalize("NFC", line)`

Normalizing before tokenizing looks like it could alter the text being measured.

- On the samples: **0 of 10** lines change in either file, and every number is identical with it removed (row 4, all deltas +0.0000).
- On FLORES with `gpt2`: 93 Hindi lines change, and fertility moves by 0.11%.
- **Verdict:** harmless for the report's numbers. It is a no-op here.
- **One qualification, measured.** It is not harmless for every tokenizer. With Sarvam-1 on Bengali, NFC lowers the premium from 1.28× to 1.12× (`results/08_a3_devtest_nfc.txt`). FLORES stores য় as the single code point U+09DF, which Sarvam's vocabulary lacks: 5 tokens raw, 2 after NFC. So normalization is a serving choice worth making deliberately. It is not a bug in this script.

### H2. `random.seed(1337)`

A seed in a script that reports "final" numbers suggests hidden sampling. `DETAIL 6` lists every line that mentions `random`: the import and the seed. Nothing draws a random number. Dead code, zero effect.

### H3. `add_special_tokens=False`

This looks like it drops tokens the model really sees. It is the correct choice for comparing languages. With the flag set to `True`, every sentence gains a fixed 1–2 marker tokens in both languages, which pulls the ratio toward 1:

| tokenizer | premium without | premium with | tokens added per sentence |
|---|---|---|---|
| XLM-R | 1.2466 | 1.2313 | 2 |
| MuRIL | 1.1595 | 1.1486 | 2 |
| Sarvam-1 | 1.1442 | 1.1397 | 1 |

(`a2_extra.py --only E4`.) The `tiktoken` path adds no special tokens either. Skipping empty lines and `.strip()` are likewise fine: each file has 11 raw lines and 10 real ones.
