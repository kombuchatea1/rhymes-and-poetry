#!/usr/bin/env python3
"""
Generate a deterministic torn-paper mask PNG for a blog post.

Each post slug produces a unique mask (different tear pattern), but the
same slug always produces the same mask — so re-running the script for
an existing post gives the same result. Idempotent.

Usage:
    python3 scripts/generate-tear-mask.py <slug> [<slug2> ...]

Examples:
    python3 scripts/generate-tear-mask.py we-carry-a-torch
    python3 scripts/generate-tear-mask.py we-carry-a-torch courage-to-be-kind

Output:
    public/torn-masks/<slug>.png
"""
import sys
import math
import hashlib
import random
from pathlib import Path
from PIL import Image
import numpy as np


W, H = 1600, 800
BASE_DEPTH = 14    # baseline tear depth (always at least this much)
DEPTH_RANGE = 18   # additional depth variation (max tear ≈ baseline + range)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "public" / "torn-masks"


def slug_to_seed(slug: str) -> int:
    """Deterministic seed from slug — same slug always seeds the same RNG."""
    return int(hashlib.md5(slug.encode()).hexdigest()[:8], 16)


def generate_mask(slug: str, output_path: Path) -> int:
    """Generate the mask PNG. Returns the file size in bytes."""
    rng = random.Random(slug_to_seed(slug))

    # Each slug gets its own phase offsets per edge — controls WHERE the
    # tear bumps appear. This is the primary source of per-post variation.
    def phases(n=3):
        return [rng.uniform(0, 2 * math.pi) for _ in range(n)]

    top_phases    = phases()
    right_phases  = phases()
    bottom_phases = phases()
    left_phases   = phases()

    # Per-edge baseline + amplitude jitter — secondary source of variation.
    # Each edge gets slightly different tear depth, like real torn paper.
    def edge_params():
        baseline  = BASE_DEPTH + rng.uniform(-3, 4)
        amplitude = DEPTH_RANGE + rng.uniform(-4, 4)
        return baseline, amplitude

    top_base, top_amp       = edge_params()
    right_base, right_amp   = edge_params()
    bottom_base, bottom_amp = edge_params()
    left_base, left_amp     = edge_params()

    def tear_depths(length, freqs_phases, base, amp):
        """Tear depth at each position along an edge."""
        depths = np.zeros(length)
        for i in range(length):
            offset = sum(a * math.sin(i * f + p) for a, f, p in freqs_phases)
            offset += rng.uniform(-2, 2)
            depths[i] = max(2, min(amp + base + 4, base + offset))
        return depths.astype(int)

    # Frequencies: top/bottom span 1600px, left/right span 800px — so
    # side edges use higher base frequency to look proportional.
    top_freqs    = [(10, 0.0042, top_phases[0]),    (5, 0.0140, top_phases[1]),    (3, 0.0410, top_phases[2])]
    right_freqs  = [(10, 0.0085, right_phases[0]),  (5, 0.0260, right_phases[1]),  (3, 0.0700, right_phases[2])]
    bottom_freqs = [(10, 0.0042, bottom_phases[0]), (5, 0.0140, bottom_phases[1]), (3, 0.0410, bottom_phases[2])]
    left_freqs   = [(10, 0.0085, left_phases[0]),   (5, 0.0260, left_phases[1]),   (3, 0.0700, left_phases[2])]

    top_d    = tear_depths(W, top_freqs,    top_base,    top_amp)
    bottom_d = tear_depths(W, bottom_freqs, bottom_base, bottom_amp)
    left_d   = tear_depths(H, left_freqs,   left_base,   left_amp)
    right_d  = tear_depths(H, right_freqs,  right_base,  right_amp)

    # Build alpha matrix — start opaque, tear edges to transparent
    alpha = np.full((H, W), 255, dtype=np.uint8)

    for x in range(W):
        alpha[:top_d[x], x] = 0
        alpha[H - bottom_d[x]:, x] = 0

    for y in range(H):
        alpha[y, :left_d[y]] = 0
        alpha[y, W - right_d[y]:] = 0

    rgba = np.zeros((H, W, 4), dtype=np.uint8)
    rgba[:, :, 3] = alpha
    img = Image.fromarray(rgba, mode="RGBA")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", optimize=True)

    return output_path.stat().st_size


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    for slug in sys.argv[1:]:
        out = OUTPUT_DIR / f"{slug}.png"
        size = generate_mask(slug, out)
        print(f"  {slug:40s} -> {out.relative_to(PROJECT_ROOT)} ({size:,} bytes)")


if __name__ == "__main__":
    main()
