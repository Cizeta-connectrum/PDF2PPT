---
title: PDF2PPT
emoji: 📊
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8080
pinned: false
---

# PDF2PPT

PDFファイルを忠実にPowerPoint(.pptx)へ変換するWebアプリです。

## 変換モード

- **画像モード**: 各ページを高解像度画像としてスライドに全面貼り付け。レイアウト・フォント・図形を完全に再現しますが、テキストは編集できません。
- **編集可能モード**: 各ページを画像モードと同様に高解像度でレンダリングしつつ、レンダリング前にPDFのテキストだけを除去(リダクション)しておくことで、図形・写真・グラデーションなどテキスト以外の見た目は完全に保ったまま背景画像化します。その上に、抽出したテキストを元の位置・フォントサイズ・太字/斜体・色を再現した状態で、独立した編集可能なPowerPointテキストボックスとして重ねて配置します。スキャンPDFのOCRテキストのような不可視テキストは対象外とし、見た目を変えません。
  - **PDF内に文字データが一切ない場合(スクリーンショットや画像として書き出されたPDFなど)は、自動的にOCR(Tesseract)にフォールバックします。** OCRで認識した文字領域は周囲の色で塗りつぶして背景から消し、認識結果を編集可能なテキストボックスとして重ねます。この場合、元のフォントは再現されず、認識精度もOCRの性能に依存します(近似的な再現になります)。

## セットアップ

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### OCR機能を使う場合(画像化されたPDF用)

編集可能モードでOCRフォールバックを使うには、Tesseract OCR本体を別途インストールする必要があります(pipのpytesseractはTesseractを呼び出すラッパーで、本体は含まれません)。

```bash
# macOS
brew install tesseract tesseract-lang   # 日本語などの言語データも含む

# Debian/Ubuntu
sudo apt install tesseract-ocr tesseract-ocr-jpn
```

インストールされていない状態でOCRが必要なページに遭遇すると、変換時にその旨のエラーメッセージが表示されます。

## 起動

```bash
source venv/bin/activate
python app/app.py
```

ブラウザで http://localhost:5001 を開くと、アプリ一覧ダッシュボードが表示されます。「PDF変換」のカードをクリックするとPDF変換画面(`/convert-tool`)に移動できます。

### アプリ一覧ダッシュボード

トップページ(`/`)が、他に開発したWebアプリの一覧をカードで表示・起動できるダッシュボードになっています。

- 画面上部のフォームに**アプリ名**と**URL**を入力して「追加」すると、カードとして一覧に追加されます。
- カードをクリックすると、そのアプリが新しいタブで開きます。
- 各カードの「削除」でいつでも一覧から外せます。
- 登録データはサーバー上のファイル(`APPS_DATA_FILE` 環境変数で指定したパス、未指定時は `app/data/apps.json`)に保存されます。Hugging Face SpacesやCloud Runなど、コンテナが再作成される環境では**再デプロイ時にデータが消える**点に注意してください。

デフォルトのポートは5001です(macOSではAirPlay受信機能がポート5000を使用するため)。
別のポートで起動したい場合は `PORT` 環境変数を指定してください。

```bash
PORT=8000 python app/app.py
```

## テスト

```bash
source venv/bin/activate
pip install pytest
python -m pytest tests/ -v
```

## 仕組み

- PDFのレンダリング・解析には [PyMuPDF](https://pymupdf.readthedocs.io/) を使用。
- PPTX生成には [python-pptx](https://python-pptx.readthedocs.io/) を使用。
- アップロードされたファイルは一時ディレクトリに保存され、レスポンス送信後に自動削除されます。

## Hugging Face Spacesへの公開デプロイ(推奨: 無料・カード登録不要)

クレジットカード登録なしで、誰でもどこからでもアクセスできる固定URLで公開する方法です。

1. https://huggingface.co/join でアカウントを作成する(無料、カード登録不要)。
2. https://huggingface.co/new-space で新しいSpaceを作成する。
   - **SDK**: `Docker` を選択(このリポジトリの `Dockerfile` がそのまま使われます)。
   - **Visibility**: `Public` を選択。
   - 作成すると `https://huggingface.co/spaces/<あなたのユーザー名>/<space名>` というURLのgitリポジトリが発行されます。
3. このリポジトリの内容をそのSpaceにpushする。

```bash
git remote add space https://huggingface.co/spaces/<あなたのユーザー名>/<space名>
git push space claude/pdf-to-ppt-converter-1ii8fb:main
```

4. pushが完了すると、Space側で自動的にDockerイメージがビルドされます(数分かかります)。ビルド状況はSpaceのページの「Logs」タブで確認できます。
5. ビルドが終わると `https://<あなたのユーザー名>-<space名>.hf.space` が公開URLになります。これを誰とでも共有できます。

**Hugging Face Spaces(無料CPUプラン)の特性:**
- クレジットカード登録は一切不要で、課金される可能性は構造的にありません。
- しばらくアクセスがないとコンテナがスリープし、次のアクセス時に自動的に再起動します(初回アクセス時に数秒〜数十秒の遅延が発生します)。
- README.md先頭のYAMLメタデータ(`sdk: docker`, `app_port: 8080` など)でSpaceの設定を行っています。変更した場合はこの部分も合わせて確認してください。

## (代替手段) Google Cloud Runへの公開デプロイ

より高いスペック・可用性が必要な場合の代替手段です。クレジットカード登録(billingアカウント)が必要です。事前に [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)(`gcloud` コマンド)をインストールし、GCPプロジェクトを作成しておいてください。

```bash
# 初回のみ: ログインとプロジェクト設定
gcloud auth login
gcloud config set project <あなたのプロジェクトID>

# リポジトリのルート(このDockerfileがある場所)で実行
gcloud run deploy pdf2ppt \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --timeout 300 \
  --max-instances 3
```

- `gcloud run deploy --source .` が、リポジトリ直下の `Dockerfile` を自動検出してビルド・デプロイまで行います(手動でのDockerビルド・プッシュは不要です)。
- `--allow-unauthenticated` で認証なしの完全公開になります。
- `--max-instances` は同時起動できるインスタンス数の上限です。認証なしで公開するため、意図しない大量アクセスによる課金増加を防ぐ目安として設定しています。必要に応じて調整してください。
- `--timeout` はリクエストあたりの最大処理時間(秒)です。ページ数の多いPDFやOCR処理で時間がかかる場合は増やしてください(最大3600)。
- デプロイ完了後に表示されるURLが公開アクセス用のURLです。

**公開する上での注意:**
- このアプリはアップロードされたPDFを解析・OCR処理するため負荷が比較的高く、認証なし公開では不特定多数からの連続アクセスにより課金が増える可能性があります。`--max-instances` に加えて、GCP側で予算アラート(Billing → 予算とアラート)を設定しておくことを推奨します。
- アップロードされたファイルはリクエスト処理後に自動削除されますが、Cloud Runの各インスタンスは一時的にディスク(メモリ上の`/tmp`)にファイルを書き込みます。永続化はされません。
