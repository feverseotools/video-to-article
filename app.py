from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
import streamlit as st
import tempfile
import os
from pathlib import Path
import mimetypes
import subprocess
import glob
import base64

# --- AUTENTICACIÓN SIMPLE ---
PASSWORD = "SECRETMEDIA"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if not st.session_state.authenticated:
    pw = st.text_input("Enter your super-ultra secret password (v24/06/2025 09:33h)", type="password")
    if pw == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    else:
        st.stop()

client = OpenAI()

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="STAGING Convert Video into Text")
st.title("STAGING📝 Video > Text AI Converter for SMN")

# --- CARGA DE PROMPTS EXTERNOS ---
def load_prompt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

sites = {
    "Valencia Secreta": load_prompt("prompts/sites/valencia_secreta.txt"),
    "Barcelona Secreta": load_prompt("prompts/sites/barcelona_secreta.txt"),
    "Madrid Secreto": load_prompt("prompts/sites/madrid_secreto.txt"),
    "New York City": load_prompt("prompts/sites/nyc_secret.txt"),
    "EXPERIMENTAL JAKUB": load_prompt("prompts/sites/experimental.txt")
}

editors = {
    "Álvaro Llagunes": load_prompt("prompts/editors/alvaro_llagunes.txt"),
    "Jorge López Torrecilla": load_prompt("prompts/editors/jorge_lopez.txt"),
    "Alberto del Castillo": load_prompt("prompts/editors/alberto_del_castillo.txt"),
}

categories = {
    "Gastronomy (restaurants, bars, street food)": load_prompt("prompts/category/food.txt"),
    "Sports for Secret Media": load_prompt("prompts/category/sports-smn.txt"),
    "Housing situation in big cities": load_prompt("prompts/category/problemas-vivienda.txt"),
    "Generic (use with caution)": load_prompt("prompts/category/generic.txt"),
}

languages = {
    "English for US": load_prompt("prompts/languages/en-us.txt"),
    "Español para España": load_prompt("prompts/languages/es-sp.txt"),
}

# --- SELECCIÓN DE TIPO DE SUBIDA ---
upload_type = st.radio("What do you want to upload?", ["Video", "Image"], horizontal=True)
video_file = None
image_file = None
is_smn_video = True
visual_analysis = False
frame_interval = 1

if upload_type == "Video":
    video_file = st.file_uploader(
        "Upload your video (.mp4, .mov, .avi, .mp3, .wav, .ogg, .webm):",
        type=["mp4", "mov", "avi", "mpeg", "mp3", "wav", "ogg", "webm"]
    )
    # Indicar si es SMN propio
    is_smn = st.radio("Is this an SMN-owned video?", ["Yes", "No"], horizontal=True, key="is_smn")
    is_smn_video = is_smn == "Yes"
    # Opción de análisis visual
    visual_analysis = st.checkbox("Enable frame-by-frame visual analysis", key="visual_analysis")
    if visual_analysis:
        frame_interval = st.slider("Extract one frame every N seconds", min_value=1, max_value=10, value=1, key="frame_interval")
elif upload_type == "Image":
    image_file = st.file_uploader(
        "Upload an image (.jpg, .jpeg, .png):",
        type=["jpg", "jpeg", "png"]
    )

# --- PROCESAMIENTO DE VÍDEO ---
if video_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(video_file.name).suffix) as tmp:
        tmp.write(video_file.read())
        tmp_path = tmp.name
    file_size = os.path.getsize(tmp_path)
    st.info(f"File size: {file_size} bytes")
    mime_type, _ = mimetypes.guess_type(tmp_path)
    if not mime_type or not (mime_type.startswith("video") or mime_type.startswith("audio")):
        st.error("❌ Invalid file format for Whisper. Please upload a supported video or audio file.")
        os.remove(tmp_path)
        st.stop()

# --- PROCESAMIENTO DE IMAGEN ---
elif image_file:
    if "image_description" not in st.session_state:
        image_bytes = image_file.read()
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        st.session_state.b64_image = b64_image
        with st.spinner("🧠 Analyzing image with GPT-4o..."):
            vision_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": "Describe this image in detail. Focus on visual details, place, objects, text if any."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
                    ]}
                ],
                max_tokens=800
            )
        st.session_state.image_description = vision_response.choices[0].message.content
        st.success("✅ Image description generated")
elif upload_type == "Image":
    st.info("📸 Please upload an image to continue.")

# --- PREVIEW DE DESCRIPCIÓN DE IMAGEN ---
if "image_description" in st.session_state:
    st.text_area("🖼 Description of the image:", st.session_state.image_description, height=200, key="image_desc_preview")

# --- METADATOS PARA VÍDEOS NO SMN ---
tmp_extra_video = ""
network = username = original_url = ""
if upload_type == "Video" and not is_smn_video and video_file:
    network = st.selectbox("Social network:", ["YouTube", "TikTok", "Instagram", "Facebook", "Twitter", "Other"], key="video_network")
    username = st.text_input("Account (example: @user123):", key="video_username")
    original_url = st.text_input("URL of the video:", key="video_url")
    tmp_extra_video = st.text_area("(Optional) Extra instructions for this non-SMN video (use as much context as you want):", height=100, key="extra_video_prompt")

# --- CONFIGURACIÓN DEL ARTÍCULO ---
editor = st.selectbox("Editor:", ["Select...", *editors.keys()])
site = st.selectbox("Publish site:", ["Select...", *sites.keys()])
category_key = st.selectbox("Content category:", ["Select...", *categories.keys()])
language_key = st.selectbox("Output language:", ["Select...", *languages.keys()])
extra_prompt = ""
if site != "Select...":
    extra_prompt = st.text_area("Additional editor instructions (optional):")

# --- GENERAR ARTÍCULO ---
if st.button("✍️ Create article"):
    try:
        # 1. Transcripción y análisis visual opcional
        if upload_type == "Video":
            transcription = ""
            visual_context = ""
            # Visual analysis
            if visual_analysis:
                frame_dir = tempfile.mkdtemp()
                subprocess.run([
                    "ffmpeg", "-i", tmp_path,
                    "-vf", f"fps=1/{frame_interval}",
                    os.path.join(frame_dir, "frame_%04d.jpg")
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                for img_path in sorted(glob.glob(os.path.join(frame_dir, "frame_*.jpg"))):
                    with open(img_path, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode("utf-8")
                    resp = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "user", "content": [
                                {"type": "text", "text": "Describe visual elements in this frame."},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                            ]}
                        ],
                        max_tokens=150
                    )
                    visual_context += resp.choices[0].message.content + "\n"
                for file in glob.glob(os.path.join(frame_dir, "*.jpg")):
                    os.remove(file)
                os.rmdir(frame_dir)
            # Whisper transcription
            with st.spinner("⏳ Transcribing audio with Whisper..."):
                with open(tmp_path, "rb") as audio_f:
                    tr = client.audio.transcriptions.create(
                        model="whisper-1", file=audio_f, response_format="json"
                    )
                transcription = tr.text
            st.success("✅ Transcription completed")
            st.text_area("Transcribed text:", transcription, height=200, key="video_text")
            if visual_analysis:
                st.text_area("Visual context:", visual_context, height=200, key="visual_context")
        elif upload_type == "Image" and "image_description" in st.session_state:
            transcription = st.session_state.image_description
            st.text_area("Image description:", transcription, height=200, key="image_text_area")
        else:
            st.error("❌ Upload a valid video or wait for image description.")
            st.stop()

        # 2. Construir prompt
        full_prompt = sites[site]
        if editor != "Select...": full_prompt += "\n\nEditor context:\n" + editors[editor]
        full_prompt += "\n\nTranscription for article:\n" + transcription
        if upload_type == "Video" and not is_smn_video:
            full_prompt += "\n\nNon-SMN video instructions:\n" + tmp_extra_video
            full_prompt += f"\nSource network: {network}"
            full_prompt += f"\nOriginal account: {username}"
            full_prompt += f"\nOriginal URL: {original_url}"
        if upload_type == "Video" and visual_analysis:
            full_prompt += "\n\nExtracted visual context:\n" + visual_context
        if category_key != "Select...": full_prompt += "\n\nCategory context:\n" + categories[category_key]
        if language_key != "Select...": full_prompt += "\n\nLanguage for article:\n" + languages[language_key]
        if extra_prompt: full_prompt += "\n\nAdditional editor instructions:\n" + extra_prompt

        # 3. Generar artículo
        with st.spinner("🧠 Generating article..."):
            resp = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un redactor profesional..."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.7
            )
        article = resp.choices[0].message.content

        # 4. Mostrar artículo y opciones
        st.info(f"📝 Words: {len(article.split())}")
        st.success("✅ Article ready")
        st.subheader("🔎 Article:")
        st.markdown(article, unsafe_allow_html=True)
        # ... Discover, HTML/MD preview, download button replicate as before ...

    except Exception as e:
        st.error(f"❌ Error: {e}")

    finally:
        if upload_type == "Video" and 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
