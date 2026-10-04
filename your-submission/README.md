# The Audit — submission

An audit of `REPORT_v0.md`: the tokenizer numbers (Part A), the serving capacity numbers (Part B), and a decision memo on casual tone in Indic languages (Part C).

## Where to read

| Deliverable | File |
|---|---|
| A1 corpus | `partA/A1_corpus.md` |
| A2 script and metric audit | `partA/A2_audit.md` |
| A3 corrected analysis | `partA/A3_analysis.md` |
| A4 recommendation memo | `partA/A4_memo.md` |
| B1–B4 | `partB/answers.md` |
| C memo | `partC/memo.md` |
| Lab notebook | `NOTEBOOK.md` |
| AI usage | `AI_USAGE.md` |

## Layout

```
starter_kit/                  the kit as received, untouched
data/                         FLORES-200 download (created by prepare_corpus.py, not committed)
your-submission/
  requirements.txt            pinned versions (Python 3.9.9)
  partA/
    prepare_corpus.py         A1: download, verify, extract, check alignment
    audit_a2.py               A2: one switch at a time against fertility.py
    a2_extra.py               A2: experiments E1–E6
    a3_analysis.py            A3: 8 languages × 6 tokenizers × 5 denominators
    corpus/                   the eval corpus (devtest and dev)
    corpus_extra/             10 hand-romanized Hindi sentences
    results/                  saved output of every command
  partB/
    b_capacity.py             B1–B3 and the open questions
    results/
  partC/memo.md
```

## Reproduce

From the repo root, on Python 3.9 or later:

```
python -m venv .venv
.venv\Scripts\activate                      # Windows; use `source .venv/bin/activate` elsewhere
pip install -r your-submission/requirements.txt
set PYTHONIOENCODING=utf-8                  # Windows only, so Indic text prints
```

| Claim | Command |
|---|---|
| The report's numbers reproduce | `cd starter_kit` then `python fertility.py --corpus eng=corpus_sample/eng_sample.txt --corpus hin=corpus_sample/hin_sample.txt --tokenizer gpt2` |
| Build the corpus | `python your-submission/partA/prepare_corpus.py` |
| A2 code bugs and harmless items | `python your-submission/partA/audit_a2.py` |
| A2 on real text | `python your-submission/partA/audit_a2.py --eng your-submission/partA/corpus/devtest/eng.txt --other your-submission/partA/corpus/devtest/kan.txt --label kan` |
| A2 experiments E1–E6 | `python your-submission/partA/a2_extra.py` (one only: `--only E2`) |
| A3 corrected analysis | `python your-submission/partA/a3_analysis.py` |
| A3 replication | `python your-submission/partA/a3_analysis.py --split dev` |
| A3 with NFC | `python your-submission/partA/a3_analysis.py --nfc` |
| Any sentence, all tokenizers | `python your-submission/partA/a3_analysis.py --text "आप कैसे हैं?"` |
| Add a tokenizer | `python your-submission/partA/a3_analysis.py --add ours=hf:<repo_id>` |
| Part B | `python your-submission/partB/b_capacity.py` |
| Part B counterfactual | `python your-submission/partB/b_capacity.py --kv-bytes 1` |

The first tokenizer run downloads four tokenizers from Hugging Face (no account needed). No GPU is used anywhere.
