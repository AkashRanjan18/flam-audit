#!/usr/bin/env python3
"""
fertility_fixed.py -- the intern's fertility.py with its bugs corrected.

Each fix is marked "BUG n FIXED" with the old line shown above the new one.
Reports tokens per word, per grapheme cluster, per UTF-8 byte and per sentence.
("Per sentence" only means something on a parallel corpus.)

Usage (from the repo root):
    python Flam-submission/partA/A2_script_audit/fertility_fixed.py \
        --corpus eng=starter_kit/corpus_sample/eng_sample.txt \
        --corpus hin=starter_kit/corpus_sample/hin_sample.txt

Tokenizers:
    gpt2            -> tiktoken "gpt2" encoding (default)
    hf:<repo_id>    -> any HuggingFace tokenizer, e.g. hf:sarvamai/sarvam-1
"""

import argparse
import unicodedata

import regex  # third-party: its \X pattern matches one visible character (grapheme cluster)

# REMOVED: `import random` and `random.seed(1337)`. Nothing in the script used them.


def load_tokenizer(spec: str):
    if spec.startswith("hf:"):
        from transformers import AutoTokenizer

        tok = AutoTokenizer.from_pretrained(spec[3:])
        return lambda s: tok.encode(s, add_special_tokens=False)
    else:
        import tiktoken

        enc = tiktoken.get_encoding(spec)
        return enc.encode


def read_lines(path: str):
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            # KEPT: NFC normalisation looks suspicious but changes no number here.
            line = unicodedata.normalize("NFC", line)
            lines.append(line)
    return lines


def analyze(lines, encode):
    """Return tokens per (word, grapheme cluster, UTF-8 byte, sentence)."""
    total_tokens = total_words = total_graphemes = total_bytes = 0
    for line in lines:
        # BUG 1 FIXED: lowercasing changed English tokens but not Hindi (no capitals).
        # old: line = line.lower()
        # new: the text is tokenized as written.

        tokens = encode(line)

        # BUG 2 FIXED: a double space made an empty string that was counted as a word.
        # old: words = line.split(" ")
        words = line.split()

        total_tokens += len(tokens)
        total_words += len(words)
        total_graphemes += len(regex.findall(r"\X", line))  # visible characters
        total_bytes += len(line.encode("utf-8"))

    # BUG 3 FIXED: averaging per-line ratios let a 4-word line count as much as a 12-word line.
    # old: return sum(per_line_fertility) / n      (mean of each line's tokens / words)
    # new: total tokens divided by total words.
    return (total_tokens / total_words,
            total_tokens / total_graphemes,
            total_tokens / total_bytes,
            total_tokens / len(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", action="append", required=True, metavar="LANG=PATH",
                    help="language code and path, e.g. eng=data/eng.txt (repeatable)")
    ap.add_argument("--tokenizer", default="gpt2")
    args = ap.parse_args()

    encode = load_tokenizer(args.tokenizer)

    print(f"tokenizer: {args.tokenizer}")
    print(f"{'lang':<6}{'tok/word':>10}{'tok/grapheme':>14}{'tok/byte':>10}{'tok/sentence':>14}")
    print("-" * 54)
    results = {}
    for spec in args.corpus:
        lang, path = spec.split("=", 1)
        results[lang] = analyze(read_lines(path), encode)
        w, g, b, s = results[lang]
        print(f"{lang:<6}{w:>10.4f}{g:>14.4f}{b:>10.4f}{s:>14.2f}")

    base = next(iter(results))  # the first corpus is the reference language
    print(f"\ntimes {base}:")
    print(f"{'lang':<6}{'per word':>10}{'per grapheme':>14}{'per byte':>10}{'per sentence':>14}")
    for lang, vals in results.items():
        if lang != base:
            w, g, b, s = (v / r for v, r in zip(vals, results[base]))
            print(f"{lang:<6}{w:>10.4f}{g:>14.4f}{b:>10.4f}{s:>14.4f}")


if __name__ == "__main__":
    main()
