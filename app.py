import streamlit as st
from PIL import Image
import pillow_heif
import io
import zipfile

# iPhoneのHEIC形式を読み込めるようにする設定
pillow_heif.register_heif_opener()

st.set_page_config(page_title="画像一括軽量化ツール", layout="centered")

st.title("📸 画像一括軽量化ツール (目標500kB)")
st.write("スマホやiPadの写真（HEIC / JPEG / PNG）を、縦横比を維持したまま約500kB以下に自動圧縮してJPEGで出力します。")

# 圧縮処理の関数
def compress_to_target(image, target_kb=500):
    # JPEG変換のためにRGBモードに統一
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    elif image.mode != "RGB":
        image = image.convert("RGB")
        
    # 初期リサイズ（スマホ写真は大きすぎるため、最大長辺を2000pxに制限して画質を保つ）
    max_dimension = 2000
    if max(image.size) > max_dimension:
        image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    
    # 1. まずは画質（Quality）を調整して500kB以下を目指す
    quality = 90
    while quality >= 30:
        out_io = io.BytesIO()
        image.save(out_io, format="JPEG", quality=quality)
        size_kb = out_io.tell() / 1024
        if size_kb <= target_kb:
            return out_io.getvalue(), size_kb
        quality -= 5  # 画質を少しずつ下げる

    # 2. 画質を下げても500kBを超えてしまう場合、解像度（サイズ）を徐々に小さくする
    width, height = image.size
    while size_kb > target_kb and width > 300:
        width = int(width * 0.9)
        height = int(height * 0.9)
        image = image.resize((width, height), Image.Resampling.LANCZOS)
        
        out_io = io.BytesIO()
        image.save(out_io, format="JPEG", quality=65)
        size_kb = out_io.tell() / 1024
        if size_kb <= target_kb:
            return out_io.getvalue(), size_kb

    return out_io.getvalue(), size_kb

# ファイルアップローダー（複数選択可能）
uploaded_files = st.file_uploader(
    "画像をアップロード（複数まとめて選択できます）", 
    type=["jpg", "jpeg", "png", "heic"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.write(f"--- 処理中: {len(uploaded_files)}枚の画像 ---")
    
    # メモリ上にZIPファイルを作成する準備
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for uploaded_file in uploaded_files:
            try:
                # 画像を開く
                img = Image.open(uploaded_file)
                
                # 圧縮処理を実行
                compressed_bytes, final_size = compress_to_target(img)
                
                # 元のファイル名から拡張子を変更してJPEGにする
                original_name = uploaded_file.name
                base_name = original_name.rsplit(".", 1)[0]
                new_filename = f"{base_name}_compressed.jpg"
                
                # ZIPファイルに追加
                zip_file.writestr(new_filename, compressed_bytes)
                
                # 画面に進捗を表示
                st.success(f"✅ 成功: {original_name} ➔ {final_size:.1f} kB")
                
            except Exception as e:
                st.error(f"❌ エラー ({uploaded_file.name}): {e}")
                
    st.write("---")
    
    # ダウンロードボタンの設置
    zip_buffer.seek(0)
    st.download_button(
        label="🎁 圧縮した画像をまとめてダウンロード (ZIP)",
        data=zip_buffer,
        file_name="compressed_images.zip",
        mime="application/zip",
        use_container_width=True
    )