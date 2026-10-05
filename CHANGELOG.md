# Changelog

## [Unreleased]

- bitmap: Adam7 インターレースPNGのデコード対応（スキャンラインの
  フィルタ解除を共通化し、7パス配置で全色タイプに対応）
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
