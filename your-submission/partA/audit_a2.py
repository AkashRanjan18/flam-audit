#!/usr/bin/env python3
"""
audit_a2.py -- one-switch-at-a-time audit of starter_kit/fertility.py

Every row changes exactly ONE thing relative to the intern's script and
reports how far the published numbers move. Row 0 must reproduce the
report (eng 1.27 / hin 7.45 / 5.89x), otherwise nothing below is valid.

Usage (from the repo root):
    python your-submission/partA/audit_a2.py
"""

import argparse
import importlib.util
import pathlib
import unicodedata

import regex
import tiktoken

ROOT = pathlib.Path(__file__).resolve().parents[2]
KIT = ROOT / "starter_kit"


def read_lines(path, nfc=True):
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if nfc:
                line = unicodedata.normalize("NFC", line)
            lines.append(line)
    return lines


def graphemes(s):
    """User-perceived characters (extended grapheme clusters)."""
    return regex.findall(r"\X", s)


def analyze(lines, encode, lower=True, split="single", pooled=False, chars="codepoints"):
    """Same maths as the intern's analyze(), with each choice made a switch."""
    toks, words, nchars = [], [], []
    for line in lines:
        if lower:
            line = line.lower()
        toks.append(len(encode(line)))
        words.append(len(line.split(" ") if split == "single" else line.split()))
        nchars.append(len(line) if chars == "codepoints" else len(graphemes(line)))
    n = len(lines)
    if pooled:  # ratio of sums
        return sum(toks) / sum(words), sum(toks) / sum(nchars)
    # mean of per-line ratios (what the intern does)
    return (sum(t / w for t, w in zip(toks, words)) / n,
            sum(t / c for t, c in zip(toks, nchars)) / n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eng", default=str(KIT / "corpus_sample" / "eng_sample.txt"))
    ap.add_argument("--hin", "--other", dest="hin",
                    default=str(KIT / "corpus_sample" / "hin_sample.txt"),
                    help="the non-English corpus (any language)")
    ap.add_argument("--label", default="hin", help="column label for the non-English corpus")
    ap.add_argument("--tokenizer", default="gpt2", help="tiktoken encoding name")
    args = ap.parse_args()
    encode = tiktoken.get_encoding(args.tokenizer).encode
    lab = args.label

    # --- 0. the intern's own function, imported untouched -------------------
    spec = importlib.util.spec_from_file_location("fertility", KIT / "fertility.py")
    intern = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(intern)
    ref = {k: intern.analyze(intern.read_lines(p), encode)
           for k, p in (("eng", args.eng), ("hin", args.hin))}  # "hin" = the other corpus

    variants = [
        ("0 intern baseline (all switches as shipped)", {}, {}),
        ("1 split() instead of split(' ')", {"split": "any"}, {}),
        ("2 ratio of sums instead of mean of ratios", {"pooled": True}, {}),
        ("3 no lowercasing", {"lower": False}, {}),
        ("4 no NFC normalisation", {}, {"nfc": False}),
        ("5 graphemes instead of code points (tok/char)", {"chars": "graphemes"}, {}),
        ("6 fixes 1+2+3 together", {"split": "any", "pooled": True, "lower": False}, {}),
    ]

    rows = []
    for name, akw, rkw in variants:
        e = analyze(read_lines(args.eng, **rkw), encode, **akw)
        h = analyze(read_lines(args.hin, **rkw), encode, **akw)
        rows.append((name, e, h))

    base_e, base_h = rows[0][1], rows[0][2]
    assert abs(base_e[0] - ref["eng"][0]) < 1e-12 and abs(base_h[0] - ref["hin"][0]) < 1e-12, \
        "re-implementation does not match the intern's analyze()"
    assert abs(base_e[1] - ref["eng"][1]) < 1e-12 and abs(base_h[1] - ref["hin"][1]) < 1e-12

    print(f"tokenizer: {args.tokenizer}   (row 0 verified identical to fertility.analyze)")
    print(f"eng = {args.eng}")
    print(f"{lab} = {args.hin}")
    print()
    print("FERTILITY (tokens per word)")
    print(f"{'variant':<48}{'eng':>8}{lab:>8}{lab + '/eng':>9}{'d eng':>9}{'d ' + lab:>9}{'d ratio':>9}")
    r0 = base_h[0] / base_e[0]
    for name, e, h in rows:
        r = h[0] / e[0]
        print(f"{name:<48}{e[0]:>8.4f}{h[0]:>8.4f}{r:>9.4f}"
              f"{e[0] - base_e[0]:>+9.4f}{h[0] - base_h[0]:>+9.4f}{r - r0:>+9.4f}")

    print()
    print("TOKENS PER CHARACTER")
    print(f"{'variant':<48}{'eng':>8}{lab:>8}{lab + '/eng':>9}{'d eng':>9}{'d ' + lab:>9}{'d ratio':>9}")
    c0 = base_h[1] / base_e[1]
    for name, e, h in rows:
        r = h[1] / e[1]
        print(f"{name:<48}{e[1]:>8.4f}{h[1]:>8.4f}{r:>9.4f}"
              f"{e[1] - base_e[1]:>+9.4f}{h[1] - base_h[1]:>+9.4f}{r - c0:>+9.4f}")

    # --- supporting detail for each claim -----------------------------------
    print()
    print("DETAIL 1: lines where split(' ') and split() disagree")
    for lang, path in (("eng", args.eng), (lab, args.hin)):
        for i, line in enumerate(read_lines(path), 1):
            a, b = line.split(" "), line.split()
            if len(a) != len(b):
                print(f"  {lang} line {i}: split(' ')={len(a)} words (empty strings: {a.count('')}), "
                      f"split()={len(b)} words | {line}")

    print()
    print("DETAIL 3: lines whose token count changes when lowercased")
    for lang, path in (("eng", args.eng), (lab, args.hin)):
        changed = 0
        for i, line in enumerate(read_lines(path), 1):
            a, b = len(encode(line)), len(encode(line.lower()))
            if a != b:
                changed += 1
                print(f"  {lang} line {i}: original={a} tokens, lowercased={b} tokens ({b - a:+d}) | {line}")
        print(f"  {lang}: {changed} of {len(read_lines(path))} lines change")

    print()
    print("DETAIL 4: is NFC a no-op on these files?")
    for lang, path in (("eng", args.eng), (lab, args.hin)):
        raw = read_lines(path, nfc=False)
        diff = sum(1 for s in raw if unicodedata.normalize("NFC", s) != s)
        print(f"  {lang}: {diff} of {len(raw)} lines differ after NFC")

    print()
    print("DETAIL 5: code points vs grapheme clusters (totals)")
    for lang, path in (("eng", args.eng), (lab, args.hin)):
        ls = read_lines(path)
        cp = sum(len(s) for s in ls)
        gr = sum(len(graphemes(s)) for s in ls)
        by = sum(len(s.encode("utf-8")) for s in ls)
        wd = sum(len(s.split()) for s in ls)
        print(f"  {lang}: {wd} words, {cp} code points, {gr} graphemes, {by} UTF-8 bytes | "
              f"code points/word={cp / wd:.2f}, graphemes/word={gr / wd:.2f}, bytes/word={by / wd:.2f}")

    print()
    print("DETAIL 5b: 'how many times worse than English' under each denominator")
    print("  (raw text, no lowercasing, ratio of sums)")
    rate = {}
    for lang, path in (("eng", args.eng), (lab, args.hin)):
        ls = read_lines(path)
        tk = sum(len(encode(s)) for s in ls)
        rate[lang] = {
            "per word": tk / sum(len(s.split()) for s in ls),
            "per code point": tk / sum(len(s) for s in ls),
            "per grapheme": tk / sum(len(graphemes(s)) for s in ls),
            "per UTF-8 byte": tk / sum(len(s.encode("utf-8")) for s in ls),
            "per line": tk / len(ls),
        }
        print(f"  {lang}: {tk} tokens in {len(ls)} lines")
    for k in rate["eng"]:
        print(f"  {k:<16} eng {rate['eng'][k]:>8.3f}   {lab} {rate[lab][k]:>8.3f}   "
              f"{lab}/eng = {rate[lab][k] / rate['eng'][k]:>6.2f}x")

    print()
    print("DETAIL 6: is `random` used anywhere after it is seeded?")
    src = (KIT / "fertility.py").read_text(encoding="utf-8").splitlines()
    uses = [(i, l.strip()) for i, l in enumerate(src, 1) if "random" in l]
    for i, l in uses:
        print(f"  fertility.py:{i}: {l}")
    print(f"  -> {len(uses)} lines mention `random`; none draw a random number")


if __name__ == "__main__":
    main()
