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
    pw = st.text_input("Enter your super-ultra secret password (v18/06/2025 10:30h)", type="password")
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

uploaded_file = st.file_uploader("Upload a video or an image", type=["mp4", "mov", "avi", "jpg", "jpeg", "png"])

is_image = False
is_video = False
image_description = ""

if uploaded_file:
    file_suffix = Path(uploaded_file.name).suffix.lower()
    is_image = file_suffix in [".jpg", ".jpeg", ".png"]
    is_video = file_suffix in [".mp4", ".mov", ".avi"]

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    if is_image:
        st.info("🖼 Image uploaded. Generating description with GPT-4 Vision...")

        import base64
        from PIL import Image

        image = Image.open(tmp_path)
        with open(tmp_path, "rb") as img_file:
            image_bytes = img_file.read()
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        vision_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image in detail, including key elements, ambiance, colors, people, objects, and context."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        },
                    ],
                }
            ],
            max_tokens=800
        )
        image_description = vision_response.choices[0].message.content
        st.success("✅ Image description generated.")
        st.text_area("📝 Description of the image:", image_description, height=200)

    elif is_video:
        st.session_state["is_video"] = True
    else:
        st.error("❌ Unsupported file type.")


    editor = st.selectbox("Who is the editor of the article?", ["Select...", *editors.keys()])
    site = st.selectbox("Where will be this article published?", ["Select...", *sites.keys()])
    category = st.selectbox("Select the type of content:", ["Select category...", "Gastronomy (restaurants, bars, street food)", "Sports for Secret Media", "Housing situation in big cities", "Generic (use with caution)"])
    language = st.selectbox("Select language for article output:", ["Select language...", *languages.keys()])


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
