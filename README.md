## VCClient

VCClient は、AI を用いてリアルタイム音声変換を行うソフトウェアです。

## この fork について

本リポジトリは、w-okada 氏の [VCClient / voice-changer](https://github.com/w-okada/voice-changer) を基に、[yomihime](https://github.com/yomihime) が独自に保守・開発する fork です。

- Windows / NVIDIA GPU を優先し、RVC の音質・遅延・安定性の改善を目指します。
- 既存の Legacy と RVC 公式実装を利用する Official を提供します。Official の変更は入出力などの必要な調整にとどめ、上流の推論処理をできるだけ維持します。
- 原作者の 2.1.4-alpha 配布版の使い勝手を参考に、デスクトップ起動、依存環境の導入、ポータブル配布を整備します。
- 独自バックエンド Hybrid は今後の検討対象です。現在は予約のみで、実装していません。Intel NPU 対応はこの新バックエンドで検討し、Legacy / Official には追加しません。

使用方法は [Windows のインストール・起動・パッケージ作成](docs/windows-setup.md)、バックエンドの詳細は [RVC Official 統合](docs/rvc-upstream-integration.md)を参照してください。`start-client-windows.bat` で Server とデスクトップ Client を起動できます。

Recorder（音声収録ツール）は保守対象外です。ソースは履歴資料として残しています。

## ドキュメント

- [インストール・起動・パッケージ作成](docs/windows-setup.md)
- [ドキュメント一覧・ディレクトリ案内](docs/README.md)
- [現在の構成と開発方針](docs/architecture.md)
- [上流の紹介・リリース情報](docs/archive/upstream-readme.md) / [翻訳・旧開発手順](docs/archive/README.md)

上流の配布物や対応表は、この fork のリリース・動作保証とは区別してください。

## Acknowledgments

- [立ちずんだもん素材](https://seiga.nicovideo.jp/seiga/im10792934)
- [いらすとや](https://www.irasutoya.com/)
- [つくよみちゃん](https://tyc.rei-yumesaki.net/)

```
  本ソフトウェアの音声合成には、フリー素材キャラクター「つくよみちゃん」が無料公開している音声データを使用しています。
  ■つくよみちゃんコーパス（CV.夢前黎）
  https://tyc.rei-yumesaki.net/material/corpus/
  © Rei Yumesaki
```

- [あみたろの声素材工房](https://amitaro.net/)
- [れぷりかどーる](https://kikyohiroto1227.wixsite.com/kikoto-utau)

## 利用規約

- リアルタイムボイスチェンジャーつくよみちゃんについては、つくよみちゃんコーパスの利用規約に準じ、次の目的で変換後の音声を使用することを禁止します。

```

■人を批判・攻撃すること。（「批判・攻撃」の定義は、つくよみちゃんキャラクターライセンスに準じます）

■特定の政治的立場・宗教・思想への賛同または反対を呼びかけること。

■刺激の強い表現をゾーニングなしで公開すること。

■他者に対して二次利用（素材としての利用）を許可する形で公開すること。
※鑑賞用の作品として配布・販売していただくことは問題ございません。
```

- リアルタイムボイスチェンジャーあみたろについては、あみたろの声素材工房様の次の利用規約に準じます。詳細は[こちら](https://amitaro.net/voice/faq/#index_id6)

```
あみたろの声素材やコーパス読み上げ音声を使って音声モデルを作ったり、ボイスチェンジャーや声質変換などを使用して、自分の声をあみたろの声に変換して使うのもOKです。

ただしその場合は絶対に、あみたろ（もしくは小春音アミ）の声に声質変換していることを明記し、あみたろ（および小春音アミ）が話しているわけではないことが誰でもわかるようにしてください。
また、あみたろの声で話す内容は声素材の利用規約の範囲内のみとし、センシティブな発言などはしないでください。
```

- リアルタイムボイスチェンジャー黄琴まひろについては、れぷりかどーるの利用規約に準じます。詳細は[こちら](https://kikyohiroto1227.wixsite.com/kikoto-utau/ter%EF%BD%8Ds-of-service)

## 免責事項

本ソフトウェアの使用または使用不能により生じたいかなる直接損害・間接損害・波及的損害・結果的損害 または特別損害についても、一切責任を負いません。
