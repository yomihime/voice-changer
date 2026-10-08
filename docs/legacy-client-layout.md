# 既存 Server 用 UI

`client/frontend/` 以外の `client/` は、上流追跡ブランチの
`d8ef15799470193f7c8176ef471245753a656626` と同じ内容に戻しました。
`client/demo/` と `client/lib/` の独自 UI、バックエンド選択、F0 設定、
依存関係・型・ビルド修正は撤回し、fork の `client/desktop/` Electron シェルは撤去しました。

互換 UI は既存の `/info` / `/update_settings` Server 用です。インストールと
パッケージ作成では、上流の配布済み `client/demo/dist/` を `.runtime/frontend/` に
コピーします。旧 demo/lib の npm インストールや再ビルドは行いません。
更新時の以前の出力は `.runtime/frontend-backup-*` に保持します。
既存の Electron ランタイム、プロファイル、モデルは自動削除しません。

Server の Legacy / Official バックエンドと API は維持しますが、上流 UI に
fork 専用の選択コントロールはありません。

新 UI とデスクトップ版の開発入口は
[`client/frontend/`](../client/frontend/README.md) と
[Tauri の手順](../client/frontend/TAURI.md) です。新 Client は 2.x API 用であり、
既存 Server の旧 API へのアダプターは未実装です。
