# Knowledge JSON 仕様 (`slice.knowledge/v1` / `slice.knowledge/v1.1`)

Slice の成果物の形式仕様。画像そのものではなく、画像から推論した
人体知識を保持する。`source.image_retained = false` が示す通り、
元画像は保存しない（残るのは `source.sha256` のハッシュだけ）。

この文書が形式の正本である。実装（`slice/knowledge.py` の
`build()` / `validate()`、`slice/pipeline.py`）と食い違う場合は
実装が正であり、この文書の側を直す。仕様と実装の一致は
`tests/test_knowledge_spec.py` が固定している。

## 版の体系

| `schema` 値 | 意味 |
|---|---|
| `slice.knowledge/v1` | 基本形式 |
| `slice.knowledge/v1.1` | v1 に `analysis` 拡張スロットを持つ文書として `build(analysis=...)` が刻印する版 |

- `validate()` は両版を受理する（受理集合は `knowledge.SCHEMAS`）。
- **現行パイプライン（`pipeline.analyze` 等）が出す文書は
  `slice.knowledge/v1` のまま `analysis` を持つ。** パイプラインは
  `build()` の後に `analysis` を差すため v1.1 には昇格しない。
  つまり `analysis` の有無は `schema` 値では判断できない。
  読み手はキーの有無で判断すること（互換性の約束も参照）。
- v1 文書上の `analysis` も受理される（形状検査のみ）。

## 文書の出所と必須性

文書には2つの出所があり、持つブロックが違う。

- **核**: `knowledge.build()` が常に書くブロック。
  形式として必須なのはこの範囲。
- **パイプライン追加**: `pipeline.analyze` / `analyze_multi` が
  上乗せするブロック。受け取った文書に無いことがある。

読み手は「核は常にある」「追加ブロックは欠けてもよい」を前提に
読むこと。

## トップレベル

| フィールド | 型 | 出所 | 説明 |
|---|---|---|---|
| `schema` | string | 核 | `"slice.knowledge/v1"` または `"slice.knowledge/v1.1"` |
| `id` | string | 核 | `k_<12桁の小文字hex>`。文書の同一性はこの値（保存時はファイル名と一致しなければならない） |
| `created_at` | string | 核 | ISO 8601 UTC（例 `2026-01-01T00:00:00+00:00`）。移行された旧文書では空文字列がありうる |
| `engine` | object | 核 | 推定器の識別。下記 |
| `source` | object | 核 | `{name, sha256, image_retained}`。`name` は入力のファイル名部分のみ（空もありうる。CLI に渡したパスや `X-Image-Name` のディレクトリ部分は `/` と `\` のどちらの区切りでも捨てる — 共有される文書に OS のユーザー名やフォルダ名を残さないため）、`sha256` は元画像バイト列の SHA-256 hex（画像なしで構築した場合は空文字列）、`image_retained` は常に `false` |
| `skeleton` | object | 核 | 下記 |
| `pose` | object | 核 | 姿勢分類 `{pose, label, confidence, signals}`。構築時に姿勢が渡されなければ空オブジェクト |
| `ratio` | object | 核 | 比率解析結果。下記（エラー形あり） |
| `prediction` | object | 核 | `observed` / `predicted` 関節名リスト。パイプライン文書では `filled` も加わる |
| `coverage` | object | 核 | 画像証拠への依存度。下記 |
| `export` | object | 核 | 相互運用形式。下記 |
| `style` | object | 追加 | スタイル推定 `{style, label, confidence, signals}`。`style` は `real` / `anime` / `illustration` / `unknown` |
| `warnings` | string[] | 追加 | 証拠の薄さの警告コード。下記の全コード表 |
| `analysis` | object | 追加 | 名前付き解析レイヤの辞書（v1.1 スロット）。下記 |
| `people` | object | 追加 | 複数人解析（`analyze_multi`）の文書のみ。`{index, count, components, state, basis}` — 同一画像から生まれた兄弟文書のうち何番目か。`components` は骨格化に回った前景成分数で `count` より大きいことがある |

`engine`: 構築者が渡す辞書で、形式としては中身を固定しない。
現行パイプラインは `{name, version, slice}` に加えて
`profile`（`"default"` / `"robust"`）と、任意で
`mask_threshold`（`{value, method}` — 証拠生成に使ったマスク閾値の
決定）を書く。読み手は `engine` の未知キーを無視すること。

`_` で始まるキー（`_bitmap` 等）は実行時専用で形式の一部ではない。
直列化された文書には現れない（`pipeline.strip_runtime` が除去する）。

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
  "orientation": {"facing": "front",
                  "confidence": 0.8, "symmetry": 0.981,
                  "head_shift": 1.0},
  "body_model": {"name": "adult",
                 "label": "成人（統計モデル）",
                 "confidence": 0.683,
                 "measured_head_ratio": 0.135,
                 "prior": "adult",
                 "state": "estimated"},
  "normalized": {"origin": "pelvis",
                 "unit": "neck_pelvis_length",
                 "joints": {"elbow_l": {"x": -0.398, "y": -0.129,
                                        "state": "observed"}, ...}}
}
```

- `frame`: 関節座標が生きる作業座標系の大きさ。パイプラインが
  元画像を縮小した場合は `frame.source`（`{width, height}`）に
  元画像の大きさが入り、座標を元画像へ戻せる。
- `joints`: 関節名 → `{x, y, confidence, state, basis}`。
  座標は `frame` 内のピクセル（小数第3位まで）。
  `basis` はその関節を置いた根拠の監査用文字列（空文字列もありうる）。
  文書に現れる関節は語彙（下記）の部分集合で、全関節が揃う保証はない。
- `bones`: 両端の関節が文書に存在する組だけが入る
  （`export.bones` と違い全組ではない）。
- `orientation`: `facing` は
  `front` / `left` / `right` / `side` / `three-quarter` のいずれか。
- `body_model`: `name` は `adult` / `child` / `deformed`。
  `prior` は関節配置に実際に使ったプライア表の名前で、
  計測で選ばれた `name` と異なりうる。`state` は `"estimated"`。
- `normalized`（任意）: pelvis 原点・neck–pelvis 距離 = 1 の
  正規化座標。pelvis と neck の両方が `observed` のときだけ現れる。
  各関節は `{x, y, state}` を持ち、`state` が付くのは
  推測で置かれた位置と計測位置を区別するため。
  不変条件（pelvis が原点、neck が距離1）は `validate()` が検査する。

### 関節語彙

順序固定の19個。この順序が `export.keypoint_order` そのものである。

```
head, neck, shoulder_l, shoulder_r, elbow_l, elbow_r,
wrist_l, wrist_r, chest, pelvis, hip_l, hip_r,
knee_l, knee_r, ankle_l, ankle_r, foot_l, foot_r, spine
```

`spine` はミラー推測専用の中点で、運動学ツリーの節点ではない。
`bones` の語彙は17組（`slice/landmarks.py` の `BONES` が正本）。

## state と confidence の意味論

- `state`: `observed` | `predicted` の2値のみ。
  - `observed` — 画像内のシルエット特徴がその関節を支持している。
  - `predicted` — 対称性や解剖プライアで補完した位置。証拠ではない。
- **`observed` は「人物が写っていること」の証拠ではない。**
  人物でない塊からも `observed` 関節は生まれる
  （ベンチマークの negative 種別が実測で記録している。
  `docs/BENCHMARK.md` 参照）。人物の有無の判定は読み手の側の仕事。
- `confidence`: 0〜1。prior 補完は低い固定値（0.2、足は 0.25、
  補間は 0.3）、ミラー補完は元の半分。つまり高い `confidence` は
  `observed` でのみ意味を持つ。
- UI で表示する側は `predicted` を視覚的に区別すること
  （Slice 自身のビューアでは橙表示）が形式の前提である。

## prediction / coverage

- `prediction.observed` / `prediction.predicted`:
  関節の `state` を写したリスト。関節側と矛盾する文書は
  不正であり、`validate()` が弾く（補完を証拠と偽る文書を
  形式として許さない、がこの2リストの存在理由）。
- `prediction.filled`（パイプライン追加）:
  その回の解析で予測補完が新規に置いた関節名。
- `coverage`: `{joints_total, observed, predicted, unfilled,
  observed_ratio, mean_observed_confidence}`。
  `joints_total` は語彙の総数（19）で、
  `observed + predicted + unfilled = joints_total` が成り立つ。
  `mean_observed_confidence` は observed 関節の平均
  （observed が無ければ 0）。

## pose / ratio

- `pose.pose`: `stand` / `sit` / `walk` / `run` / `lie` /
  `crouch` / `bend` / `invert` / `unknown`。
  `label` は表示用文字列で、機械可読な正は `pose` の値。
  `signals` は判定根拠の辞書（中身は分類器の版に依存する）。
- `ratio`: 身長で正規化した比率の辞書。キーは
  `body_height_px`, `head_to_body`, `shoulder_width`, `hip_width`,
  `torso_length`, `arm_l`, `arm_r`, `leg_l`, `leg_r`, `arm_span`,
  `leg_to_torso`, `limb_symmetry`、任意で `center_of_mass`。
  測れない項目は `null`。関節不足のときは比率ではなく
  `{"error": "insufficient joints"}`（または
  `"degenerate skeleton"`）というエラー形になる。

## warnings の全コード

パイプラインが書く警告は次の6つだけである。

| コード | 意味 |
|---|---|
| `few_observed_joints` | observed 関節が8未満 |
| `no_observed_torso` | pelvis / chest / neck / head のどれも observed でない（座標系の根が推測） |
| `no_observed_wrists` | 手首が両方とも observed でない |
| `no_observed_feet` | 足首・足先が observed でない |
| `no_observed_head` | head が observed でない |
| `unknown_body_model` | 指定された体モデル名が未知で、既定プライアが使われた |

## export

```json
{
  "keypoints_2d": [x0, y0, c0, x1, y1, c1, ...],
  "keypoint_order": ["head", "neck", ...],
  "keypoints_state": ["observed", "predicted", "absent", ...],
  "bones": [[a, b], ...]
}
```

- OpenPose `pose_keypoints_2d` と同じ x,y,c 三つ組の並び。
  長さは `3 * len(keypoint_order)`（現行語彙では57）。
  文書に無い関節は `0, 0, 0`。
- `keypoints_state` は同じ順序の状態配列。値は
  `observed` / `predicted` / `absent`（文書に無い関節）。
  平坦配列だけでは補完と証拠を区別できないための併記であり、
  関節側の `state` と矛盾する文書は `validate()` が弾く。
- `export.bones` は語彙の全17組（関節の有無で絞らない）。
  `skeleton.bones`（存在する組だけ）との違いに注意。
- 3D 化時は `keypoints_3d` を追加する拡張点とする（未実装）。

## v1.1: `analysis` 拡張スロット

名前付き解析レイヤを格納する `analysis` キー。

```json
"analysis": {
  "angles": {"elbow_l_flex": 174.2, ...},
  "gesture": {"gestures": [], "count": 0},
  "occlusion": {"reasons": {...}}
}
```

- 各レイヤは自由形式の dict — 独自の `state` / `basis` /
  `assumption` 語彙（estimated / implied 等）を持ってよい。
  現行パイプラインのレイヤは `angles`, `symmetry`, `balance`,
  `spine`, `gesture`, `dynamics`, `occlusion`, `frame`,
  `consistency` の9つ（空のレイヤは省略される）。
- レイヤの中身はこの仕様の固定対象ではない。固定するのは
  「`analysis` はレイヤ名 → dict の辞書である」という容器の形だけ。
- 関節の `state` は引き続き observed / predicted のみ
  （拡張語彙はジョイントではなくレイヤ側に閉じ込める）。

## 互換性の約束

### 読み手の義務

- 未知のキー（トップレベル・サブオブジェクト内とも）を無視する。
  フィールド追加は予告なく起こる。
- 任意ブロック（`normalized`, `analysis`, `people`, `style`,
  `warnings`, `frame.source`, `engine` の追加キー）の欠落を許容する。
- `analysis` の有無は `schema` 値ではなくキーの有無で判断する
  （v1 文書が `analysis` を持つことがあるため）。
- `label` のような表示用文字列に依存しない。機械可読な正は
  `pose` / `style` / `name` 等の値キーである。

### 書き手（Slice）の保証

`slice.knowledge/v1` / `v1.1` の範囲では:

- 必須キー（`schema`, `id`, `created_at`, `engine`, `source`,
  `skeleton`, `pose`, `ratio`, `prediction`, `coverage`,
  `export`）の削除・改名・型変更をしない。
- 関節語彙19個の名前と順序、`bones` の17組を変えない。
- `state` の2値とその意味論を変えない。`confidence` は常に 0〜1。
- フィールドの**追加**はできる。新しい名前付きブロックの追加は
  `analysis` のようなマイナー昇格（v1.1）として行い、
  既存ブロックを必須化する形では行わない。
- 破壊的変更は `slice.knowledge/v2` として出す。v1 系の
  `validate()` は v2 文書を受理しない。
- 旧文書の移行は `slice/migrate.py` の `upgrade()` が行い、
  修理した箇所はすべて変更記録として開示される
  （推測で埋めた関節は `predicted` と明記され、
  `observed` と偽られることはない）。

## 検証

### ツール

```console
$ python3 -m slice validate knowledge.json [other.json ...]
knowledge.json: valid (slice.knowledge/v1)
```

- 終了コード: 全て valid なら 0、invalid な文書があれば 1、
  読み込み・JSON パースに失敗したら 2。
- invalid の場合は理由が1件ずつ表示される（黙って落ちない）。
- 実装は `knowledge.validate()` そのもの（ストア保存・梱包と
  同じゲート）であり、別の検証実装は存在しない。

### `validate()` が検査するもの

- `schema` が `slice.knowledge/v1` / `v1.1` のいずれか
- 必須キー `id`, `created_at`, `engine`, `skeleton`, `export` の存在
- 各関節の `x` / `y` / `confidence` / `state` の存在、
  `state` の2値性、`confidence` の 0〜1
- `prediction` リストと関節 `state` の整合
- `skeleton.frame` の width / height が正
- `normalized` の不変条件（pelvis 原点・neck 距離1）
- `export.keypoints_2d` の長さと `keypoints_state` の整合
- `analysis` の形状（レイヤ名 → dict）

### 検査しないもの（正直な境界）

次は形式上の約束ではあるが `validate()` の機械検査の対象外である:
`ratio` / `pose` / `style` / `warnings` / `people` の中身、
`coverage` の数値整合、`id` の形式（保存時に
`KnowledgeStore.save` が別途検査する）、`engine` の中身。
文書の「形式」ではなく「信頼性」の監査は
`slice/audit.py`（honesty lint）が別層として担う。
