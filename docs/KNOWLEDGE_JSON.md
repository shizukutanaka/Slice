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
                 "state": "estimated"}
}
```

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
