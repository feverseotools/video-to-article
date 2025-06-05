
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
    pw = st.text_input("Introduce la contraseña para acceder (v05/06/2025 16:32)", type="password")
    if pw == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    else:
        st.stop()

client = OpenAI()

st.set_page_config(page_title="Convertir vídeo en texto")
st.title("📝 Conversor de vídeo a texto para SMN")

from prompts import PROMPTS
from editors import EDITORS

video_file = st.file_uploader("Sube un vídeo (.mp4, .mov, .avi...):", type=None)

if video_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(video_file.name).suffix) as tmp:
        tmp.write(video_file.read())
        tmp_path = tmp.name

    mime_type, _ = mimetypes.guess_type(tmp_path)
    if not mime_type:
        mime_type = "video/mp4"

    editor = st.selectbox("¿Quién es el editor del contenido?", ["Ningun@", *EDITORS.keys()])
    site = st.selectbox("¿Para qué site es este artículo?", ["Selecciona...", "Valencia Secreta", "Barcelona Secreta"])

    if site != "Selecciona...":
        extra_prompt = st.text_area("¿Quieres añadir instrucciones adicionales al prompt? (opcional)")
        if st.button("✍️ Generar artículo"):
            try:
                with st.spinner("⏳ Transcribiendo vídeo con Whisper..."):
                    with open(tmp_path, "rb") as audio_file:
                        transcript_response = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
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
                    article_response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "Eres un redactor profesional especializado en contenido local."},
                            {"role": "user", "content": full_prompt}
                        ],
                        temperature=0.7
                    )
                    article = article_response.choices[0].message.content

                st.success("✅ Artículo generado")

                st.subheader("🏷 Secondary title (subtítulo del artículo)")
                secondary_title = article.split("\n")[0].strip("# ").strip()
                st.text_input("Subtítulo sugerido:", value=secondary_title)

                st.subheader("🔎 Vista previa del artículo")
                st.markdown(article, unsafe_allow_html=True)

                st.subheader("✨ Posibles titulares para Google Discover")
                with st.spinner("🧠 Generando titulares..."):
                    discover_instructions = (
                        "A partir del siguiente artículo, genera 5 titulares optimizados para Google Discover. "
                        "Ten en cuenta las siguientes instrucciones:\n\n"
                        "Un artículo optimizado para Google Discover debe presentar un enfoque temático claro y alineado "
                        "con intereses actuales o de tendencia, utilizando un titular con fuerte carga emocional que despierte "
                        "curiosidad, urgencia o empatía, e incluya entidades reconocibles como nombres de ciudades, celebridades, "
                        "marcas o términos sociales y económicos. El título debe usar lenguaje natural, incorporar adjetivos potentes, "
                        "evitar fórmulas neutras o meramente SEO, y, siempre que sea posible, incluir citas textuales que aumenten el CTR."
                    )
                    discover_prompt = discover_instructions + "\n\nArtículo:\n" + article
                    discover_response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "Eres un experto en redacción de titulares optimizados para Google Discover."},
                            {"role": "user", "content": discover_prompt}
                        ],
                        temperature=0.7
                    )
                    st.markdown(discover_response.choices[0].message.content)

                st.subheader("💻 Código HTML")
                st.code(article, language="html")

                st.subheader("📋 Código Markdown")
                st.code(article)

                st.download_button("⬇️ Descargar como HTML", data=article, file_name="articulo.html", mime="text/html")
                st.button("📋 Copiar artículo", on_click=lambda: st.toast("Texto copiado (usa Ctrl+C en el área Markdown)", icon="✅"))

            except Exception as e:
                st.error(f"❌ Error al procesar el archivo: {str(e)}")
            finally:
                os.remove(tmp_path)