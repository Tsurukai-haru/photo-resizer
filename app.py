import streamlit as st
from PIL import Image
import pillow_heif
import io
import zipfile

pillow_heif.register_heif_opener()

st.set_page_config(page_title="画像一括軽量化ツール", layout="centered")

custom_css = """
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<style>
.stApp {
    background: linear-gradient(135deg, #fce4ec 0%, #e8eaf6 50%, #e3f2fd 100%);
}

.stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3 {
    color: #333344;
    font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', sans-serif;
}

[data-testid="stMetric"] {
    background-color: rgba(255, 255, 255, 0.7);
    border-radius: 20px;
    padding: 15px 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.5);
}

div.stButton > button {
    background: linear-gradient(90deg, #8ec5fc 0%, #e0c3fc 100%);
    color: white;
    border: none;
    border-radius: 30px;
    padding: 10px 24px;
    font-weight: bold;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    transition: all 0.3s ease;
}
div.stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(142, 197, 252, 0.4);
    color: white;
}

[data-testid="stFileUploader"] {
    background-color: rgba(255, 255, 255, 0.6);
    border-radius: 20px;
    padding: 10px;
    border: 2px dashed #b2ccff;
}

hr {
    border-bottom-color: rgba(0,0,0,0.05);
}

.app-title {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 0.25rem;
}
.app-title i { color: #7aabda; }

.section-heading {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0.5rem 0 1rem;
}
.section-heading i { color: #7aabda; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


st.markdown(
    '<div class="app-title"><i class="fa-solid fa-camera"></i> Photo Compression Tool</div>',
    unsafe_allow_html=True
)
st.markdown("スマホの高画質な写真を、**画質と縦横比を保ちながら**指定サイズに圧縮します。")

st.divider()

st.markdown(
    '<div class="section-heading"><i class="fa-solid fa-sliders"></i> 圧縮設定</div>',
    unsafe_allow_html=True
)
col1, col2 = st.columns([3, 1])
with col1:
    target_kb = st.slider(
        "目標の最大サイズ（kB）",
        min_value=100,
        max_value=3000,
        value=500,
        step=100
    )
with col2:
    st.info(f"目標サイズ:\n### {target_kb} kB")

st.divider()


def compress_to_target(image, target_kb):
    if image.mode != "RGB":
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


st.markdown(
    '<div class="section-heading"><i class="fa-solid fa-cloud-arrow-up"></i> 画像のアップロード</div>',
    unsafe_allow_html=True
)
uploaded_files = st.file_uploader(
    "ここをクリックするか、画像をドラッグ＆ドロップしてください",
    type=["jpg", "jpeg", "png", "heic"],
    accept_multiple_files=True
)

if uploaded_files:
    st.markdown(
        '<div class="section-heading"><i class="fa-solid fa-hourglass-half"></i> 処理ステータス</div>',
        unsafe_allow_html=True
    )

    progress_bar = st.progress(0)
    status_text = st.empty()

    zip_buffer = io.BytesIO()
    total_original_size = 0
    total_compressed_size = 0
    success_details = []

    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"処理中... {i+1} / {len(uploaded_files)} 枚")

            original_size_kb = uploaded_file.size / 1024
            total_original_size += original_size_kb

            img = Image.open(uploaded_file)
            compressed_bytes, final_size = compress_to_target(img, target_kb)
            total_compressed_size += final_size

            base_name = uploaded_file.name.rsplit(".", 1)[0]
            new_filename = f"{base_name}_compressed.jpg"
            zip_file.writestr(new_filename, compressed_bytes)

            success_details.append(f"{uploaded_file.name} : {original_size_kb:.1f} kB → **{final_size:.1f} kB**")
            progress_bar.progress((i + 1) / len(uploaded_files))

    status_text.success("すべての画像の圧縮が完了しました。")

    st.divider()
    st.markdown(
        '<div class="section-heading"><i class="fa-solid fa-chart-bar"></i> 圧縮結果</div>',
        unsafe_allow_html=True
    )

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("処理枚数", f"{len(uploaded_files)} 枚")
    with m2:
        st.metric("元の合計サイズ", f"{total_original_size / 1024:.2f} MB")
    with m3:
        if total_original_size > 0:
            reduction_ratio = (1 - (total_compressed_size / total_original_size)) * 100
            delta_str = f"-{reduction_ratio:.1f}%"
        else:
            delta_str = "0%"
        st.metric("圧縮後の合計サイズ", f"{total_compressed_size / 1024:.2f} MB", delta_str, delta_color="inverse")

    with st.expander("詳細な処理結果を見る"):
        for detail in success_details:
            st.markdown(detail)

    st.divider()
    zip_buffer.seek(0)
    st.download_button(
        label="圧縮した画像をまとめてダウンロード (ZIP)",
        data=zip_buffer,
        file_name="compressed_images.zip",
        mime="application/zip",
        use_container_width=True
    )
