# Lab notebook

Chronological. Each entry is hypothesis → experiment → result → what changed. All experiments were run on 2026-10-04 in one working session with Claude Code driving the terminal (see `AI_USAGE.md`). Commands are run from the repo root unless a `cd` is shown.

---

## 1. Can I reproduce the report at all?

- **Hypothesis:** the "5.89×" is an arithmetic slip, because 7.45 ÷ 1.27 from the report's table is 5.87.
- **Experiment:** `cd starter_kit && python fertility.py --corpus eng=corpus_sample/eng_sample.txt --corpus hin=corpus_sample/hin_sample.txt --tokenizer gpt2`
- **Result:** eng 1.27, hin 7.45, tok/char 0.226 and 1.579, "hin is 5.89x". Identical to the report.
- **Revision:** hypothesis wrong. The script divides unrounded values (7.4485 ÷ 1.2652 = 5.8871). The arithmetic is fine; dropped this as a finding.

## 2. Raw file inspection before touching code

- **Experiment:** read both sample files as bytes. Checked BOM, CRLF, tabs, non-breaking spaces, zero-width characters, lines changed by NFC, double spaces.
- **Result:** no BOM, no CRLF, no hidden characters. 11 raw lines, 10 non-empty in each. **NFC changes 0 lines in both files.** One double-space line in each file.
- **Revision:** NFC is a candidate for the "looks suspicious but is fine" item. The double spaces make `split(" ")` a candidate bug.

## 3. One-switch-at-a-time audit on the samples

- **Question:** how much of the 5.89 do the suspected code bugs explain?
- **Experiment:** wrote `partA/audit_a2.py`. It imports the intern's `analyze()` and asserts my re-implementation matches it exactly before flipping switches. `python your-submission/partA/audit_a2.py`
- **Result:**
  - `split()`: ratio 5.887 → 5.922
  - ratio of sums: → 5.908
  - no lowercasing: → 6.059 (3 English lines change, 0 Hindi)
  - no NFC: → 5.887 (no change)
  - all three fixes: → 6.114
- **Revision:** the bugs are real but move the ratio by under 4% combined. The report's problem must be elsewhere: the metric, the corpus or the tokenizer. This redirected the rest of Part A.

## 4. Surprise in the character counts

- **Result from the same run:** Hindi has 4.75 code points per word, English 5.74. The report's root cause ("Hindi has more Unicode characters per word") is contradicted by its own data. Hindi has more *bytes* per word (12.5 against 5.7).
- **Also:** switching "char" from code points to graphemes moves the tok/char ratio from 7.0 to 10.9.
- **Revision:** the "two metrics agree" claim needs a table of every denominator. Added `DETAIL 5b` later (entry 11).

## 5. Are the samples parallel?

- **Observation:** reading the files side by side, line 1 is about an airport in English and about morning tea in Hindi.
- **Open question at this point:** how to turn "they look different" into a measurement. Deferred until a real parallel corpus existed to compare against (entry 9).

## 6. Corpus choice

- **Decision:** FLORES-200 `devtest` from the official tarball, verified by SHA-256.
- **Not tested:** the Hugging Face hub copies. I went straight to the original release because it needs no account or terms acceptance, and one checksum pins it.
- **Experiment:** `python your-submission/partA/prepare_corpus.py`
- **Result:** 1,012 lines × 8 languages, all aligned, no empty lines. Domains: wikinews 341, wikibooks 351, wikivoyage 320.
- **Surprises:**
  - Words per sentence for the same content: eng 21.6, hin 25.3, kan 15.9, mal 14.8.
  - NFC is **not** a no-op here: 609 Bengali lines and 93 Hindi lines change.
  - Double spaces are common: 213 Kannada lines.
- **Revision:** "NFC is harmless" now needs a qualifier and a measurement on this corpus. The `split(" ")` bug matters more than the toy sample showed.

## 7. Which tokenizers load without gated access?

- **Experiment:** loaded six candidates and tokenized one Hindi sentence.
- **Result:** all loaded. XLM-R, MuRIL, Sarvam-1 and IndicBERTv2 gave 8 tokens; mT5 gave 12; Qwen2.5 gave 33.
- **Decision:** `gpt2`, `o200k_base`, Qwen2.5, XLM-R, MuRIL, Sarvam-1. Dropped mT5 and IndicBERTv2 to keep the table readable. Pinned each Hugging Face tokenizer to its commit hash.

## 8. Dead end: script crash

- **Experiment:** first run of `partA/a3_analysis.py`.
- **Result:** `SyntaxError: f-string expression part cannot include a backslash` (Python 3.9, a regex `\X` inside an f-string).
- **Fix:** computed the grapheme count on its own line first.

## 9. Corrected analysis

- **Question:** how far apart are per-word and per-sentence, and in which direction?
- **Experiment:** `python your-submission/partA/a3_analysis.py`
- **Result:** the direction is not the same for every language. With `gpt2`, per-word says Hindi is 6.33× and per-sentence says 7.41×, so per-word **understates** Hindi. It overstates Kannada (18.5 against 13.6), Tamil and Malayalam. The direction follows words per sentence.
- **Result:** the Hindi premium runs from 7.41× (`gpt2`) to 1.14× (Sarvam-1) on identical text.
- **Revision:** "property of the script" is refuted. The headline number is the per-sentence premium, and the memo must say the answer depends on which tokenizer we serve.

## 10. Rerunning the A2 switches on the real corpus

- **Experiment:** `audit_a2.py --eng …/eng.txt --other …/hin.txt --label hin`, then the same for Kannada. Needed a small change to the script so the second corpus can be any language.
- **Result (Hindi):** `split()` +0.001, pooling +0.012, no lowercasing +0.21, no NFC −0.007.
- **Result (Kannada):** `split()` +0.35 on a ratio of 17.5, because of the 213 double-space lines.
- **Revision:** lowercasing is the largest code bug on real text (469 of 1,012 English lines change). NFC moves `gpt2`/Hindi fertility by 0.11%.

## 11. Supporting experiments (`partA/a2_extra.py`)

- **E1, parallel check:** line-length correlation is 0.285 for the samples and 0.922 for FLORES. Among 5,000 random 10-line parallel subsets, 0.02% score as low as the sample. This answers the open question from entry 5.
- **E2, sample size:** the intern's metric on 10-sentence FLORES subsets ranges 5.03–7.36; 95% band 5.48–6.75.
- **E3, which tokenizer:** model spec says vocab 128k; `gpt2` has 50,257.
- **E4, special tokens:** `add_special_tokens=True` adds 1–2 tokens per sentence and lowers the premium by about 1%. The intern's `False` is correct.
- **E5, domain:** Hindi/`gpt2` premium 7.33–7.50 across the three domains.
- **E6, romanized Hindi:** on 10 hand-romanized sentences the ranking reverses: Sarvam-1 needs 166 tokens and `gpt2` 143. `gpt2` was expected to do better on Latin letters; Sarvam-1 doing worse than `gpt2` was not. This became the memo's main caveat.
- Added `DETAIL 5b` to `audit_a2.py`: on the samples, Hindi is 2.80× per byte, 6.11× per word, 7.39× per code point, 11.39× per grapheme.

## 12. NFC, measured properly

- **Hypothesis:** NFC is harmless everywhere.
- **Experiment:** `a3_analysis.py --nfc`, compared with the raw run.
- **Result:** 41 of 42 premiums move under 1.5%. Sarvam-1 on Bengali moves 1.28 → 1.12.
- **Follow-up:** listed which code points NFC changes. U+09DF (য়) is rewritten as U+09AF + U+09BC. Sarvam-1 encodes the single code point as 5 tokens and the two-code-point form as 2.
- **Revision:** NFC is fine in the intern's script (zero effect on their numbers) but is not universally harmless. Wrote it up with that qualifier.

## 13. Replication

- **Experiment:** `a3_analysis.py --split dev` (997 different sentences).
- **Result:** all 42 premiums within 2.7% of `devtest`.

## 14. Part B: capacity model

- **Hypothesis:** KV bytes per token = 2 × 28 × 8 × 128 × 2 = 114,688, and capacity is 25 sequences.
- **Experiment:** `python your-submission/partB/b_capacity.py`. Opened the CSV first: it is comma-separated, not tab-separated as I had assumed from the pasted view.
- **Result:** predicted utilization matches all 13 rows to two decimals; preemptions 7 and 23 match.
- **Side test:** if "24 GB" were GiB, batch 24 would read 0.82. Logged 0.93. Decimal GB it is.
- **Side test:** `--kv-heads 24` gives 8 sequences, which batch 16 contradicts.

## 15. Part B: the throughput column

- **Hypothesis:** `reported_tok_s` counts prompt plus generated tokens.
- **Result:** `num_requests × (prompt_len + gen_len) ÷ wall_clock_s` reproduces every row within 0.2 tok/s.
- **Result:** batch-24 goodput is 200.9 tok/s two ways. The decode-only estimate is 249.8; the gap is the 12.0 s of the run that is not steady decode.

## 16. Part B: bandwidth model

- **Hypothesis:** decode is limited by reading weights plus KV from memory each step.
- **Result:** floor ÷ measured ITL is 0.638–0.667 on all 11 non-preempted rows. One constant explains ITL across batch 1 to 64 and both prompt lengths.
- **Used for:** the fp8 KV prediction (batch 48: ~97 ms ITL, ~74 s wall, ~333 tok/s).

## 17. Part B: unresolved

- `e2e_ms_p95` is larger than `wall_clock_s` in 12 of 13 rows. I do not know which column is defined differently.
- Median TTFT stays near 0.5 s from batch 4 to 24, although prefilling 24 long prompts needs at least 6 s of compute. Prefix caching would explain TTFT but contradicts the KV utilization column.
- **Decision:** reported both as open questions. Did not build any conclusion on TTFT or e2e.

## 18. Dead end: vLLM metric names

- **First lookup:** the vLLM metrics design page, as summarized, listed no preemption counter.
- **Second lookup:** the usage metrics page and `vllm/v1/metrics/loggers.py` define a Counter named `vllm:num_preemptions`.
- **Also corrected:** the KV gauge is `vllm:kv_cache_usage_perc`, and current vLLM preempts by recompute only.

## 19. Part C

- **Arithmetic first:** reviewer 800 judgments a week; LoRA epoch 12 minutes; rewriter delays first token to about 8 s.
- **Realization:** with no API, the fine-tuning data can only come from a prompted model, so option (a) cannot start before option (c) works. That ordering decided the recommendation.

## 20. Dead end: line endings

- **Observation:** after the first commit, the committed `kan.txt` and the file on disk had different SHA-256 hashes.
- **Cause:** Python's text mode on Windows wrote CRLF line endings, and git stored LF. A first check with `grep` reported no carriage returns, because that `grep` strips them in text mode; counting the raw bytes in Python showed them.
- **Fix:** `prepare_corpus.py` now writes with `newline="\n"`, and `.gitattributes` sets `eol=lf`.
- **Effect on results:** none. The scripts read lines without their endings; the A3 and E1–E6 logs are identical before and after.
