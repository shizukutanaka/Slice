# Slice benchmark results

Generated: 2026-11-17 by `benchmarks/run_benchmark.py` (Slice 0.1.0, Python 3.12.3, Linux-7.0.0-44-generic-x86_64-with-glibc2.39, repeats=5).
Absolute times are this machine's; ratios and rates are the portable signal. See the methodology in the script docstring of `benchmarks/run_benchmark.py`.

| Category | Cases | Success rate | Median ms/image | Detection | Observed | Mean error (px) | Mean OKS |
|---|---|---|---|---|---|---|---|
| Clean flat-background figures (illustration-like) | 3 | 1.00 | 413.4 | 1.0 | 1.0 | 2.06 | 0.9782 |
| Photo-like stand-ins (synthetic: gradient / noise / shadow backgrounds) | 3 | 1.00 | 422.2 | 1.0 | 1.0 | 3.6 | 0.9075 |
| Partial body (lower-right quadrant erased) | 1 | 1.00 | 562.9 | — | — | — | — |
| Body-model variants (child / deformed) on the clean figure | 2 | 1.00 | 431.3 | — | — | — | — |
| No person in the image | 2 | 1.00 | 129.5 | — | — | — | — |
| Large clean figures (latency scaling) | 2 | 1.00 | 573.6 | 0.7778 | 0.7778 | 8.24 | 0.6679 |

## Per-case detail

| Case | Model | Size | Success | Observed joints | Median ms | Mean ms | Error / note |
|---|---|---|---|---|---|---|---|
| stand-flat-160x300-stand | adult | 160x300 | yes | 19 | 413.4 | 413.5 |  |
| stand-flat-160x300-t | adult | 160x300 | yes | 19 | 217.8 | 218.4 |  |
| stand-flat-240x320 | adult | 240x320 | yes | 19 | 657.4 | 656.4 |  |
| gradient-wall | adult | 160x300 | yes | 19 | 422.2 | 427.5 |  |
| sensor-noise | adult | 160x300 | yes | 19 | 413.3 | 412.1 |  |
| cast-shadow | adult | 160x300 | yes | 19 | 423.9 | 428.3 |  |
| lower-right-erased | adult | 160x300 | yes | 19 | 562.9 | 555.7 |  |
| model-child | child | 160x300 | yes | 19 | 462.9 | 458.5 |  |
| model-deformed | deformed | 160x300 | yes | 19 | 399.7 | 398.4 |  |
| blank-background | adult | 160x300 | yes | 0 | 112.7 | 110.3 | no skeleton fabricated (warnings issued) |
| rectangle-block | adult | 160x300 | yes | 0 | 146.3 | 146.0 | no skeleton fabricated (warnings issued) |
| stand-flat-640x960 | adult | 640x960 | yes | 15 | 543.8 | 550.7 | warnings: no_observed_wrists |
| stand-flat-1200x1800 | adult | 1200x1800 | yes | 15 | 603.4 | 626.1 | warnings: no_observed_wrists |

## Reading these numbers

- Positional error is in the estimator's working frame; inputs taller than 512 px are downscaled first, so the `large` category's pixel errors are working-frame pixels.
- A plain rectangle is no longer reported as a person: the primary upright scan is structure-gated — a discrete blob whose silhouette narrows nowhere (no neck, waist or leg gap) yields no detection, like the blank background (0 observed joints, full warnings). The gate is a heuristic, not a proof: adopters must still not treat `observed` as proof that a person was present.
- The `large` cases lose the elbows and wrists for a different, investigated reason: after the 512 px downscale the arm runs sit one column from the torso edge, inside the arm scan's two-column separation margin, so no arm candidates form. A resolution limit of the arm scan, unrelated to the rectangle gate; recorded here and left for a separate change.
- Ground truth for `models` (child / deformed) is not scored: the fixture is drawn with adult proportions, so positional accuracy against it would not measure those models. Success, latency and observed-joint counts only.

## Not measured

- Real photographs: no redistributable photo corpus is bundled with this repository, so no number here describes performance on real photos. `photo_like` is a synthetic stand-in (same flat figure, hostile backgrounds).
- JPEG / WebP input (requires Pillow), the REST server (`slice serve`) latency, multi-person images, and video.
- Any form of identity: Slice reports anatomical inference, never who a person is, and this suite measures nothing identity-related by design.
