# AI usage

I used Claude (Claude Code), and Grok for a second opinion.

## Where it helped

- **Part A:** I asked Claude to find the bugs in `fertility.py`, and to write `prepare_corpus.py`, the script that builds the corpus.
- **Part B:** I did the calculations myself. I took Claude's help for the theory behind them: the KV cache, GQA, preemption and goodput.
- **Part C:** I read Claude's reasoning and Grok's reasoning, and then made my own conclusion.
- **Throughout:** Claude wrote the code and the text the way I asked for it. What to include, what to cut and what to conclude were my decisions.

## Where it misled me

1. Claude called the report's 5.89× an arithmetic error. It reproduces exactly when the script is run.
2. Claude's first list of bugs had three that do not exist: special tokens, `zip()` cutting lines, and a wrong encoding.
3. Claude stated assumptions as facts ("our traffic is chat", "our own tokenizer"). The kit has neither. I had both reworded.
4. Claude's first Part C memo offered fine-tuning as a rescue for a failed prompt, though the training data would come from that same prompt.
5. Grok's B4 named a counter that could not be found in vLLM's source, and gave two metrics where one was asked.

## What is estimated, not measured

The `--max-num-seqs 24` gain in B2 and the fp8 option are estimates from the log and the spec. Nothing was run on a GPU.
