# Lab notebook

In the order I did them. Each experiment: what I expected, what I did, what came out, what I changed.

## Part A

**Experiment 1: reproduce the report's numbers**
- Expected: the 5.89× is an arithmetic slip, because 7.45 ÷ 1.27 from the report's table is 5.87.
- Did: ran `fertility.py` unchanged on the two sample files.
- Result: 1.2652, 7.4485 and 5.8871. The script divides the unrounded numbers.
- Changed: dropped "wrong arithmetic" as a finding.

**Experiment 2: the effect of each code bug**
- Expected: each fix would move the 5.89, but I did not know by how much.
- Did: put one bug back at a time into the fixed script and reran it.
- Result: lowercase 5.93, split 6.09, averaging 6.09, against 6.11 with all three fixed. Together they are 3.8%.
- Changed: the code is not the main problem, so I tested the metric next.

**Experiment 3: NFC and `random.seed`**
- Expected: both are harmless.
- Did: deleted the NFC line and reran; searched the script for `random`.
- Result: 6.1137 before and after. `random` is never used after the seed.
- Changed: listed both as "looks suspicious, is fine". Kept NFC in the fixed script and removed `random`.

**Experiment 4: tokens per word against tokens per sentence**
- Expected: the two would differ, but I did not know in which direction.
- Did: ran the fixed script on the A1 corpus with `gpt2`.
- Result: Hindi is 6.34× English per word and 7.42× per sentence. Tamil is 20.28× and 15.54×. Per word is too low for Hindi and too high for Tamil.
- Changed: reported per word as the conceptual problem and used per sentence as the headline.

**Experiment 5: a second tokenizer**
- Expected: an Indic-aware tokenizer would need fewer tokens for Hindi than `gpt2`.
- Did: ran the fixed script on the same corpus with Sarvam-1.
- Result: Hindi takes 198.3 tokens per sentence with `gpt2` and 35.1 with Sarvam-1. The ratio to English falls from 7.42 to 1.13.
- Changed: rejected the report's "property of the script, not the tokenizer", and wrote the routing recommendation around the tokenizer.

## Part B

**Experiment 6: check B1 against the log**
- Expected: 105,329 tokens of KV cache, so 25 full sequences.
- Did: predicted `kv_cache_util` and `preempted_seqs` for every row of `bench_log.csv`.
- Result: both match on 13 of 13 rows. If "24 GB" meant GiB, batch 24 would read 0.82; the log says 0.93.
- Changed: nothing. Used 25 in B2.

**Experiment 7: does a cap of 24 requests fix the anomaly?**
- Expected: it would help at every overloaded batch.
- Did: worked it out from the log's batch-8 and batch-24 rows.
- Result: batch 48 goes from 151.41 s to 122.3 s (+24%). Batch 32 does not improve: 97.5 s against 94.71 s.
- Changed: kept the fix, and wrote in that it does not help at batch 32.

**Experiment 8: is the latency column consistent?**
- Expected: no request takes longer than the whole run, so `e2e_ms_p95` should be below `wall_clock_s`.
- Did: compared the two columns row by row.
- Result: `e2e_ms_p95` is larger in 12 of 13 rows. I could not explain it.
- Changed: did not use `e2e_ms_p95` for any conclusion.

## Part C

No experiment. It is a reasoning memo.
