
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
    pw = st.text_input("Introduce la contraseña para acceder", type="password")
    if pw == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    else:
        st.stop()

client = OpenAI()

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Convertir vídeo en texto")
st.title("📝 Conversor de vídeo a texto para SMN")

PROMPTS = {
    "Valencia Secreta": "Prompt Valencia Secreta...",
    "Barcelona Secreta": "Prompt Barcelona Secreta...",
    "V2 Valencia Secreta": "Prompt V2 Valencia Secreta..."
}

EDITORS = {
    "Álvaro Llagunes": "Te llamas Álvaro Llagunes, eres un redactor en Secret Media Network con formación en Periodismo y Cine Documental con muchos años de experiencia y escribes actualmente en varios sitios web. "
}

video_file = st.file_uploader("Sube un vídeo (.mp4, .mov, .avi...):", type=None)

if video_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(video_file.name).suffix) as tmp:
        tmp.write(video_file.read())
        tmp_path = tmp.name

    file_size = os.path.getsize(tmp_path)
    st.info(f"Tamaño del archivo: {file_size} bytes")

    if file_size == 0:
        st.error("❌ El archivo está vacío. Por favor, sube un vídeo con audio.")
        st.stop()

    mime_type, _ = mimetypes.guess_type(tmp_path)
    if not mime_type:
        mime_type = "video/mp4"

    site = st.selectbox("¿Para qué site es este artículo?", ["Selecciona...", *PROMPTS.keys()])

    if site != "Selecciona...":
        editor = st.selectbox("¿Quién es el editor del contenido?", ["Ningun@", *EDITORS.keys()])

        if editor:
            extra_prompt = st.text_area("¿Quieres añadir instrucciones adicionales al prompt? (opcional)")

            if st.button("🎬 Generar artículo"):
                try:
                    with st.spinner("⏳ Transcribiendo vídeo con Whisper..."):
                        with open(tmp_path, "rb") as audio_file:
                            transcript_response = client.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio_file,
                                filename=Path(tmp_path).name,
                                file_content_type=mime_type,
                                response_format="json"
                            )
                        transcription = transcript_response.text

                    st.success("✅ Transcripción completada")
                    st.text_area("Texto transcrito:", transcription, height=200)

                    full_prompt = PROMPTS[site]
                    if editor != "Ningun@":
                        full_prompt += "\n\nContexto del editor:\n" + EDITORS[editor]
                    full_prompt += "\n\nTranscripción:\n" + transcription
                    if extra_prompt:
                        full_prompt += "\n\nInstrucciones adicionales del editor:\n" + extra_prompt

                    with st.spinner("🧠 Generando artículo con ChatGPT..."):
                        chat_response = client.chat.completions.create(
                            model="gpt-4",
                            messages=[
                                {"role": "system", "content": "Eres un redactor profesional especializado en contenido local."},
                                {"role": "user", "content": full_prompt}
                            ],
                            temperature=0.7
                        )
                        article = chat_response.choices[0].message.content

                    st.success("✅ Artículo generado")
                    st.subheader("🔎 Vista previa del artículo")
                    st.markdown(article, unsafe_allow_html=True)

                    st.subheader("📋 Código Markdown")
                    st.code(article)

                    st.download_button("⬇️ Descargar como HTML", data=article, file_name="articulo.html", mime="text/html")
                    st.button("📋 Copiar artículo", on_click=lambda: st.toast("Texto copiado (usa Ctrl+C en el área Markdown)", icon="✅"))

                except Exception as e:
                    st.error(f"❌ Error al procesar el archivo: {str(e)}")
                finally:
                    os.remove(tmp_path)
