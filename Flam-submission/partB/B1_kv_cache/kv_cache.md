# B1 — KV cache and how many sequences fit

All numbers are from `bench/model_spec.md`. The check against every row of the log is in `results.txt`.

## (a) KV-cache bytes per token

```
2 × 28 × 8 × 128 × 2 = 114,688 bytes
```

| Number | Where it comes from                                   |
|--------|-------------------------------------------------------|
| 2      | each token stores a K and a V                         |
| 28     | layers                                                |
| 8      | KV heads (GQA). Not 24: only K and V are cached       |
| 128    | head_dim                                              |
| 2      | KV cache precision is fp16 = 16 bits = 2 bytes        |

## (b) Maximum concurrent 4,096-token sequences

```
usable memory       24 GB × 0.92             = 22.08 GB
weights             4.2 B × 2 bytes (fp16)   =  8.40 GB
left for KV cache   22.08 − 8.40 − 1.60      = 12.08 GB
tokens that fit     12.08 GB ÷ 114,688       = 105,329 tokens
sequences that fit  105,329 ÷ 4,096          = 25.7  →  25
```

The 1.60 GB is the non-KV runtime overhead given in the spec. I round down because a 26th sequence would not fit completely.

**Answer: about 25 sequences.**

## Check against the log

I predicted two columns of `bench_log.csv` from the numbers above:

- KV utilization = tokens in use ÷ 105,329
- preempted sequences = requests − 25, when more than 25 are sent

| batch | prompt + gen | predicted util | logged util | predicted preempted | logged preempted |
|-------|--------------|----------------|-------------|---------------------|------------------|
| 16    | 768          | 0.12           | 0.12        | 0                   | 0                |
| 64    | 768          | 0.47           | 0.47        | 0                   | 0                |
| 16    | 4,096        | 0.62           | 0.62        | 0                   | 0                |
| 24    | 4,096        | 0.93           | 0.93        | 0                   | 0                |
| 32    | 4,096        | 0.97           | 0.97        | 7                   | 7                |
| 48    | 4,096        | 0.97           | 0.97        | 23                  | 23               |

Both columns match on all 13 rows of the log (full table in `results.txt`). So the log agrees with 25.
