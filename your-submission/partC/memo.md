# Part C — Casual tone in six Indic languages: recommendation

**Recommendation: ship (c) prompt engineering, with (a) LoRA fine-tuning as a fallback that starts on day 6 only if the kill criterion fires. Reject (b).**

The scarce resource is the reviewer, not the GPU. A fine-tune takes minutes; checking that its Hindi sounds natural takes hours, and nobody can check four of the six languages.

## Assumptions

- The main model is the 4.2 B model from Part B, served with vLLM on an L4. Replies average 150 tokens.
- Without an API budget, "casualized" training pairs can only come from a prompted open model on our A100.
- The reviewer makes one blind A/B judgment in 45 seconds.
- A sample of real user prompts exists in Hindi and Kannada.

## Arithmetic

| item | calculation | result |
|---|---|---|
| Reviewer capacity | 10 h × 80 judgments/h | 800 per week, 2,400 in 3 weeks, **2 of 6 languages** |
| One evaluation round | 200 pairs × 2 languages | 400 judgments = 5 h; ±6.4 points at 70% |
| (c) prompt overhead | 300 extra prompt tokens × 114,688 B | 34 MB of KV per request (7% of a full context); ~21 ms prefill |
| (a) data | 6 languages × 2,000 pairs × 250 tokens | 3.0 M tokens; generating it takes about 1 h |
| (a) training | 6 × 4.2 B × 3.0 M = 7.6 × 10¹⁶ FLOPs ÷ (35% of 312 TFLOPS) | **12 min per epoch**; under 1% of the 336 A100-hours |
| (b) latency | rewriter needs the full reply first: 150 × 43.5 ms + 150 × 10 ms | first token after **~8 s** instead of 0.07 s; streaming is lost |
| (b) memory | 1 B × 2 bytes = 2 GB out of the 12.08 GB KV budget | concurrency falls from 25 to 21 sequences |

## Why this path

- **(a) depends on (c).** Its training pairs come from a prompted model, so a fine-tune can at best reproduce what the prompt already does. The prompt has to be built first either way. Fine-tuning then buys back the 300 prompt tokens and adds consistency, at the price of new weights to re-validate inside three weeks.
- **(b) costs every request, permanently:** 8 seconds to first token, 16% less concurrency, and a second model that can change the meaning of an answer.

## Success metric

Blind pairwise test, current reply against new reply, 200 prompts per language. The reviewer prefers the new reply as natural casual speech in **at least 70%** of pairs, and flags a change of meaning in **at most 3%**.

## Kill criterion

**By end of day 5,** after two prompt iterations: if the best prompt wins **under 55%** in Hindi or Kannada, or changes meaning in over 5% of replies, stop prompt-only work. Start LoRA on day 6, trained on reviewer-approved outputs, with a second gate on day 14. A language still under 70% on day 14 stays formal at launch.

## Day-1 experiment

Take 100 real prompts each in Hindi and Kannada. Generate replies with the current prompt and with one casual prompt (register rules plus five reviewer-written examples). The reviewer blind-rates the 200 pairs in 2.5 hours. Record win rate, meaning-change rate, and tokens per reply, since casual text mixes in English and may tokenize differently (Part A).

## The risk to raise at launch review

Tamil, Telugu, Bengali and Marathi get no human check. An LLM judge can stand in only if it agrees with the reviewer on at least 85% of Hindi and Kannada pairs first. The cheaper fix is two hours of a native speaker per language.
