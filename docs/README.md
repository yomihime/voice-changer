# ドキュメント

この fork の利用・保守手順は、以下を参照してください。主な対象は Windows / NVIDIA GPU と RVC です。

## 利用する

- [Windows のインストール・起動・パッケージ作成](windows-setup.md)
- [VCClient の紹介と保守方針](../README.md)

## 開発・保守する

- [現在の構成と開発方針](architecture.md)
- [Official RVC の統合仕様（英語）](rvc-upstream-integration.md)
- [Official RVC の更新手順](rvc-upstream-update.md)
- [Desktop Client](../client/desktop/README.md)
- [独立新フロントエンド voice-changer-client](https://github.com/yomihime/voice-changer-client)
- [既存 Server 用の互換 UI](legacy-client-layout.md)
- [上流コードの固定バージョンと変更点](../third_party/rvc/UPSTREAM.md)

統合仕様は実装上の詳細を保持しています。新規の案内は日本語を基本とします。

## ディレクトリ案内

| 場所 | 内容 |
| --- | --- |
| `client/frontend/` | 独立リポジトリの Git submodule。開発・ビルドはその中で実行、2.x API 用 |
| `client/demo/` | 既存 Server 用の互換 UI。上流のレイアウトと RVC バックエンド設定を維持 |
| `client/lib/` | ブラウザ音声処理、通信、React hooks |
| `client/desktop/` | 既存 Server UI 専用の Electron ウィンドウ |
| `server/` | API、音声宿主、モデル管理、推論バックエンド |
| `third_party/rvc/` | 固定した Official RVC の推論コード |
| `scripts/`、ルートの Windows `.bat` | 現行のインストール・起動・検証・パッケージ作成 |
| `docs/` | 現行ドキュメントと資料索引 |
| `docs/archive/` | 上流説明、旧 README、翻訳、Notebook、過去の構成図 |
| `tutorials/` | 上流由来の旧操作チュートリアル。現行手順は Windows ガイドを優先 |
| `recorder/` | 保守対象外の音声収録ツール。旧公開ファイルは `legacy-site/` |
| `docker*/`、`script/`、`trainer/`、旧ルート `.sh` | 従来の実行・学習・配布資材。現行 Windows 手順とは別に保持 |

`script/` は旧 Docker 配布用、`scripts/` は現行の製品用ツールです。旧資材には上流リポジトリ・旧イメージへの参照が残っています。現在の fork 向けに検証済みの入口としては案内していません。起動・参照パスを壊さないため、今回の文書整理では移動していません。

## ローカルの生成物

`.runtime/`、`.venv/`、`build/`、`dist/` は実行環境・ビルド・配布物です。モデルや設定は [Windows ガイド](windows-setup.md)の保存先に従います。これらはソースコードではありません。

作業計画・調査・検証記録は、Git の対象外となる `.architecture-refactor/` にまとめます。作業用ファイルを正式ドキュメントや README の入口に混在させません。

## 過去の資料

[アーカイブ一覧](archive/README.md)を参照してください。上流のリリース番号・対応モデル・配布先は、本 fork の実装や検証範囲とは区別します。
