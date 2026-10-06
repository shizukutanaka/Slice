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
- **ウィトルウィウス比例**: 両腕の水平伸展 ≈ 身長、脚長/胴長は
  成長曲線で変化。ratio.py の `arm_span`・`leg_to_torso` の根拠。
  Cañon/Vitruvius 系の身体比例はイラスト解剖書の共通基準。

## ヒートマップ型推定（Phase 2 候補）

現在のシルエット走査の次段は位置ごとの関節存在確率マップ。

- **Stacked Hourglass** (Newell et al., ECCV 2016) — 中間監督で
  ヒートマップを段階的に洗練。Slice の confidence 概念と親和。
- **PAF (Part Affinity Fields)** (OpenPose, CVPR 2017) —
  関節点だけでなく「骨方向のベクトル場」を推定し、接続の曖昧さを
  二分マッチングで解く。Slice の BONES グラフと直交する設計。
- **BlazePose** (MediaPipe) — 33関節・ビデオ向けトラッキング前提。
  Slice は静止画・説明可能性優先で別路線だが、関節語彙の
  交換フォーマットとして参照価値あり。

## 3D化（Phase 3 候補）

- **SMPL ファミリー** — pelvisルートの運動学木＋形状パラメータ。
  landmarks.py の `PARENT` は同じルート規約で揃え済み。
- **HMR / SPIN / ROMP** — 画像→SMPL回帰。Slice 経路は
  2D関節→リフティングの方が説明可能性を保てる（Videopose3D系）。
- **GLTF/BVH エクスポート** — normalized 座標 → ボーン階層への
  変換で Unity/Blender 連携の土台。

## 不確実性の扱い

単一画像から服の下・遮蔽部は確定不能（SRS P0リスク）。
Slice は確率的断定を避け、observed/predicted 分離 + confidence +
`basis`（根拠文字列）で監査可能性を確保する設計を採用。

## 実装済み設計との対応（v1.1時点）

| 先行技術 | Slice 実装 |
|---|---|
| 対称性補完・プライア補完 | predict.py（ミラー・中間関節線形補間・チェーン継続） |
| 頭身比モデル選択 | anatomy.py `select_model`（マージン反映 confidence） |
| 規則ベース姿勢分類 | classify.py（立つ/座る/歩く/走る/寝る/しゃがむ/前傾） |
| 画像統計スタイル検出 | style.py（real/anime/illustration + 肌色シグナル） |
| 解像度非依存ポーズ比較 | compare.py（pelvis原点・胴長=1） |
| 評価ハーネス | evaluate.py（検出率・位置誤差） |
