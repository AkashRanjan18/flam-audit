#!/usr/bin/env python3
"""
prepare_corpus.py -- build the Part A eval corpus from FLORES-200.

Source : the official FLORES-200 release (Meta / NLLB team), CC-BY-SA 4.0
         https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz
Split  : devtest (1012 sentences) by default; dev (997) is used as a
         replication set.
Output : your-submission/partA/corpus/<split>/<lang>.txt, one sentence per
         line, line N is the same sentence in every language.

Preprocessing: NONE beyond removing the trailing newline. No lowercasing,
no Unicode normalisation, no punctuation stripping -- we want to tokenize
the text the way a user would send it. The script only *measures* what NFC
would change, so the choice is documented rather than assumed.

Usage (from the repo root):
    python your-submission/partA/prepare_corpus.py
    python your-submission/partA/prepare_corpus.py --split dev
"""

import argparse
import hashlib
import pathlib
import tarfile
import unicodedata
import urllib.request

import pandas as pd
import regex

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OUT = pathlib.Path(__file__).resolve().parent / "corpus"

URL = "https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz"
SHA256 = "b8b0b76783024b85797e5cc75064eb83fc5288b41e9654dabc7be6ae944011f6"

# code -> (FLORES file stem, language, family, script)
LANGS = {
    "eng": ("eng_Latn", "English", "Indo-European (Germanic)", "Latin"),
    "hin": ("hin_Deva", "Hindi", "Indo-Aryan", "Devanagari"),
    "mar": ("mar_Deva", "Marathi", "Indo-Aryan", "Devanagari"),
    "ben": ("ben_Beng", "Bengali", "Indo-Aryan", "Bengali"),
    "kan": ("kan_Knda", "Kannada", "Dravidian", "Kannada"),
    "tam": ("tam_Taml", "Tamil", "Dravidian", "Tamil"),
    "tel": ("tel_Telu", "Telugu", "Dravidian", "Telugu"),
    "mal": ("mal_Mlym", "Malayalam", "Dravidian", "Malayalam"),
}


def fetch():
    DATA.mkdir(exist_ok=True)
    tgz = DATA / "flores200_dataset.tar.gz"
    if not tgz.exists():
        print(f"downloading {URL}")
        urllib.request.urlretrieve(URL, tgz)
    digest = hashlib.sha256(tgz.read_bytes()).hexdigest()
    if digest != SHA256:
        raise SystemExit(f"checksum mismatch: {digest}")
    root = DATA / "flores200_dataset"
    if not root.exists():
        with tarfile.open(tgz) as t:
            t.extractall(DATA)
    return root


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="devtest", choices=["devtest", "dev"])
    args = ap.parse_args()

    root = fetch()
    out = OUT / args.split
    out.mkdir(parents=True, exist_ok=True)

    corpus = {}
    for code, (stem, *_rest) in LANGS.items():
        text = (root / args.split / f"{stem}.{args.split}").read_text(encoding="utf-8")
        lines = text.split("\n")
        if lines and lines[-1] == "":
            lines.pop()  # the file ends with a newline
        corpus[code] = lines
        (out / f"{code}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # --- alignment checks: a parallel corpus must have the same shape -------
    n = {len(v) for v in corpus.values()}
    assert len(n) == 1, f"line counts differ: { {k: len(v) for k, v in corpus.items()} }"
    n = n.pop()
    empty = {k: sum(1 for s in v if not s.strip()) for k, v in corpus.items()}
    assert not any(empty.values()), f"empty lines: {empty}"

    rows = []
    for code, lines in corpus.items():
        _, name, family, script = LANGS[code]
        words = sum(len(s.split()) for s in lines)
        cps = sum(len(s) for s in lines)
        gr = sum(len(regex.findall(r"\X", s)) for s in lines)
        by = sum(len(s.encode("utf-8")) for s in lines)
        rows.append({
            "lang": code, "language": name, "family": family, "script": script,
            "sentences": len(lines), "words": words, "graphemes": gr,
            "code_points": cps, "utf8_bytes": by,
            "words/sent": round(words / len(lines), 2),
            "bytes/word": round(by / words, 2),
            "nfc_changed_lines": sum(1 for s in lines if unicodedata.normalize("NFC", s) != s),
            "lines_with_double_space": sum(1 for s in lines if "  " in s),
            "lines_with_zwj_zwnj": sum(1 for s in lines if "‌" in s or "‍" in s),
        })
    df = pd.DataFrame(rows)

    meta = pd.read_csv(root / f"metadata_{args.split}.tsv", sep="\t")
    print(f"FLORES-200 {args.split}: {n} parallel sentences x {len(corpus)} languages")
    print(f"archive sha256: {SHA256}")
    print()
    print("domain mix (sentences):")
    print(meta["domain"].value_counts().to_string())
    print()
    print(df.to_string(index=False))
    df.to_csv(out / "corpus_stats.csv", index=False)

    # parallel sanity check: sentence lengths must move together across languages
    blen = pd.DataFrame({k: [len(s.encode("utf-8")) for s in v] for k, v in corpus.items()})
    print()
    print("correlation of per-line UTF-8 length with English (parallel text => high):")
    print(blen.corr()["eng"].round(3).to_string())
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
