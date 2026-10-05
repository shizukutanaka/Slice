# Changelog

## [Unreleased]

- `slice.dataset` 新設 — Knowledge Store の一括エクスポート
  （ドキュメント要約CSV／関節ロングフォーマットCSV／JSONL）。
  欠損関節は行を出さず state/basis を保持 — Phase 2 の
  データセット管理を外部ツールへ橋渡し
- `slice.topology` 新設 — シルエット位相解析（前景成分数＋
  囲まれた背景穴＋Euler数）。「腰に手」の三角穴のような
  骨格では表せないポーズ意味を直接計測
- topology: Devin Review 3件修正 — `_largest_component` の bytearray
  ラベルが256成分で溢れてクラッシュ（pose推定自体も影響、
  list化で解消）、穴スキャンを最大成分→全前景に拡大（小さい
  リングの穴も計数）、`fg_px` を最大成分のみ→全前景合計に
- `slice.norm` 新設 — 座標変換（crop/resize/to_unit/from_unit）。
  画像変換に骨格座標を追従、フレーム外に出た関節は消さず
  `state:"out_of_frame"`＋basisに"lost to transform"を記録 —
  測れなくなったことを知識として残す
- `slice.ik` 新設 — 2ボーン逆運動学ソルバ（肩→手首目標から肘位置
  を円の交点で解析的に求解。bendで屈曲側選択、届かない目標は
  最大伸展にclampして「解剖学的に届く所」を正直に返す）。
  ポーズ編集・制約付き補完の基礎
- Anatomy Engine: `select_model` の confidence に第2候補との
  マージンを反映 — 測定値が2モデルの境界近くにあるとき自信を下げ、
  誠実な曖昧さを表明（境界では ~0.5 に減衰）
- Prediction Engine: 中間関節の線形補間 — 肘/膝が欠損でもチェーン末端
  （手首/足首）が既知なら、親子間を四肢比率で内分して配置。
  盲目的な真下へのプライア配置を解消（confidence 0.3、basis記録）
- Pose Engine: 向き推定を強化。肩幅/身長比の側面判定＋頭頂行の偏移で
  left/right/side の向きを推定（`orientation.head_shift` 信号を追加）
- Pose Classification: 関節ジオメトリの規則で 立つ/座る/歩く/走る/寝る/しゃがむ
  を推定し Knowledge JSON の `pose` フィールドとビューアに出力。
  観測率で信頼度を減衰、判別不能時は `unknown`（座る=脛垂直、しゃがむ=両脚折れ）
- Style Detection: 色数・平坦領域・エッジ密度・彩度の画像統計で
  real/anime/illustration/unknown を推定し `style` フィールドとビューアに出力
- Pose Engine: 腕候補スキャンを股下〜足元まで拡張。腰より下に垂れた腕・手首を
  observed として検出（脚領域では最広2ラン=脚を除外し、胴体横の腕バンドを追跡）

## [0.1.0] - 2026-10-05

Phase 1 MVP。

- 画像入力: PNG / BMP（stdlib デコード）、JPEG/WebP は Pillow 任意対応
- Pose Engine: シルエットヒューリスティックで19関節を推定（confidence + basis 付き）
- Prediction Engine: 対称ミラー→統計プライアの2段で欠損補完、observed/predicted 完全分離
- Anatomy Engine: 成人/子供/デフォルメの統計モデル、頭身比で選択（estimated 状態）
- Ratio Engine: 頭身・肩幅・胴長・四肢長・重心・左右対称性
- Knowledge Engine: `slice.knowledge/v1` JSON、検証、ファイルストア
- Export: OpenPose 型 x,y,c キーポイント配列
- REST: `POST /analyze`, `GET /knowledge[/<id>]`, `GET /overlay/<id>.png`, `GET /health`
- Viewer: ドラッグ&ドロップ解析、青(observed)/橙(predicted)表示、比率パネル
- CLI: `analyze` / `serve` / `list`
- テスト: unittest 21件
