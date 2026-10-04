# Lab notebook

In the order things happened. Each entry: what I expected → what I ran → what came out → what I changed.

## Part A

**1. Is the report's 5.89× an arithmetic slip?**
- Expected: yes. 7.45 ÷ 1.27 from the report's table is 5.87, not 5.89.
- Ran `fertility.py` unchanged: 1.2652, 7.4485 and 5.8871.
- Wrong. The script divides unrounded numbers. Dropped it as a finding.

**2. How much do the three code bugs matter?**
- Put each bug back alone into the fixed script: lowercase 5.93, split 6.09, averaging 6.09, against 6.11 fixed.
- All three together are only 3.8%.
- So the report's problem is not the code. Looked at the metric next.

**3. Tokens per word against tokens per sentence.**
- Question: does per word push every language the same way?
- Ran the fixed script on the corpus. Hindi: 6.34 per word, 7.42 per sentence. Tamil: 20.28 and 15.54.
- No. Per word is too low for Hindi and too high for Tamil, because the same sentence is 25.3 words in Hindi and 16.6 in Tamil.

**4. NFC and `random.seed`: bugs or not?**
- Expected: harmless, but that needed a measurement.
- Deleted the NFC line: 6.1137 before and after. `random` is never used after the seed.
- Both are fine. Listed them as "looks suspicious, is fine".

**5. Which denominator is the headline? I argued for bytes.**
- My view: tokens per UTF-8 byte. I had an answer claiming a 1.1 to 1.3× band per byte with XLM-R.
- Ran XLM-R on the corpus. Per byte: 0.42 to 0.49× English. Per sentence: 1.25 to 1.35×.
- The claim did not reproduce. Per byte makes Hindi look cheaper than English, because the same sentence is 131 bytes in English and 333 in Hindi. Changed to per parallel sentence.

**6. Memo: two statements I could not back.**
- "Our traffic is chat" and "our own tokenizer". The kit has no traffic sample and no tokenizer.
- Reworded the first as an assumption. Rewrote the recommendation as a choice between the two tokenizers I measured.

## Part B

**7. B1: is it 25 sequences?**
- Expected from the spec: 114,688 bytes per token, 105,329 tokens, 25 sequences.
- Predicted `kv_cache_util` and `preempted_seqs` for every row of the log: matches on 13 of 13.
- Two side checks. If "24 GB" meant GiB, batch 24 would read 0.82; the log says 0.93. With 24 KV heads only 8 sequences fit, but batch 16 ran with no preemption.

**8. B2: changed the proposed fix.**
- First choice: an fp8 KV cache. Its capacity is simple arithmetic, but its speed gain needed too many assumptions.
- Switched to `--max-num-seqs 24`, predicted from two rows of the log: 2 × 61.16 = 122.3 s against 151.41 s, +24%.
- Surprise: at batch 32 the same fix does not help (97.5 s against 94.71 s). Kept that in the write-up.

**9. Two things in the log I cannot explain.**
- `e2e_ms_p95` is larger than `wall_clock_s` in 12 of 13 rows. With all requests sent together that should not be possible.
- Median TTFT stays near 0.5 s from batch 4 to 24 on long prompts.
- I did not use either column for any conclusion.

## Part C

No experiment. It is a reasoning memo. The first version was rewritten after I found that fine-tuning cannot rescue a prompt that fails, since the training data would come from that same prompt.
