import streamlit as st
from PIL import Image
import pillow_heif
import io
import zipfile

# iPhoneのHEIC形式を読み込めるようにする設定
pillow_heif.register_heif_opener()

# ページ設定（タブのアイコンとレイアウト）
st.set_page_config(page_title="画像一括軽量化ツール", page_icon="✨", layout="centered")

# --- UIヘッダー ---
st.title("✨ Image Resizer & Compressor")
st.markdown("スマホやiPadの高画質な写真を、**画質と縦横比を保ちながら**サクッと指定サイズに圧縮します。")

st.divider() # 区切り線

# --- 設定エリア（カラムを使ってカッコよく配置） ---
st.subheader("⚙️ 圧縮設定")
col1, col2 = st.columns([3, 1])
with col1:
    # スライダーで500kB以外のサイズも設定可能に
    target_kb = st.slider(
        "目標の最大サイズ（kB）", 
        min_value=100, 
        max_value=3000, 
        value=500, 
        step=100,
        help="数値を小さくすると軽くなりますが、画質が下がる場合があります。"
    )
with col2:
    # 現在の目標値を強調表示
    st.info(f"目標サイズ:\n### {target_kb} kB")

st.divider()

# 圧縮処理の関数（引数にtarget_kbを追加して連動）
def compress_to_target(image, target_kb):
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    elif image.mode != "RGB":
        image = image.convert("RGB")
        
    max_dimension = 2000
    if max(image.size) > max_dimension:
        image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    
    quality = 90
    while quality >= 30:
        out_io = io.BytesIO()
        image.save(out_io, format="JPEG", quality=quality)
        size_kb = out_io.tell() / 1024
        if size_kb <= target_kb:
            return out_io.getvalue(), size_kb
        quality -= 5

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

# --- メインエリア：ファイルアップロード ---
st.subheader("📂 画像のアップロード")
uploaded_files = st.file_uploader(
    "ここをクリックするか、画像をドラッグ＆ドロップしてください（複数選択可）", 
    type=["jpg", "jpeg", "png", "heic"], 
    accept_multiple_files=True
)

# --- 処理と結果表示エリア ---
if uploaded_files:
    st.subheader("🚀 処理ステータス")
    
    # プログレスバー（進行状況バー）の設置
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    zip_buffer = io.BytesIO()
    total_original_size = 0
    total_compressed_size = 0
    success_details = []
    
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for i, uploaded_file in enumerate(uploaded_files):
            # ステータス文字の更新
            status_text.text(f"処理中... {i+1} / {len(uploaded_files)} 枚 ({uploaded_file.name})")
            
            # 元サイズの記録
            original_size_kb = uploaded_file.size / 1024
            total_original_size += original_size_kb
            
            # 画像を開いて圧縮
            img = Image.open(uploaded_file)
            compressed_bytes, final_size = compress_to_target(img, target_kb)
            total_compressed_size += final_size
            
            # ZIPに追加
            original_name = uploaded_file.name
            base_name = original_name.rsplit(".", 1)[0]
            new_filename = f"{base_name}_compressed.jpg"
            zip_file.writestr(new_filename, compressed_bytes)
            
            # 詳細ログの追加
            success_details.append(f"✅ {original_name} : {original_size_kb:.1f} kB ➔ **{final_size:.1f} kB**")
            
            # プログレスバーの更新
            progress_bar.progress((i + 1) / len(uploaded_files))
            
    status_text.success("✨ すべての画像の圧縮が完了しました！")
    
    # --- 結果のサマリー（カッコいいダッシュボード風） ---
    st.divider()
    st.subheader("📊 圧縮結果サマリー")
    
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("処理枚数", f"{len(uploaded_files)} 枚")
    with m2:
        st.metric("元の合計サイズ", f"{total_original_size / 1024:.2f} MB")
    with m3:
        # 削減率の計算
        if total_original_size > 0:
            reduction_ratio = (1 - (total_compressed_size / total_original_size)) * 100
            delta_str = f"-{reduction_ratio:.1f}%"
        else:
            delta_str = "0%"
        
        # delta_color="inverse" でマイナス（削減）を緑色で表示
        st.metric("圧縮後の合計サイズ", f"{total_compressed_size / 1024:.2f} MB", delta_str, delta_color="inverse")
        
    # 画面が長くなるのを防ぐため、詳細はアコーディオン（折りたたみ）に格納
    with st.expander("詳細な処理結果を見る"):
        for detail in success_details:
            st.markdown(detail)
            
    # --- ダウンロードボタン ---
    st.divider()
    zip_buffer.seek(0)
    st.download_button(
        label="🎁 圧縮した画像をまとめてダウンロード (ZIP)",
        data=zip_buffer,
        file_name="compressed_images.zip",
        mime="application/zip",
        use_container_width=True,
        type="primary"  # ボタンをメインカラーにして目立たせる
    )