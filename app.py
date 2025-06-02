import streamlit as st
import openai
import tempfile
import os
from pathlib import Path
from typing import Literal

# --- AUTENTICACIÓN SIMPLE ---
PASSWORD = "SECRETMEDIA"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    pw = st.text_input("Introduce la contraseña para acceder", type="password")
    if pw == PASSWORD:
        st.session_state.authenticated = True
        st.experimental_rerun()
    else:
        st.stop()

# --- CONFIGURA TUS CLAVES API AQUÍ ---

from dotenv import load_dotenv
load_dotenv()

WHISPER_API_KEY = os.getenv("WHISPER_API_KEY")
CHATGPT_API_KEY = os.getenv("CHATGPT_API_KEY")

# --- ASOCIACIÓN DE PROMPTS POR SITE ---
PROMPTS = {
    "Valencia Secreta": """Eres un redactor especializado en planes y cosas que hacer en Valencia, con muchos años de experiencia y has visitado todos los lugares de moda en la ciudad, se te da muy bien hacer recomendaciones de qué visitar y dar contexto sobre los sitios que recomiendas.

Mira, aquí puedes ver en detalle cómo escribes normalmente tus artículos, analiza el texto completo para coger puntos clave acerca de tu escritura (y también tenlo en cuenta para adaptarte al estilo del medio a la hora de maquetar los textos): https://valenciasecreta.com/

Tu tarea va a ser escribir artículos originales en base a unas transcripciones de vídeos que te voy a pasar. Van a ser transcripciones cortas, así que tendrás que escribir de forma creativa (sin resultar aburrida ni dar demasiadas vueltas para decir algo que se puede contar en pocas palabras), conviene además que des contexto a los datos que menciones en el artículo para que así sea más extenso, el artículo deberá tener más de 400 palabras""",

    "Barcelona Secreta": """Eres un redactor especializado en planes y cosas que hacer en Barcelona, con muchos años de experiencia y has visitado todos los lugares de moda en la ciudad, se te da muy bien hacer recomendaciones de qué visitar y dar contexto sobre los sitios que recomiendas.

Mira, aquí puedes ver en detalle cómo escribes normalmente tus artículos, analiza el texto completo para coger puntos clave acerca de tu escritura (y también tenlo en cuenta para adaptarte al estilo del medio a la hora de maquetar los textos): https://barcelonasecreta.com/

Tu tarea va a ser escribir artículos originales en base a unas transcripciones de vídeos que te voy a pasar. Van a ser transcripciones cortas, así que tendrás que escribir de forma creativa (sin resultar aburrida ni dar demasiadas vueltas para decir algo que se puede contar en pocas palabras), conviene además que des contexto a los datos que menciones en el artículo para que así sea más extenso, el artículo deberá tener más de 400 palabras"""
}

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Convertir vídeo en artículo")
st.title("📝 Conversor de vídeo a artículo para medios Secreta")

# --- SUBIDA DE ARCHIVO ---
video_file = st.file_uploader("Sube un vídeo (.mp4, .mov, .avi...):", type=None)

site = st.selectbox("¿Para qué site es este artículo?", list(PROMPTS.keys()))
extra_prompt = st.text_area("¿Quieres añadir instrucciones adicionales al prompt? (opcional)")

if video_file and site:
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(video_file.name).suffix) as tmp:
        tmp.write(video_file.read())
        tmp_path = tmp.name

    st.info("Transcribiendo vídeo con Whisper...")
    openai.api_key = WHISPER_API_KEY
    with open(tmp_path, "rb") as audio_file:
        transcript_response = openai.Audio.transcribe("whisper-1", audio_file)
    transcription = transcript_response["text"]

    st.success("✅ Transcripción completada")
    st.text_area("Texto transcrito:", transcription, height=200)

    full_prompt = PROMPTS[site] + "\n\nTranscripción:\n" + transcription
    if extra_prompt:
        full_prompt += "\n\nInstrucciones adicionales del editor:\n" + extra_prompt

    st.info("Generando artículo con ChatGPT...")
    openai.api_key = CHATGPT_API_KEY
    chat_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres un redactor profesional especializado en contenido local."},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.7
    )

    article = chat_response["choices"][0]["message"]["content"]

    st.success("✅ Artículo generado")
    st.subheader("🔎 Vista previa del artículo")
    st.markdown(article, unsafe_allow_html=True)

    st.subheader("📋 Código Markdown")
    st.code(article)

    st.download_button("⬇️ Descargar como HTML", data=article, file_name="articulo.html", mime="text/html")
    st.button("📋 Copiar artículo", on_click=lambda: st.toast("Texto copiado (usa Ctrl+C en el área Markdown)", icon="✅"))

    os.remove(tmp_path)
