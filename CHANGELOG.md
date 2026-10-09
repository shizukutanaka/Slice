# Changelog

## [Unreleased]

- predict: 推測関節をアンカーにした連鎖推測をbasisで開示。
  `prior off X`・`interpolated A-B`・`foot below ankle` の
  アンカー関節がpredictedのとき `(predicted anchor)` を付記。
  推測の上に推測を積んだ位置が観測由来の補間/ドロップと
  区別できなかった欠陥を解消（挙動は不変・開示のみ）。

- `slice rig <image> [-o rig.json]` — rig層のCLI接続。骨階層（parent/head/tail/length/dir/confidence）＋hierarchy木＋合計骨長をJSON出力。アニメーションリグ入力。

- 成分ラベリングの統合 — `people._components` が独自実装していた
  4近接BFSラベリングを `pose._label_components` 呼出に置換
  （bbox算出のみ単パスで残す）。重複アルゴリズムを1系統化、
  挙動変更なし。

- REST `POST /audit`＋CLI `slice audit <dir>` — セルフ監査の
  全経路接続（RESTでもselfcheck全層を返却、CLIはディレクトリ
  一括監査で件ごとverdict＋pass/warn/fail集計、exit codeは
  CIゲート可）

- 未使用import一掃＋デッドヘルパ削除 — 31モジュールで参照のなくなったtyping/シンボルimport（Optional/Tuple/Dict/List/Joint/Skeleton/OBSERVED/PREDICTED等36件）と、一度も呼ばれない `balance._dist_to_segment` を除去。リント相当の静的棚卸しで死荷重を削減、挙動変更なし。

- 重複ヘルパの統合 — 6モジュール（balance/dominance/dynamics/gait/plumb/reach）に同一ロジックで分散していたobserved限定ルックアップ `_obs` を `skeleton.observed_point` に一本化（`observed_body_span` と同じ置き場）。挙動変更なし、-52行。

- デッド公開面の削除 — `paf.direction_at`（PAF生成後に誰も参照しないクエリヘルパ）と `pipeline.predicted_count`（未参照の対称アクセサ）を除去。スペキュラティブAPIは保守コストだけを払うので、YAGNI原則で消去。利用者向け挙動の変更なし。

- `slice human <image>` — human層のCLI接続。前景成分ごとに人物らしさ4信号（縦横比/充填率/頭部重心/左右対称）を採点、person_like判定。成分なし/全成分非人物は exit 1。

- `slice imgqual <image>` — imgqual層のCLI接続。推定前段の画像証拠適格性（size/dynamic/blur/contrastの4計測フラグ→adequate/marginal/inadequate）。inadequateは exit 1。

- `slice evid <image>` — evid層の単体CLI接続。chamfer距離変換の正逆で各関節を interior/on_boundary/off_mask に分類、observed_on_mask_fraction＋off_mask列挙。unsupported関節ありは exit 1。

- `slice export <image> --format F [-o file]` — エクスポート層のCLI接続。bvh/gltf/coco/svg/ascii/paf/heatmapの7形式を1コマンド統合（バイナリはPNG直接出力、テキストはstdout）。外部連携フォーマットがライブラリ専用だった状態を解消。

- `slice autocrop <image> [-o out.png] [--margin m] [--aspect W:H]` — autocrop層のCLI接続。最大前景成分bboxからのクロップ提案（coverage/state/basis開示）＋`-o`でcrop.crop実クロップPNG書き出し。フレーム境界へのclampは誠実設計を継承。

- `slice compare <img|doc> <img|doc>` — compare層のCLI接続。骨盤→首単位の正規化ポーズ距離（共通関節の平均・関節別内訳、`--min-confidence`でフィルタ）。正規化不能は exit 1。

- `slice describe <image>` — NLG層のCLI接続。推定＋姿勢分類→1文の英語説明（pose/facing/四肢のobserved状況＋関節数）。describe層がライブラリ専用だった状態を解消。
- plumb: plumb line・forward_head・baseをobserved関節のみに
  修正。弦配置のpredicted chestがforward_headの胴体基準を、
  predicted ankleが支持基準offsetを捏造していた → predictedは
  欠損扱い（forward_headはNoneで測定不能）。
- pose: 水平腕（Tポーズ/腕上げ）検出 — 最広行が胴幅×1.6超のとき
  腕ストリップと判定し、肩=胴縁・肘=中点・手首=先端を観測
  （従来は肩が腕先端に吸収され118px誤差＋肘/手首未検出）。
  `evaluate.draw_case(pose="t")` でポーズ多様性のあるフィクスチャ。
- lift: 出力に関節の `state` を同梱。zの出典（basis）は従来通り
  だが、x,yがpredictedでも観測座標と区別不能だった — 推測座標は
  prior fillとして明示。

- contour: features()に`contour_closed`を開示（トレースが反復上限で未閉鎖打ち切りの際、perimeter/compactnessが下界として完全計測値を装っていた欠陥を解消）
- pipeline: warningsに`no_observed_torso`追加（四肢は観測でも運動学ルートの体幹が全て推測のdocを「アンカー未測定」として開示）
- stats/dataset: `mean_observed_confidence`を開示（観測と推測を混ぜた混成mean_confidenceが証拠品質を系統的に過小評価していた欠陥を解消、混成列は互換のため据え置き）
- predict: プライア由来のbasisにモデル名を同梱（`prior off X (child)` — どの体型モデル表で置かれたか不明だった推測関節の由来を開示）
- motion: 異フレーム骨格の変位をb→a座標系に再スケール＋`frame_scaled`/`frame_b`開示（解像度違いの生px差を運動と誤認していた欠陥）
- pipeline: warningsに`no_observed_head`追加 — 頭関節がpredicted
  のdocは、スケールアンカーとなる最重要ランドマークを未測定の
  まま下流層（headroom/ゾーン/実寸/比率）がプライア位置に依存する
  ことを開示（wrists/feetと同じ証拠の薄さコード、KNOWLEDGE_JSON
  の語彙表も同期）。

- `slice reid <A> <B>` — reid層のCLI接続。骨長比率のポーズ不変特徴量で同一人物照合（距離・same_person・共有特徴数・両側特徴量を開示）。`--threshold`調整可、照合=exit 0。basisに「2Dキューであり生体認証ではない」誠実注記を継承。

- `slice contrad <image>` — contrad層のCLI接続。classify×axis×ground×balanceのレイヤ間矛盾ルール（例: 立位なのに軸が水平/空中浮遊）。absent層はスキップ（仮定しない）。contradicted/insufficientは exit 1。

- `slice oks <A> <B>` — oks層のCLI接続。2画像のCOCO OKS骨格類似度＋関節別スコア（スケール=参照側頭高で正規化）。比較可能関節なしはnull＋exit 1。
- ratio: predicted関節を含む比率を「計測値」として出力していた
  欠陥を修正。ミラー/プライア配置の肢は構造的にプライア比率を
  再現するため、arm_l/limb_symmetry/arm_span等が捏造計測値に
  （ミラー肢のlimb_symmetryは構造的1.0）。全端点observedのみ
  計測、predictedはNoneで報告。
- sample: joints_reportをobserved関節のみに修正。predicted
  関節位置（プライア補完）で実画素を採取し `wrist_l: covered`
  等の部位帰属ラベルを捏造していた → predictedはレポート
  から除外。
- skeleton: `normalized()` のアンカーをobserved関節のみに
  修正。predictedのpelvis/neckが正規化の原点・単位になり
  推測座標がKnowledgeドキュメントに載っていた → アンカーが
  predictedならブロックごと棄権（None）。
- pose: 肩上腕（Vポーズ）検出 — 腕プローブの探索開始を肩行から
  頭帯下端に拡張し、肩より上に上がった腕を捕捉（従来は範囲外で
  肘/手首が未検出か肩近傍に誤置）。`tests.raised_arms_person`
  フィクスチャで回帰ガード。
- compare/dedup: predicted関節がポーズ距離に混入していた欠陥を
  修正。プライア配置の推測関節を距離計算に含めるとプライアを
  測るだけ（一致ならdup誤判定、ずれなら虚偽の差分）。両ドキュメント
  でobservedの関節のみ比較、predictedは欠損扱いで除外。

- skeleton: normalized 各関節に state を同梱（正規化空間で推測位置が観測と区別不能だった欠陥を解消、export.keypoints_state と同契約）
- selfcheck: 無効なmodel名を`model:unknown_body_model`理由コードで開示（analyze経路と同型のサイレントフォールバックがaudit経路に残留していた欠陥を解消）
- `slice diff <A> <B> [--store DIR]` — 比較層のCLI接続。画像パスまたは`k_<id>`を受け取り、フィールド差分（moved/added/removed/state_changed/confidence_delta＋pose/model変更）＋正規化ポーズ距離をJSON出力。diff/compare層がライブラリ専用だった状態を解消。

- bundle: unpackもpackと同型に耐性化（validate raiseのmemberをskip）＋manifest非dict拒否＋list_entryのbody_model非dict耐性（#283レビュー修正）
- bundle: unpackも同様に耐性化（validate raiseのmemberをskip）＋manifestが非dictをValueErrorで明示拒否
- bitmap: `get`の負座標がPython負インデックスで画像末尾行を
  巻き戻り読み取り、不在画素を実データとして返していた
  フェイルオープンを修正 — 全OOB読み取りはIndexErrorに
- balance: 重心・支持多角形・com_spanをobserved関節のみに
  修正。"foot below ankle"プライアのpredicted足が支持多角形
  （projected:inside）を、predicted四肢が質量カバレッジを
  捏造していた → predictedは欠損扱い（足が全predictedなら
  unknown/no_feet）。
- dominance: pelvis offset/脱荷脚キューをobserved関節のみに
  修正。predicted膝が `unloaded` キュー（利き脚を反転させる
  虚偽証拠）を、predicted足首が `pelvis_centered` の均衡証拠を
  捏造していた → predictedは欠損扱いでキュー不発。
- mutate: `crop` が負・範囲外の起点でフレーム外領域に画素を捏造
  していた欠陥を修正（`Bitmap.get` の負インデックス巻き戻りで
  反対端の画素を混入 — 頑健性テスト変換自身が偽証拠を生成）。
  フレーム外は初期化背景を保持。
- limbs: `delta`（左右差）は両側が完全計測の場合のみ報告 —
  片側が中間関節欠損で弦化（partial）した肢長を完全計測値と
  直接比較すると、弦の短縮分を「左右非対称」として捏造して
  いた（#222のpartial開示が出揃った後の比較側の対応）。
- lift: z深度スケール（肩/腰幅の半分）を観測ペアのみから計測。
  predicted端点はプライア幾何のため、借用するとモデル表の幅が
  計測値としてz軸に書き込まれていた（#330のof_body_hと同型）

- consensus: 全関節predictedの骨格を`state:observed`と虚偽報告していた欠陥を修正（1件以上observedで初めてobserved、joints有りではpredicted）
- segment: predicted骨が前景ピクセルに部位ラベルを付けていた
  欠陥を修正。プライア配置の骨は測定ではないため、両端点が
  observedの骨のみラベル付け（predicted端点の骨は欠損扱い）。
- fit: 説明済み画素の計測をobserved関節のみに修正。predicted骨
  （プライア直線四肢）がシルエット画素を「説明済み」に水増し
  し、全腕predictedでもfractionが0.80→0.81に改善したかのように
  報告していた → predicted骨/関節はカバレッジから除外。
- gait: predicted関節を含む脚の位相キューをunknownに修正。
  プライア直線脚が「stance/knee_angle ~170」として報告されて
  いた。observed関節のみで判定、predictedは欠損扱い（step_width
  も両足observedのみ）。
- stability/pose: `probe` の摂動が実効閾値に届くよう
  `threshold_offset` を追加 — adaptive(Otsu) モードでは
  `bg_threshold` を±10してもOtsu分割が不変で、3ラン同一マスクの
  「stable」判定を捏造していた欠陥を修正（robust プロファイルで
  感度が実測されるように）。
- reid: predicted由来の比率特徴を比較から除外し
  `predicted_features`/`excluded_predicted`で開示。プライア表で
  置かれた比率は同一BODY_MODELなら誰でも一致する定数のため、
  「別人が同じプライアでsame_person」という偽陽性を生んでいた
- handpos: ゾーン参照点（head/chest/pelvis/knee/hip）を観測関節
  限定に修正 — 観測 wrist が predicted ランドマークのプライア位置に
  対してゾーン判定され、推測が身体ゾーン境界を捏造していた欠陥
  を解消（全参照が predicted ならゾーン未判定、#331 gesture と同型）。

- norm: crop/resize/to_unit/from_unitが新フレームを宣言（関節座標と`image_width/height`の乖離でdocのframeが実座標空間を偽っていた欠陥を解消）
- consensus: バリアントパネルが呼出側のadaptive/reject_shadow/
  cleanを伝播（閾値・解像度の摂動だけを計るはずが、呼出側が
  robustプロファイルだと4バリアントだけ別プロファイルで走り、
  median投票が未開示のプロファイル差を混入させていた欠陥を
  解消、#333 recoverと同型）。

- recover: relaxed_threshold段が呼出側のadaptive/reject_shadow/
  cleanフラグを伝播（色ゲートだけ緩めるはずが、シャドウ棄却・
  形態クリーンも外れた別プロファイルで沈黙回復し、開示の
  "gate relaxed to N"より強い緩和が適用されていた欠陥を解消）。

- pipeline: warningsに`unknown_body_model`追加（無効なmodel名が黙ってadultプライアにフォールバックし推測関節の根拠が記録されない穴を開示）
- trust: predicted関節をoff_maskで「low」降格しない — プライアが
  シルエット外に関節を置くのは正常（evid.unsupportedと同じ
  OBSERVED限定ルール）。証拠を主張していない関節に証拠不在を
  咎めていた矛盾を解消。
- pose: 向きリトライ採用時、orientationにも回転量を開示
  （`estimated_on_rotated_deg`）し、180°ではfacing/head_shiftの
  左右を反転補正。回転フレームの向きを原画像座標の値として
  誤報していた欠陥（関節座標は逆回転済みだったが向きは未補正）
- knowledge/migrate: exportブロックに`keypoints_state`追加。
  フラット `keypoints_2d` は [x,y,conf] のみでpredicted関節が
  観測と区別不能だった → keypoint_orderと整合する
  observed/predicted/absent配列を同梱。migrateは旧docへ
  `keypoints_state_backfilled` として開示的に補完。

- selfcheck: 未知verdictのunmeasured降格を修正（語彙外判定をadvisoryへ — 未認識の証拠を「測定不能」と誤記していた静黙フォールバック）
- rig: predicted端点を持つ骨に state="predicted" を開示（推測構造を観測解剖学と区別不能にしていた欠陥）
- skeleton: Joint.stateのデフォルトをpredictedに（フェイルオープン修正—state未指定で観測を捏造する穴。観測主張は明示必須）
- audit: docの`warnings`ブロックを監査対象に追加。関節stateと
  矛盾する警告コード（例: 観測8件以上なのに
  `few_observed_joints`）を `stale_warning` として報告。
  陳腐な警告申告が消費者を誤誘導する経路を遮断。
  語彙外コードは外部語彙として据え置き（stale扱いしない）。

- pipeline: `frame.source`に元画像解像度を開示（downscale作業空間の関節座標が`image_sha256`の元画像にマップ不能だった穴を解消）
- pose: `body_model.prior`に実際に適用したプライア表を開示（測定選択名`name`と適用表が食い違う際に配置由来が不明だった穴を解消）
- viewer: doc.warningsを表示（unknown_body_model・no_observed_torso等の注意付きdocがクリーンdocと同じ見た目になっていた欠陥を解消）
- bvh: `report(skel)`開示サイドカー追加（BVH形式がjoint metadataを持てずpredicted骨が実測と区別不能で書き出されていた欠陥を解消）
- analysisブロックに `consistency` 追加 — 骨格健全性監査のissuesを
  全analyzeドキュメントに同梱（CLI/REST/Storeの全経路で可視）。

- migrate: state未記入関節の由来補記が既存basisと区切りなしで
  直結していたのを修正（"measured row 10migrated: state unknown"
  のように既存由来を破損、recoverと同じ "; " 区切りに統一）。

- knowledge: list()がファイル名と内部id不一致のdocを列挙しない（取得不可能な幽霊entryを報告していた穴 — id無しファイルも同様に除外）
- signature: スカラー部（体幹傾き・正規化子）も観測関節限定に —
  #232が骨方向ベクトルをobserved化した際、末尾4スカラーが
  `skel.point`でpredictedのhead/neck/pelvis/footを計測値として
  混入し続けていた残件（obs版の死行も併せて除去）。
- limbs: `of_body_h` の正規化子を観測関節のみの垂直スパンに修正 —
  predicted の頭/足がプライア位置で身体スパンを伸縮させ、「計測
  された」肢長比率が推測を分母にしていた欠陥を解消（全関節
  predicted では None を返す）。
- angles: predicted関節を含む角度を「計測値」として出力していた
  欠陥を修正。プライア配置の四肢は構造的に~180°に伸びるため
  elbow_flex等が捏造計測値になっていた（実測 175.8°）。
  全端点observedの角度のみ出力、predictedは欠損扱いで省略。

- ik: `solve_ik` が退化セグメント（L1/L2 が0以下）でドキュメント
  契約通り `None` を返すよう修正。これまでは骨長ゼロのチェーンに
  対して 1e-6px の捏造 mid/end を返していた — 「解くべきチェーンが
  存在しない」場合に幾何をでっち上げない（誠実性契約）。

- skeleton: `observed_body_span` 共通ヘルパ追加 — contact/reach の身体スパンが predicted 関節を混入し、近接閾値・リーチ半径が未観測の長い脚で捏造されていた欠陥を修正（ground/dynamics も同ヘルパに統一）
- contour: perimeterを弧長計測に修正（トレース画素数→直交1/対角√2のポリライン長、対角境界の~29%過小評価を解消）
- rest: オーバーレイPNGをdoc隣に永続化＋メモリは上限128件の読通キャッシュ（再起動でoverlay_urlが404化＋無制限肥大の修正）
- consistency: 監査をobserved関節のみに修正。predicted
  head/feet（プライア補完）がbody extentを捏造し
  `no_body_extent` を回避して虚構スケールで監査を通過
  させていた → 部位長/対称チェックは両端observedのみ、
  extentが全predictedなら `no_body_extent`。
- gesture: ルールの参照点（head/pelvis/hip/shoulder）を観測関節
  限定に修正 — 腕の証拠はobserved限定でも、predictedの頭や腰が
  ジェスチャー判定の基準線を捏造していた欠陥を解消（upright判定
  とhands_on_hipsの参照が推測で構成されなくなった）。
- horizon: predicted足/足首でground line・カメラロールを計測して
  いた欠陥を修正。「foot below ankle」複製は接地の証拠ではなく、
  その線はプライア配置を測るだけ — 観測接地関節ペアのみ使用、
  全てpredictedならstate=unknown（roll None）を返す。
- motion: predicted関節のフレーム間変位を出力しない欠陥を修正。
  推測関節の「移動」はプライアの動きであり人の動きではない —
  両フレームでobservedの関節のみ報告、predictedは欠損扱いで除外。

- `slice bias` — bias層のCLI接続。正解フィクスチャ群で推定器を走らせ、
  関節別の系統誤差（符号付き平均誤差ベクトル）と散布を分離して報告。
  worst関節がベンチゲート(10px)超なら exit 1。
- pose: neckを頭帯下端（顎）から肩行直下の鎖骨中点へ修正 — bias層が
  検出した系統誤差26pxを1pxへ解消（bench err 3.5→2.05px, OKS 0.92→0.975）。
- `slice probe <layer> <image>` — 未接続13層の汎用CLI接続。axis/plumb/limbs/rom/contact/dominance/handpos/framefit/ground/reach/horizon/mass/extjoints を `{layer, result}` JSONで直接呼出。`doc["analysis"]` に入らない層も単体検査可能に。
- cli: `slice analyze` のstderr要約にwarnings行を追加。
  `doc.warnings`（few_observed_joints 等の薄証拠コード）を持つ
  docがCLI上ではクリーンなdocと同一表示になっていた
  （viewer側と同型の沈黙表示）。警告がある場合のみ
  `warnings: <code>, ...` を出力。

- `slice mirror <image>` — mirror層のCLI接続。`est(flip(img))` vs `flip(est(img))` の関節別ドリフトで推定器の左右バイアスを監査。併せて flip_skeleton の座標系を `w-1-x` に修正（bitmap反転とのoff-by-oneで一様1pxドリフトしていた実バグ、centroid同様、閾値3px→2pxに引き締め）。

- bundle: unpackが破損zipメンバー（zlib/BadZipFile/非UTF8）をskip（1件の破損で全体が死ぬ経路を解消）
- norm: 変換がcentroidも写像（関節だけ動かしてcentroidを旧フレーム座標のまま残し`ratio.analyze`等へ陳腐座標を流していた欠陥を解消）
- norm: 変換でフレーム外に出た関節をpredictedに降格（語彙外state "out_of_frame"がvalidate()を通らずdoc保存不可だった契約違反を解消、由来はbasisに開示）
- knowledge: list()が索引構築後に上書きされたdocを再読込（mtime比較で陳腐entryを排除 — 一覧が存在しない内容を報告する穴を解消）
- basis: 先頭1語だけが一致するbasisをobservationと誤分類する穴を修正（完全な観測語彙prefixのみ許容 — 捏造由来の証拠なりすまし防止）
- knowledge: get()がファイル名と内部idの不整合をKeyErrorで拒否（k_A.jsonが別idを名乗る破損docを誤同一視していた穴を解消）
- framepos: bounds/headroomをobserved関節のみで計測。
  predicted関節（"foot below ankle"プライア等）が関節クラウド
  bboxを伸ばしfootroom/side_gap/body_fractionを捏造していた
  （実測 footroom 0.037→0.014）。predictedは欠損扱い。
- pose: 股より下の腕を「底行到達連結性」で脚と判別 — 従来のx重複
  足判定は広い足（しゃがみ/開脚/足開き）に隣接する腕を脚と誤認し
  腕を股で切断（手首が腰高に浮く計測誤差）。ランのx帯を下方向に
  追跡し底行に届くもののみ脚とする。`tests.crouch_person`で回帰
  ガード（wrist 197→239pxへ復帰）。

- pose: 向きリトライ（±90°/180°再推定）を estimate_multi にも適用。
  複数人画像内の横たわり・逆さま人物が、単一推定と違って
  直立スキャンだけで誤計測されていた経路を解消
  （_estimate_oriented 抽出で両経路が同一判定を使用）。
- cli: `slice batch` に `--robust` を追加。analyze/audit にだけ
  あった robust プロファイル（adaptive閾値・影除去・形態学
  クリーンアップ）をバルク経路でも有効化可能に — ノイズの多い
  実写真の一括解析が最もそれを必要とする経路だった。
  docの `engine.profile` に "robust" と記録される。
- track: アンカー/胴体長正規化をobserved関節のみに修正。
  predictedのpelvisがリンク距離・jump計測の根拠になっていた
  （推測位置での"linked"判定）。predicted pelvisはcentroidに
  フォールバック。

- mass: 身長スパンをobserved関節のみに修正。predicted足
  （"foot below ankle"プライア）がスパンを~3%伸ばしてcm_per_px
  を狂わせ、predicted頭でも推定値を返していた → 推測頭なら
  測定不能として None を返す。

- signature: predicted骨の方向ベクトルが指紋に混入していた欠陥を
  修正。推測肢が観測とほぼ同一の指紋を生成し（距離0.0039）、
  dedup/queryが「測定された一致」として誤認していた。predicted
  端点を欠損扱い（[0,0]）に変更、距離0.23へ復元。
  スカラー部（腕/脚/肩幅・トルソ傾き）も同様にobserved限定。

- spine: predictedトルソで「measured」脊柱カーブを報告していた
  欠陥を修正。chestはプライアでneck–pelvis弦上に置かれるため
  predictedだとカーブは構造的に「直線」に — 測定の捏造。
  neck/chest/pelvisが全てobservedの場合のみ計測、それ以外は
  unknownに保留。

- ground: 最低点・clearance・スパンをobserved関節のみに修正。
  "foot below ankle"プライアが観測足より下に置かれ、接地した
  人物にclearance 7.8pxの浮遊ギャップを捏造していた。

- dynamics: cues/spanをobserved関節のみに修正。docstringが
  "all on observed joints"と謳いながらpredicted関節を含めて
  いた — プライア位置でleg_off_axis/arm_out/com_outside_feet/
  wide_stepが発火し得た。predictedは欠損扱い。

- selfcheck: `consistency` 層を統合。ワンショット監査が骨格健全性
  監査（肢長プライア違反・左右非対称・フレーム外・逆転検出）を
  実行していなかった欠落を解消。issuesはadvisory重大度
  （実在する人体はプライア範囲を正当に外れうるためfailはしない）
  ＋`consistency:<issue>`理由コードを列挙。

- smooth: observed関節の平滑位置が近傍フレームのpredicted座標に
  引きずられる誠実性の欠陥を修正（実測: 手首が真値49px→69pxに
  20px偏移）。observed中心はobservedサンプルのみで平均し、
  predicted中心は従来どおり全サンプル平均（証拠は集める側）。

- axis: 主軸PCAをobserved関節のみに限定。predicted関節（捏造
  幾何）が「計測された」身体主軸をプライア方向へ引きずっていた
  誠実性の欠陥を修正。observed<3個ならNone（unmeasured）。

- calib: ビン境界の浮動小数点バグ修正 — `conf / 0.1` は 0.6 で
  5.999... となり lookup（`conf * 10`）とビンが不一致になるのを
  `conf * bins` に統一。`slice calib` は全ビン空（未測定）でも
  exit 0 になっていたのを exit 1 に修正（Devin Review #206）。

- reach: predicted腕でも `measured: True` を返していた欠陥を修正。
  プライア直線腕の長さを「測定済み」作業空間半径と偽装していた
  — observed関節のみ計測、predictedは欠損扱いでプライア
  フォールバック（`measured: False`）、predicted肩は None。

- pose: 向きリトライ（±90°/180°）— 横たわり・逆立ちの人物に対し
  直立スキャンがゴミ骨格をobservedとして出力し、逆立ちでは監査
  をすり抜ける完全な嘘骨格すら生成していた誠実性の穴を修正。
  全4向きを推定し「issues減 or 頭帯幅1.3倍超」の厳格条件でのみ
  回転を採用、座標を画像空間へ逆写像しbasisにrotated明記。
  実測: 逆立ちで頭/足首/手首が正位置に復帰、直立・幅広手・
  腕遮蔽は誤回転なし。`tests`反転ケースで回帰ガード。

- dominance: 双側膝屈曲（スクワット）の捏造利き脚を修正。
  unloaded_l+unloaded_r が同時発火して同票決 max() が "l" を
  返していた（実測 conf 0.37）。双側屈曲は相殺し
  both_legs_flexed（even）キューに変換 → even/conf 1.0。

- skeleton: `body_span()` 共通ヘルパ追加（頭→最下端、逆転/欠損
  時は胴体長、非計測時0）。contact/dynamics/ground/reach の
  身体スパン退化を一括修正：contact は逆転骨格で閾値1pxに潰れ
  接触を見逃し、dynamics は wide_step が常時発火、ground は
  uneven_support が常時発火、reach は半径0の偽ワークスペースを
  返していた。

- classify: 逆さま判定追加＋スパン計測の修正。逆立ち・頭下がりの
  骨格が「寝る」と誤分類されていた実欠陥を修正（下端を足関節
  のみで計っていたため逆転時にspan_y=0→水平判定に誤爆）。
  下端を全関節のmaxに変更し、全足が頭より上なら `invert`
  （逆さま）を返す。斜め寝そべりは従来どおり `lie` 優先。

- describe: ポーズ語彙の欠落修正。classifyが返す `crouch` が
  _POSE_ENに無く説明文が生キー（"Crouch;"）になっていた。
  `crouch`（crouching）＋将来の `invert`（upside down）を追加。

- signature: body_h正規化の欠陥修正。足関節が無い骨格では
  スカラー4要素が生px値で出力され、同じポーズ同士のsignature
  距離が16.2に化けていた（実測）。足欠損・逆転（body_h≤0）時は
  compare/dedupと同じ胴体長で正規化→距離0.24（骨欠損分のみ）。

- gesture: 逆転骨格で wave が両腕発火していた欠陥を修正。
  「頭上の手首」判定が画像座標のみで身体の向きを見ていなかった
  ため、逆さま骨格では全手首が頭上に → 検出捏造。
  wave は直立時（head 上方に pelvis）のみ発火させる。

- symmetry: predicted関節を含むペアを計測対象から除外。
  predictedは観測側のミラー複製で作られるため、含めると
  対称スコアが構造的に1.0に — 「計測された対称性」の捏造。
  ペアは両骨4端点が全てobservedの場合のみ比較し、それ以外は
  missingに報告（推測しない）。実測: 右腕predicted骨格で
  score 1.0/compared 7 → missing 3ペア報告に。

- framepos: headroomを頭関節y→関節群最上端に修正。腕上げ
  （手首が頭より上）で上端余白を過大評価し tight を portrait
  と誤判定していた（実測 headroom 0.089→0.005）。

- plumb: 逆転/退化骨格のスパン退化を修正。頭が最下端の骨格で
  body_h=1.0に潰れ生pxを「身長比」として出力し、forward_head
  閾値が負値で常時発火していた。胴体長フォールバック＋スケール
  不在時は posture=unknown に。

- limbs: チェーン中間関節欠損を partial として報告。肘が無い
  腕で肩→手首の弦長を「全計測」扱いしていた誠実性の欠陥を修正
  （欠損関節で弦化したチェーンは過小計測）。併せて body_h≤0
  の退化時は of_body_h=None に。

- bundle: packがvalidateのraiseで死なない（処理不能docをskip転換＋body_model非dict耐性）
- diff: 不正docの関節エントリで落ちない — 非dict関節/
  非数値座標/非dict入力をmalformedとして列挙し比較対象外に。

- `slice.storechk`＋`slice audit --store DIR` — KnowledgeStore側の監査経路。selfcheckが画像を監査するのに対し、保存済みドキュメント群を監査：audit lint（invalid/flagged/cleanの文書別集計）＋近重複検出（dedup）＋関節別観測率の全ストア集計（`blind_joints`=全ドキュメントで一度も観測されなかった関節）。索引未登録ファイルも`unreadable`として失格扱い（見えない不正は最も危険なため）。verdict=pass/warn/fail＋exit codeでCIゲート可。
- selfcheck: 関節系レイヤをエスティメータ解像度で比較（Devin Review #152修正）— >max_dim画像で骨格座標はダウンスケール済みなのにフル解像度マスクと比較していたため、全関節がoff_mask・fit=0になる誤警告を修正。`ground`も`small.height`へ。
- selfcheck: `human`レイヤを最大成分のみで採点 — フレーム内の無関係な物体がperson-like判定を歪めていた問題を修正（推定器と同じ成分を監査）。
- stability: probe変体が推定器の`adaptive`/`reject_shadow`/`clean`フラグを引き継ぐ — robust プロファイルのベースラインをdefault変体と比較し「プロファイル差」を「閾値感度」と誤読する問題を修正。

- bundle/dataset: 手置き不正docでconsumerが落ちない。
  unpack内corrupt/非dict memberが全体abortしていたのを
  個別スキップに、id無しdocのstore.get(None) TypeErrorを
  isinstance(kid,str)ガードで防止、非dict docのvalidate
  AttributeErrorもpack/unpack/from_store全てでガード。

- knowledge: `validate` がframe・normalizedブロックを検査する
  ように。frame幅高の正数性＋normalized不変条件（pelvis=原点・
  neck=1単位）— 陳腐/書換えブロックを拒否。

- knowledge: `validate` がexportブロックを検査するように。
  keypoints_2d長の検査＋`keypoints_state`（存在する場合）の
  skeleton.jointsとの整合検査 — フラット出口で推測関節が
  観測を装う矛盾docを拒否。

- `slice calib` — calib層のCLI接続。evaluate正解フィクスチャ群で
  推定器を走らせ、confidenceビン別の実測命中率（reliability
  diagram）を報告。overconfidentビンがあれば exit 1。

- `slice limbcov <image>` — limbcov層の単体CLI接続。各骨を~2px刻みサンプリし、6px超の背景横断をbroken検出（predicted端点は断罪しない）。gaps/insufficientは exit 1。

- `slice audit` CLI＋`slice.selfcheck` 新設 — 全監査層の
  ワンショット統合（imgqual→検出→evid/limbcov/fit/stability/
  contrad→gate を1デコードで実行、各層のverdict語彙を
  ok/advisory/problem/unmeasuredへ正規化して総合判定、
  unmeasurable層は評価を偽装しない）

- `docs/SMPL.md` 新設 — Slice関節→SMPL/SMPL-X対応表
  （17関節マッピング、未対応関節明示、座標系差異、
  lift→rig→gltf→bvhの既存パイプライン位置づけ、
  β/θ/メッシュ残作業、AUDIT P3-18対応）
- READMEモジュール一覧の全面更新 — 14行の古い表を全77モジュールの
  関心事別索引に拡張（コア/意味レイヤ/形状・前処理/時系列・照合/
  評価・QA/描画/3D・外部形式の7群、AUDIT P4-21対応）
- `docs/PHASES.md` 新設 — Phase完了基準の定量化（各条件を
  モジュール/テスト/コマンドで検証可能に、充足率ベースの
  完成度計算＋主要ギャップを第一原理順に列挙、AUDIT P4-24対応）
- CI導入 — `.github/workflows/test.yml`: push/PRごとに
  `python -m unittest discover -s tests` をPython 3.9/3.11/3.12
  で自動実行（stdlib専用・依存インストール不要、
  AUDIT P1-6対応）
- REST認証オプション — `serve(token=)` / `--token` / `SLICE_TOKEN`
  でAPIルートに `Authorization: Bearer` を要求（hmac比較、
  `/`と`/health`はviewer/プローブ用に開放、未設定時は従来の
  オープン動作、AUDIT P2-17対応）
- `examples/demo_3d.py` 新設 — Phase 3 パイプラインの
  エンドツーエンド実演（estimate→lift→rig→retarget→bvh/gltfを
  1コマンドで、各段がprovenanceを保持することを示す、
  AUDIT P3-20対応）
- `slice batch <dir>` CLI 追加 — ディレクトリ内画像を一括解析し
  KnowledgeStoreへ投入（png/bmp/jpg/webp、-r再帰、デコード不能は
  理由付きでskip＋exit1、ファイル毎にid+observed数を出力、
  AUDIT P2-16対応）
- `pipeline.analyze` に `analysis` ブロック追加 — Knowledge
  ドキュメントが angles/symmetry/balance/spine/gesture/dynamics/
  occlusion/frame の8解析レイヤを同梱（これまでstyleのみ統合、
  空入力でも全レイヤ安全にdegrade、AUDIT P1-9対応）
- `slice.extjoints` 新設 — v2拡張関節語彙（v1の17関節を不変のまま、
  mid_hip/waist/mid_thigh等の補間関節＋fingertip/toe/heelを
  predictedとして導出、nose/eye/earは証拠なし=reservedで
  発行しない、basisは共有語彙の接頭辞規約に準拠、
  AUDIT P2-15対応）
- `analyze(robust=True)` / REST `?robust=1` / CLI `--robust` —
  頑健性プロファイルのパイプライン接続（adaptive閾値＋落ち影除去
  ＋形態学クリーンアップを1フラグで有効化、実写向けopt-in、
  `engine.profile` で使用プロファイルを記録）
- `slice.diag` 新設 — 空Skeletonの理由診断（no_foreground/
  too_small/too_short/foreground_at_edge/low_contrast の
  理由コード＋coverage計測、AUDIT P0-5対応）
- `slice.modelchk` 新設 — 選択モデルの整合性監査（頭身比だけで
  選ばれたBODY_MODELを、肩/腰/胴/腕/脚の実測比率5次元で再検証、
  2+次元乖離または総誤差超過でmismatch、better_modelは助言のみ）
- `slice.limbcov` 新設 — 骨レベルのシルエット被覆監査（各骨を
  ~2px刻みでサンプリし6px超の背景横断をbroken検出、predicted
  端点の骨は計測のみで断罪しない、evidの点検査を線分へ拡張）
- `slice.framefit` 新設 — 部分人体/フレーム切り取りの推定
  （骨格端点のフレーム辺距離、上下左右の辺別 possibly_truncated、
  extremity判定で誤検出抑制、state:"estimated"、AUDIT P0-2対応）
- `slice.bias` 新設 — 関節別系統誤差プロファイル（正解ペア群から
  関節ごとの平均誤差ベクトル＋除去後の残差を計測、systematic=
  補正可能/unbiased=散布/insufficient=サンプル不足、correction()
  は非systematicに0を返して散布へのオフセット適用を防止）
- `KnowledgeStore.list()` に `_index.json` キャッシュ索引追加
  （save時に追記、不在/破損/陳腐時は全走査で自動再構築、
  索引自身はdocとして列挙しない、AUDIT P1-10対応）
- `render` の状態表現を色+形状の二重符号化に — predicted骨を
  破線・predicted関節を中抜きリングに（色覚特性/グレースケール
  でもobserved/predictedを区別可能、AUDIT P4-23対応）
- `slice.trust` 新設 — 関節信頼度の合成グレード（calib精度/stability感度/
  evid証拠位置の既計算結果を任意サブセットで統合→high/medium/low＋
  downgrade要因をfactorsに開示。入力なし時はheuristicと明示）
- `slice.priorchk` 新設 — 解剖学プライア自体の監査（keyset/bounds/
  limb_order[thigh≥shin, upper_arm≥forearm]/stack合計/head_order
  [deformed>child>adult]の5チェック、発火時はモデル・コード・生値を開示）
- `slice.track` 新設 — フレーム列の骨格に安定track_idを付与
  （pelvis/centroid距離の貪欲対応、トルソ正規化の最大ジャンプ閾値、
  空フレーム・再獲得・ギャップ数を正直に記録、単一人物前提を
  assumptionに明記、AUDIT P3-19対応）
- `slice.knowledge/v1.1` 導入 — `analysis` 拡張スロット
  （レイヤ名→自由形式dict、v1との相互後方互換、v1での
  analysis付け足しはvalidate拒否、build(analysis=...)で
  自動v1.1化、AUDIT P1-7/8対応）
- `slice.migrate` 新設 — 旧Knowledgeドキュメントのスキーマ正規化
  （export/prediction/coverage/bonesを関節から再構築、欠損stateは
  predicted+記録、座標なし関節はdropped、created_at捏造せず空のまま、
  全変更をchangesに列挙＋valid_before/afterで検証可能）
- pose: 骨盤幅を胴カラムランで計測（外縁=腕を含みpriorと66%乖離
  していた問題を解消）＋膝を足ランのアンカーで選択（膝行の
  最端ラン=腕を拾う誤りを修正）＋rom: 1px未満セグメントは
  角度測定しない（方向を定義できない値でoverextendedを出すのは
  発見の捏造）
- pose: 股検出を隣接ラン間ギャップに修正（首尾ラン比較が
  「腕|胴|腕」を胸部で誤検出→ hip -32px の系統誤差を解消）
  ＋肘をプライア長ではなく計測した肩→手首距離の上腕比に配置
  （elbow -30px→+2px）。bench: err 15.55→4.49px, OKS 0.53→0.90


- `estimate_multi` 追加 — top-K前景成分を独立に推定して複数
  Skeletonを返す複数人検出経路（連結成分のラベル化を共有化、
  接触した人物は1成分=1骨格のまま推測しないことをdocstringに
  明記、AUDIT P0-1本体対応）
- `slice.basis` 新設 — 関節provenance文字列の語彙レジストリ
  （既存basisを観測/ミラー/補間/プライア/変換/不明の6カテゴリに
  分類、新規は接頭辞規約、audit()で骨格の証拠内訳を集計、
  既存文字列は改名せず保存ドキュメントを保護、AUDIT P4-22対応）
- `slice.morph` 新設＋`clean` オプション — 前景マスクの
  形態学的クリーンアップ（open=斑点除去/close=ピンホール充填、
  4連結で成分ラベリングと整合。圧縮ノイズ・AA端由来の偽前景を除去）


- `slice.shadow` 新設＋`reject_shadow` オプション — 背景を
  一様減色した落ち影画素を前景から除去（色だけでは暗色服と
  区別できないため扁平形状ゲート併用、<0.35倍の極暗色は
  影と断定せず残す誠実設計、除去数をlast_shadow_removedで開示）

- `slice.adapt` 新設＋`HeuristicPoseEstimator(adaptive=True)`
  — Otsuクラス間分散で前景閾値を画像ごとに自動決定
  （二峰性なしなら固定閾値へフォールバック、methodを
  last_thresholdで開示）。`Bitmap.set` の非4要素代入を
  ValueError化（バッファ静黙破壊の防止）

- `slice.recover` 新設 — 段階的フォールバック推定（primary→非最大成分
  リトライ→半分閾値の順に再試行、回復runと全失敗はstate/methodに開示、
  回復関節はbasisに `"recovered: <method>"` 記録）


- `render.overlay_multi` 新設 — 複数人オーバーレイ（人物は色相で
  区別、observed/predicted契約は輝度で維持。`overlay`の描画部を
  `_draw(out,skel,tint)`に抽出して再利用、単一経路の色は不変）


- `slice.split` + `estimate_split` 新設 — 融合シルエットの
  距離変換watershed分割（頭バンド複数コアを証拠に発動、分割由来
  の関節はbasisに "split region" 記録。AUDIT P0-1の接触ケース）

- 複数人API接続 — REST `POST /analyze?multi=1`（`{people,count}`
  + save時は各docにoverlay_url）とCLI `slice analyze --multi`
  （JSON配列出力）。`analyze` 単一経路は不変

- `pipeline.analyze_multi` 追加 — 1画像から複数人のKnowledge
  ドキュメント配列を生成（各docに `people:{index,count,state,
  basis}` ブロック、接触シルエットは1成分のまま推測しない）

- `slice.calib` 新設 — confidenceのキャリブレーション（正解フィクスチャ上で
  confidence→実命中率のreliabilityテーブル、overconfident/underconfident
  ビン集計、`apply`はraw scoreを残して較正値をサイド記録）


- `slice.human` 新設 — 前景形状の人物らしさ検定（aspect/fill/head_mass/
  symmetryの4信号→score＋weakest_signal、いずれかが床未満なら否。
  「成分=人」の暗黙前提を検証する層。判定はadvisory＝推測しない）


- `slice.imgqual` 新設 — 入力画像の証拠適格性評価（size/dynamic/blur/contrast
  の4計測フラグ→adequate/marginal/inadequate。推定前段の前提条件層、
  各フラグは計測値を保持し「どれだけ不足か」を開示）


- `slice.contrad` 新設 — レイヤ間矛盾検出（classify×axis×ground×balanceの
  規則セット: 寝姿勢だが主軸垂直、立位だが浮遊、安定だが接地なし等、
  発火時は両側の生値をevidenceに保持。欠損レイヤはスキップ）


- `slice.fit` 新設 — 骨格↔シルエット整合度（前景画素の骨/関節への距離で
  explained fraction＋mean/worst距離＋未説明領域centroidを計測、
  空マスク/空骨格はunmeasurable。推定が証拠を説明しているかの自己監査）


- `slice.consensus` 新設 — 複数パラメータ実行の合意骨格（閾値±25%/解像度±25%
  の5変体で推定→関節位置は中央値投票、confidenceは観測率で割引、
  合意未達関節はdisputedに列挙。stabilityの感度計測に対し頑健な骨格を
  実際に生成する側）


- `slice.gate` 新設 — 品質判定の統一ゲート（detection+consistency+document
  auditを1回に集約、verdict=pass/warn/fail＋layer別生結果、`keep()`で
  保存可否判定。理由コードは各レイヤの語彙をそのまま通過）


- `slice.evid` 新設 — 関節ごとの証拠ローカライゼーション（chamfer距離変換で
  各関節を interior/on_boundary/off_mask に分類、マスク外のobserved関節は
  unsupported()で列挙。`fit`の全体整合に対し関節粒度の監査）


- `slice.repro` 新設 — 再現性検証（記録済み骨格を入力画像から再推定し
  position_drift/state_flip/missing/addedを関節別に列挙→
  reproducible/drifted/changed。フレーム解像度差はリスケールで吸収）


- `slice.stability` 新設 — 摂動下の関節安定度（bg_threshold±10で再推定し
  関節ごとの最大変位を計測→stable/sensitive/unstable、1runのみ観測は
  single_runで不明扱い。calibの精度計測と対になる感度計測）


- `estimate_multi` 追加 — top-K前景成分を独立に推定して複数
  Skeletonを返す複数人検出経路（連結成分のラベル化を共有化、
  接触した人物は1成分=1骨格のまま推測しないことをdocstringに
  明記、AUDIT P0-1本体対応）
- `slice.bench` 新設 — 推定ベンチマーク＋回帰ゲート
  （`python -m slice.bench`: 推定時間/detection/observed/
  mean_error/OKSを評価、精度閾値は現状実測値に固定＝
  回帰検出器、timingは情報のみ、AUDIT P2-13対応）
- `slice.people` 新設 — 前景連結成分の人物候補列挙（top-K
  成分のbbox/面積/辺接触、単一成分前提の最初の一歩、
  成分≠人物をnoteに明記、AUDIT P0-1対応）
- `docs/AUDIT.md` 新設 — 長所50/短所50/改善点の製品監査
  （第一原理＋ソクラテス問答によるP0–P4優先度付け）
- `mask.cutout` 修正 — 透過黒初期化が暗色被写体を再推定で
  消失させるバグ（#101レビュー指摘）: 元RGBを保持し
  背景アルファのみゼロ化
- `tests/realistic.py` + `test_realistic.py` 新設 — 準実写
  フィクスチャ（グラデ壁・センサーノイズ・遮蔽物・落ち影、
  背景画素のみ再描画で前景形状は共通）。強いグラデは
  observed低下する既知の劣化も数値で固定。AUDIT P0-4対応
- `pose._mask` の背景推定を辺バンド別ローカル推定に改良
  （`_background_bands`: y軸6バンドの境界モード色 — グラデ壁で
  depth=140でも全身19関節を維持、旧単一モードはdepth=60で
  observed 15に劣化、AUDIT P0-3対応）
- `pose._background` 修正 — 透過画素のRGBを背景色として読んで
  いたバグ（cutout等の透過入力で背景推定が狂い暗色被写体を
  消失）。不透明サンプル優先・全て透過なら従来動作に
  フォールバック（AUDIT短所#18/P0-3対応）
- `knowledge.KnowledgeStore.save` を原子的書き込みに
  （tmp+os.replace — クラッシュ時の半端なJSON残存を防止、
  AUDIT P1-11対応）
- `slice.svg` 新設 — 骨格をSVGベクタードキュメントとして
  レンダリング（render.pyのPNGと対）。observed=青実線・
  predicted=橙破線（stroke-dasharray）、全関節に
  state/confidence/basis の `<title>` ツールチップ
- `slice.ascii` 新設 — 骨格のターミナル文字描画（観測=`@`/#、
  予測=`o`/: の誠実性グリフ、行数はフレーム縦横比×文字セル補正）。
  CLI/ログでの第3描画バックエンド
- `slice.mask` 新設 — 推定器の前景マスクを公開（foreground/
  coverage/to_bitmap可視化/cutout背景透過）。downscale座標系の
  注意書き付き
- `slice.sheet` 新設 — 複数骨格レンダを1枚のグリッド画像に並べる
  コンタクトシート（アスペクト比保持レターボックス、歪めず
  データセット丸ごと目視QA）
- `slice.diff` 新設 — Knowledgeドキュメント差分監査（関節の
  追加/消失/移動px・state反転（observed→predicted降格を明示）・
  信頼度ドリフト・モデル/ポーズ変更をフィールド単位列挙）
- `slice.autocrop` 新設 — 前景bboxの人物クロップ提案
  （マージン/アスペクト比指定、フレーム超過は正直にclamp、
  空フレームは state:"unknown" で推測しない）。前処理ユーティリティ
- `slice.horizon` 新設 — 両足接地線から地面傾斜=カメラロール角を
  推定＋足の奥行きヒント（低い足=近い）＋カメラ高さ仮定での
  horizon_y。仮定は `assumption` に全開示、足が揃わなければ
  state:"unknown" で推測しないシーン幾何層
- `slice.audit` 新設 — Knowledgeドキュメントの誠実性リント
  （validateの先：観測率閾値・basis有無・confidence疑義・
  prediction帳簿の陳腐化・低証拠上の意味ラベルを警告コード化）
- `slice.dedup` 新設 — データセット重複検出（pelvis基準・
  トルソ正規化の平均関節距離がeps未満のペアを列挙、
  解像度/平行移動不変）
- `slice.bundle` 新設 — Knowledge Store の単一zip梱包/展開
  （manifest.json付き配布フォーマット、スキーマ検証ゲート
  をexport側にも適用、id無しエントリはskipped計上）
- `slice.pad` 新設 — Bitmapレターボックス（中央配置＋オフセット
  返却で座標系を保全、縮小は拒否してcropへ誘導、
  to_aspect/to_square）
- `slice.crop` 新設 — Bitmap矩形切り出し（autocropのcrop提案を
  適用する実行側、枠外はclamp・重なり無しはValueError）
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
- `slice.evaluate` 新設 — 正解座標を記録しながら図を描く
  `draw_case()` と、検出率・observed率・平均位置誤差(px)を報告する
  `evaluate()`。推定精度を「言い張る」のでなく測るための評価系
- `slice.mirror` 新設 — `flip_bitmap` / `flip_skeleton`（x反転＋
  _l/_r交換、facingも反転）。推定器の左右整合性
  `estimate(flip) ≈ flip(estimate)` を検証・拡張に使う
- `slice.distfield` 新設 — チャンファ(3-4)距離変換でシルエット内の
  各画素の「背景までの距離」を算出し、局所的な肢体の太さを計測
  （関節点の距離×2≈その部位の幅。胴=太・腕=細の定量化）。
  肢幅プライアや筋肉/肌量推定の土台
- `slice.motion` 新設 — フレーム間モーション解析。`vectors()` で
  関節ごとの移動ベクトル、`summarize()` で平均速度・並進量・
  最速関節・部位別最大移動を集計。連続画像の歩行・ジェスチャ・
  アニメーションリターゲット検証の土台
- `slice.heatmap` 新設 — 関節をガウシアン分布としてグレースケール
  描画する OpenPose系 confidence map 出力。輝度=confidence で
  observedは明るく・predictedは gain 0.3 で薄く — 「どこに自信を
  持っているか」を同じ表現形式で示す（Hourglass/PAF/BlazePose
  系の標準中間表現に準拠）
- `slice.stats` 新設 — 複数解析結果の集約統計。`joint_stats` で
  関節ごとの観測率/補完率/平均信頼度、`weakest_joints` で推定器の
  死角を同定、`summary` でケース数＋平均観測率＋弱点リストの
  メタ知識化。入力ドメインと推定器の相性を数値で見る層
- `slice.signature` 新設 — ポーズ指紋。骨方向ベクトル（17骨×2、
  固定順）＋胴傾き/腕幅/脚幅/肩幅の正規化スカラーで38次元の
  固定長特徴量。`distance()` のRMS差でポーズ類似検索・近似重複
  検出 — 関節マッチング不要の高速比較（解像度・構図に非依存）
- `slice.framepos` 新設 — 構図解析。関節クラウドbboxで
  headroom/footroom/side_gap/center_offset/body_fraction/三分割
  ゾーンをフレーム比で計測、framing=tight|portrait|wide
- `slice.describe` 新設 — 骨格＋姿勢/向きラベルを人間可読な
  説明文に変換する NLG 層（"standing; facing the camera; left arm
  not directly observed; 19 of 19 joints observed"）。observed と
  predicted を文面で厳密に区別し、データが言っていないことは言わない
- `slice.symmetry` 新設 — 左右対称性スコア。左骨方向を垂直軸で
  ミラーして右骨と内積（0–1、欠側ペアはmissing報告）。T字/直立
  の高対称 vs 片腕上げの非対称を定量化、`asymmetric_side` で
  最も逸脱するペアを同定
- `slice.axis` 新設 — 身体主軸。関節クラウドの2x2 PCA（閉形式、
  numpy不要）で主軸角度＋異方性＋散布＋重心（直立=90°近辺・
  横臥=0°・`tilt`=縦からの傾き連続量）
- `slice.plumb` 新設 — 鉛直線姿勢整列。head/neck/chest/pelvis/足首
  の横偏移を身長比で計測（頭部前方位=forward_head検出、
  stack_score=胴チェーン平均偏移で姿勢品質を連続量化）
- `slice.retarget` 新設 — ポーズ・リターゲット。src骨格の骨方向
  ×dst骨格の骨長でpelvisから運動学ツリーを下りて座標再構成 —
  同じポーズを別体格へ転写。出力は全て state=predicted
  basis=retargeted（合成幾何は観測証拠ではない）
- `slice.lift` 新設 — 2D骨格の擬似3Dリフト。向き推定の奥行き
  手がかりからz座標を割当（front/unknown=全z0「奥行き証拠なし
  =平坦を正直に」、side=遠側肢に+z肩幅半分）。全zにbasis
  （no_depth_cue/facing_side）を明記 — zは計測ではなくプライア
- `slice.mass` 新設 — 体重推定。シルエット面積×身長プライア換算
  ×奥行係数0.28×軟組織密度1.04 → kg（仮定チェーン全開示: depth_cm/
  height_cm/volume_l、全出力estimated明記）＋BMI
- `slice.limbs` 新設 — 四肢長プロファイル。腕（肩→手首）/脚
  （股関→足）のチェーン合計をpx＋身長比＋partial（一部predicted
  含む）＋左右差deltaで計測 — 人体測定レポート層
- `slice.mutate` 新設 — ノイズ・遮蔽・クロップの画像変換。
  証拠が部分的な時に関節が predicted/欠損に落ち（observed を
  捏造しない）誠実性をロバストネステストで検証するための道具
- `slice.angles` 新設 — 関節角度の解剖学的計測（度数）。
  屈曲角=中間関節の内角（180°=完全伸展）、挙上角=胴体垂直からの
  方向角（0°=下垂/90°=水平/180°=頭上）＋torso_lean。欠損関節は
  推測せず項目ごと省略
- `slice.oks` 新設 — OKS（Object Keypoint Similarity）評価指標。
  関節ごと exp(-d²/2(sk)²)：s=参照骨格bbox面積の平方根（スケール
  正規化）、k=関節別許容度（股関節は厳格・手首は寛容）。
  参照に存在しない関節は評価対象外、推定側欠損は0点。
  COCO公式評価メトリクス実装
- Landmarks: 運動学ツリー追加 — pelvisルートの `PARENT` マップと
  `chain()` ヘルパ（SMPL系と同じルート規約。補完・正規化・将来の
  3D化で共有する関節語彙）
- `slice.scale` 新設 — 頭長の人体計測プライア（成人~23cm等）から
  px→cm換算率を推定し、身長/胴/四肢/肩幅を実寸（cm）で報告。
  `state:"estimated"` 明記 — 世界の実測ではなくプライア由来の
  推定スケールであることを誠実に表明
- `slice.handpos` 新設 — 手の位置意味づけ。手首を身体スキーマ
  相対でゾーニング（above_head/at_head/at_chest/at_waist/at_hip/
  at_knee/hanging）、胴体スパン比で身長非依存、predicted手首は
  ゾーニングしない
- `slice.dynamics` 新設 — 運動含意スコア。単フレームから「動きの
  最中っぽさ」をキュー加重投票（脚軸外れ・腕外振り・重心が足外・
  広い歩幅）→ static/possibly_dynamic/dynamic。state:"implied"
  で「動いている」とは言わない誠実設計
- `slice.coco` 新設 — COCOキーポイント形式エクスポート。
  17関節[x,y,v]で v=2観測/1不可視/0欠損のCOCO可視性規約が
  observed/predicted/missingに対応（誠実性契約がそのままCOCOの
  意味論に乗る）。Slice固有関節は unmapped_joints に列挙。
  学習データセット標準との互換レイヤー
- `slice.reach` 新設 — 機能的リーチ包絡。肩中心に上腕+前腕(+8%手)
  の作業空間で任意点の届き判定（inside<85%/edge/outside、欠腕骨は
  身長プライアでestimated明記）。`workspace()` で両腕包絡
- `slice.paf` 新設 — Part Affinity Field。各骨に「親→子の方向
  ベクトル場」を帯域上に生成（OpenPoseの連結チャネル）。検出点
  だけでなく「どの関節同士が繋がるか」を場として表現。predicted
  骨は strength 減衰 — 連結の確からしさも誠実に表現
- `slice.smooth` 新設 — 関節軌跡の時系列スムージング（対称移動
  平均）。フレームごとの推定ジッタを抑えつつ位置のみ平滑化し
  state/confidenceは中央フレームを保持。欠損フレームは欠損の
  まま — 平滑化が存在しない位置を捏造しない設計。`jitter()` で
  フレーム間変位の定量計測
- `slice.spine` 新設 — 脊柱カーブ。neck-chest-pelvisで横偏移
  （側弯様）＋前傾角（前弯様）＋curvature（鎖長/弦長）を計測、
  classify=straight|lateral / upright|leaning
- `slice.dominance` 新設 — 荷重優位側推定。骨盤の足首中点偏移
  （>15%半脚間=側方荷重）＋膝屈曲による脱荷脚の逆側投票で
  dominant l|r|even|unknown＋confidence＋全cues開示
- `slice.rig` 新設 — 骨格をアニメーション用リグとして出力
  （name/parent/head/tail/length/dir/confidence の17ボーン、
  pelvisルート）。リターゲット・BVH/GLTF変換・3D化で使う骨構造。
  欠損関節の骨はゼロ化せず省略 — リグは知っている分だけを正直に表す
- `slice.contact` 新設 — 自己接触検出。observed関節ペアの近接を
  身長比で判定（hands_together/hand_at_head/arms_crossed/
  feet_together）。predicted関節は絶対に接触と報告しない —
  推測同士の近接は証拠にならない
- `slice.rom` 新設 — 可動域監査。肘10–180°/膝15–180°/足首30–175°
  /肩20–175°の解剖学的限界を超えた角度をoverextended（observed）
  またはimplausible（predicted混入）として報告、境界±8°は
  hypermobile。violations()で違反のみ抽出
- `slice.bvh` 新設 — 骨格をBVH（Biovision Hierarchy）テキスト出力。
  pelvisルート・OFFSETは親相対・CHANNELSはroot6+各関節3、
  1フレームモーション（回転は未観測ゆえ全0 — 誠実なゼロ埋め）。
  Blender/MotionBuilder等のリターゲットツールが読む標準形式
- `slice.ik` 新設 — 2ボーン逆運動学ソルバ（肩→手首目標から肘位置
  を円の交点で解析的に求解。bendで屈曲側選択、届かない目標は
  最大伸展にclampして「解剖学的に届く所」を正直に返す）。
  ポーズ編集・制約付き補完の基礎
- `slice.occlusion` 新設 — 欠損理由推定。unobserved関節を理由別に
  分類（シルエット内=occluded、フレーム外=truncated、未予測=
  absent、マスク外=unobserved）。「欠損」を単一語でなく証拠の
  性質で区別する監査層
- `slice.segment` 新設 — 前景ピクセルを最寄りの骨セグメントで
  部位ラベル付け（head/torso/upper_arm/forearm/thigh/shin/foot L/R）。
  DensePose系のdense part labelingの軽量版。`summary()` で部位ごとの
  証拠ピクセル量・割合を集計。骨が欠損した部位はピクセル0 —
  証拠のみをラベルし予測で増やさない設計
- `slice.contour` 新設 — 前景マスクの外周トレース（Moore近傍追跡）
  と形状記述子（面積・周長・bboxアスペクト・コンパクト性・重心）。
  部位をまたがない「形そのもの」の特徴量で、姿勢変動に頑健な
  シルエット記述（古典的形状記述子系に準拠）
- `slice.consistency` 新設 — `audit(skel)` が骨格の健全性違反を
  列挙（画像外座標・プライア範囲を大きく外れた四肢長・左右非対称・
  反転/平坦な身体）。「ありえない骨格」を機械検出する監査層
- `slice.sample` 新設 — 関節周辺ウィンドウの色統計（mean RGB・
  肌色率・輝度）で「素肌/被覆/画素なし」を部位別に判定。
  素肌の腕と衣類の腕では知識の意味が違う — 性別的・解剖学的
  知識の原料となる局所色解析。画素のない関節は推測せず no_pixels
- `slice.gait` 新設 — 歩行位相キュー。脚ごとに stance/swing/unknown
  （膝屈曲角150°+股関直下=支持脚、膝屈曲or軸外=遊脚）＋step_width
  ＋double_support。静止画で「歩行中に見える」位相推測、欠損脚は
  unknown
- `slice.balance` 新設 — 静的バランス評価。Winter人体計測質量プライア
  で重心を推定し足の支持多角形に投影（inside/marginal/outside、
  証拠不足はunknown推測せず）。バイオメカニクス的「立っていられるか」
- `slice.compare` 新設 — 2つの Knowledge ドキュメント間のポーズ距離
  （pelvis原点・胴長=1の正規化空間で共通関節の平均距離）。
  解像度・構図に非依存で、比較に使った関節数も報告
- `slice.ground` 新設 — 地面ライン推定。最下observed支持関節
  （foot→ankle）でground_yを決め、接地/浮遊/端切れを判定
  （support_is_lowest=grounded、フレーム端=cropped — 推測で
  接地と言わない、他関節が足下=airborne）＋clearance
- `slice.gesture` 新設 — 規則ベースジェスチャ検出（wave=手首が
  頭の上0.3腕長、hands_on_hips=手首が腰+肘外張り、point=腕水平
  ~完全伸展）。証拠はobserved関節のみ — predicted肢からは
  ジェスチャを主張しない
- Anatomy Engine: `select_model` の confidence に第2候補との
  マージンを反映 — 測定値が2モデルの境界近くにあるとき自信を下げ、
  誠実な曖昧さを表明（境界では ~0.5 に減衰）
- Knowledge JSON: `coverage` フィールド追加 — 関節総数・observed/predicted/
  unfilled件数・観測率・observed平均信頼度。「画像証拠にどれだけ基づくか」
  をドキュメントが数値で表明
- CLI: `--model` 未指定時に adult を強制していたバグを修正 — 省略時は
  推定器が選んだ body model で補完。`analyze` の stderr に
  pose/style/model の要約行を追加
- Skeleton: `normalized` エクスポート追加 — pelvis原点・neck–pelvis
  距離=1の正規化座標を skeleton ブロックに出力。解像度・構図に
  非依存で画像間のポーズ比較が可能に（pelvis/neck欠損時は省略）
- Ratio Engine: `arm_span`（指先-指先/身長、ウィトルウィウス的比例）と
  `leg_to_torso`（脚長/胴長）を追加 — 姿勢と身体プロポーションの
  両シグナルとして Knowledge JSON に出力
- Pipeline: `warnings` フィールド追加 — 観測関節<8個・手首未観測・
  足部未観測の警告コードを Knowledge JSON に記録
- Viewer: 関節行に `basis`（配置根拠）をツールチップ表示、Ratiosに
  arm_l/arm_r/arm_span/leg_to_torso を追加
- Overlay: facing が left/right のとき頭上に向き矢印を描画（緑、
  状態色と区別）
- Pose Classification: `bend`（前傾/お辞儀）ラベル追加 — 脚は直立なのに
  胴体軸の水平傾きが胴長の45%超。`torso_tilt` 信号を追加
- Style Detection: 肌色シグナル `skin_ratio` を追加 — クラシックな
  肌色域（R>G>B・暖色）のピクセル率をsignalsに記録し、
  ポートレート系写真を `real` に拾う第2の写実手がかりとして利用
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
