#!/usr/bin/env python3
"""
b_capacity.py -- Part B: capacity reconciliation for bench/bench_log.csv.

Everything is derived from bench/model_spec.md, then checked row by row
against the log. Nothing here is fitted to the log except one number that
is clearly marked (the decode bandwidth efficiency in B2).

Usage (from the repo root):
    python Flam-submission/partB/b_capacity.py
    python Flam-submission/partB/b_capacity.py --kv-bytes 1          # fp8 KV cache
    python Flam-submission/partB/b_capacity.py --gpu-util 0.95
    python Flam-submission/partB/b_capacity.py --max-model-len 8192
    python Flam-submission/partB/b_capacity.py --kv-heads 24         # no GQA
"""

import argparse
import math
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
LOG = ROOT / "starter_kit" / "bench" / "bench_log.csv"

GB = 1e9  # the spec's "24 GB" is decimal; B1 shows GiB does not fit the log


def main():
    ap = argparse.ArgumentParser()
    # --- model spec (bench/model_spec.md) ---
    ap.add_argument("--params", type=float, default=4.2e9)
    ap.add_argument("--layers", type=int, default=28)
    ap.add_argument("--kv-heads", type=int, default=8, help="GQA KV heads (not the 24 query heads)")
    ap.add_argument("--head-dim", type=int, default=128)
    ap.add_argument("--weight-bytes", type=float, default=2, help="fp16 = 2")
    ap.add_argument("--kv-bytes", type=float, default=2, help="fp16 = 2, fp8 = 1")
    # --- hardware and serving config ---
    ap.add_argument("--gpu-gb", type=float, default=24)
    ap.add_argument("--gpu-util", type=float, default=0.92)
    ap.add_argument("--overhead-gb", type=float, default=1.6)
    ap.add_argument("--max-model-len", type=int, default=4096)
    ap.add_argument("--bandwidth-gbs", type=float, default=300)
    ap.add_argument("--peak-tflops", type=float, default=121)
    ap.add_argument("--block", type=int, default=16, help="vLLM KV block size in tokens")
    args = ap.parse_args()

    pd.set_option("display.width", 250)

    # ===================== B1 ==============================================
    kv_per_tok = 2 * args.layers * args.kv_heads * args.head_dim * args.kv_bytes
    weights = args.params * args.weight_bytes
    budget = args.gpu_gb * GB * args.gpu_util
    kv_budget = budget - weights - args.overhead_gb * GB
    kv_tokens = kv_budget / kv_per_tok
    kv_blocks = math.floor(kv_tokens / args.block)
    seq_bytes = kv_per_tok * args.max_model_len
    max_seqs = math.floor(kv_tokens / args.max_model_len)

    print("B1  KV CACHE ARITHMETIC")
    print(f"  KV bytes per token = 2 (K and V) x {args.layers} layers x {args.kv_heads} KV heads "
          f"x {args.head_dim} head_dim x {args.kv_bytes:g} bytes = {kv_per_tok:,.0f} bytes "
          f"({kv_per_tok / 1024:.1f} KiB)")
    print(f"  usable GPU memory  = {args.gpu_gb:g} GB x {args.gpu_util} = {budget / GB:.2f} GB")
    print(f"  weights            = {args.params / 1e9:g} B params x {args.weight_bytes:g} bytes = {weights / GB:.2f} GB")
    print(f"  KV budget          = {budget / GB:.2f} - {weights / GB:.2f} - {args.overhead_gb} = {kv_budget / GB:.2f} GB")
    print(f"  KV capacity        = {kv_budget / GB:.2f} GB / {kv_per_tok:,.0f} B = {kv_tokens:,.0f} tokens "
          f"({kv_blocks:,} blocks of {args.block})")
    print(f"  one {args.max_model_len}-token sequence = {seq_bytes / 1e6:.1f} MB")
    print(f"  max concurrent {args.max_model_len}-token sequences = {kv_tokens / args.max_model_len:.2f} -> {max_seqs}")

    gib_tokens = (args.gpu_gb * 2**30 * args.gpu_util - weights - args.overhead_gb * GB) / kv_per_tok
    print(f"  (if '24 GB' meant GiB: {gib_tokens:,.0f} tokens -> "
          f"{math.floor(gib_tokens / args.max_model_len)} sequences)")

    df = pd.read_csv(LOG)
    df["seq_len"] = df.prompt_len + df.gen_len
    df["fit"] = (kv_tokens // df.seq_len).astype(int).clip(upper=df.num_requests)   # that fit at full length
    df["pred_util"] = (df.fit * df.seq_len / kv_tokens).round(2)
    df["pred_preempt"] = df.num_requests - df.fit
    df["util_if_GiB"] = ((gib_tokens // df.seq_len).astype(int).clip(upper=df.num_requests)
                         * df.seq_len / gib_tokens).round(2)
    print("\n  prediction vs log (no parameter is fitted here):")
    print("  " + df[["batch_size", "prompt_len", "gen_len", "seq_len", "fit", "pred_util", "kv_cache_util",
                     "util_if_GiB", "pred_preempt", "preempted_seqs"]]
          .to_string(index=False).replace("\n", "\n  "))
    ok_u = (df.pred_util - df.kv_cache_util).abs().max()
    ok_p = (df.pred_preempt == df.preempted_seqs).all()
    print(f"  max |predicted - logged| utilisation = {ok_u:.3f}; preemption counts all match: {ok_p}")

    # ===================== B3 (needed before B2) ===========================
    df["total_tok"] = df.num_requests * df.seq_len
    df["out_tok"] = df.num_requests * df.gen_len
    df["recomputed_reported"] = (df.total_tok / df.wall_clock_s).round(1)
    df["goodput_wall"] = df.out_tok / df.wall_clock_s                               # way 1
    df["goodput_from_reported"] = df.reported_tok_s * df.gen_len / df.seq_len       # way 2
    df["decode_rate_itl"] = df.fit / (df.itl_ms_p50 / 1000)                         # steady-state decode only
    print("\nB3  WHAT reported_tok_s COUNTS, AND THE HONEST GOODPUT")
    print("  reported_tok_s == num_requests x (prompt_len + gen_len) / wall_clock_s ?")
    print("  " + df[["batch_size", "prompt_len", "reported_tok_s", "recomputed_reported", "goodput_wall",
                     "goodput_from_reported", "decode_rate_itl"]].round(1)
          .to_string(index=False).replace("\n", "\n  "))
    print(f"  max |reported - recomputed| = {(df.reported_tok_s - df.recomputed_reported).abs().max():.2f} tok/s")

    r = df[(df.prompt_len == 3584) & (df.batch_size == 24)].iloc[0]
    print(f"\n  batch-24 long-prompt row:")
    print(f"    way 1: generated tokens / wall clock = {int(r.num_requests)} x {int(r.gen_len)} / {r.wall_clock_s} "
          f"= {r.goodput_wall:.1f} tok/s")
    print(f"    way 2: reported x gen/(prompt+gen)   = {r.reported_tok_s} x {int(r.gen_len)}/{int(r.seq_len)} "
          f"= {r.goodput_from_reported:.1f} tok/s")
    print(f"    cross-check, decode phase only: {int(r.num_requests)} seqs / {r.itl_ms_p50} ms = "
          f"{r.decode_rate_itl:.1f} tok/s (higher: it ignores the "
          f"{r.wall_clock_s - r.gen_len * r.itl_ms_p50 / 1000:.1f} s that are not steady decode)")
    s16 = df[(df.prompt_len == 512) & (df.batch_size == 16)].iloc[0]
    l16 = df[(df.prompt_len == 3584) & (df.batch_size == 16)].iloc[0]
    print(f"  the report's comparison at batch 16: reported {l16.reported_tok_s} (long) vs {s16.reported_tok_s} (short); "
          f"goodput {l16.goodput_wall:.1f} (long) vs {s16.goodput_wall:.1f} (short)")
    l48 = df[(df.prompt_len == 3584) & (df.batch_size == 48)].iloc[0]
    print(f"  the report's batch-48 forecast: 3200 tok/s; the log's batch-48 row: reported {l48.reported_tok_s}, "
          f"goodput {l48.goodput_wall:.1f}")

    # ===================== B2 ==============================================
    print("\nB2  THE LONG-CONTEXT ANOMALY")
    long = df[df.prompt_len == 3584].copy()
    long["goodput_per_seq"] = long.goodput_wall / long.batch_size
    print("  " + long[["batch_size", "reported_tok_s", "goodput_wall", "goodput_per_seq", "wall_clock_s",
                       "ttft_ms_p50", "itl_ms_p50", "e2e_ms_p95", "preempted_seqs", "kv_cache_util"]]
          .round(2).to_string(index=False).replace("\n", "\n  "))

    # decode is memory-bound: each step reads the weights + every running sequence's KV cache
    df["avg_ctx"] = df.prompt_len + df.gen_len / 2
    df["bytes_per_step"] = weights + df.fit * df.avg_ctx * kv_per_tok
    df["itl_floor_ms"] = df.bytes_per_step / (args.bandwidth_gbs * GB) * 1000
    df["bw_eff"] = df.itl_floor_ms / df.itl_ms_p50
    clean = df[df.preempted_seqs == 0]
    eff = clean.bw_eff.mean()
    print("\n  decode step = read weights + all running KV, at 300 GB/s peak:")
    print("  " + df[["batch_size", "prompt_len", "fit", "bytes_per_step", "itl_floor_ms", "itl_ms_p50", "bw_eff"]]
          .assign(bytes_per_step=lambda d: (d.bytes_per_step / GB).round(2))
          .rename(columns={"bytes_per_step": "GB_per_step"}).round(3)
          .to_string(index=False).replace("\n", "\n  "))
    print(f"  bandwidth efficiency on the {len(clean)} non-preempted rows: mean {eff:.3f}, "
          f"min {clean.bw_eff.min():.3f}, max {clean.bw_eff.max():.3f}  (the one fitted number)")

    # --- proposed change A: admission control, max_num_seqs = 24 ---
    b24 = long[long.batch_size == 24].iloc[0]
    waves = 2
    wall_a = waves * b24.wall_clock_s
    good_a = 48 * 512 / wall_a
    print(f"\n  change A: --max-num-seqs 24 (never admit more than fits). 48 requests run as {waves} waves of 24:")
    print(f"    predicted wall {wall_a:.1f} s (log: {l48.wall_clock_s}), goodput {good_a:.1f} tok/s "
          f"(log: {l48.goodput_wall:.1f}, {100 * (good_a / l48.goodput_wall - 1):+.0f}%), preemptions 0 (log: {int(l48.preempted_seqs)})")

    # --- proposed change B: fp8 KV cache ---
    kv8 = kv_per_tok / 2
    cap8 = kv_budget / kv8
    fit8 = math.floor(cap8 / args.max_model_len)
    itl8 = (weights + 48 * (3584 + 256) * kv8) / (args.bandwidth_gbs * GB * eff) * 1000
    non_decode_24 = b24.wall_clock_s - 512 * b24.itl_ms_p50 / 1000
    wall_b = 512 * itl8 / 1000 + 2 * non_decode_24
    good_b = 48 * 512 / wall_b
    print(f"  change B: fp8 KV cache ({kv8:,.0f} B/token) -> {cap8:,.0f} tokens -> {fit8} full sequences")
    print(f"    batch 48: KV util {48 * 4096 / cap8:.2f}, preemptions 0, predicted ITL {itl8:.1f} ms, "
          f"wall ~{wall_b:.0f} s, goodput ~{good_b:.0f} tok/s ({good_b / l48.goodput_wall:.2f}x the logged {l48.goodput_wall:.1f})")
    print(f"    (prefill time assumed to scale linearly from batch 24: {non_decode_24:.1f} s -> {2 * non_decode_24:.1f} s)")

    # ===================== open questions ==================================
    print("\nUNRESOLVED (logged, not explained)")
    df["e2e_over_wall"] = df.e2e_ms_p95 / 1000 / df.wall_clock_s
    n_bad = int((df.e2e_over_wall > 1).sum())
    print(f"  e2e_ms_p95 exceeds wall_clock_s in {n_bad} of {len(df)} rows "
          f"(ratio min {df.e2e_over_wall.min():.2f}, max {df.e2e_over_wall.max():.2f}); with simultaneous submission "
          f"no request can outlast the run")
    df["prefill_tflop"] = df.num_requests * df.prompt_len * 2 * args.params / 1e12
    df["prefill_floor_s"] = df.prefill_tflop / args.peak_tflops
    df["non_decode_s"] = df.wall_clock_s - df.gen_len * df.itl_ms_p50 / 1000
    print("  TTFT vs the compute needed to prefill the whole batch (2 x params FLOPs per token):")
    print("  " + df[["batch_size", "prompt_len", "prefill_tflop", "prefill_floor_s", "non_decode_s", "ttft_ms_p50"]]
          .round(2).to_string(index=False).replace("\n", "\n  "))


if __name__ == "__main__":
    main()
