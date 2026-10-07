# Knowledge JSON v1 (`slice.knowledge/v1`)

Slice の成果物。画像そのものではなく、画像から推論した人体知識を保持する。
`source.image_retained = false` が示す通り、元画像は保存してよい。

## トップレベル

| フィールド | 型 | 説明 |
|---|---|---|
| `schema` | string | 固定 `"slice.knowledge/v1"` |
| `id` | string | `k_<12hex>` |
| `created_at` | string | ISO 8601 UTC |
| `engine` | object | `{name, version, slice}` — 推定器識別 |
| `source` | object | `{name, sha256, image_retained}` |
| `skeleton` | object | 下記 |
| `pose` | object | `{pose, label, confidence, signals}` 姿勢分類（`unknown` あり） |
| `style` | object | `{style, label, confidence, signals}` スタイル推定（real/anime/illustration/unknown） |
| `ratio` | object | 比率解析結果 |
| `prediction` | object | `observed`/`predicted`/`filled` 関節名リスト |
| `coverage` | object | `{joints_total, observed, predicted, unfilled, observed_ratio, mean_observed_confidence}` — 画像証拠への依存度 |
| `warnings` | string[] | 証拠の薄さの警告コード（`few_observed_joints`, `no_observed_wrists`, `no_observed_feet`） |
| `export` | object | 相互運用形式 |

## skeleton

```json
{
  "frame": {"width": 240, "height": 420},
  "joints": {
    "elbow_l": {"x": 76.0, "y": 169.0,
                "confidence": 0.574,
                "state": "observed",
                "basis": "arm blob mid-extent"}
  },
  "bones": [["shoulder_l", "elbow_l"], ...],
  "orientation": {"facing": "front|side|three-quarter",
                  "confidence": 0.0, "symmetry": 0.0},
  "body_model": {"name": "adult|child|deformed",
                 "label": "...", "confidence": 0.0,
                 "measured_head_ratio": 0.0,
                 "state": "estimated"},
  "normalized": {"origin": "pelvis",
                 "unit": "neck_pelvis_length",
                 "joints": {"elbow_l": {"x": 0.5, "y": -0.3}, ...}}
}
```

- `normalized`（任意）: pelvis原点・neck–pelvis距離=1の正規化座標。
  画像サイズ・構図に非依存なので画像間のポーズ比較に使う。
  pelvisかneckが欠損している場合は省略される。

- `state`: `observed` | `predicted`。predicted はUIで橙表示必須。
- `basis`: その関節を置いた根拠（監査用文字列）。
- `confidence`: 0〜1。prior補完は 0.2、ミラーは元の半分。

## export

```json
{
  "keypoints_2d": [x0, y0, c0, x1, y1, c1, ...],
  "keypoint_order": ["head", "neck", ...],
  "bones": [[a, b], ...]
}
```

OpenPose `pose_keypoints_2d` と同じ x,y,c 三つ組の並び
（欠損は `0,0,0`）。`keypoint_order` が COCO 等とのマッピング表になる。
3D 化時は `keypoints_3d` を追加する拡張点。

## 互換性方針

- `schema` 値を変えずにフィールド**追加**は可（読み手は未知キーを無視）
- 破壊的変更は `slice.knowledge/v2` として新スキーマ
- `validate()` は必須キー・state 値・confidence 範囲を検査

## v1.1: `analysis` 拡張スロット (`slice.knowledge/v1.1`)

v1 の全フィールドに加えて、名前付き解析レイヤを格納する
`analysis` キーを持てるマイナー拡張。`knowledge.build(analysis=...)`
に渡すとスキーマが自動的に v1.1 になる。

```json
"analysis": {
  "angles": {"elbow_l_flex": 174.2, ...},
  "gesture": {"gestures": [], "count": 0},
  "occlusion": {"reasons": {...}},
}
```

- 各レイヤは自由形式のdict — 独自の `state`/`basis`/`assumption`
  語彙（estimated/implied 等）を持ってよい
- 新規ドキュメントで `analysis` を持つ場合は **v1.1** として
  ビルドする（`build(analysis=...)` が自動昇格）
- v1ドキュメント上の `analysis` も受理（先行して書き出された
  ドキュメントの読み込み互換。形状検査のみ適用）
- 関節の `state` は引き続き observed/predicted のみ
  （拡張語彙はジョイントではなくレイヤ側に閉じ込める）
