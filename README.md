# PDF2PPT

PDFファイルを忠実にPowerPoint(.pptx)へ変換するWebアプリです。

## 変換モード

- **画像モード**: 各ページを高解像度画像としてスライドに全面貼り付け。レイアウト・フォント・図形を完全に再現しますが、テキストは編集できません。
- **編集可能モード**: 各ページを画像モードと同様に高解像度でレンダリングしつつ、レンダリング前にPDFのテキストだけを除去(リダクション)しておくことで、図形・写真・グラデーションなどテキスト以外の見た目は完全に保ったまま背景画像化します。その上に、抽出したテキストを元の位置・フォントサイズ・太字/斜体・色を再現した状態で、独立した編集可能なPowerPointテキストボックスとして重ねて配置します。スキャンPDFのOCRテキストのような不可視テキストは対象外とし、見た目を変えません。

## セットアップ

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

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
