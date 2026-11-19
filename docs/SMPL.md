# SMPL / SMPL-X 対応表（Phase 3 設計図）

Sliceの関節語彙を SMPL（24 joints）/ SMPL-X に写す対応表。
Phase 3 の目標「3D人体モデルへの接続」は、まずこの写像が正確
であることにかかっている。未対応関節は推測せず明示する。

## 関節マッピング

| Slice joint | SMPL index | SMPL name | 備考 |
|---|---|---|---|
| pelvis | 0 | pelvis | ルート一致 |
| hip_l | 1 | left_hip | |
| hip_r | 2 | right_hip | |
| spine | 3 | spine1 | SMPLのspineは3分割; Sliceは1点 |
| knee_l | 4 | left_knee | |
| knee_r | 5 | right_knee | |
| chest | 9 | spine3 | Slice"chest"≒SMPL spine3（上胸椎） |
| neck | 12 | neck | |
| head | 15 | head | SMPL headは頭頂ではなく顎基部寄り |
| shoulder_l | 16 | left_shoulder | SMPLは鎖骨基部 |
| shoulder_r | 17 | right_shoulder | |
| elbow_l | 18 | left_elbow | |
| elbow_r | 19 | right_elbow | |
| wrist_l | 20 | left_wrist | |
| wrist_r | 21 | right_wrist | |
| ankle_l | 7 | left_ankle | |
| ankle_r | 8 | right_ankle | |
| foot_l | 10 | left_foot | SMPL foot=足先（つま先） |
| foot_r | 11 | right_foot | |

## Sliceに無いSMPL関節（推測しない）

| SMPL index | name | 補完方針 |
|---|---|---|
| 6 | spine2 | chest–pelvis間を補間可能（predicted） |
| 13,14 | left/right_collar | neck–shoulder間補間 |
| 22,23 | left/right_hand | wrist先端にobserved無し |
|  | eyes/ears (SMPL-X) | 顔情報はSliceの関節語彙外 |
|  | fingers (SMPL-X) | Phase 3後期の拡張ランドマーク待ち |

## 座標系の差異（最重要）

| | Slice | SMPL |
|---|---|---|
| 空間 | 2D画像 px | 3Dメートル空間 |
| y軸 | **下向き**（画像座標） | **上向き**（世界座標） |
| 基準 | 画像左上原点 | pelvisルート相対 |
| 深度 | 無し（`lift`が擬似z推定） | 完全な3D |

変換パイプライン（既存モジュールで構成済み）:

```
Skeleton --(lift: 擬似z推定)--> 深度の診断
  |------(rig: 骨ツリー/長さ/方向)--> リグ定義
  `------(retarget: 別の体格に姿勢を移す)--> 推定骨格
               |------(gltf)--> glTFノード階層
               `------(bvh)--> BVH単一フレーム
```

`python3 examples/demo_3d.py [出力先]` は合成画像から推定・リグ化・
リターゲットを行い、再構成した骨格を `figure.bvh` と `figure.gltf` に出力する。
推定関節は `figure.bvh.json` と glTF のノード `extras` で確認できる。
両形式の出力は平面（Z=0）で、デモ中の `lift` は診断のみ。

### Blender での読み込み検証

デモで生成した `figure.gltf` は Blender の **File → Import → glTF 2.0**
で開ける。関節は親子関係を持つ Empty として読み込まれ、Custom
Properties に `state`、`confidence`、`basis` が残る。
Blender は glTF の Y-up を Z-up に変換するため、平面は Blender では
XZ 平面になる。メッシュ、Armature、アニメーションは含まない。

Blender 4.5.4 LTS で動作確認済み。インポートを再検証するには、
Blender 実行ファイルを `PATH` に置くか `BLENDER_BIN` で指定し、
リポジトリのルートで次を実行する。

```bash
python3 -m unittest tests.test_demo3d.TestDemo3d.test_blender_import -v
```

実際の glTF インポーターをヘッドレスで起動し、全関節の階層・変換後の
座標・推定の由来を照合する。Blender が見つからない場合はこのテストだけ
スキップされる。Unity と Blender の BVH インポートは未検証。

## SMPL化に必要な残作業

1. **β（形状）推定** — 現在の`body_model`(adult/child)は粗い
   プライア。SMPLの10次元βに相当する連続形状が必要
2. **θ（ポーズ）推定** — 骨方向→axis-angleへの変換層
   （`rig`の出力がその前段）
3. **グローバル回転** — `axis`/`horizon`の推定を
   カメラ外部パラメータとして利用可能
4. **SMPLメッシュの頂点写像** — 6890頂点はリポジトリに
   持てないため、外部アセット参照の設計が要

## 正直さ契約の継承

3D化しても誠実性契約は維持する: SMPL推定のθ/βは全て
`state:"predicted"`、`lift`の擬似zは`basis`に推定根拠を
記録する。観測できない深度を「観測した」ことにしない。
