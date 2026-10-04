# AI usage

## Tool

Claude Code (Claude Opus), used in the terminal on my machine.

## What the AI did

Honestly: most of the production work.

- **Code.** Claude wrote all five scripts: `partA/prepare_corpus.py`, `partA/audit_a2.py`, `partA/a2_extra.py`, `partA/a3_analysis.py` and `partB/b_capacity.py`.
- **Experiments.** Claude ran every command and saved the outputs in `partA/results/` and `partB/results/`. The numbers in the write-ups are copied from those logs.
- **Write-ups.** Claude drafted A1–A4, the Part B answers, the Part C memo and the notebook.
- **Study plan.** Before the work started, Claude gave me a syllabus and a video list for tokenizers, Unicode, KV-cache arithmetic and vLLM.
- **One data file.** Claude hand-romanized the ten Hindi sample sentences in `partA/corpus_extra/hin_roman_sample.txt`.

## What I did

<!-- TODO (author): replace this block with what you personally did and checked before submitting.
     Be specific and truthful: which scripts you re-ran, which numbers you re-derived by hand,
     which parts you read and can explain, and which parts you are less sure about. -->

## Where the AI was wrong or misleading

1. **It called the report's 5.89× an arithmetic error.** From the rounded table it computed 7.45 ÷ 1.27 = 5.87 and flagged the report. Running the script showed 5.8871 from unrounded values. Had I submitted that as a flaw, it would have been an unverified claim.
2. **Its first list of "likely bugs" included three that do not exist:** special tokens being counted, `zip()` truncating parallel files, and a wrong file encoding. The script uses `add_special_tokens=False`, has no `zip`, and opens files as UTF-8. Only measurement removed them from the list.
3. **It guessed that NFC normalization is harmless.** That is true for the intern's setup (zero lines change). As a general statement it is false: with Sarvam-1 on Bengali it changes the result by 13%. The guess held for this script only, and I know that only because it was measured.
4. **It told me `bench_log.csv` was tab-separated** and suggested `sep="\t"`. The file is comma-separated.
5. **It quoted vLLM details from memory that were out of date:** the gauge name `gpu_cache_usage_perc` (now `kv_cache_usage_perc`) and "recompute or swap" (current vLLM recomputes only). Its first documentation lookup also reported that no preemption counter exists; the source code shows `vllm:num_preemptions`.
6. **Its first version of `a3_analysis.py` crashed** on Python 3.9 with an f-string syntax error.

## Where I should be trusted least

- **The romanized Hindi file and the English gloss of Hindi line 1** were written by the AI. They are illustrative and marked as such.
- **The fp8 KV prediction in B2** is a model output, not a measurement. No GPU was used anywhere in this submission.
- **The two anomalies in the log** (e2e above wall clock, flat TTFT) are unexplained. The AI offered guesses; none is verified, so none is claimed.
- **Part C's arithmetic rests on stated assumptions** (45 seconds per judgment, 150-token replies, 35% GPU utilization during training). They are estimates, not measurements.
