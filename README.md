# The Audit — submission

An audit of `starter_kit/REPORT_v0.md`: the tokenizer numbers (Part A), the serving capacity numbers (Part B) and a decision memo (Part C).

## What is where

| Part | Folder                                        | Read this                    |
|------|-----------------------------------------------|------------------------------|
| A1   | `Flam-submission/partA/A1_eval_corpus`        | `eval_corpus.md`             |
| A2   | `Flam-submission/partA/A2_script_audit`       | `fertility_audit.md`         |
| A3   | `Flam-submission/partA/A3_corrected_analysis` | `corrected_analysis.md`      |
| A4   | `Flam-submission/partA/A4_memo`               | `recommendation_memo.md`     |
| B1   | `Flam-submission/partB/B1_kv_cache`           | `kv_cache.md`                |
| B2   | `Flam-submission/partB/B2_throughput_anomaly` | `throughput_anomaly.md`      |
| B3   | `Flam-submission/partB/B3_goodput`            | `goodput.md`                 |
| B4   | `Flam-submission/partB/B4_counter`            | `counter.md`                 |
| C    | `Flam-submission/partC`                       | `memo.md`                    |
|      | `Flam-submission`                             | `NOTEBOOK.md`, `AI_USAGE.md` |

Each `results.txt` is the saved output behind the numbers in the write-up next to it. Parts B and C have no code: B is arithmetic shown in the write-ups, and C is a memo.

## Setup

Python 3.9 or later. Run everything from the repo root (the folder that contains `starter_kit/` and `Flam-submission/`).

```
pip install tiktoken==0.14.0 transformers==4.57.6 tokenizers==0.22.2 sentencepiece==0.2.2 regex==2026.1.15 protobuf==6.33.6
```

On Windows, set this first so Indic text prints correctly:

```
set PYTHONIOENCODING=utf-8
```

## Run

**1. Build the corpus (A1).** Downloads FLORES-200 once into `data/`, checks its SHA-256, and writes the four language files.

```
python Flam-submission/partA/A1_eval_corpus/prepare_corpus.py
```

**2. The corrected script on the intern's samples (A2).** Prints 6.1137 for Hindi ÷ English per word.

```
python Flam-submission/partA/A2_script_audit/fertility_fixed.py --corpus eng=starter_kit/corpus_sample/eng_sample.txt --corpus hin=starter_kit/corpus_sample/hin_sample.txt
```

**3. The corrected analysis (A3).** Same script on the A1 corpus, once per tokenizer. `C` stands for `Flam-submission/partA/A1_eval_corpus/corpus`.

```
python Flam-submission/partA/A2_script_audit/fertility_fixed.py --corpus eng=C/eng.txt --corpus hin=C/hin.txt --corpus tam=C/tam.txt --corpus tel=C/tel.txt --tokenizer gpt2
python Flam-submission/partA/A2_script_audit/fertility_fixed.py --corpus eng=C/eng.txt --corpus hin=C/hin.txt --corpus tam=C/tam.txt --corpus tel=C/tel.txt --tokenizer hf:sarvamai/sarvam-1
```

**4. Any other text or tokenizer.** Save the text in a file, one sentence per line, and pass it as a corpus. Any Hugging Face tokenizer works with `hf:<repo_id>`.

```
python Flam-submission/partA/A2_script_audit/fertility_fixed.py --corpus x=my_text.txt --tokenizer hf:xlm-roberta-base
```

## Things to know

- **Internet is needed on the first run.** `prepare_corpus.py` downloads FLORES-200 (about 25 MB). The `gpt2` and Sarvam-1 tokenizer files are downloaded the first time each is used, then cached. No account or login is required.
- **`data/` is not in the repo.** It is created by step 1.
- **No GPU is used anywhere.**
- **To see one bug from A2 on its own,** change that one line in `fertility_fixed.py` back to the old line shown in the comment above it, and rerun step 2. `Flam-submission/partA/A2_script_audit/results.txt` lists each edit and its output.
- **The domain counts in A1** (Wikinews 341, Wikibooks 351, Wikivoyage 320) come from FLORES's own metadata file, `data/flores200_dataset/metadata_devtest.tsv`, in its `domain` column.
- **`Flam-submission/partB/B1_kv_cache/results.txt`** is the B1 arithmetic applied to all 13 rows of `bench_log.csv`. Any row can be checked by hand: batch × (prompt_len + gen_len) ÷ 105,329.
