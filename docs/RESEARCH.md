# 調査メモ — 先行技術との対応

## シルエットベース姿勢推定（非DL）

深層学習なしの古典手法は確立された研究領域であり、Slice の
`HeuristicPoseEstimator` はその最小実装。

- **Pose from Silhouettes (PfS)** — シルエット面積の回転連続性を使い
  大域最適な6DoF姿勢を求める（Sengupta et al., Zuse Institute）。
  対応関係不要・任意形状に適用可。Slice Phase 3 の3D投影で参照。
  https://agnivsen.github.io/pose-from-silhouette/
- **RVM回帰による3D姿勢復元** (Agarwal & Triggs, CVPR 2004) —
  shape-context ヒストグラム→回帰。明示的身体モデル不要。
- **距離レベルセットによる尤度** (Telea et al., WSCG 2002) —
  モデルベース照合の attraction/explanation 項。
  skeleton smoothing で探索を安定化 → slice/predict.py の
  対称性補完と同じ思想。

## キーポイント仕様の業界標準

- **OpenPose** `pose_keypoints_2d`: `[x0,y0,c0, x1,y1,c1, ...]`
  （c は 0〜1、未検出は `0,0,0`）。Knowledge JSON の
  `export.keypoints_2d` はこの三つ組に倣い、
  `keypoint_order` で語彙を自己記述。
  https://github.com/CMU-Perceptual-Computing-Lab/openpose/blob/master/doc/02_output.md
- **COCO-17 / BlazePose-33**: Slice は19関節語彙
  （頭・首・肩・肘・手首・胸・骨盤・膝・足首・足先・spine）。
  顔パーツを持たず chest/pelvis/spine を持つのは
  SMPL系の骨盤中心モデル寄り。

## 統計的人体モデル

- **頭身比**: 成人 ≈7.5頭身、子供 ≈5.5、デフォルメ 2.5〜3.5。
  anatomy.py の priors に直写し。SMPL/SMPL-X は Phase 3 の等価モデル候補。

## 不確実性の扱い

単一画像から服の下・遮蔽部は確定不能（SRS P0リスク）。
Slice は確率的断定を避け、observed/predicted 分離 + confidence +
`basis`（根拠文字列）で監査可能性を確保する設計を採用。
