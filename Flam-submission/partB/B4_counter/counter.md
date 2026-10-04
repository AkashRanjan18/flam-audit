# B4 — The counter that confirms the B2 mechanism

I would pull **`vllm:num_preemptions_total`**, the counter vLLM exports for the number of preemptions. If B2 is right, its increase over a run should be **0 for every batch up to 24**, **at least 7 for batch 32** and **at least 23 for batch 48**. It is "at least" because the counter counts every preemption and one sequence can be preempted more than once, while the log's `preempted_seqs` counts each sequence once. If the counter stayed at 0 for batch 32 or 48, my B2 explanation would be wrong.
