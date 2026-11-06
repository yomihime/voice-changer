# VCClient A / B / C 実装状況

更新日：2026-11-06。Tauri 接続、既存 VCC 制御、音声と復旧を対象とした試用候補です。C は有声音の受入を一部残しています。D 以降の Host 分離・新 Official・C++・NPU は本変更に含めません。

| 段階 | 状態 | 実装と確認範囲 |
| --- | --- | --- |
| A 接続 | 接続部分を検証済み | BackendClient、localhost:18888 の有限探索、手動 URL、内部ポート回退、原生 profile、旧 IndexedDB 移行。実 Windows EXE で無 backend、再試行、手動 base path、再起動、旧 origin 占有時の移行を確認 |
| B VCC 制御 | 制御部分を検証済み | 集中 LegacyVccAdapter、設定の回読、能力別 UI、安全な空 slot 登録。実 VCC と EXE で登録失敗後の復旧と競合拒否を確認 |
| C 音声と復旧 | 実装済み、一部受入待ち | 両 Device モードの経路と終了、Client Device の停止・再開・出力復旧・backend 再起動、約30分のほぼ無音負荷、自動生成 WAV を確認。真人の聴感等は未検証 |

## 対応するソースと構築

公開変更の基準は Server `64c5eeec168a1cc56b18d9b90d49fd9db3475e0f`、Client `661a10a3ce4618ba205f1c0180119e0eca1964c1` です。対応する Client は親 commit の `client/frontend` gitlink に固定します。Client の変更を先にマージし、その commit を取得可能な状態で親変更をマージしてください。

Client 内で次を実行します。Node.js 24.20+（24.x）、Windows 向け Rust/MSVC、WebView2 が必要です。詳細は [TAURI.md](../../client/frontend/TAURI.md) を参照してください。

```powershell
npm ci
npm run build
npm test
npm run test:browser
cargo test --manifest-path src-tauri/Cargo.toml --locked --offline
npm run desktop:build
```

EXE は `client/frontend/src-tauri/target/release/voice-changer-client.exe`、NSIS は同じ release 配下の `bundle/nsis/` に生成します。EXE は毎回 localhost:18888 を確認し、失敗時に接続先を入力できます。入力・出力・監視端は各 PC のデバイス名を確認して選択します。Client Device はクライアント PC、Server Device は backend PC のデバイスです。

## インターフェースと安全性

- `/info` の実フィールドで旧 VCC と 2.x を識別します。旧 VCC の制御を集中変換し、未対応操作は理由付きで無効化します。
- 旧設定は `/update_settings` の FormData を使い、GET 回読と値一致を要求します。複数変更は事前検証後に直列処理します。旧 API に設定トランザクションはありません。
- `/load_model_if_empty` は共有 lock と原子的ディレクトリ予約で既存 slot を保護します。競合時は409、失敗時の部分ファイルは保持します。この能力がない旧 Server では新規登録を無効化します。従来の `/load_model` は既存の上書き仕様を維持します。
- `/test` は JSON / base64 の mono little-endian Int16 PCM です。Float32 変換は Client 境界で一度だけ行い、既存 Server が履歴・resampling・SOLA を担当します。通常 Legacy は同率・同サンプル数、Official の可変出力は別に扱います。
- `/reset_audio` と epoch/sequence で旧フレームと重複を拒否します。有限 warmup、1 inflight + 1 pending、有界入出力キュー、設定変更時の旧ストリーム停止を実装しています。Server Device が所有する音声は Client からリセット・追加送信できません。
- Client Device は Client 終了時に音声を解放し、backend は継続します。Server Device は制御ウィンドウ終了後も継続し、明示停止またはデバイス・backend 故障で停止します。

## 検証済みの範囲

- 同一の機能ソースで Node 96項、Rust 33項、Server 77項、Windows release EXE/NSIS 構築が通過しました。実 WebView2 で接続・設定移行・制御・アップロード失敗復旧を確認しています。
- 実デバイスで両モードの入力・出力・監視経路、終了時の挙動、Client の `none` からの復旧、停止・再開、同一 checkpoint の slot 切替と backend 再起動後の復帰を確認しました。
- 最終音声候補のほぼ無音負荷は1,800.86秒、48 kHz / 6,144 sample、14,084ブロック送受信でした。入出力破棄・音声エラー・backend 推論失敗はいずれもゼロ。出力キュー最大12,288 / 48,000 sample、HTTP 同時処理最大1件です。`/info` の proxy 接続失敗を1件記録しています。
- Client プロセスツリーの working set は553→903 MiB、約5分以降は主に860〜905 MiBで変動しました。これは長期メモリ上限の証明ではありません。採取した HTTP RTT は音響端から端の遅延ではありません。

## Legacy の chunkSec 修正

旧 backend の48単位（0.128秒）が選択肢にないため誤表示され、0.1秒の指定が37.5単位として拒否されていました。さらに Device モード切替が古い値を再送する問題がありました。

48 kHz 基準の128フレーム単位に丸め、backend の実値を選択肢に含めます。0.1秒プリセットは38単位 / 4,864フレーム / 約0.101333秒、0.2秒は75単位 / 9,600フレームです。範囲は8〜1,875単位です。一般設定更新から古い raw 値を除き、専用の chunkSec 更新だけがこの値を書き込みます。

実 EXE と隔離 backend で両モードの選択・切替・画面更新・backend 再起動後の保持を確認しました。動作中 Client の変更は旧ストリームを停止し、明示再開後に新しい長さを使います。動作中 Server は先に停止する必要があり、この拒否は回帰試験で確認しています。自動生成した12秒 / 48 kHz / mono Int16 の倍音 WAV を実ファイル選択画面から開き、4,864と9,600フレームで非ゼロ出力を確認しました。

## PR 後の追加確認

- Node 96/96、Rust 33/33、Server 77/77 とフロントエンド構築、offline ブラウザ UI 検査が通過しました。
- 同じ release EXE を独立 profile と `--deny-media` で実行し、無関係な200応答の拒否、手動 base path、ポート回退、設定移行と保持、実 VCC 識別、backend 不在の入力画面、遅延起動後の再試行を確認しました。音声キャプチャと推論は行っていません。
- 最初の desktop 接続試験は、接続後に削除される旧 DOM マーカーを待って失敗しました。試験を現在の接続欄と BackendClient の phase/address/protocol、主画面の一致へ修正し、再実行は通過しました。アプリケーションの挙動変更はありません。
- 草稿 PR の時点では CI チェックの実行記録はありません。上記はローカルで実施した結果です。

## 既知の問題と未検証

- 旧候補の連続試験で単発 `/test` 502 による停止がありました。現在は native proxy 自身が識別した転送失敗に限り、稼働中 Legacy の連続していない1回を破棄し、次の sequence へ進みます。同じ sequence を再送せず、2回連続失敗で停止します。分岐は回帰試験で確認しましたが、底層502の根因は未確定です。
- マイク入力はほぼ無音でした。真人の有声音と聴感、有声音の長時間負荷、物理的抜き差し、異なるモデル/GPU、音響端から端の遅延、長期メモリ上限、別 PC の LAN は未検証です。
- Windows 音声は共有ダイアログが返す音声トラックを使います。対象ソースを指定したキャプチャは未実施です。トラックがない場合は停止します。
- checkpoint 内部の ValueError が `invalid_resource` に分類される場合があります。登録は明示的に失敗し、ファイルを保持します。

この記録は公開可能な検証要約です。音声・モデル・個人設定・生の診断はソースや構築入力に含めません。
