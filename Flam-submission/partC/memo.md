# Part C — Casual tone in six Indic languages

**Recommendation: (c) prompt engineering.** Use the GPU for (a) only if the day-5 result is in the middle band below. Do not build (b).

**The reasoning in three lines**

1. The scarce resource is the reviewer, not the GPU. I get 30 reviewer-hours in total, for 2 of the 6 languages.
2. With no API, training pairs for (a) or (b) can only come from our own prompted model. So training cannot teach a tone the prompt cannot already produce. It can only make a working prompt more consistent.
3. So the prompt has to be tested first whichever path is chosen, and it is the cheapest thing to test.

## Assumptions

- "Casual" means how people actually talk: everyday spoken words, slang, Hindi-English mix and short sentences. Slang is fine when it is not aimed at anyone. The reply never insults or talks down to the user, whatever the user says to it.
- The main model is the 4.2 B model from Part B. Cost scales with size if it is bigger.
- The reviewer needs about 2 minutes for one blind A/B judgment.
- I can get about 120 real user prompts each in Hindi and Kannada.

## Arithmetic

| Item                  | Calculation                                   | Result                                           |
|-----------------------|-----------------------------------------------|--------------------------------------------------|
| Reviewer throughput   | 10 h × 30 judgments/h                         | 300 a week, 900 in 3 weeks, 2 languages only     |
| One test round        | 90 pairs × 2 languages × 2 min                | 6 h; a 70% result is ±9.5 points                 |
| Data volume for (a)   | 6 languages × 2,000 pairs × 250 tokens        | 12,000 pairs, 3.0 M tokens                       |
| Share I can check     | 900 ÷ 12,000                                  | 7.5%, and 0% in four languages                   |
| Training cost for (a) | 6 × 4.2 B × 3.0 M FLOPs ÷ (35% of 312 TFLOPS) | about 12 min per epoch; 2 h even if I am off 10× |
| Serving cost for (c)  | about 400 extra prompt tokens per request     | about 10% of a 4,096-token context               |
| Serving cost for (b)  | a second model writes the whole reply again   | no streaming until the first reply is finished   |

Training is minutes. Checking is weeks. That is why I do not start with the GPU.

## Success metric

Blind A/B on 90 held-out prompts per language (Hindi, Kannada), new reply against current reply:

- the reviewer prefers the new reply in **at least 70%** of pairs, and
- **at most 3 of the 90** new replies change the meaning or are insulting to the user.

Tamil, Telugu, Bengali and Marathi cannot be measured with this reviewer. I make no "casual" claim for them without a native speaker checking 30 replies each.

## Kill criterion

**End of day 5, on the 90-pair test:**

| Result in Hindi or Kannada | Decision                                                                                |
|----------------------------|-----------------------------------------------------------------------------------------|
| 70% or more                | Keep the prompt. Confirm on fresh prompts in week 3.                                    |
| 55% to 70%                 | Works, but not reliably. Week 2: one LoRA run (a) on reviewer-preferred replies.        |
| **Under 55%**              | **Abandon the casual-tone launch for that language.** Go to review with the limitation. |

At 90 pairs, 55% cannot be told apart from a coin flip (±10 points). A model that cannot write casual text with examples in the prompt will not learn it from its own output.

## Day-1 experiment

The reviewer writes 5 casual example replies in each language (2 h). I take 30 prompts per language and generate replies with the current prompt and with a casual prompt (rules plus those 5 examples). The reviewer blind-rates the 60 pairs (2 h). This tells me in one day whether the model can write casual Hindi and Kannada at all, before any GPU time is spent.
