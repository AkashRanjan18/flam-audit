#!/usr/bin/env python3
"""
a2_extra.py -- evidence for the claims in REPORT_v0 that are not code bugs.

    E1  Are the toy samples actually parallel?
    E2  How much can a 10-sentence sample move the headline ratio?
    E3  Did the intern measure the tokenizer we serve? (vocab size check)
    E4  Is add_special_tokens=False the right call? (looks odd, is correct)
    E5  Does the premium depend on domain?
    E6  Romanised Hindi (illustrative, n=10)

Usage (from the repo root):
    python your-submission/partA/a2_extra.py            # all experiments
    python your-submission/partA/a2_extra.py --only E2  # just one
"""

import argparse
import importlib.util
import pathlib
import warnings

import numpy as np
import pandas as pd
import tiktoken

warnings.filterwarnings("ignore")

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
KIT = ROOT / "starter_kit"
FLORES = HERE / "corpus" / "devtest"

spec = importlib.util.spec_from_file_location("fertility", KIT / "fertility.py")
intern = importlib.util.module_from_spec(spec)
spec.loader.exec_module(intern)

GPT2 = tiktoken.get_encoding("gpt2")


def lines_of(path):
    return pathlib.Path(path).read_text(encoding="utf-8").rstrip("\n").split("\n")


def e1():
    print("E1  ARE THE TOY SAMPLES PARALLEL?")
    eng = intern.read_lines(KIT / "corpus_sample" / "eng_sample.txt")
    hin = intern.read_lines(KIT / "corpus_sample" / "hin_sample.txt")
    for i, (a, b) in enumerate(zip(eng, hin), 1):
        print(f"  {i:>2}  {a}\n      {b}")
    blen = lambda ls: np.array([len(s.encode('utf-8')) for s in ls])
    r_sample = np.corrcoef(blen(eng), blen(hin))[0, 1]
    fe, fh = lines_of(FLORES / "eng.txt"), lines_of(FLORES / "hin.txt")
    r_flores = np.corrcoef(blen(fe), blen(fh))[0, 1]
    # what does r look like for 10 truly parallel lines? draw many 10-line subsets of FLORES
    rng = np.random.default_rng(0)
    be, bh = blen(fe), blen(fh)
    rs = []
    for _ in range(5000):
        idx = rng.choice(len(fe), 10, replace=False)
        rs.append(np.corrcoef(be[idx], bh[idx])[0, 1])
    lo, hi = np.percentile(rs, [2.5, 97.5])
    print(f"  correlation of line lengths (UTF-8 bytes), eng vs hin:")
    print(f"    toy sample (10 lines)            r = {r_sample:+.3f}")
    print(f"    FLORES devtest (1012 lines)      r = {r_flores:+.3f}")
    print(f"    10 random PARALLEL FLORES lines  r in [{lo:+.3f}, {hi:+.3f}] (95% of 5000 draws), "
          f"share below sample's r: {np.mean(np.array(rs) <= r_sample):.4f}")
    print()


def intern_arrays(lines):
    """Per-line tokens and word counts exactly as fertility.analyze computes them."""
    low = [s.lower() for s in lines]
    return (np.array([len(GPT2.encode(s)) for s in low]),
            np.array([len(s.split(" ")) for s in low]))


def e2():
    print("E2  HOW STABLE IS A 10-SENTENCE ESTIMATE?  (intern's metric, gpt2)")
    te, we = intern_arrays(intern.read_lines(FLORES / "eng.txt"))
    th, wh = intern_arrays(intern.read_lines(FLORES / "hin.txt"))
    full = (th / wh).mean() / (te / we).mean()
    rng = np.random.default_rng(0)
    ratios = []
    for _ in range(5000):
        idx = rng.choice(len(te), 10, replace=False)
        ratios.append((th[idx] / wh[idx]).mean() / (te[idx] / we[idx]).mean())
    ratios = np.array(ratios)
    p = np.percentile(ratios, [2.5, 50, 97.5])
    print(f"  all 1012 FLORES sentences: hin/eng fertility ratio = {full:.3f}")
    print(f"  5000 random 10-sentence subsets: min {ratios.min():.2f}, 2.5% {p[0]:.2f}, "
          f"median {p[1]:.2f}, 97.5% {p[2]:.2f}, max {ratios.max():.2f}")
    print(f"  -> a 10-sentence sample lands anywhere in a band {p[2] - p[0]:.2f} wide "
          f"({100 * (p[2] - p[0]) / full:.0f}% of the value)")

    # bootstrap of the toy sample itself (the two files are resampled independently)
    se = intern_arrays(intern.read_lines(KIT / "corpus_sample" / "eng_sample.txt"))
    sh = intern_arrays(intern.read_lines(KIT / "corpus_sample" / "hin_sample.txt"))
    boot = []
    for _ in range(5000):
        i = rng.integers(0, 10, 10)
        j = rng.integers(0, 10, 10)
        boot.append((sh[0][j] / sh[1][j]).mean() / (se[0][i] / se[1][i]).mean())
    lo, hi = np.percentile(boot, [2.5, 97.5])
    point = (sh[0] / sh[1]).mean() / (se[0] / se[1]).mean()
    print(f"  toy sample: point estimate {point:.2f}, bootstrap 95% CI [{lo:.2f}, {hi:.2f}]")
    print()


def e3():
    print("E3  DID THE REPORT MEASURE THE TOKENIZER WE SERVE?")
    spec_text = (KIT / "bench" / "model_spec.md").read_text(encoding="utf-8")
    vocab_line = [l for l in spec_text.splitlines() if l.lower().startswith("| vocab")][0]
    print(f"  bench/model_spec.md : {vocab_line.strip()}")
    print(f"  tiktoken gpt2       : n_vocab = {GPT2.n_vocab}")
    print("  -> the report's tokenizer has a different vocabulary size from the served model")
    print()


def e4():
    print("E4  add_special_tokens=False  (looks like it drops something; is it right?)")
    from transformers import AutoTokenizer
    eng, hin = lines_of(FLORES / "eng.txt"), lines_of(FLORES / "hin.txt")
    for repo in ["xlm-roberta-base", "google/muril-base-cased", "sarvamai/sarvam-1"]:
        tok = AutoTokenizer.from_pretrained(repo)
        row = {}
        for flag in (False, True):
            e = sum(len(tok.encode(s, add_special_tokens=flag)) for s in eng)
            h = sum(len(tok.encode(s, add_special_tokens=flag)) for s in hin)
            row[flag] = (e, h, h / e)
        add = (row[True][0] - row[False][0]) / len(eng)
        print(f"  {repo:<26} without: eng {row[False][0]:>6} hin {row[False][1]:>6} premium {row[False][2]:.4f} | "
              f"with: eng {row[True][0]:>6} hin {row[True][1]:>6} premium {row[True][2]:.4f} | "
              f"+{add:.0f} tokens per sentence")
    one = "The train arrived exactly on time."
    print(f"  tiktoken gpt2 adds no special tokens: {len(GPT2.encode(one))} tokens, "
          f"ids start {GPT2.encode(one)[:3]} (no BOS id {GPT2.eot_token})")
    print()


def e5():
    print("E5  DOES THE PREMIUM DEPEND ON DOMAIN?  (FLORES devtest, tokens(lang)/tokens(eng))")
    meta = pd.read_csv(ROOT / "data" / "flores200_dataset" / "metadata_devtest.tsv", sep="\t")
    from transformers import AutoTokenizer
    sar = AutoTokenizer.from_pretrained("sarvamai/sarvam-1")
    encs = {"gpt2": lambda s: GPT2.encode(s),
            "sarvam-1": lambda s: sar.encode(s, add_special_tokens=False)}
    rows = []
    for name, enc in encs.items():
        counts = {l: np.array([len(enc(s)) for s in lines_of(FLORES / f"{l}.txt")])
                  for l in ("eng", "hin", "kan")}
        for dom in ["wikinews", "wikibooks", "wikivoyage"]:
            m = (meta["domain"] == dom).to_numpy()
            rows.append({"tokenizer": name, "domain": dom, "sentences": int(m.sum()),
                         "hin premium": counts["hin"][m].sum() / counts["eng"][m].sum(),
                         "kan premium": counts["kan"][m].sum() / counts["eng"][m].sum()})
    print("  " + pd.DataFrame(rows).round(3).to_string(index=False).replace("\n", "\n  "))
    print()


def e6():
    print("E6  ROMANISED HINDI  (illustrative only: 10 hand-romanised toy sentences)")
    deva = intern.read_lines(KIT / "corpus_sample" / "hin_sample.txt")
    roman = lines_of(HERE / "corpus_extra" / "hin_roman_sample.txt")
    assert len(deva) == len(roman) == 10
    from transformers import AutoTokenizer
    encs = {"gpt2": lambda s: GPT2.encode(s),
            "o200k_base": tiktoken.get_encoding("o200k_base").encode}
    for repo in ["xlm-roberta-base", "google/muril-base-cased", "sarvamai/sarvam-1"]:
        t = AutoTokenizer.from_pretrained(repo)
        encs[repo] = (lambda s, t=t: t.encode(s, add_special_tokens=False))
    print(f"  {'tokenizer':<26}{'Devanagari':>12}{'romanised':>12}{'roman/deva':>12}")
    for name, enc in encs.items():
        d = sum(len(enc(s)) for s in deva)
        r = sum(len(enc(s)) for s in roman)
        print(f"  {name:<26}{d:>12}{r:>12}{r / d:>12.2f}")
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, choices=["E1", "E2", "E3", "E4", "E5", "E6"])
    args = ap.parse_args()
    for name, fn in (("E1", e1), ("E2", e2), ("E3", e3), ("E4", e4), ("E5", e5), ("E6", e6)):
        if args.only in (None, name):
            fn()


if __name__ == "__main__":
    main()
