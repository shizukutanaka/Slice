# Slice benchmark results

Generated: 2026-11-17 by `benchmarks/run_benchmark.py` (Slice 0.1.0, Python 3.12.3, Linux-7.0.0-44-generic-x86_64-with-glibc2.39, repeats=5).
Absolute times are this machine's; ratios and rates are the portable signal. See the methodology in the script docstring of `benchmarks/run_benchmark.py`.

| Category | Cases | Success rate | Median ms/image | Detection | Observed | Mean error (px) | Mean OKS |
|---|---|---|---|---|---|---|---|
| Clean flat-background figures (illustration-like) | 3 | 1.00 | 222.8 | 1.0 | 1.0 | 2.06 | 0.9782 |
| Photo-like stand-ins (synthetic: gradient / noise / shadow backgrounds) | 3 | 1.00 | 216.7 | 1.0 | 1.0 | 3.6 | 0.9075 |
| Partial body (lower-right quadrant erased) | 1 | 1.00 | 234.8 | — | — | — | — |
| Body-model variants (child / deformed) on the clean figure | 2 | 1.00 | 280.5 | — | — | — | — |
| No person in the image | 2 | 1.00 | 175.6 | — | — | — | — |
| Large clean figures (latency scaling) | 2 | 1.00 | 640.9 | 0.9445 | 0.9445 | 7.57 | 0.8324 |

## Per-case detail

| Case | Model | Size | Success | Observed joints | Median ms | Mean ms | Error / note |
|---|---|---|---|---|---|---|---|
| stand-flat-160x300-stand | adult | 160x300 | yes | 19 | 222.8 | 231.3 |  |
| stand-flat-160x300-t | adult | 160x300 | yes | 19 | 215.3 | 220.3 |  |
| stand-flat-240x320 | adult | 240x320 | yes | 19 | 319.1 | 328.8 |  |
| gradient-wall | adult | 160x300 | yes | 19 | 217.8 | 227.5 |  |
| sensor-noise | adult | 160x300 | yes | 19 | 216.7 | 217.4 |  |
| cast-shadow | adult | 160x300 | yes | 19 | 209.3 | 209.3 |  |
| lower-right-erased | adult | 160x300 | yes | 19 | 234.8 | 231.3 |  |
| model-child | child | 160x300 | yes | 19 | 256.2 | 271.9 |  |
| model-deformed | deformed | 160x300 | yes | 19 | 304.9 | 327.8 |  |
| blank-background | adult | 160x300 | yes | 0 | 147.1 | 139.0 | no skeleton fabricated (warnings issued) |
| rectangle-block | adult | 160x300 | yes | 0 | 204.0 | 214.3 | no skeleton fabricated (warnings issued) |
| stand-flat-640x960 | adult | 640x960 | yes | 19 | 663.7 | 683.2 |  |
| stand-flat-1200x1800 | adult | 1200x1800 | yes | 17 | 618.1 | 615.9 |  |

## Reading these numbers

- Positional error is in the estimator's working frame; inputs taller than 512 px are downscaled first, so the `large` category's pixel errors are working-frame pixels.
- A plain rectangle is no longer reported as a person: the primary upright scan is structure-gated — a discrete blob whose silhouette narrows nowhere (no neck, waist or leg gap) yields no detection, like the blank background (0 observed joints, full warnings). The gate is a heuristic, not a proof: adopters must still not treat `observed` as proof that a person was present.
- The `large` cases used to lose the elbows and wrists: after the 512 px downscale the arm runs sit one column from the torso edge, inside the arm scan's former two-column separation margin, so no arm candidates formed. The scan now accepts a one-column separation (a distinct run has at least one empty column by construction), which recovers both arms at 640x960 and the right arm at 1200x1800. The 1200x1800 left arm is still lost for a different reason: at that scale the downscale fuses it into the torso run itself — no distinct run exists at any row — so no scan margin can recover it; that is a silhouette-fusion limit, recorded here rather than papered over.
- Ground truth for `models` (child / deformed) is not scored: the fixture is drawn with adult proportions, so positional accuracy against it would not measure those models. Success, latency and observed-joint counts only.

## Not measured

- Real photographs: no redistributable photo corpus is bundled with this repository, so no number here describes performance on real photos. `photo_like` is a synthetic stand-in (same flat figure, hostile backgrounds).
- JPEG / WebP input (requires Pillow), the REST server (`slice serve`) latency, multi-person images, and video.
- Any form of identity: Slice reports anatomical inference, never who a person is, and this suite measures nothing identity-related by design.
