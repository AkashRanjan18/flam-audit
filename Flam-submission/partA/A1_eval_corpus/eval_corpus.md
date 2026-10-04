# A1 — Evaluation corpus

**Build:** `python Flam-submission/partA/A1_eval_corpus/prepare_corpus.py` (48 lines; output in `results.txt`)

**Choice:** FLORES-200 `devtest`, official Meta release, SHA-256 checked by the script. I chose it because line *N* is the same sentence in every language, so the content is held fixed across languages.

**Languages:** English, Hindi, Tamil, Telugu (Tamil and Telugu are the two Dravidian languages).

## Size

| lang | sentences | words | UTF-8 bytes | words / sentence |
|---|---|---|---|---|
| eng | 1,012 | 21,901 | 132,096 | 21.6 |
| hin | 1,012 | 25,643 | 337,094 | 25.3 |
| tam | 1,012 | 16,775 | 421,641 | 16.6 |
| tel | 1,012 | 16,938 | 353,711 | 16.7 |

## Domain

Formal written prose: Wikinews (341 sentences), Wikibooks (351), Wikivoyage (320). The Indic text was translated from English by professionals.

## Preprocessing

None. The four corpus files are byte-for-byte copies of the FLORES files (`cmp` reports no difference). No lowercasing, no Unicode normalization, no punctuation changes. The script only checks that all four files have the same number of lines and no empty line.

## What this corpus cannot tell me

It cannot tell me what our users' text costs, because I have no sample of our traffic. FLORES is edited, encyclopedic writing in native script. Our product is an assistant, so real requests are probably shorter and more informal, and may include Hindi typed in Latin letters or mixed with English. None of that appears here, and I am assuming it, not measuring it. The Indic sentences are translations, so they follow English sentence structure and may be longer or shorter than text first written in those languages. It covers text going in, not the replies the model generates. And 1,012 sentences from one source is enough for a stable average but too few to study rare cases, and it cannot show how much the numbers would move on a different corpus.
