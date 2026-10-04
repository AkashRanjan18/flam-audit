# B3 — The misread column and the honest goodput

## The misreading

The report read `reported_tok_s` as output speed. That column counts **prompt tokens plus generated tokens**:

```
reported_tok_s = batch × (prompt_len + gen_len) ÷ wall_clock_s
```

It reproduces the two numbers the report quoted, and the batch-24 row:

| row            | calculation               | result | log    |
|----------------|---------------------------|--------|--------|
| batch 16 short | 16 × (512 + 256) ÷ 13.91  | 883    | 883.2  |
| batch 16 long  | 16 × (3584 + 512) ÷ 49.97 | 1,311  | 1311.4 |
| batch 24 long  | 24 × (3584 + 512) ÷ 61.16 | 1,607  | 1607.4 |

Prompt tokens are not output. In a long request the prompt is 3,584 of 4,096 tokens, which is 87.5%. So a long prompt makes the number bigger without producing more for the user. Both conclusions come from this: "longer prompts give better throughput" compares 1,311 with 883, and "batch 48 → ~3200" doubles the batch-24 reading: 1607.4 × 2 ≈ 3215.

## Honest goodput of the batch-24 long-prompt row

Goodput = generated tokens per second.

**Way 1, from `wall_clock_s`:** count what was generated.

```
24 requests × 512 generated tokens ÷ 61.16 s = 200.9 tok/s
```

**Way 2, from `reported_tok_s`:** remove the prompt tokens from the counter. Only 512 of every 4,096 counted tokens were generated.

```
1607.4 × 512 ÷ 4,096 = 200.9 tok/s
```

Both ways give **200.9 tok/s**.

## What the report should have said

| row            | reported tok/s | goodput (generated tok/s) |
|----------------|----------------|---------------------------|
| batch 16 short | 883.2          | 294.5                     |
| batch 16 long  | 1311.4         | 163.9                     |
| batch 24 long  | 1607.4         | 200.9                     |
| batch 48 long  | 1298.5         | 162.3                     |

- Longer prompts give **lower** throughput: 163.9 against 294.5 generated tok/s at batch 16.
- Batch 48 does not deliver ~3200 tok/s. The log's own batch-48 row shows 1,298.5 reported and 162.3 generated tok/s.
- For long prompts, plan on about 200 generated tok/s per L4, reached at batch 24. Throughput does not scale linearly with batch.
