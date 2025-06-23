from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
import streamlit as st
import tempfile
import os
from pathlib import Path
import mimetypes

# --- AUTENTICACIÓN SIMPLE ---
PASSWORD = "SECRETMEDIA"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if not st.session_state.authenticated:
    pw = st.text_input("Enter your super-ultra secret password (v23/06/2025 16:16h)", type="password")
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
if upload_type == "Video":
    video_file = st.file_uploader(
        "Upload your video (.mp4, .mov, .avi, .mp3, .wav, .ogg, .webm):",
        type=["mp4", "mov", "avi", "mpeg", "mp3", "wav", "ogg", "webm"]
    )
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
    import base64
    if "image_description" not in st.session_state:
        image_bytes = image_file.read()
        if image_bytes:
            b64_image = base64.b64encode(image_bytes).decode("utf-8")
            st.session_state.b64_image = b64_image
            with st.spinner("🧠 Analyzing image with GPT-4o."):
                try:
                    vision_response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "Describe this image in detail. Focus on visual details, place, objects, text if any."},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
                                ]
                            }
                        ],
                        max_tokens=800
                    )
                    st.session_state.image_description = vision_response.choices[0].message.content
                    st.success("✅ Image description generated")
                except Exception as e:
                    st.error(f"❌ Error during image analysis: {e}")
elif upload_type == "Image" and image_file is None:
    st.info("📸 Please upload an image to continue.")

if "image_description" in st.session_state:
    st.text_area("🖼 Description of the image:", st.session_state.image_description, height=200)

# --- CONFIGURACIÓN DEL ARTÍCULO ---
editor = st.selectbox("Who is the editor of the article?", ["Select...", *editors.keys()])
site = st.selectbox("Where will be this article published?", ["Select...", *sites.keys()])
category_key = st.selectbox("Select the type of content:", ["Select category...", *categories.keys()])
language_key = st.selectbox("Select language for article output:", ["Select language...", *languages.keys()])
extra_prompt = ""
if site != "Select...":
    extra_prompt = st.text_area("Any extra info for the prompt? (optional)")

# --- BOTÓN DE CREACIÓN DE ARTÍCULO ---
if st.button("✍️ Create article"):
    try:
        # 1. Obtener transcripción o descripción
        if upload_type == "Video":
            with st.spinner("⏳ Getting transcription of the video with Whisper..."):
                with open(tmp_path, "rb") as audio_file:
                    transcript_response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="json"
                    )
                transcription = transcript_response.text
            st.success("✅ Transcription completed")
            st.text_area("Text of the video:", transcription, height=200)

        elif upload_type == "Image" and "image_description" in st.session_state:
            transcription = st.session_state.image_description
            st.text_area("🖼 Description of the image:", transcription, height=200)
        else:
            st.error("❌ Por favor, sube un vídeo válido o espera a que se genere la descripción de la imagen.")
            st.stop()

        # 2. Construir el prompt completo
        full_prompt = sites[site]
        if editor != "Select...":
            full_prompt += "\n\nContexto del editor:\n" + editors[editor]
        full_prompt += "\n\nTranscripción:\n" + transcription

        if category_key != "Select category...":
            full_prompt += "\n\nContexto de la categoría:\n" + categories[category_key]

        if language_key != "Select language...":
            full_prompt += "\n\nIdioma del artículo:\n" + languages[language_key]

        if extra_prompt:
            full_prompt += "\n\nInstrucciones adicionales del editor:\n" + extra_prompt

        # 3. Generar artículo
        with st.spinner("🧠 Writing article with ChatGPT."):
            chat_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un redactor profesional especializado en contenido local."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.7
            )
        article = chat_response.choices[0].message.content

        # 4. Mostrar artículo y opciones adicionales
        word_count = len(article.split())
        st.info(f"📝 Word count: {word_count} words")
        st.success("✅ Article ready")
        st.subheader("🔎 Here is your article:")
        st.markdown(article, unsafe_allow_html=True)

        # Generar titulares para Google Discover
        st.subheader("📰 Headlines ideas Google Discover")
        with st.spinner("✨ Generating headlines for Google Discover."):
            discover_prompt = (
                "(Adapta el output al idioma del artículo) A partir del siguiente artículo, genera varias sugerencias de titulares siguiendo estas instrucciones:"  
                "... (instrucciones específicas)...\n\nArtículo:\n" + article
            )
            discover_response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": discover_prompt}]
            )
            st.markdown(discover_response.choices[0].message.content, unsafe_allow_html=True)

        # Mostrar código HTML y Markdown, y botón de descarga
        st.subheader("💻 HTML code")
        st.code(article, language='html')
        st.subheader("📋 Markdown code")
        st.code(article)
        st.download_button("⬇️ Download as HTML", data=article, file_name="articulo.html", mime="text/html")

        # Limpieza de archivo temporal si existe (solo en flujo de vídeo)
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)

        st.text_input("Press Ctrl+C to copy the article from here", value=article)

    except Exception as e:
        if "openai" in str(type(e)).lower():
            st.error(f"❌ OpenAI API error: {e}")
        elif isinstance(e, FileNotFoundError):
            st.error(f"❌ File not found error: {e}")
        else:
            st.error(f"❌ General error: {e}")

    finally:
        # Asegurar borrado de tmp_path solo si existe y es video
        try:
            if upload_type == "Video" and 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except NameError:
            pass
