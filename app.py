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
    pw = st.text_input("Enter your super-ultra secret password (v10/06/2025 10:49h)", type="password")
    if pw == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    else:
        st.stop()

client = OpenAI()

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Convert Video into Text")
st.title("📝 Video > Text AI Converter for SMN")

# --- CARGA DE PROMPTS EXTERNOS ---
def load_prompt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

sites = {
    "Valencia Secreta": load_prompt("prompts/sites/valencia_secreta.txt"),
    "Barcelona Secreta": load_prompt("prompts/sites/barcelona_secreta.txt"),
    "New York City": load_prompt("prompts/sites/nyc_secret.txt"),
    "EXPERIMENTAL JAKUB": load_prompt("prompts/sites/experimental.txt")
}

editors = {
    "Álvaro Llagunes": load_prompt("prompts/editors/alvaro_llagunes.txt"),
    "Jorge López Torrecilla": load_prompt("prompts/editors/jorge_lopez.txt"),
}

video_file = st.file_uploader("Upload your video (.mp4, .mov, .avi...):", type=None)

if video_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(video_file.name).suffix) as tmp:
        tmp.write(video_file.read())
        tmp_path = tmp.name

    file_size = os.path.getsize(tmp_path)
    st.info(f"File size: {file_size} bytes")

    if file_size == 0:
        st.error("❌ File is empty. Please, upload a video with audio.")
        st.stop()

    mime_type, _ = mimetypes.guess_type(tmp_path)
    if not mime_type:
        mime_type = "video/mp4"

    editor = st.selectbox("Who is the editor of the article?", ["Select...", *editors.keys()])
    site = st.selectbox("Where will be this article published?", ["Select...", *sites.keys()])

    if site != "Select...":
        extra_prompt = st.text_area("Any extra info for the prompt? (optional)")

if st.button("✍️ Create article"):
    try:
        with st.spinner("⏳ Getting transcription of the video with Whisper..."):
            with open(tmp_path, "rb") as audio_file:
                transcript_response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="json"
                )
            transcription = transcript_response.text

        st.success("✅ Transcription completed")

        # Word count
        word_count = len(article.split())
        st.info(f"📝 Word count: {word_count} words")


        st.text_area("Text of the video:", transcription, height=200)

        full_prompt = sites[site]
        if editor != "Select...":
            full_prompt += "\n\nContexto del editor:\n" + editors[editor]
        full_prompt += "\n\nTranscripción:\n" + transcription
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

        st.success("✅ Article ready")
        st.subheader("🔎 Here is your article:")
        st.markdown(article, unsafe_allow_html=True)

        st.subheader("📰 Headlines ideas Google Discover")
        with st.spinner("✨ Generating headlines for Google Discover..."):
            discover_prompt = (
                "(Adapta el output de este prompt al idioma en el que está el texto de la transcripción: si la transcripción está en español, escribe los titulares en español; si la transcripción está en inglés, escribe las ideas de titulares en inglés). A partir del siguiente artículo, genera varias sugerencias de titulares siguiendo estas instrucciones:"
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
        st.text_input("Press Ctrl+C to copy the article from here", value=article)

    except Exception as e:
        if "openai" in str(type(e)).lower():
            st.error(f"❌ OpenAI API error: {e}")
        elif isinstance(e, FileNotFoundError):
            st.error(f"❌ File not found error: {e}")
        else:
            st.error(f"❌ General error: {e}")
    finally:
        os.remove(tmp_path)
