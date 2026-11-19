# Slice benchmark results

Generated: 2026-11-18 by `benchmarks/run_benchmark.py` (Slice 0.1.0, Python 3.12.15, macOS-26.6.2-arm64-arm-64bit, repeats=5).
Absolute times are this machine's; ratios and rates are the portable signal. See the methodology in the script docstring of `benchmarks/run_benchmark.py`.

| Category | Cases | Success rate | Median ms/image | Detection | Observed | Mean error (px) | Mean OKS |
|---|---|---|---|---|---|---|---|
| Clean flat-background figures (illustration-like) | 3 | 1.00 | 71.8 | 1.0 | 1.0 | 2.06 | 0.9782 |
| Photo-like stand-ins (synthetic: gradient / noise / shadow backgrounds) | 3 | 1.00 | 69.3 | 1.0 | 1.0 | 3.6 | 0.9075 |
| Partial body (lower-right quadrant erased) | 1 | 1.00 | 78.6 | — | — | — | — |
| Body-model variants (child / deformed) on the clean figure | 2 | 1.00 | 65.4 | — | — | — | — |
| No person in the image | 2 | 1.00 | 36.8 | — | — | — | — |
| Large clean figures (latency scaling) | 2 | 1.00 | 206.1 | 1.0 | 0.9445 | 6.94 | 0.8873 |

## Per-case detail

| Case | Model | Size | Success | Observed joints | Median ms | Mean ms | Error / note |
|---|---|---|---|---|---|---|---|
| stand-flat-160x300-stand | adult | 160x300 | yes | 19 | 71.8 | 73.3 |  |
| stand-flat-160x300-t | adult | 160x300 | yes | 19 | 65.3 | 65.8 |  |
| stand-flat-240x320 | adult | 240x320 | yes | 19 | 116.1 | 118.5 |  |
| gradient-wall | adult | 160x300 | yes | 19 | 72.9 | 72.7 |  |
| sensor-noise | adult | 160x300 | yes | 19 | 69.3 | 70.0 |  |
| cast-shadow | adult | 160x300 | yes | 19 | 67.6 | 68.7 |  |
| lower-right-erased | adult | 160x300 | yes | 19 | 78.6 | 80.0 |  |
| model-child | child | 160x300 | yes | 19 | 66.3 | 66.4 |  |
| model-deformed | deformed | 160x300 | yes | 19 | 64.5 | 66.0 |  |
| blank-background | adult | 160x300 | yes | 0 | 33.3 | 33.8 | no skeleton fabricated (warnings issued) |
| rectangle-block | adult | 160x300 | yes | 0 | 40.2 | 39.3 | no skeleton fabricated (warnings issued) |
| stand-flat-640x960 | adult | 640x960 | yes | 19 | 218.2 | 223.1 |  |
| stand-flat-1200x1800 | adult | 1200x1800 | yes | 17 | 193.9 | 198.1 |  |

## Reading these numbers

- Positional error is in the estimator's working frame; inputs taller than 512 px are downscaled first, so the `large` category's pixel errors are working-frame pixels.
- A plain rectangle is no longer reported as a person: the primary upright scan is structure-gated — a discrete blob whose silhouette narrows nowhere (no neck, waist or leg gap) yields no detection, like the blank background (0 observed joints, full warnings). The gate is a heuristic, not a proof: adopters must still not treat `observed` as proof that a person was present.
- The `large` cases used to lose the elbows and wrists: after the 512 px downscale the arm runs sit one column from the torso edge, inside the arm scan's former two-column separation margin, so no arm candidates formed. The scan now accepts a one-column separation (a distinct run has at least one empty column by construction), which recovers both arms at 640x960 and the right arm at 1200x1800. The 1200x1800 left arm has no distinct run at any row — at that scale the arm is fused into the torso run itself — so it is inferred instead from the torso run's excess width: the fused arm leaves a ledge of a few columns on that side from the shoulder down to the wrist, asymmetric against the opposite side's chest half-width. Those two joints are reported as `predicted` at low confidence with an "inferred" basis. They count toward detection and positional accuracy, but not toward the observed rate; a figure whose arms fuse symmetrically on both sides shows no such asymmetry and still yields nothing.
- Ground truth for `models` (child / deformed) is not scored: the fixture is drawn with adult proportions, so positional accuracy against it would not measure those models. Success, latency and observed-joint counts only.

## Not measured

- Real photographs: no redistributable photo corpus is bundled with this repository, so no number here describes performance on real photos. `photo_like` is a synthetic stand-in (same flat figure, hostile backgrounds).
- JPEG / WebP input (requires Pillow), the REST server (`slice serve`) latency, multi-person images, and video.
- Any form of identity: Slice reports anatomical inference, never who a person is, and this suite measures nothing identity-related by design.
