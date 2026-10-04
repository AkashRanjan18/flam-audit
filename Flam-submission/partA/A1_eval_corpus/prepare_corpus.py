#!/usr/bin/env python3
"""
prepare_corpus.py -- A1: build the eval corpus from FLORES-200 (devtest).

Usage (from the repo root):
    python Flam-submission/partA/A1_eval_corpus/prepare_corpus.py
"""

import hashlib
import pathlib
import tarfile
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = pathlib.Path(__file__).resolve().parent / "corpus"
URL = "https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz"
SHA256 = "b8b0b76783024b85797e5cc75064eb83fc5288b41e9654dabc7be6ae944011f6"
LANGS = {"eng": "eng_Latn", "hin": "hin_Deva", "tam": "tam_Taml", "tel": "tel_Telu"}

# 1. download once, and refuse to continue if the file is not the official one
tgz = ROOT / "data" / "flores200_dataset.tar.gz"
tgz.parent.mkdir(exist_ok=True)
if not tgz.exists():
    urllib.request.urlretrieve(URL, tgz)
assert hashlib.sha256(tgz.read_bytes()).hexdigest() == SHA256, "checksum mismatch"
src = ROOT / "data" / "flores200_dataset" / "devtest"
if not src.exists():
    tarfile.open(tgz).extractall(ROOT / "data")

# 2. copy the four languages unchanged (the output files are byte-identical to FLORES)
OUT.mkdir(exist_ok=True)
corpus = {}
for code, stem in LANGS.items():
    lines = (src / f"{stem}.devtest").read_text(encoding="utf-8").rstrip("\n").split("\n")
    corpus[code] = lines
    with open(OUT / f"{code}.txt", "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

# 3. parallel means: same number of lines everywhere, and none empty
assert len({len(v) for v in corpus.values()}) == 1, "line counts differ"
assert all(s.strip() for v in corpus.values() for s in v), "empty line found"

# 4. size
print(f"{'lang':<6}{'sentences':>10}{'words':>8}{'utf8_bytes':>12}{'words/sentence':>16}")
for code, lines in corpus.items():
    words = sum(len(s.split()) for s in lines)
    nbytes = sum(len(s.encode("utf-8")) for s in lines)
    print(f"{code:<6}{len(lines):>10}{words:>8}{nbytes:>12}{words / len(lines):>16.1f}")
