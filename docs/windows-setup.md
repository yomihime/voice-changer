# Windows でのインストール・起動・パッケージ作成

## 動作環境

- Windows x64 / NVIDIA GPU
- CUDA 13.0 に対応する NVIDIA ドライバー
- 初回インストール時のインターネット接続
- 空き容量の目安は 15 GB 以上。パッケージ作成には追加の作業領域が必要です。

Python、Anaconda、Node.js、CUDA Toolkit の事前インストールは不要です。本リポジトリ専用の環境を `.runtime/` と `.venv/` に作成します。既存の Python や他の VCClient / RVC 環境は変更しません。

## ソースコードから使用する

リポジトリを clone するか、ソースコードの ZIP をダウンロードして展開してください。

1. `install-windows.bat` をダブルクリックします。ツールのダウンロードと検証、依存ライブラリのインストール、上流互換 UI のコピー、実行環境のチェックを行います。
2. `start-client-windows.bat` をダブルクリックします。Server を非表示で起動し、VCClient 固有の `/info` 応答を確認してから上流互換 UI を既定ブラウザで開きます。初回のインストールやウェイトのダウンロードには数分以上かかることがあるため、完了するまで待ってください。ログは `.runtime/launcher/` に保存されます。
3. Client でモデルを登録します。Server だけを起動したい場合は従来どおり `start-windows.bat` を使用します。

起動後の設定とモデルスロットは従来どおりサーバ側で管理します。既定のバックエンドは Legacy です。

サーバの引数は `--` の後に指定できます。

```bat
start-windows.bat -- -p 18889
start-windows.bat -- --skip-downloads
```

Server と Client を一度に起動する入口には、テスト向けの引数があります。

```bat
start-client-windows.bat -Port 18889
start-client-windows.bat -Port 18889 -Lan
start-client-windows.bat -SkipDownloads -NoBrowser
start-client-windows.bat -Browser
```

`-Lan` は Server を `0.0.0.0` に bind しますが、ローカル Client は安全な
`127.0.0.1` URL で開きます。既に同じポートで、VCClient の必須フィールドを持つ
`/info` が応答している場合は、重複起動せず既存 Client を開きます。別の HTTP
サービス、壊れた JSON、TCP 接続だけのプロセスは VCClient として扱わず、終了コード
2 で停止します。起動中のインストールまたはウェイト取得は `-ReadyTimeoutSeconds`
（既定 900 秒）まで待ち、タイムアウト時は自分で起動したプロセスツリーだけを停止します。
既定ブラウザで上流互換 UI を開きます。`-Browser` は互換用の別名、`-NoBrowser` は URL の表示のみです。旧 Electron シェルの組み立てと同梱は終了しました。

ブラウザを閉じても Server は停止しません。ランチャーが新しく開始したサービスは、開いたままの起動ウィンドウで Enter を押すと停止します。`-NoBrowser` は待機せず URL を表示して終了します。開始・停止を GUI で管理する場合は、最初から Server GUI でサービスを開始してください。GUI が停止できるのは自分で開始したサービスだけです。`start-client-windows.bat` で開始した既存サービスは GUI では外部サービスとして扱います。既存のデスクトップ実行環境、プロファイル、モデルは自動削除しません。

## 独立した新フロントエンドの開発

2.1.4-alpha 由来の新フロントエンドは
[voice-changer-client](https://github.com/yomihime/voice-changer-client) で管理します。
このリポジトリでは `client/frontend` を Git submodule として参照します。
Server のインストール、起動、パッケージ作成には子モジュールの取得もビルドも不要です。
`client/demo` / `client/lib` は上流原版の参照・互換 UI です。配布済み dist をブラウザで使用します。

```powershell
git submodule update --init client/frontend
cd client/frontend
npm ci
npm run build
npm run dev
```

接続設定と必要な Node 環境は新リポジトリの README を参照してください。
ブラウザ出力は新リポジトリ内の `dist/` に置きます。デスクトップ版は Tauri 2 の EXE / NSIS インストーラーとして独立してビルドします。詳細は [TAURI.md](../client/frontend/TAURI.md) を参照してください。新 Client は 2.x API 用で、既存 Server の旧 API アダプターは未実装です。
旧 `build-frontend-windows.bat` / `start-frontend-windows.bat` は移行案内のみを表示し、
旧 demo のビルドや新 UI の起動は行いません。

## Voice Changer Server GUI

`server-gui-windows.bat` から **Voice Changer Server** を開きます。
UI は PyQt6 / qfluentwidgets のコミュニティ版を使用し、設定、プロセス管理、
トレイ、ログ表示を提供します。新 Tauri Client とは別のサービス管理アプリです。

依存関係は `server/requirements/windows-gui.lock` で固定しています。
ソース版の初回 GUI 起動時に必要な GUI ライブラリだけを導入します。
ポータブル版には Qt ランタイム、plugins と依存ライセンスを含みます。
GPLv3 / 商用ライセンスの条件と構成の詳細は [Server GUI](server-gui.md) を参照してください。

```powershell
.venv\Scripts\python.exe scripts/server_gui.py --self-test
.venv\Scripts\python.exe scripts/server_gui.py --preview .runtime/server-gui-fluent-preview.png
```

この確認は UI のみを実行し、推論サービス、モデル、音声入力は起動しません。
旧 `scripts/server-gui.ps1 -SelfTest` 入口も Python の確認へ転送します。
設定は引き続き `.runtime/server-gui/settings.json` を使用します。
GUI が開始するサービスは従来の `scripts/windows.ps1 -Action start` と同じ経路です。
CLI の起動方法は維持されます。

通常の初回起動では、既存のサーバ処理に従って共通の推論用ウェイトをダウンロードします。依存ライブラリのインストールとは別の処理です。CLI はこの処理と Server 起動を同じ待機状態として表示し、GUI は Starting として表示します。既存の外部 VCClient を検出した場合、GUI はそれを Ready と表示しますが、Stop では終了しません。

`--skip-downloads` は、必要なウェイトを用意済みのオフライン環境や起動確認で使用します。ウェイトが不足している場合は推論できません。LAN 接続では、従来の HTTPS と allowed-origins の設定を使用してください。

`.venv` は単独で移動しないでください。ソースディレクトリを移動した場合は環境を作り直すか、下記のポータブルパッケージを使用してください。

### 実行環境のチェック

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/windows.ps1 -Action check
```

Legacy / Official のモジュール読み込み、リサンプリング、HTTPS 証明書の生成、Torch CUDA 演算、ONNX CUDA セッションを確認します。モデルの音質や音声デバイス、長時間動作の確認は別途必要です。初回は Numba のコンパイルに時間がかかる場合があります。

## ポータブルパッケージを作成する

`build-windows.bat` を実行します。依存関係とフロントエンドを確認し、移動可能な Python とライブラリをコピーします。コピー先で実行環境のチェックに成功すると、`dist/vcclient-windows-cuda.zip` を作成します。

受け取った人は ZIP を展開し、`start-windows.bat` を実行してください。Python / Node.js のインストールは不要ですが、NVIDIA ドライバーは必要です。共通ウェイトは初回起動時にダウンロードするか、別途用意してください。モデルを含む完全オフラインパッケージではありません。

パッケージには以下を含めます。

- Python 本体と固定した Python ライブラリ
- ビルド済みフロントエンドとサーバの実行コード
- 固定バージョンの Official RVC 実行コードとライセンス
- 起動スクリプト、環境チェック、ファイル検証用の `package-manifest.json`

個人モデル、`server/pretrain`、保存済み設定、アップロード、秘密鍵、ローカル作業文書、`.architecture-refactor` は含めません。ライブラリに同梱されたライセンスは実行環境に保持します。
実行時に不要な ONNX / setuptools のテストデータと Torch の C++ ビルド用
ヘッダー・CMake ファイルも除外し、通常の Windows 展開先でパス長制限に
当たらないようにします。ポータブル配布物は C++ 拡張のビルド環境ではありません。

既存の ZIP は上書きしません。出力先を変える場合は次のように指定します。

```bat
build-windows.bat --output dist\vcclient-test.zip
```

Official RVC の実機受入では、通常のモデルスロットを選択してから次のツールを
使います。デバイス試験はサーバー側のマイク→変換→出力コールバックを監視し、
途中で chunk サイズを変更します。LAN 試験は loopback ではなくサーバーの LAN
アドレスを指定し、複数の PCM shape を実時間ペースで送信します。

```powershell
python server/tools/soak_rvc_runtime.py device `
  --duration 600 --json test-output\device-soak.json

python server/tools/soak_rvc_runtime.py lan `
  --wav server\test.wav --duration 600 `
  --json test-output\lan-soak.json `
  --url http://192.168.1.10:18888
```

レポートには初回パケット観測、推論回数、P50/P95、エラー、shape 切替、
CUDA allocated/reserved/peak の推移が保存されます。同一 PC の LAN NIC を使う
場合だけ `--same-host-lan-interface` を付け、別端末試験と区別してください。

ビルドはソース環境で実行してください。ポータブルパッケージは起動と環境チェックに対応しています。

## 依存ライブラリの方針

バージョン調査日：2026-09-06。インストール可能で動作を確認できる最新の安定版の組み合わせを使用します。起動時にライブラリを自動更新することはありません。

Python の全依存バージョンと SHA-256 は `server/requirements/windows-cuda.lock`、ツールのバージョンとダウンロード検証値は `scripts/runtime-versions.json` に記録しています。

| 項目 | 採用バージョン | 互換性について |
| --- | --- | --- |
| Python | 3.12.14 | Legacy で使用する fairseq の Windows wheel に合わせています。 |
| Torch / torchaudio | 2.11.0 + CUDA 13.0 | 対応する組み合わせを使用します。調査時点で Torch 単体の最新版はこれより新しく、torchaudio は 2.11.0 です。 |
| ONNX Runtime GPU | 1.29.0 | CUDA 13 環境でセッションを実行して確認します。 |
| NumPy / SciPy / librosa | 2.5.2 / 1.18.1 / 1.0.0 | 数値計算と音声処理の依存を更新します。 |
| Transformers | 5.16.1 | 既存の Official HuBERT の呼び出しを使用し、vendor のアルゴリズムは変更しません。 |
| fairseq | fairseq-fixed 0.12.3.1 | CPython 3.12 の Windows wheel を提供するサードパーティー互換版です。Meta 公式の新バージョンや fairseq2 ではありません。 |
| Hydra / OmegaConf | 1.3.2 / 2.3.0 | fairseq-fixed の固定依存に合わせています。 |
| pyworld | 0.3.5 | 0.3.6 には CPython 3.12 の Windows wheel がないため、利用者側でのコンパイルを避けています。 |
| Node.js | 新 Client の開発環境に従う | Server の導入・互換 UI のコピーには不要です。 |

参考：[PyTorch](https://docs.pytorch.org/get-started/locally/)、[torchaudio](https://docs.pytorch.org/audio/stable/installation.html)、[ONNX CUDA](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html)、[fairseq-fixed](https://pypi.org/project/fairseq-fixed/)、[互換版ソース](https://github.com/JackismyShephard/fairseq)、[pyworld](https://pypi.org/project/pyworld/)、[Node.js](https://nodejs.org/dist/v24.20.0/)。

Legacy HuBERT の読み込みでは、既知の fairseq Dictionary メタデータのみを局所的に許可します。Torch の weights-only 制限をプロセス全体で無効にしません。別形式の checkpoint が読み込めない場合は、その内容を確認して個別に対応してください。

`client/demo` / `client/lib` の依存関係と配布済み dist は上流原版を保持します。互換 UI は `client/demo/dist` から `.runtime/frontend` にコピーし、以前の出力は `.runtime/frontend-backup-*` に残します。新 Client の依存・ロックファイルは独立リポジトリで管理します。

## 更新・トラブルシューティング

- Python の更新：`server/requirements/windows-cuda.in` を編集し、lock を再生成します。環境チェックと実モデルの確認後に反映してください。lock のバージョンやハッシュだけを手作業で書き換えないでください。
- フロントエンドの更新：新 Client は独立リポジトリでビルド・テストします。上流互換 UI の更新は上流の原版 dist を確認して反映し、旧 demo/lib に独自修正を追加しません。
- ダウンロード失敗：ターミナルのエラーと接続先を確認して再実行してください。検証に失敗したキャッシュは削除して取得し直し、ハッシュ検証は無効にしないでください。
- GPU チェック失敗：選択した CUDA バージョンにドライバーと GPU が対応しているか確認してください。CPU への暗黙の切り替えは行いません。
- インストール中断：ビルドと環境チェックがすべて成功した後にだけ完了マーカーを書きます。再実行して続行できます。
- モデルと設定：依存ライブラリを再インストールしても、既存のモデルと設定ディレクトリは消去しません。
- ポート使用中：起動は失敗コードを返して終了します。別のポートを指定するか、そのポートを使用しているアプリケーションを終了してください。

### 更新確認（2026-10-08）

- `client/frontend` 以外の `client/` は上流追跡コミットとファイル・モード・blob が一致します。
- 上流互換 UI の 26 ファイルを実際にコピーし、コピー先と以前の出力のバックアップを SHA-256 で照合しました。
- Python スクリプト全体の 52 テストと、その後追加したブラウザ起動・停止検証を含むランチャー 13 テストが通過しました。サービスの識別は HTTP fixture、停止の流れは模擬サービスと合成プロセスで検証しています。
- 新 Client の Node 9 テスト、Rust 22 テスト、ブラウザ確認、Tauri release EXE / NSIS ビルド、実際の WebView2 と模擬バックエンドによる確認が通過しました。詳細と制限は新 Client の `VALIDATION.md` に記録しています。

この更新では CUDA ポータブル ZIP 全体、実モデル推論、実マイク入力、物理ショートカットは再検証していません。下記は以前の構成による記録です。

### 動作確認記録（2026-09-07）

Windows / RTX 5090 D v2 / NVIDIA ドライバー 616.56 で、以下を確認しました。

- 固定した依存関係のインストール、`pip check`、フロントエンドの本番ビルド
- Torch / ONNX CUDA 演算、Legacy と Official の実 HuBERT 読み込み
- 同一 MIA モデルを使った両バックエンドの短い合成音声推論
- ブラウザーの初期画面表示、HTTP API、オフライン起動、ポート競合時の終了
- コピー先のポータブル Python による実行環境チェック

マイク入力から再生までの長時間動作、聴感品質、端末間の互換性は未確認です。短い推論テストの結果をエンドツーエンドの遅延保証として扱わないでください。

開発者向けの lock 再生成コマンド：

```powershell
.runtime/uv/uv.exe pip compile server/requirements/windows-cuda.in --python .venv/Scripts/python.exe --index https://download.pytorch.org/whl/cu130 --index-strategy unsafe-best-match --generate-hashes --output-file server/requirements/windows-cuda.lock
```

今回の主な対象は Windows NVIDIA 上の RVC Legacy / Official です。独立した `recorder` プロジェクト、学習環境、他のモデルバックエンド、Linux/macOS、DirectML はこのインストール・パッケージの検証対象に含めません。従来の非 Windows 向け依存は `server/requirements/legacy-platforms.txt` に保存しており、更新・動作確認済みとは扱いません。Hybrid は引き続き予約用のコメントのみです。
