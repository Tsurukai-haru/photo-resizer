# Photo Compression Tool

スマホやデジカメで撮影した高画質な写真を、画質と縦横比を保ちながらブラウザ上で圧縮するツールです。

**URL**: https://tsurukai-haru.github.io/photo-resizer/

## 機能

- JPEG / PNG / WebP 形式の画像に対応
- 目標ファイルサイズ（kB）をスライダーで指定して圧縮
- 複数枚を一括処理し、ZIP ファイルでダウンロード
- サーバーへのアップロード不要（すべてブラウザ内で処理）
- PC・スマホ両対応のレスポンシブデザイン

## 使い方

1. 画像をアップロードエリアにドロップ、またはクリックして選択
2. スライダーで目標サイズを指定（デフォルト: 500 kB）
3. 「圧縮してZIPで保存」ボタンをクリック
4. `compressed_images.zip` がダウンロードされる

## 構成

```
photo-resizer/
├── index.html      # ブラウザで動作するメインアプリ（GitHub Pages でホスト）
├── app.py          # Streamlit 版（HEIC 形式にも対応）
└── requirements.txt
```

## ローカルで動かす（Streamlit 版）

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 技術スタック

- [JSZip](https://stuk.github.io/jszip/) — ZIP ファイルの生成
- [heic2any](https://github.com/alexcorvi/heic2any) — HEIC 形式の変換
- [Font Awesome](https://fontawesome.com/) — アイコン
- [Streamlit](https://streamlit.io/) / [Pillow](https://pillow.readthedocs.io/) — Python 版
