# 既存 Server 用 UI

`client/demo/` は既存の `/info` / `/update_settings` Server に接続する互換用 UI です。
上流のレイアウトを維持し、モデル一覧、音声デバイス、録音、詳細設定は従来の位置に表示します。
新しい UI の開発入口は [`client/frontend/`](../client/frontend/README.md) です。

## 保守範囲

- RVC の Legacy / Official 切り替えと、各バックエンドが対応する設定の表示を維持します。
- Official の F0 検出器は `rmvpe` / `fcpe` / `pm` です。旧 DirectML edition の Legacy 用フィルターは適用しません。
- 既存の音声処理と Server API、現在の依存関係に必要なビルド・型の互換修正を維持します。
- 2.1.4 風の追加 CSS、ページ切り替え、独自のデバイス設定モーダルは使用しません。

2.1.4-alpha 復元 UI は 2.x API を使用します。互換 UI の表示を戻しても、新フロントエンドと既存 Server の API 差異は解消しません。

## 検証

ビルド出力は `.runtime/` 配下に指定し、追跡済みの `client/demo/dist/` を上書きしないでください。
Webpack の production ビルドと TypeScript の全体チェックは別に実行します。
現時点では Web edition の依存型、React の JSX 型、モデル型などに既存の TypeScript 診断が残っています。
