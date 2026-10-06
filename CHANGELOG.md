# Changelog

## [Unreleased]

- `slice.diff` 新設 — Knowledgeドキュメント差分監査（関節の
  追加/消失/移動px・state反転（observed→predicted降格を明示）・
  信頼度ドリフト・モデル/ポーズ変更をフィールド単位列挙）
||||||| 7a75385
- `slice.autocrop` 新設 — 前景bboxの人物クロップ提案
  （マージン/アスペクト比指定、フレーム超過は正直にclamp、
  空フレームは state:"unknown" で推測しない）。前処理ユーティリティ
||||||| 7a75385
- `slice.horizon` 新設 — 両足接地線から地面傾斜=カメラロール角を
  推定＋足の奥行きヒント（低い足=近い）＋カメラ高さ仮定での
  horizon_y。仮定は `assumption` に全開示、足が揃わなければ
  state:"unknown" で推測しないシーン幾何層
||||||| 7a75385
- `slice.audit` 新設 — Knowledgeドキュメントの誠実性リント
  （validateの先：観測率閾値・basis有無・confidence疑義・
  prediction帳簿の陳腐化・低証拠上の意味ラベルを警告コード化）
||||||| 7a75385
- `slice.dedup` 新設 — データセット重複検出（pelvis基準・
  トルソ正規化の平均関節距離がeps未満のペアを列挙、
  解像度/平行移動不変）
||||||| 7a75385
- `slice.bundle` 新設 — Knowledge Store の単一zip梱包/展開
  （manifest.json付き配布フォーマット、スキーマ検証ゲート
  をexport側にも適用、id無しエントリはskipped計上）
||||||| 7a75385
- `slice.pad` 新設 — Bitmapレターボックス（中央配置＋オフセット
  返却で座標系を保全、縮小は拒否してcropへ誘導、
  to_aspect/to_square）
||||||| 7a75385
- `slice.crop` 新設 — Bitmap矩形切り出し（autocropのcrop提案を
  適用する実行側、枠外はclamp・重なり無しはValueError）
||||||| 7a75385
- dataset+knowledge: Devin Review 3件修正 — ストア内の非object
  JSON（`[]`等）で `list()` が AttributeError で全エクスポート
  中止 → スキップ、`from_store` がスキーマ不正docを通す →
  `validate()` で除外、`to_jsonl([])` が `"\n"` の幽霊レコード
  を返す → `""` に
- `slice.dataset` 新設 — Knowledge Store の一括エクスポート
  （ドキュメント要約CSV／関節ロングフォーマットCSV／JSONL）。
  欠損関節は行を出さず state/basis を保持 — Phase 2 の
  データセット管理を外部ツールへ橋渡し
- `slice.reid` 新設 — 人物再同定。骨長比率ベクトル（前腕/上腕・
  下腿/大腿・肩幅/胴長など9種）でポーズが変わっても追跡できる
  同一人物キュー。`state:"estimated"`（2D投影のソフトキュー、
  生体認証ではない）、共有特徴0なら同定判定は None で推測しない
||||||| 7a75385
- `slice.gltf` 新設 — 骨格を glTF 2.0 ノード階層としてエクスポート
  （pelvisルートの運動学ツリー、子translationは親相対、各ノードの
  extrasに state/confidence/basis を保持）。2D→XY平面リフトで
  Z=0を asset.extras に正直に開示 — Phase 3 への第2ブリッジ
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
- `slice.plumb` 新設 — 鉛直線姿勢整列。head/neck/chest/pelvis/足首
  の横偏移を身長比で計測（頭部前方位=forward_head検出、
  stack_score=胴チェーン平均偏移で姿勢品質を連続量化）
||||||| 7a75385
- `slice.retarget` 新設 — ポーズ・リターゲット。src骨格の骨方向
  ×dst骨格の骨長でpelvisから運動学ツリーを下りて座標再構成 —
  同じポーズを別体格へ転写。出力は全て state=predicted
  basis=retargeted（合成幾何は観測証拠ではない）
||||||| 7a75385
- `slice.lift` 新設 — 2D骨格の擬似3Dリフト。向き推定の奥行き
  手がかりからz座標を割当（front/unknown=全z0「奥行き証拠なし
  =平坦を正直に」、side=遠側肢に+z肩幅半分）。全zにbasis
  （no_depth_cue/facing_side）を明記 — zは計測ではなくプライア
||||||| 7a75385
- `slice.mass` 新設 — 体重推定。シルエット面積×身長プライア換算
  ×奥行係数0.28×軟組織密度1.04 → kg（仮定チェーン全開示: depth_cm/
  height_cm/volume_l、全出力estimated明記）＋BMI
||||||| 7a75385
- `slice.limbs` 新設 — 四肢長プロファイル。腕（肩→手首）/脚
  （股関→足）のチェーン合計をpx＋身長比＋partial（一部predicted
  含む）＋左右差deltaで計測 — 人体測定レポート層
||||||| 7a75385
- `slice.mutate` 新設 — ノイズ・遮蔽・クロップの画像変換。
  証拠が部分的な時に関節が predicted/欠損に落ち（observed を
  捏造しない）誠実性をロバストネステストで検証するための道具
||||||| 7a75385
- `slice.angles` 新設 — 関節角度の解剖学的計測（度数）。
  屈曲角=中間関節の内角（180°=完全伸展）、挙上角=胴体垂直からの
  方向角（0°=下垂/90°=水平/180°=頭上）＋torso_lean。欠損関節は
  推測せず項目ごと省略
||||||| 7a75385
- `slice.oks` 新設 — OKS（Object Keypoint Similarity）評価指標。
  関節ごと exp(-d²/2(sk)²)：s=参照骨格bbox面積の平方根（スケール
  正規化）、k=関節別許容度（股関節は厳格・手首は寛容）。
  参照に存在しない関節は評価対象外、推定側欠損は0点。
  COCO公式評価メトリクス実装
||||||| 7a75385
- Landmarks: 運動学ツリー追加 — pelvisルートの `PARENT` マップと
  `chain()` ヘルパ（SMPL系と同じルート規約。補完・正規化・将来の
  3D化で共有する関節語彙）
||||||| 7a75385
- `slice.scale` 新設 — 頭長の人体計測プライア（成人~23cm等）から
  px→cm換算率を推定し、身長/胴/四肢/肩幅を実寸（cm）で報告。
  `state:"estimated"` 明記 — 世界の実測ではなくプライア由来の
  推定スケールであることを誠実に表明
||||||| 7a75385
- `slice.handpos` 新設 — 手の位置意味づけ。手首を身体スキーマ
  相対でゾーニング（above_head/at_head/at_chest/at_waist/at_hip/
  at_knee/hanging）、胴体スパン比で身長非依存、predicted手首は
  ゾーニングしない
||||||| 7a75385
- `slice.dynamics` 新設 — 運動含意スコア。単フレームから「動きの
  最中っぽさ」をキュー加重投票（脚軸外れ・腕外振り・重心が足外・
  広い歩幅）→ static/possibly_dynamic/dynamic。state:"implied"
  で「動いている」とは言わない誠実設計
||||||| 7a75385
- `slice.coco` 新設 — COCOキーポイント形式エクスポート。
  17関節[x,y,v]で v=2観測/1不可視/0欠損のCOCO可視性規約が
  observed/predicted/missingに対応（誠実性契約がそのままCOCOの
  意味論に乗る）。Slice固有関節は unmapped_joints に列挙。
  学習データセット標準との互換レイヤー
||||||| 7a75385
- `slice.reach` 新設 — 機能的リーチ包絡。肩中心に上腕+前腕(+8%手)
  の作業空間で任意点の届き判定（inside<85%/edge/outside、欠腕骨は
  身長プライアでestimated明記）。`workspace()` で両腕包絡
||||||| 7a75385
- `slice.paf` 新設 — Part Affinity Field。各骨に「親→子の方向
  ベクトル場」を帯域上に生成（OpenPoseの連結チャネル）。検出点
  だけでなく「どの関節同士が繋がるか」を場として表現。predicted
  骨は strength 減衰 — 連結の確からしさも誠実に表現
||||||| 7a75385
- `slice.smooth` 新設 — 関節軌跡の時系列スムージング（対称移動
  平均）。フレームごとの推定ジッタを抑えつつ位置のみ平滑化し
  state/confidenceは中央フレームを保持。欠損フレームは欠損の
  まま — 平滑化が存在しない位置を捏造しない設計。`jitter()` で
  フレーム間変位の定量計測
||||||| 7a75385
- `slice.spine` 新設 — 脊柱カーブ。neck-chest-pelvisで横偏移
  （側弯様）＋前傾角（前弯様）＋curvature（鎖長/弦長）を計測、
  classify=straight|lateral / upright|leaning
||||||| 7a75385
- `slice.dominance` 新設 — 荷重優位側推定。骨盤の足首中点偏移
  （>15%半脚間=側方荷重）＋膝屈曲による脱荷脚の逆側投票で
  dominant l|r|even|unknown＋confidence＋全cues開示
||||||| 7a75385
- `slice.rig` 新設 — 骨格をアニメーション用リグとして出力
  （name/parent/head/tail/length/dir/confidence の17ボーン、
  pelvisルート）。リターゲット・BVH/GLTF変換・3D化で使う骨構造。
  欠損関節の骨はゼロ化せず省略 — リグは知っている分だけを正直に表す
||||||| 7a75385
- `slice.contact` 新設 — 自己接触検出。observed関節ペアの近接を
  身長比で判定（hands_together/hand_at_head/arms_crossed/
  feet_together）。predicted関節は絶対に接触と報告しない —
  推測同士の近接は証拠にならない
||||||| 7a75385
- `slice.rom` 新設 — 可動域監査。肘10–180°/膝15–180°/足首30–175°
  /肩20–175°の解剖学的限界を超えた角度をoverextended（observed）
  またはimplausible（predicted混入）として報告、境界±8°は
  hypermobile。violations()で違反のみ抽出
||||||| 7a75385
- `slice.bvh` 新設 — 骨格をBVH（Biovision Hierarchy）テキスト出力。
  pelvisルート・OFFSETは親相対・CHANNELSはroot6+各関節3、
  1フレームモーション（回転は未観測ゆえ全0 — 誠実なゼロ埋め）。
  Blender/MotionBuilder等のリターゲットツールが読む標準形式
||||||| 7a75385
- `slice.ik` 新設 — 2ボーン逆運動学ソルバ（肩→手首目標から肘位置
  を円の交点で解析的に求解。bendで屈曲側選択、届かない目標は
  最大伸展にclampして「解剖学的に届く所」を正直に返す）。
  ポーズ編集・制約付き補完の基礎
||||||| 7a75385
- `slice.occlusion` 新設 — 欠損理由推定。unobserved関節を理由別に
  分類（シルエット内=occluded、フレーム外=truncated、未予測=
  absent、マスク外=unobserved）。「欠損」を単一語でなく証拠の
  性質で区別する監査層
||||||| 7a75385
- `slice.segment` 新設 — 前景ピクセルを最寄りの骨セグメントで
  部位ラベル付け（head/torso/upper_arm/forearm/thigh/shin/foot L/R）。
  DensePose系のdense part labelingの軽量版。`summary()` で部位ごとの
  証拠ピクセル量・割合を集計。骨が欠損した部位はピクセル0 —
  証拠のみをラベルし予測で増やさない設計
||||||| 7a75385
- `slice.contour` 新設 — 前景マスクの外周トレース（Moore近傍追跡）
  と形状記述子（面積・周長・bboxアスペクト・コンパクト性・重心）。
  部位をまたがない「形そのもの」の特徴量で、姿勢変動に頑健な
  シルエット記述（古典的形状記述子系に準拠）
||||||| 7a75385
- `slice.consistency` 新設 — `audit(skel)` が骨格の健全性違反を
  列挙（画像外座標・プライア範囲を大きく外れた四肢長・左右非対称・
  反転/平坦な身体）。「ありえない骨格」を機械検出する監査層
||||||| 7a75385
- `slice.sample` 新設 — 関節周辺ウィンドウの色統計（mean RGB・
  肌色率・輝度）で「素肌/被覆/画素なし」を部位別に判定。
  素肌の腕と衣類の腕では知識の意味が違う — 性別的・解剖学的
  知識の原料となる局所色解析。画素のない関節は推測せず no_pixels
||||||| 7a75385
- `slice.gait` 新設 — 歩行位相キュー。脚ごとに stance/swing/unknown
  （膝屈曲角150°+股関直下=支持脚、膝屈曲or軸外=遊脚）＋step_width
  ＋double_support。静止画で「歩行中に見える」位相推測、欠損脚は
  unknown
||||||| 7a75385
- `slice.balance` 新設 — 静的バランス評価。Winter人体計測質量プライア
  で重心を推定し足の支持多角形に投影（inside/marginal/outside、
  証拠不足はunknown推測せず）。バイオメカニクス的「立っていられるか」
||||||| 7a75385
- `slice.compare` 新設 — 2つの Knowledge ドキュメント間のポーズ距離
  （pelvis原点・胴長=1の正規化空間で共通関節の平均距離）。
  解像度・構図に非依存で、比較に使った関節数も報告
||||||| 7a75385
- `slice.ground` 新設 — 地面ライン推定。最下observed支持関節
  （foot→ankle）でground_yを決め、接地/浮遊/端切れを判定
  （support_is_lowest=grounded、フレーム端=cropped — 推測で
  接地と言わない、他関節が足下=airborne）＋clearance
||||||| 7a75385
- `slice.gesture` 新設 — 規則ベースジェスチャ検出（wave=手首が
  頭の上0.3腕長、hands_on_hips=手首が腰+肘外張り、point=腕水平
  ~完全伸展）。証拠はobserved関節のみ — predicted肢からは
  ジェスチャを主張しない
- Anatomy Engine: `select_model` の confidence に第2候補との
  マージンを反映 — 測定値が2モデルの境界近くにあるとき自信を下げ、
  誠実な曖昧さを表明（境界では ~0.5 に減衰）
- Ratio Engine: `arm_span`（指先-指先/身長、ウィトルウィウス的比例）と
  `leg_to_torso`（脚長/胴長）を追加 — 姿勢と身体プロポーションの
  両シグナルとして Knowledge JSON に出力
||||||| 7a75385
- Pipeline: `warnings` フィールド追加 — 観測関節<8個・手首未観測・
  足部未観測の警告コードを Knowledge JSON に記録
||||||| 7a75385
- Viewer: 関節行に `basis`（配置根拠）をツールチップ表示、Ratiosに
  arm_l/arm_r/arm_span/leg_to_torso を追加
||||||| 7a75385
- Overlay: facing が left/right のとき頭上に向き矢印を描画（緑、
  状態色と区別）
||||||| 7a75385
- Pose Classification: `bend`（前傾/お辞儀）ラベル追加 — 脚は直立なのに
  胴体軸の水平傾きが胴長の45%超。`torso_tilt` 信号を追加
||||||| 7a75385
- Style Detection: 肌色シグナル `skin_ratio` を追加 — クラシックな
  肌色域（R>G>B・暖色）のピクセル率をsignalsに記録し、
  ポートレート系写真を `real` に拾う第2の写実手がかりとして利用
||||||| 7a75385
- Pose Engine: 股下の腕追跡を修正 — 脚の識別を「最広2ラン」から
  「足（最下行ラン）のx区間上に中心があるラン」へ変更。脚より幅広い
  手が脚と誤除外され残った脚が手首と誤観測される問題を解消。
  腕バンドも受容ランで拡張し、外側へ流れる腕の追跡が切れないように
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
