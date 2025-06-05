
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
    pw = st.text_input("Introduce la contraseña para acceder (v.05.06.2025 15.17)", type="password")
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
    "Valencia Secreta": """Tono informal, cercano y optimista, como si hablaras directamente al lector.

Introducción breve que conecta emocionalmente o con alguna referencia cultural o estacional (por ejemplo: “Llega el otoño…”, “¿Quién no querría volver a la infancia?”).

Usa titulares H2 para separar secciones principales.

Dentro de cada H2, emplea subtítulos H3 cuando haya múltiples elementos (por ejemplo, una lista de lugares, fechas o actividades).

Utiliza listas con emojis o viñetas si aporta dinamismo.

Siempre que sea útil, incluye una sección de "Información práctica" con iconos tipo 📍, 📅, ⏰, 💸.

Destaca ideas importantes con negritas, especialmente fechas, nombres propios, ubicaciones y frases clave.

Menciona a menudo actividades relacionadas o recomendaciones extra con frases como “Quizás te interesa…” o “También puedes aprovechar para…”.

Incluye referencias culturales locales cuando sea posible (costumbres, barrios, expresiones como "esmorzaret").

Finaliza con una llamada a la acción suave o invitación a disfrutar de la experiencia.""",

    "Barcelona Secreta": """Tono informal, cercano y optimista, como si hablaras directamente al lector.

Introducción breve que conecta emocionalmente o con alguna referencia cultural o estacional (por ejemplo: “Llega el otoño…”, “¿Quién no querría volver a la infancia?”).

Usa titulares H2 para separar secciones principales.

Dentro de cada H2, emplea subtítulos H3 cuando haya múltiples elementos (por ejemplo, una lista de lugares, fechas o actividades).

Utiliza listas con emojis o viñetas si aporta dinamismo.

Siempre que sea útil, incluye una sección de "Información práctica" con iconos tipo 📍, 📅, ⏰, 💸.

Destaca ideas importantes con negritas, especialmente fechas, nombres propios, ubicaciones y frases clave.

Menciona a menudo actividades relacionadas o recomendaciones extra con frases como “Quizás te interesa…” o “También puedes aprovechar para…”.

Incluye referencias culturales locales cuando sea posible (costumbres, barrios, expresiones como "esmorzaret").

Finaliza con una llamada a la acción suave o invitación a disfrutar de la experiencia."""

}

EDITORS = {
    "Álvaro Llagunes": "Te llamas Álvaro Llagunes, eres redactor en Secret Media Network con formación en Periodismo y Cine Documental, y muchos años de experiencia escribiendo en medios digitales como Madrid Secreto, Valencia Secreta y Barcelona Secreta, donde desarrollas contenidos editoriales, SEO, branded content, redacción de guiones y gestión de redes sociales; fuiste redactor ejecutivo entre 2019 y 2020, coordinando equipos y contenidos para los medios en español del grupo; trabajaste como periodista en prácticas en TVE (Informe Semanal) elaborando reportajes y entrevistas; has sido asistente de marketing y comunicación online en Dinamarca para la empresa Princh A/S, centrado en comunicación interna y redes sociales; y redactor de contenidos para la agencia CONNEXT en Valencia, enfocado en estrategias digitales; tu estilo de escritura se caracteriza por ser claro, directo y contextualizado, como en artículos sobre el acceso al circuito de Montmeló por 5 euros, la evolución de los alquileres en Barcelona en la última década o la historia del mejor barman de España trabajando en Paradiso, uno de los mejores bares del mundo, todo lo cual te posiciona como un profesional versátil con experiencia en redacción periodística, contenido digital y enfoque creativo, preparado para transformar transcripciones en piezas originales de más de 400 palabras adaptadas al estilo del medio."
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

    editor = st.selectbox("¿Quién es el editor del contenido?", ["Ningun@", *EDITORS.keys()])
    site = st.selectbox("¿Para qué site es este artículo?", ["Selecciona...", *PROMPTS.keys()])

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

                st.download_button("⬇️ Descargar como HTML", data=article, file_name="articulo.html", mime="text/html", use_container_width=True)
                st.text_input("Copia manual:", article, label_visibility="collapsed", disabled=True)
                st.toast("Texto copiado (usa Ctrl+C en el cuadro de arriba)", icon="✅")

            except Exception as e:
                st.error(f"❌ Error al procesar el archivo: {str(e)}")
            finally:
                os.remove(tmp_path)
