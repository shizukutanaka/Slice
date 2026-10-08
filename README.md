# Slice

人物画像・イラストを棒人間として捉え、統計的人体モデルに基づき全身を推定し、
2D/3Dの**知識**として保存する人体理解エンジン。

「画像を見るAI」ではなく「人体を理解するAI」。
画像は捨ててよい。**Knowledge JSON だけが残る。**

> [!IMPORTANT]
> 推定結果は解剖学モデルに基づく**推論**であり、被写体の断定ではない。
> 全関節は `observed`（観測）と `predicted`（推定）に分離され、
> 0〜1 の信頼度を持つ。UI・データ構造の両方でこの区別を保持する。

## セットアップ

依存なし。Python 3.9+ の標準ライブラリのみで動く。

```bash
git clone https://github.com/shizukutanaka/Slice.git
cd Slice
python3 -m slice analyze <image.png>
```

JPEG / WebP は `Pillow` がある場合のみ対応（PNG / BMP は標準でOK）。

## 使い方

### CLI

```bash
# 解析して Knowledge JSON を出力
python3 -m slice analyze person.png -o knowledge.json

# 骨格オーバーレイPNGも描く（青=observed / 橙=predicted）
python3 -m slice analyze person.png --overlay overlay.png

# ファイルストアに保存
python3 -m slice analyze person.png --store knowledge/

# 人体モデル指定（adult / child / deformed）
python3 -m slice analyze person.png --model deformed
```

### REST + ビューア

```bash
python3 -m slice serve --port 8000
# → http://127.0.0.1:8000 にドラッグ&ドロップで解析
```

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/` | 2Dスケルトンビューア |
| POST | `/analyze?model=&save=1` | 画像bytes → Knowledge JSON |
| GET | `/models` | 身体モデル一覧（adult/child/deformed） |
| GET | `/knowledge` | 保存済み一覧 |
| GET | `/knowledge/<id>` | 個別取得 |
| GET | `/overlay/<id>.png` | 骨格オーバーレイPNG |
| GET | `/health` | 生存確認 |

## パイプライン

```
Import → Pose(シルエット推定) → Skeleton
       → Prediction(対称+プライアで欠損補完)
       → Ratio(頭身/肩幅/脚長/重心/対称性)
       → Pose Classification(立つ/座る/歩く/走る/寝る/しゃがむ)
       → Knowledge(slice.knowledge/v1 JSON) → Export
```

## モジュール

70+モジュールが関心事で層分けされている。どれも stdlib のみ。

**コア（画像→骨格→知識）**

| ファイル | 責務 |
|---|---|
| `slice/bitmap.py` | PNG/BMPデコード・PNGエンコード（stdlibのみ） |
| `slice/landmarks.py` | 関節語彙・骨格グラフ・左右ミラー |
| `slice/skeleton.py` | Joint/Skeletonモデル（state/basis/confidence） |
| `slice/pose.py` | PoseEstimatorポート + シルエットヒューリスティック |
| `slice/anatomy.py` | 統計的人体モデル（成人/子供/デフォルメ）+ 選択 |
| `slice/predict.py` | 欠損推定（対称ミラー → プライア配置） |
| `slice/knowledge.py` | Knowledge JSON 構築・検証・ファイルストア |
| `slice/pipeline.py` | CLI/REST共通の解析パイプライン |
| `slice/rest.py` / `slice/viewer.html` / `slice/__main__.py` | REST API・ビューア・CLI |

**姿勢・形態の意味レイヤ（骨格ベース）**

`angles`（関節角度） `axis`（体軸PCA） `balance`（重心×支持多角形）
`classify`（姿勢分類） `contact`（自己接触） `dominance`（荷重優位側）
`dynamics`（運動含意） `framepos`（構図） `gait`（歩行位相）
`gesture`（ジェスチャ） `ground`（地面/接地） `handpos`（手の位置）
`horizon`（カメラロール） `limbs`（四肢長） `occlusion`（欠損理由）
`plumb`（鉛直整列） `reach`（リーチ包絡） `rom`（可動域監査）
`spine`（脊柱カーブ） `symmetry`（左右対称） `ratio`（比率）
`mass`（体重推定） `style`（スタイル推定）

**シルエット形状・前処理**

`contour`（輪郭） `distfield`（肢体太さ） `mask`（前景マスク）
`topology`（穴/位相） `autocrop`（クロップ提案） `crop` / `pad`
（画像変換） `mirror` / `mutate` / `norm`（座標・反転・変換）

**時系列・同一人物・照合**

`motion`（フレーム間移動） `smooth`（軌跡平滑） `reid`（人物再同定）
`compare`（ポーズ距離） `signature`（ポーズ指紋）

**評価・QA・データセット**

`evaluate`（正解フィクスチャ） `oks`（COCO類似度） `bench`（回帰ゲート）
`audit`（誠実性リント） `consistency`（骨格健全性） `stats`（死角集計）
`diff`（ドキュメント差分） `dedup`（近重複） `dataset` / `bundle`
（エクスポート/配布） `diag`（失敗診断）

**描画・出力**

`render`（PNGオーバーレイ） `svg`（ベクター） `ascii`（ターミナル）
`heatmap` / `paf`（OpenPose式場） `sheet`（コンタクトシート）
`describe`（自然言語説明）

**3D・外部形式**

`lift`（擬似3D） `rig`（骨ツリー） `retarget`（ポーズ転写）
`ik`（2-bone IK） `scale`（実寸換算） `bvh` / `gltf` / `coco`
（標準形式エクスポート） `sample`（部位色） `segment`（部位ラベル）

## テスト

```bash
python3 -m unittest discover -s tests
```

## 設計原則

- **Observed / Predicted の完全分離** — 推定は推定と名付ける
- **知識保存、画像は捨てられる** — Knowledge JSON が成果物
- **モデルは候補、断定ではない** — 人体モデル選択も confidence 付き推定
- **依存ゼロ** — 新しい推定器は `PoseEstimator` ポート実装として差し替え可能

## ロードマップ

- Phase 1（本リリース）: 単一画像→骨格推定→全身補完→比率→Knowledge JSON
- Phase 2: 複数モデル切替・姿勢分類・ヒートマップ・データセット管理
- Phase 3: 3D投影（SMPL等価モデル）・Rig・GLTF・Blender/Unity連携

詳細は `docs/` 参照。調査メモは `docs/RESEARCH.md`。
