# VCClient Desktop（Windows x64）

既存の Python Server と同じ画面を独立ウィンドウで開く、小さな Electron
アプリケーションです。Server の起動・停止は Windows ランチャーが担当します。
この Client 自体は Python プロセスを起動したり終了させたりしません。

## ビルド

Electron 44.2.0 の公式 Windows x64 ZIP と SHA-256 を
`electron-runtime.json` に固定しています。Node の追加パッケージ、C++、Rust、
WebView2 のインストールは不要です。既存のフロントエンド依存関係も変更しません。

```powershell
python scripts/desktop.py build
python scripts/desktop.py verify
```

手元の公式 ZIP を検証して使用する場合は `build --archive <絶対パス>` を指定します。
出力は `.runtime/desktop/vcclient-desktop.exe` です。ZIP 配布時は同じディレクトリの
DLL、resources、locales、LICENSE、LICENSES.chromium.html などをすべて含めます。
exe 単体を移動して使用しないでください。ダウンロード失敗や検証不一致時は停止します。

```powershell
.runtime/desktop/vcclient-desktop.exe --url http://127.0.0.1:18888/
```

Server が応答していることをランチャーで確認してから開きます。別のポートも指定できます。
ウィンドウの × または Client → 終了で Client を終了し、音声入力を解放します。
GUI が管理する Server は Client を閉じても動作を続けます。

## 設定とマイク

Client の設定は `%LOCALAPPDATA%/Yomihime/VoiceChanger/Desktop/` に保存します。
展開先の絶対パスと接続先 origin ごとに分離し、原作者のアプリ設定は読み書きしません。
同じ場所・ポートなら次回も設定を使用します。場所やポートを変えると別の設定になります。
同じ設定領域への重複起動では既存ウィンドウを表示し、新しい Client を終了します。

マイクは確認ダイアログで許可した場合だけ使用します。許可は Client の終了まで有効です。
画面はデバイス一覧を得るためにもマイクを要求します。拒否してもモデルアップロードなどは
利用できます。許可し直すには Client メニューの「マイクの許可を再確認」を選択します。
カメラ・画面キャプチャ・未知の権限は許可しません。

`--deny-media` は音声入力を常に拒否する検証用オプションです。
`--profile-root <絶対パス>` で検証用の保存先を分離できます。通常は指定不要です。

ヘルプ・ライセンス・支援リンクは許可された HTTPS サイトを既定ブラウザーで開きます。
ページに Node やシステムコマンドを公開する IPC はありません。
音声処理を最小化中も継続させるため、このウィンドウのバックグラウンドタイマー制限を
無効にしています。Web のセキュリティと renderer sandbox は有効です。

## 開発時の確認

```powershell
node --test client/desktop/tests/policy.test.cjs
python -m unittest discover -s scripts/tests -p test_desktop.py
```

非表示 mock 試験は実機マイクと再生を使用せず、入力権限を拒否して実行します。
実際のマイク、出力デバイス選択、AudioWorklet、長時間の最小化動作、音質については
別の実機受入試験が必要です。ページが表示されたことだけで音声互換性を保証しません。

Electron と Chromium のセキュリティ更新は、この固定バージョンを更新して再配布します。
自動更新やテレメトリーは追加していません。アプリの JS は本リポジトリの MIT License、
Electron と Chromium のライセンスは同梱の各ファイルを参照してください。

参考: [Electron 配布方法](https://www.electronjs.org/docs/latest/tutorial/application-distribution)、
[セキュリティ](https://www.electronjs.org/docs/latest/tutorial/security)、
[BrowserWindow](https://www.electronjs.org/docs/latest/api/browser-window)。
# 新前端入口

桌面壳现已内置 [`client/frontend`](../frontend/README.md) 中的 2.1.4-alpha 恢复基线。
无参数启动默认连接 `http://127.0.0.1:18000/`，也可传 `--backend URL`。
新界面由 Electron 进程内的本地代理在 21416 端口提供，随窗口退出关闭。
`--url URL` 保留原有加载后端页面的路径，不能与 `--backend` 同时使用。

在根目录运行 `build-frontend-windows.bat` 生成包含前端的独立桌面 ZIP；
`start-frontend-windows.bat --backend http://127.0.0.1:18000/` 启动。
此包不含推理后端与模型，2.x API 和全局快捷键移植状态见前端 README。
