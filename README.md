# somaticstudio website

Firebase Hosting + Firebase Authentication + Cloud Firestore で動く、静的サイトです。

```
public/
  index.html        トップページ（全セクション・認証・マイページ）
  terms.html        利用規約
  privacy.html      プライバシーポリシー
  tokushoho.html    特定商取引法に基づく表記
  robots.txt / sitemap.xml
  assets/
    tailwind.css    ビルドで生成されるCSS（直接編集しない）
    favicon.svg / ogp.png
src/tailwind.css    CSSビルドの入力ファイル
tailwind.config.js  CSSビルドの設定
firestore.rules     Firestoreのセキュリティルール
firebase.json       Hosting / Firestore の設定
```

## セットアップ

```bash
npm install
```

## デプロイ

```bash
npm run deploy
```

これは以下の2つをまとめて実行します。

```bash
npm run build                                        # CSSを生成
firebase deploy --only hosting,firestore:rules       # 公開
```

セキュリティルールを反映しないと、お問い合わせもニュースレター登録も保存されません。
**必ず `firestore:rules` を含めてデプロイしてください。**

### HTMLを編集したら、必ずCSSを作り直す

見た目は `public/assets/tailwind.css` に事前ビルドされています。
HTMLに**新しいCSSクラスを追加した場合**は、ビルドし直さないとそのクラスが効きません。

```bash
npm run build      # 一度だけ生成
npm run watch      # 編集しながら自動生成（作業中はこちらが便利）
```

`npm run deploy` を使えばビルドは自動で走るので、通常は意識不要です。

> 以前は Tailwind をCDNから読み込んでいましたが、表示が外部サービスの状態に
> 依存し、読み込みが終わるまで無装飾の画面が見えてしまうため、事前ビルドに
> 変更しました（約400KB → 18KB）。

---

## 公開前に必ず対応すること

### 1. 決済リンクを設定する（これがないと課金が始まりません）

`public/index.html` の `SITE_CONFIG.checkoutUrls` に、Square または Stripe の
サブスクリプション決済リンクを入れてください。

```js
const SITE_CONFIG = {
    checkoutUrls: {
        library:    'https://...',
        collective: 'https://...',
        essential:  'https://...'
    },
    newsletterUrl: ''
};
```

空のままでも動作します。その場合、「このプランに申し込む」を押した人は
お問い合わせフォームに案内され、希望プランが `contacts` の `interestedPlan` に
記録されるので、手動でご案内できます。

### 2. プラン付与の運用を決める

新規登録者は必ず `plan: 'free'`（無料会員）になります。
利用者が自分で有料プランに書き換えることは、Firestoreルールで禁止しています。

入金を確認したら、Firebaseコンソールで対象ユーザーの `users/{uid}` ドキュメントの
`plan` を `library` / `collective` / `essential` のいずれかに変更してください。
希望プランは同じドキュメントの `requestedPlan` に入っています。

> 将来的には、決済サービスのWebhookを受けるCloud Functionsで自動化するのが理想です。

### 3. Zoomのパスコードを変更する

**重要:** 以前のバージョンではZoomのミーティングIDとパスコードがHTMLに直接
書かれており、誰でもソースを見れば取得できる状態でした。この情報はGitの履歴にも
残っています。**現在有効なパスコードは変更してください。**

新しい情報は、HTMLではなくFirestoreの以下のドキュメントに登録します。
（Firebaseコンソールから手動で作成してください。ルールにより、書き込みは
管理者のみ、読み取りは該当プランの会員のみに制限されています。）

| ドキュメント | 読める人 | フィールド |
| --- | --- | --- |
| `protected/zoom_group` | The Collective 以上 | `meetingId`, `passcode` |
| `protected/zoom_private` | The Essential | `meetingId`, `passcode` |

ドキュメントが存在しない場合、マイページには
「ご予約完了後のご案内でお知らせします」と表示されます。

### 4. 法務ページの空欄を埋める

`public/tokushoho.html` に `【要記入】` が2か所あります（黄色くハイライトされています）。

- 問い合わせ用メールアドレス
- 支払い方法（利用する決済代行サービス名）

所在地と電話番号は「請求があれば遅滞なく開示する」形式にしてあります。これは
通信販売において認められている記載方法ですが、請求を受けたら実際に開示する必要が
あります。

利用規約・プライバシーポリシーは一般的な内容の草案です。**公開前に内容をご確認ください。**

### 5. 写真を用意する

現在、主宰者の顔写真とコンテンツのサムネイルは、色面のプレースホルダーです
（CSSクラス `visual-placeholder`）。**信頼に直結する部分なので、本人の写真への
差し替えを最優先でお願いします。**

OGP画像 `public/assets/ogp.png` も、現状はブランドカラーのグラデーションのみです。
ロゴや写真の入ったものに差し替えると、SNSでシェアされたときの見え方が良くなります。

### 6. 独自ドメインを使う場合

以下のファイルに `https://somatic-studio-e53b8.web.app/` が書かれています。
独自ドメインに切り替える際は、あわせて変更してください。

- `public/index.html`（canonical、OGP）
- `public/robots.txt`
- `public/sitemap.xml`

### 7. ジャーナル記事の文章を確認する

`public/index.html` の記事ページ（「ゆるむ」とは何か）は、サイト内の既存の説明を
もとに作成した下書きです。**大沼さんご自身の言葉に書き換えてください。**

---

## 運用メモ

### 届いたデータの見かた

Firebaseコンソール > Firestore Database で確認できます。

| コレクション | 内容 |
| --- | --- |
| `contacts` | お問い合わせ（`interestedPlan` に希望プランが入ることがあります） |
| `newsletter_subscribers` | ニュースレター登録者のメールアドレス |
| `users` | 会員情報（`plan` と `requestedPlan`） |

セキュリティルールにより、これらはブラウザからは読み出せません。
コンソールまたはAdmin SDKからのみ参照できます。

### 新着通知が欲しい場合

`contacts` への書き込みをトリガーにするCloud Functionsを作り、メールやSlackに
通知するのがおすすめです。現状は、コンソールを定期的に確認する運用になります。

### アクセス解析

Google Analytics 4（測定ID `G-34V43FRWKC`）を読み込んでいます。
以下のイベントを送信しているので、どこで離脱しているか追えます。

- `newsletter_signup` — ニュースレター登録
- `select_plan` — プランのボタンを押した（`plan_id` 付き）
- `sign_up` / `login` — 会員登録・ログイン
- `contact_submit` — お問い合わせ送信

### スパム対策

お問い合わせとニュースレター登録は、誰でも書き込める必要があるため、
ルールでは形式と文字数のみを検証しています。スパムが増えるようであれば、
Firebase App Check の導入を検討してください。

### Firebase APIキーについて

`index.html` に書かれているAPIキーは、Firebaseの仕様上クライアントに公開される
もので、秘密情報ではありません。ただし、GCPコンソールで
「HTTPリファラーによる制限」をかけておくことをおすすめします。
