# Part B — Capacity reconciliation

**Run it:** `python your-submission/partB/b_capacity.py` (log: `results/b_capacity.txt`)
Every number below is printed by that script. Counterfactuals are flags, for example `--kv-bytes 1` (log: `results/b_counterfactuals.txt`).

## B1 — KV cache per token and maximum concurrency

**(a) KV-cache bytes per token**

```
2 (K and V) × 28 layers × 8 KV heads × 128 head_dim × 2 bytes (fp16) = 114,688 bytes (112 KiB)
```

The count uses the **8 KV heads**, not the 24 query heads. With grouped-query attention, groups of three query heads share one K and one V, and only K and V are cached.

**(b) Maximum concurrent 4,096-token sequences**

```
usable GPU memory   24 GB × 0.92                 = 22.08 GB
weights             4.2 B params × 2 bytes       =  8.40 GB
runtime overhead                                 =  1.60 GB
KV budget           22.08 − 8.40 − 1.60          = 12.08 GB
KV capacity         12.08 GB ÷ 114,688 B         = 105,329 tokens (6,583 blocks of 16)
one full sequence   4,096 × 114,688 B            = 469.8 MB
max sequences       105,329 ÷ 4,096              = 25.7  →  25
```

**Check against the log.** The model has no fitted parameter. Predicted peak utilization is (sequences that fit × sequence length) ÷ 105,329.

| batch | prompt + gen | fit | predicted util | logged util | predicted preempted | logged preempted |
|---|---|---|---|---|---|---|
| 16 | 768 | 16 | 0.12 | 0.12 | 0 | 0 |
| 64 | 768 | 64 | 0.47 | 0.47 | 0 | 0 |
| 8 | 4,096 | 8 | 0.31 | 0.31 | 0 | 0 |
| 16 | 4,096 | 16 | 0.62 | 0.62 | 0 | 0 |
| 24 | 4,096 | 24 | 0.93 | 0.93 | 0 | 0 |
| 32 | 4,096 | 25 | 0.97 | 0.97 | 7 | 7 |
| 48 | 4,096 | 25 | 0.97 | 0.97 | 23 | 23 |

- All 13 rows match to two decimals, and both preemption counts match exactly (32 − 25 = 7, 48 − 25 = 23).
- **"24 GB" is decimal.** Read as GiB, capacity would be 119,526 tokens and batch 24 would show 0.82, against the logged 0.93.
- **GQA is confirmed by the data.** With 24 KV heads the capacity would be 8 sequences, and batch 16 could not have run without preemption.

## B2 — The long-context anomaly

**The anomaly.** In the prompt-3584 sweep, `reported_tok_s` rises to batch 24 and then falls as batch grows:

| batch | reported tok/s | wall clock (s) | ITL p50 (ms) | TTFT p50 (ms) | preempted | KV util |
|---|---|---|---|---|---|---|
| 16 | 1311.4 | 49.97 | 77.20 | 498.3 | 0 | 0.62 |
| 24 | 1607.4 | 61.16 | 96.07 | 500.5 | 0 | 0.93 |
| 32 | 1384.0 | 94.71 | 101.79 | 636.9 | 7 | 0.97 |
| 48 | 1298.5 | 151.41 | 100.00 | 955.4 | 23 | 0.97 |

Doubling the batch from 24 to 48 multiplies wall clock by 2.48 and lowers throughput by 19%.

**Mechanism: the KV cache is full, so the scheduler preempts.**

1. Capacity is 25 full-length sequences (B1). `kv_cache_util` reaches 0.93 at batch 24 and pins at 0.97 for batches 32 and 48.
2. `preempted_seqs` is 0 up to batch 24, then 7 and 23: exactly the requests beyond 25.
3. vLLM preempts by recompute. A preempted sequence gives up its KV blocks and its prompt is prefilled again later, so its earlier work is wasted.
4. `itl_ms_p50` stops growing: 96 → 102 → 100 ms. Per-step decode time depends on how many sequences run at once, and that number is stuck at about 25.
5. So beyond batch 24 the GPU does the same work per second, and the extra requests wait in line. Batch 48 behaves like two waves, plus the wasted prefill.

**Supporting check: decode is memory-bandwidth-bound.** Each decode step reads the weights and every running sequence's KV cache. Dividing those bytes by the L4's 300 GB/s gives a floor on ITL. Measured ITL is that floor ÷ 0.65 on all 11 non-preempted rows (efficiency 0.638–0.667), and the two preempted rows fit only if 25 sequences are running, not 32 or 48.

**Proposed change: store the KV cache in fp8.**

| | fp16 (logged) | fp8 (predicted) |
|---|---|---|
| KV bytes per token | 114,688 | 57,344 |
| capacity | 105,329 tokens, 25 sequences | 210,658 tokens, **51 sequences** |
| batch 48: KV utilization | 0.97 | **0.93** |
| batch 48: preempted | 23 | **0** |
| batch 48: ITL p50 | 100 ms | **≈ 97 ms** |
| batch 48: wall clock | 151.4 s | **≈ 74 s** |
| batch 48: goodput | 162 tok/s | **≈ 333 tok/s (2.05×)** |

- The ITL prediction uses the bandwidth model above: 48 sequences of fp8 KV are the same bytes per step as 24 sequences of fp16.
- The wall-clock prediction assumes prefill time doubles from batch 24 (12.0 s → 23.9 s).
- **Not tested here:** whether fp8 KV costs output quality. That needs an eval before rollout.
- **A zero-risk alternative** is admission control with `--max-num-seqs 24`. Batch 48 then runs as two clean waves: predicted wall clock 122 s and goodput 201 tok/s (+24%), with no preemptions.

## B3 — The misread column and the honest goodput

**The misreading.** `reported_tok_s` counts **prompt tokens plus generated tokens**:

```
reported_tok_s = num_requests × (prompt_len + gen_len) ÷ wall_clock_s
```

This reproduces all 13 rows to within 0.2 tok/s. Prompt tokens are processed once, in parallel, and are not output. A long prompt therefore inflates the counter without producing anything for the user.

Both conclusions in Section 2 come from reading this column as output speed:
- "Longer prompts give better throughput" compares 1311 against 883 at batch 16. Seven-eighths of the long-prompt figure is prompt tokens.
- "Batch 48 → ~3200 tok/s" scales the inflated 1607 linearly.

**Goodput of the batch-24 long-prompt row,** meaning generated tokens per second:

| way | calculation | result |
|---|---|---|
| 1. Count what was generated | 24 requests × 512 tokens ÷ 61.16 s | **200.9 tok/s** |
| 2. Strip prompt tokens from the counter | 1607.4 × 512 ÷ 4,096 | **200.9 tok/s** |
| Cross-check from decode speed | 24 sequences ÷ 96.07 ms | 249.8 tok/s |

The cross-check is higher because it covers the decode phase only. The run spent 12.0 of its 61.2 seconds outside steady decode, and 249.8 × (49.2 ÷ 61.2) = 200.9.

**What the report should have said.**

- At batch 16, long prompts deliver **164** generated tok/s against **294** for short prompts. Longer prompts are 44% worse.
- The best long-prompt goodput is **201 tok/s at batch 24**. Beyond that the KV cache is full and goodput falls, to 162 tok/s at batch 48. The log's own batch-48 row contradicts the 3200 forecast.
- Capacity planning should use about 200 generated tok/s per L4 for 4,096-token requests, with at most 24 concurrent requests. Packing more context per request lowers the number of requests an L4 can hold.

## B4 — The counter that would confirm the mechanism

I would pull **`vllm:num_preemptions_total`**, the cumulative preemption counter that vLLM exports to Prometheus (defined as `vllm:num_preemptions` in `vllm/v1/metrics/loggers.py`; the Prometheus client adds `_total`). I expect its increase over each run to be **0 for every batch up to 24, at least 7 for batch 32 and at least 23 for batch 48**. It is "at least" because a sequence can be preempted more than once, while the log counts sequences preempted at least once. A value of zero at batch 32 or 48 would refute the mechanism. Alongside it, the gauge `vllm:kv_cache_usage_perc` should sit near 0.97 for the whole decode phase of those two runs and peak at 0.93 for batch 24, and `vllm:num_requests_waiting` should be above zero only for batches 32 and 48.

## Two things in the log I could not explain

I report these as open questions. Neither changes B1–B4.

1. **`e2e_ms_p95` exceeds `wall_clock_s` in 12 of 13 rows** (ratio 1.03–1.18). If all requests are submitted together, no request can take longer than the whole run. One of the two columns is measured differently from what the notes say.
2. **TTFT does not grow with batch size.** Prefilling 24 prompts of 3,584 tokens needs about 723 TFLOP, at least 6.0 s at the L4's peak 121 TFLOPS, and the wall clock does contain about 12 s of non-decode time. Yet median TTFT is 0.50 s, the same as at batch 4. Prefix caching of the identical prompts could explain a fast TTFT, but then KV utilization would not scale with batch size as it does. I would read the harness code before using TTFT or e2e for any decision.
