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

ブラウザで http://localhost:5001 を開き、PDFをアップロードして変換モードを選択してください。

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
