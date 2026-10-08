# Phase 完了基準（定量化版）

「完成度」を感覚でなく**検証可能な条件の充足率**で定義する。
各条件はモジュールの存在・テスト・コマンド実行で確認できる。

検証方法: `python3 -m unittest discover -s tests`（全テスト）と
`python3 -m slice.bench`（精度・速度の回帰ゲート）が基本ゲート。
個別条件は右欄の確認法で点検する。

## Phase 1 — 基礎エンジン（10/10 = 100%）

| # | 条件 | 確認 |
|---|---|---|
| 1 | PNG/BMPを標準ライブラリでデコード | `bitmap.py`, tests/test_bitmap |
| 2 | 人物シルエット→関節推定 | `pose.py` HeuristicPoseEstimator |
| 3 | Jointに observed/predicted + confidence + basis | `skeleton.py` |
| 4 | 欠損を対称+プライアで補完 | `predict.py` |
| 5 | 比率解析（頭身/四肢/重心/対称） | `ratio.py` |
| 6 | Knowledge JSON 構築・検証・ストア | `knowledge.py` |
| 7 | 骨格オーバーレイ描画 | `render.py` |
| 8 | CLI（analyze/serve/list） | `python3 -m slice --help` |
| 9 | REST + ビューア | `rest.py`, `viewer.html` |
| 10 | 自動テストと回帰ゲート | `python3 -m slice.bench` |

## Phase 2 — 解析の深化（12/14 = 86%）

| # | 条件 | 確認 | 状態 |
|---|---|---|---|
| 1 | 複数人体モデル + 切替 | `anatomy.py`, `--model` | 済 |
| 2 | 姿勢分類 | `classify.py` | 済 |
| 3 | OpenPose式場（heatmap/paf） | `heatmap.py`, `paf.py` | 済 |
| 4 | スタイル推定 | `style.py` | 済 |
| 5 | 時系列（motion/smooth/track） | `motion.py`, `smooth.py` | 一部（trackはPR中） |
| 6 | 評価ハーネス + OKS | `evaluate.py`, `oks.py` | 済 |
| 7 | 意味レイヤの拡充（角度/バランス/歩行/ジェスチャ等） | `angles.py`他~20層 | 済 |
| 8 | データセット管理（export/bundle/dedup/diff/stats） | 該当モジュール | 済 |
| 9 | 実画像フィクスチャ | 実写正解データ | **未** |
| 10 | CI | GitHub Actions | **PR中** |
| 11 | 複数人検出 | `estimate_multi`経路 | 一部（peopleはPR中） |
| 12 | 部分人体診断 | `framefit`相当 | **PR中** |
| 13 | スキーマv1.1（analysis拡張・state拡張） | `knowledge.py` SCHEMAS | **PR中** |
| 14 | REST認証 | `serve(token=)` | **PR中** |

## Phase 3 — 3D人体（5/10 = 50%）

| # | 条件 | 確認 | 状態 |
|---|---|---|---|
| 1 | 擬似3Dリフト | `lift.py` | 済 |
| 2 | 骨ツリー/リグ定義 | `rig.py` | 済 |
| 3 | 体格間リターゲット | `retarget.py` | 済 |
| 4 | 標準形式エクスポート | `bvh.py`, `gltf.py`, `coco.py` | 済 |
| 5 | SMPL対応表 | `docs/SMPL.md` | **PR中** |
| 6 | IK solver | `ik.py` | 済 |
| 7 | 真の深度推定（単眼3D） | 学習系 or 幾何推定 | **未** |
| 8 | SMPL θ/β フィッティング | 形状+ポーズパラメータ | **未** |
| 9 | メッシュ/スキニング出力 | 頂点重み付きメッシュ | **未** |
| 10 | Blender/Unity実連携 | glTFを実ツールで検証 | **未** |

## 総合スコアの計算

```
完成度 = (達成条件数 / 全条件数) × 100
       = (10 + 12 + 5) / (10 + 14 + 10) = 27/34 ≈ 79%
```

Phase 3 が最重量級（真の3D化）であり、単純平均では
「97%」のような体感値はでない — 項目は粒度が違うため
この表は**進捗の構造**を示すものであって絶対尺度ではない。

## 残りの主要ギャップ（第一原理順）

1. **実写対応** — 全検証が合成シルエット。実写真の
   背景・服装・髪・顔は未カバー（AUDIT P0-4/P1-12）
2. **複数人** — 単一成分前提。top-K成分の複数Skeleton化
3. **真の深度** — liftは擬似z。単眼深度推定器ポートが要
4. **SMPLフィット** — 対応表はあるが最適化層が無い
