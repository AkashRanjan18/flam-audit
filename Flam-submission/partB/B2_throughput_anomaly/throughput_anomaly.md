# B2 — The throughput anomaly in the long-prompt runs

These are the prompt-3584 rows of `bench/bench_log.csv`:

| batch | reported tok/s | wall clock (s) | ITL (ms) | preempted | KV util |
|-------|----------------|----------------|----------|-----------|---------|
| 4     | 565.4          | 28.98          | 51.33    | 0         | 0.16    |
| 8     | 902.6          | 36.30          | 62.26    | 0         | 0.31    |
| 16    | 1311.4         | 49.97          | 77.20    | 0         | 0.62    |
| 24    | 1607.4         | 61.16          | 96.07    | 0         | 0.93    |
| 32    | 1384.0         | 94.71          | 101.79   | 7         | 0.97    |
| 48    | 1298.5         | 151.41         | 100.00   | 23        | 0.97    |

## The anomaly

A bigger batch should give more throughput. It does up to batch 24 (565 → 1,607 tok/s). After that it goes down: 1,384 at batch 32 and 1,298 at batch 48. Going from batch 24 to 48 gives 19% less throughput and takes 2.5 times as long (61 s → 151 s).

## Why it happens

The KV cache is full, so the server pauses requests.

- From B1, the GPU holds 25 full sequences. Batches 32 and 48 need more than that.
- `kv_cache_util` reaches 0.93 at batch 24 and then stays at 0.97. It cannot go higher.
- `preempted_seqs` is 0 up to batch 24, then 7 and 23. That is exactly 32 − 25 and 48 − 25.
- `itl_ms_p50` stops growing (96 → 102 → 100 ms). Only about 25 sequences run at the same time, however many are sent.
- `wall_clock_s` jumps from 61 to 95 to 151 s, because the extra requests have to wait.

A paused request has its KV blocks freed, so its prefill is redone when there is room again. The GPU is as busy as at batch 24, but part of the work is repeated.

## The change I propose

**Limit the server to 24 requests at a time (`--max-num-seqs 24`).** Then nothing is paused. Extra requests wait their turn and no work is repeated.

Predicted effect for batch 48: it runs as two groups of 24, and the log shows one group of 24 takes 61.16 s.

```
wall clock   2 × 61.16             = 122.3 s       (log: 151.41 s)
throughput   48 × 4,096 ÷ 122.3    = 1,607 tok/s   (log: 1,298.5)
gain         1,607 ÷ 1,298.5       = +24%
preempted    0                                     (log: 23)
```

This is an estimate from the log, not a measurement. It assumes the two groups run back to back and each takes the logged 61.16 s.

This helps when the overload is large. For batch 32 it does not: 24 then 8 takes 61.16 + 36.30 = 97.5 s, against 94.71 s in the log.

Another option is storing the KV cache in fp8. That halves the bytes per token to 57,344, so 51 sequences fit and batch 48 would not be paused at all. It changes the stored numbers, so output quality would have to be checked first.
