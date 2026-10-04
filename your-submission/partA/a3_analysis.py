#!/usr/bin/env python3
"""
a3_analysis.py -- corrected cross-language tokenizer comparison.

For every (tokenizer, language) it counts tokens on the SAME 1012 parallel
sentences and divides by five denominators:

    per whitespace word      (what the intern used)
    per code point           (what the intern called "char")
    per grapheme cluster     (what a reader calls a character)
    per UTF-8 byte
    per parallel sentence    (same meaning in every language)

Headline number: the TOKEN PREMIUM =
    total tokens for language L / total tokens for English
on identical content, with a paired-bootstrap 95% confidence interval.

Usage (from the repo root):
    python your-submission/partA/a3_analysis.py
    python your-submission/partA/a3_analysis.py --split dev          # replication
    python your-submission/partA/a3_analysis.py --text "नमस्ते दुनिया"  # one string, all tokenizers
    python your-submission/partA/a3_analysis.py --add ours=hf:<repo_id>   # add any tokenizer
    python your-submission/partA/a3_analysis.py --add c100k=tiktoken:cl100k_base
"""

import argparse
import pathlib
import unicodedata
import warnings

import numpy as np
import pandas as pd
import regex

warnings.filterwarnings("ignore")

HERE = pathlib.Path(__file__).resolve().parent
LANGS = ["eng", "hin", "mar", "ben", "kan", "tam", "tel", "mal"]

# name -> (kind, id, pinned revision)
TOKENIZERS = {
    "gpt2": ("tiktoken", "gpt2", None),
    "o200k_base": ("tiktoken", "o200k_base", None),
    "qwen2.5": ("hf", "Qwen/Qwen2.5-7B-Instruct", "a09a35458c702b33eeacc393d103063234e8bc28"),
    "xlm-r": ("hf", "xlm-roberta-base", "e73636d4f797dec63c3081bb6ed5c7b0bb3f2089"),
    "muril": ("hf", "google/muril-base-cased", "afd9f36c7923d54e97903922ff1b260d091d202f"),
    "sarvam-1": ("hf", "sarvamai/sarvam-1", "e9607337286ddf496d4a2562b194e489dcf3feea"),
}


def load(name):
    """Return (encode, unk_id). encode(str) -> list of token ids, no special tokens."""
    kind, ident, rev = TOKENIZERS[name]
    if kind == "tiktoken":
        import tiktoken
        enc = tiktoken.get_encoding(ident)
        return (lambda s: enc.encode(s, disallowed_special=())), None
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(ident, revision=rev)
    return (lambda s: tok.encode(s, add_special_tokens=False)), tok.unk_token_id


def read(split, lang):
    text = (HERE / "corpus" / split / f"{lang}.txt").read_text(encoding="utf-8")
    return text.rstrip("\n").split("\n")


def units(lines):
    """Per-line denominators as numpy arrays."""
    return {
        "word": np.array([len(s.split()) for s in lines]),
        "codepoint": np.array([len(s) for s in lines]),
        "grapheme": np.array([len(regex.findall(r"\X", s)) for s in lines]),
        "byte": np.array([len(s.encode("utf-8")) for s in lines]),
    }


def bootstrap_ratio(num, den, reps=2000, seed=0):
    """Paired bootstrap over sentences for sum(num)/sum(den)."""
    rng = np.random.default_rng(seed)
    n = len(num)
    idx = rng.integers(0, n, size=(reps, n))
    r = num[idx].sum(axis=1) / den[idx].sum(axis=1)
    return np.percentile(r, [2.5, 97.5])


def one_text(text):
    print(f"text: {text!r}")
    n_graphemes = len(regex.findall(r"\X", text))
    n_bytes = len(text.encode("utf-8"))
    print(f"words={len(text.split())} graphemes={n_graphemes} "
          f"code_points={len(text)} utf8_bytes={n_bytes}")
    for name in TOKENIZERS:
        encode, _ = load(name)
        print(f"  {name:<12}{len(encode(text)):>5} tokens")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="devtest", choices=["devtest", "dev"])
    ap.add_argument("--tokenizers", nargs="+", default=list(TOKENIZERS))
    ap.add_argument("--langs", nargs="+", default=LANGS)
    ap.add_argument("--nfc", action="store_true", help="NFC-normalise before tokenizing")
    ap.add_argument("--limit", type=int, default=None, help="use only the first N sentences")
    ap.add_argument("--text", default=None, help="tokenize one string with every tokenizer and exit")
    ap.add_argument("--add", action="append", default=[], metavar="NAME=KIND:ID",
                    help="extra tokenizer, e.g. ours=hf:org/model or c100k=tiktoken:cl100k_base")
    args = ap.parse_args()

    for item in args.add:
        name, rest = item.split("=", 1)
        kind, ident = rest.split(":", 1)
        TOKENIZERS[name] = (kind, ident, None)
        if name not in args.tokenizers:
            args.tokenizers.append(name)

    if args.text is not None:
        return one_text(args.text)

    corpus = {l: read(args.split, l)[: args.limit] for l in args.langs}
    if args.nfc:
        corpus = {l: [unicodedata.normalize("NFC", s) for s in v] for l, v in corpus.items()}
    den = {l: units(v) for l, v in corpus.items()}
    n = len(corpus["eng"])

    rows, per_line = [], {}
    for name in args.tokenizers:
        encode, unk_id = load(name)
        for lang in args.langs:
            ids = [encode(s) for s in corpus[lang]]
            t = np.array([len(x) for x in ids])
            per_line[(name, lang)] = t
            unk = sum(x.count(unk_id) for x in ids) if unk_id is not None else 0
            rows.append({
                "tokenizer": name, "lang": lang, "tokens": int(t.sum()),
                "tok/sentence": t.sum() / n,
                "tok/word": t.sum() / den[lang]["word"].sum(),
                "tok/grapheme": t.sum() / den[lang]["grapheme"].sum(),
                "tok/codepoint": t.sum() / den[lang]["codepoint"].sum(),
                "tok/byte": t.sum() / den[lang]["byte"].sum(),
                "unk_%": 100 * unk / t.sum(),
            })
    df = pd.DataFrame(rows)

    # premium vs English on the same sentences, per tokenizer
    prem = []
    for name in args.tokenizers:
        e = per_line[(name, "eng")]
        eng = df[(df.tokenizer == name) & (df.lang == "eng")].iloc[0]
        for lang in args.langs:
            t = per_line[(name, lang)]
            row = df[(df.tokenizer == name) & (df.lang == lang)].iloc[0]
            lo, hi = bootstrap_ratio(t, e)
            prem.append({
                "tokenizer": name, "lang": lang,
                "premium": t.sum() / e.sum(), "ci_lo": lo, "ci_hi": hi,
                "x_per_word": row["tok/word"] / eng["tok/word"],
                "x_per_grapheme": row["tok/grapheme"] / eng["tok/grapheme"],
                "x_per_codepoint": row["tok/codepoint"] / eng["tok/codepoint"],
                "x_per_byte": row["tok/byte"] / eng["tok/byte"],
            })
    pf = pd.DataFrame(prem)
    df = df.merge(pf, on=["tokenizer", "lang"])

    pd.set_option("display.width", 250)
    pd.set_option("display.float_format", lambda v: f"{v:.3f}")
    tag = args.split + ("_nfc" if args.nfc else "") + (f"_first{args.limit}" if args.limit else "")
    print(f"corpus: FLORES-200 {args.split}, {n} parallel sentences, nfc={args.nfc}")

    print("\n[1] RAW RATES per tokenizer and language")
    print(df[["tokenizer", "lang", "tokens", "tok/sentence", "tok/word", "tok/grapheme",
              "tok/codepoint", "tok/byte", "unk_%"]].to_string(index=False))

    print("\n[2] TOKEN PREMIUM vs English (same sentences) -- the headline number")
    print(pf.pivot(index="lang", columns="tokenizer", values="premium")
          .loc[args.langs, args.tokenizers].to_string())

    print("\n[3] 95% bootstrap CI of the premium (2000 paired resamples of sentences)")
    ci = pf.assign(ci=pf.apply(lambda r: f"{r.ci_lo:.2f}-{r.ci_hi:.2f}", axis=1))
    print(ci.pivot(index="lang", columns="tokenizer", values="ci").loc[args.langs, args.tokenizers].to_string())

    print("\n[4] ABSOLUTE tokens per sentence (what you actually pay for)")
    print(df.pivot(index="lang", columns="tokenizer", values="tok/sentence")
          .loc[args.langs, args.tokenizers].to_string())

    print("\n[5] 'HOW MANY TIMES WORSE THAN ENGLISH' depends on the denominator")
    cols = ["x_per_word", "x_per_codepoint", "x_per_grapheme", "x_per_byte", "premium"]
    for name in args.tokenizers:
        sub = pf[pf.tokenizer == name].set_index("lang").loc[args.langs, cols]
        sub = sub.rename(columns={"premium": "x_per_sentence"})
        print(f"\n  tokenizer = {name}")
        print("  " + sub.to_string().replace("\n", "\n  "))

    out = HERE / "results"
    out.mkdir(exist_ok=True)
    df.to_csv(out / f"a3_{tag}.csv", index=False)
    print(f"\nwrote {out / f'a3_{tag}.csv'}")


if __name__ == "__main__":
    main()
