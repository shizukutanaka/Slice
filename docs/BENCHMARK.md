# Slice benchmark results

Generated: 2026-11-16 by `benchmarks/run_benchmark.py` (Slice 0.1.0, Python 3.12.3, Linux-7.0.0-44-generic-x86_64-with-glibc2.39, repeats=5).
Absolute times are this machine's; ratios and rates are the portable signal. See the methodology in the script docstring of `benchmarks/run_benchmark.py`.

| Category | Cases | Success rate | Median ms/image | Detection | Observed | Mean error (px) | Mean OKS |
|---|---|---|---|---|---|---|---|
| Clean flat-background figures (illustration-like) | 3 | 1.00 | 414.4 | 1.0 | 1.0 | 2.06 | 0.9782 |
| Photo-like stand-ins (synthetic: gradient / noise / shadow backgrounds) | 3 | 1.00 | 428.2 | 1.0 | 1.0 | 3.6 | 0.9075 |
| Partial body (lower-right quadrant erased) | 1 | 1.00 | 527.6 | — | — | — | — |
| Body-model variants (child / deformed) on the clean figure | 2 | 1.00 | 418.4 | — | — | — | — |
| No person in the image | 2 | 0.50 | 142.4 | — | — | — | — |
| Large clean figures (latency scaling) | 2 | 1.00 | 567.5 | 0.7778 | 0.7778 | 8.24 | 0.6679 |

## Per-case detail

| Case | Model | Size | Success | Observed joints | Median ms | Mean ms | Error / note |
|---|---|---|---|---|---|---|---|
| stand-flat-160x300-stand | adult | 160x300 | yes | 19 | 414.4 | 434.8 |  |
| stand-flat-160x300-t | adult | 160x300 | yes | 19 | 189.7 | 191.2 |  |
| stand-flat-240x320 | adult | 240x320 | yes | 19 | 656.8 | 655.8 |  |
| gradient-wall | adult | 160x300 | yes | 19 | 411.6 | 414.9 |  |
| sensor-noise | adult | 160x300 | yes | 19 | 428.2 | 442.0 |  |
| cast-shadow | adult | 160x300 | yes | 19 | 434.4 | 432.5 |  |
| lower-right-erased | adult | 160x300 | yes | 19 | 527.6 | 531.6 |  |
| model-child | child | 160x300 | yes | 19 | 429.4 | 439.7 |  |
| model-deformed | deformed | 160x300 | yes | 19 | 407.4 | 411.7 |  |
| blank-background | adult | 160x300 | yes | 0 | 112.9 | 113.4 | no skeleton fabricated (warnings issued) |
| rectangle-block | adult | 160x300 | NO | 15 | 171.8 | 172.7 | warnings: no_observed_wrists |
| stand-flat-640x960 | adult | 640x960 | yes | 15 | 546.4 | 549.7 | warnings: no_observed_wrists |
| stand-flat-1200x1800 | adult | 1200x1800 | yes | 15 | 588.7 | 585.5 | warnings: no_observed_wrists |

## Reading these numbers

- Positional error is in the estimator's working frame; inputs taller than 512 px are downscaled first, so the `large` category's pixel errors are working-frame pixels.
- A plain rectangle is reported as a failure in `negative`: the silhouette heuristic treats a person-sized blob as a person and marks joints `observed`. The blank background behaves honestly (0 observed joints, full warnings). Adopters must not treat `observed` as proof that a person was present.
- Ground truth for `models` (child / deformed) is not scored: the fixture is drawn with adult proportions, so positional accuracy against it would not measure those models. Success, latency and observed-joint counts only.

## Not measured

- Real photographs: no redistributable photo corpus is bundled with this repository, so no number here describes performance on real photos. `photo_like` is a synthetic stand-in (same flat figure, hostile backgrounds).
- JPEG / WebP input (requires Pillow), the REST server (`slice serve`) latency, multi-person images, and video.
- Any form of identity: Slice reports anatomical inference, never who a person is, and this suite measures nothing identity-related by design.
