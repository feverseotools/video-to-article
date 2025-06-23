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
# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="STAGING Convert Video into Text")
st.title("STAGING📝 Video > Text AI Converter for SMN")
# --- CARGA DE PROMPTS EXTERNOS ---
def load_prompt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()
# Where will be published the article? (site) We use this info to adjust the tone and the writing style of the article
sites = {
    "Valencia Secreta": load_prompt("prompts/sites/valencia_secreta.txt"),
    "Barcelona Secreta": load_prompt("prompts/sites/barcelona_secreta.txt"),
    "Madrid Secreto": load_prompt("prompts/sites/madrid_secreto.txt"),
    "New York City": load_prompt("prompts/sites/nyc_secret.txt"),
    "EXPERIMENTAL JAKUB": load_prompt("prompts/sites/experimental.txt")
}
# Who wil sign the article? (editor) We use this info to adjust the tone and the writing style of the article (more personal touch)
editors = {
    "Álvaro Llagunes": load_prompt("prompts/editors/alvaro_llagunes.txt"),
    "Jorge López Torrecilla": load_prompt("prompts/editors/jorge_lopez.txt"),
    "Alberto del Castillo": load_prompt("prompts/editors/alberto_del_castillo.txt"),
}
# Category selection to adjust the output of the article according to the type of content
category = {
    "Gastronomy (restaurants, bars, street food)": load_prompt("prompts/category/food.txt"),
    "Sports for Secret Media": load_prompt("prompts/category/sports-smn.txt"),
    "Housing situation in big cities": load_prompt("prompts/category/problemas-vivienda.txt"),
    "Generic (use with caution)": load_prompt("prompts/category/generic.txt"),
}
# Languages
languages = {
    "English for US": load_prompt("prompts/languages/en-us.txt"),
    "Español para España": load_prompt("prompts/languages/es-sp.txt"),
}
upload_type = st.radio("What do you want to upload?", ["Video", "Image"], horizontal=True)
video_file = None
image_file = None
if upload_type == "Video":
    video_file = st.file_uploader("Upload your video (.mp4, .mov, .avi...):", type=["mp4", "mov", "avi", "mpeg", "mp3", "wav", "ogg", "webm"])
elif upload_type == "Image":
    image_file = st.file_uploader("Upload an image (.jpg, .jpeg, .png):", type=["jpg", "jpeg", "png"])
if video_file:
    # Asegurarte de que el código aquí solo procese vídeo
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(video_file.name).suffix) as tmp:
        tmp.write(video_file.read())
        tmp_path = tmp.name
    file_size = os.path.getsize(tmp_path)
    st.info(f"File size: {file_size} bytes")
    if image_file is not None and image_file.size == 0:
     if image_file.size == 0:
        st.error("⚠️ Uploaded image is empty.")
        st.stop()
    mime_type, _ = mimetypes.guess_type(tmp_path)
    if not mime_type or not mime_type.startswith("video") and not mime_type.startswith("audio"):
        st.error("❌ Invalid file format for Whisper. Please upload a supported video or audio file.")
        st.stop()
    if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
    # Aquí sigue la lógica del flujo de creación de artículos por transcripción (como ya tienes en tu código)
elif image_file:
    import base64
    if "image_description" not in st.session_state:
        image_bytes = image_file.read()
        if image_bytes:
            b64_image = base64.b64encode(image_bytes).decode("utf-8")
            st.session_state.b64_image = b64_image
            with st.spinner("🧠 Analyzing image with GPT-4o..."):
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
    transcription = st.session_state.image_description
    st.text_area("🖼 Description of the image:", transcription, height=200)
editor = st.selectbox("Who is the editor of the article?", ["Select...", *editors.keys()])
site = st.selectbox("Where will be this article published?", ["Select...", *sites.keys()])
category = st.selectbox("Select the type of content:", ["Select category...", "Gastronomy (restaurants, bars, street food)", "Sports for Secret Media", "Housing situation in big cities", "Generic (use with caution)"])
language = st.selectbox("Select language for article output:", ["Select language...", *languages.keys()])
if site != "Select...":
    extra_prompt = st.text_area("Any extra info for the prompt? (optional)")
if st.button("✍️ Create article"):
    try:
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
        full_prompt = sites[site]
        if editor != "Select...":
            full_prompt += "\n\nContexto del editor:\n" + editors[editor]
        full_prompt += "\n\nTranscripción:\n" + transcription
        if category == "Gastronomy (restaurants, bars, street food)":
            category_prompt = load_prompt("prompts/category/food.txt")
            full_prompt += "\n\nContexto de la categoría:\n" + category_prompt
        if category == "Sports for Secret Media":
            category_prompt = load_prompt("prompts/category/sports-smn.txt")
            full_prompt += "\n\nContexto de la categoría:\n" + category_prompt
        if category == "Housing situation in big cities":
            category_prompt = load_prompt("prompts/category/problemas-vivienda.txt")
            full_prompt += "\n\nContexto de la categoría:\n" + category_prompt
        if category == "Generic (use with caution)":
            category_prompt = load_prompt("prompts/category/generic.txt")
            full_prompt += "\n\nContexto de la categoría:\n" + category_prompt
        if language == "English (United States)":
            language_prompt = load_prompt("prompts/languages/en-us.txt")
            full_prompt += "\n\nIdioma del artículo:\n" + language_prompt
        if language == "Español (España)":
            language_prompt = load_prompt("prompts/languages/es-sp.txt")
            full_prompt += "\n\nIdioma del artículo:\n" + language_prompt
        if extra_prompt:
            full_prompt += "\n\nInstrucciones adicionales del editor:\n" + extra_prompt
        with st.spinner("🧠 Writing article with ChatGPT..."):
            chat_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un redactor profesional especializado en contenido local."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.7
            )
        article = chat_response.choices[0].message.content
        # ✅ Word count (calculated after article is generated)
        word_count = len(article.split())
        st.info(f"📝 Word count: {word_count} words")
        st.success("✅ Article ready")
        st.subheader("🔎 Here is your article:")
        st.markdown(article, unsafe_allow_html=True)
        st.subheader("📰 Headlines ideas Google Discover")
        with st.spinner("✨ Generating headlines for Google Discover..."):
            discover_prompt = (
                "(Adapta el output de este prompt al idioma en el que está el texto del artículo final (el idioma que el editor ha seleccionado como idioma del artículo): si el contenido está en español, escribe los titulares en español; si el contenido está en inglés, escribe las ideas de titulares en inglés). A partir del siguiente artículo, genera varias sugerencias de titulares siguiendo estas instrucciones:"
                "\n\nUn artículo optimizado para Google Discover debe presentar un enfoque temático claro y alineado "
                "con intereses actuales o de tendencia, utilizando un titular con fuerte carga emocional que despierte curiosidad, "
                "urgencia o empatía, e incluya entidades reconocibles como nombres de ciudades, celebridades, marcas o términos sociales "
                "y económicos. El título debe usar lenguaje natural, incorporar adjetivos potentes, evitar fórmulas neutras o meramente SEO, "
                "y, siempre que sea posible, incluir citas textuales que aumenten el CTR.\n\nArtículo:\n" + article
            )
            discover_response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": discover_prompt}]
            )
            st.markdown(discover_response.choices[0].message.content, unsafe_allow_html=True)
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
        if upload_type == "Video":
            try:
                if tmp_path:
                    os.remove(tmp_path)
            except NameError:
                pass
            