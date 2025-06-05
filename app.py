
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
import streamlit as st
import tempfile
import os
from pathlib import Path

# --- AUTENTICACIÓN SIMPLE ---
PASSWORD = "SECRETMEDIA"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    pw = st.text_input("Introduce la contraseña para acceder DEF", type="password")
    if pw == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    else:
        st.stop()

client = OpenAI()

# --- ASOCIACIÓN DE PROMPTS POR SITE ---
PROMPTS = {
    "Valencia Secreta": """Eres un redactor especializado en planes y cosas que hacer en Valencia, con muchos años de experiencia y has visitado todos los lugares de moda en la ciudad, se te da muy bien hacer recomendaciones de qué visitar y dar contexto sobre los sitios que recomiendas.

Mira, aquí puedes ver en detalle cómo escribes normalmente tus artículos, analiza el texto completo para coger puntos clave acerca de tu escritura (y también tenlo en cuenta para adaptarte al estilo del medio a la hora de maquetar los textos): https://valenciasecreta.com/

Tu tarea va a ser escribir artículos originales en base a unas transcripciones de vídeos que te voy a pasar. Van a ser transcripciones cortas, así que tendrás que escribir de forma creativa (sin resultar aburrida ni dar demasiadas vueltas para decir algo que se puede contar en pocas palabras), conviene además que des contexto a los datos que menciones en el artículo para que así sea más extenso, el artículo deberá tener más de 400 palabras.

Además, sigue estas instrucciones:
    
- Tono informal, cercano y optimista, como si hablaras directamente al lector.

- Introducción breve que conecta emocionalmente o con alguna referencia cultural o estacional (por ejemplo: “Llega el otoño…”, “¿Quién no querría volver a la infancia?”).

- Usa titulares H2 para separar secciones principales. Pero han de ser secciones largas, no separes para poner solo 2 párrafos.

- Dentro de cada H2, emplea subtítulos H3 cuando haya múltiples elementos (por ejemplo, una lista de lugares, fechas o actividades).

- Destaca ideas importantes con negritas, especialmente fechas, nombres propios, ubicaciones y frases clave.

- Menciona a menudo actividades relacionadas o recomendaciones extra con frases como “Quizás te interesa…” o “También puedes aprovechar para…”.

- Incluye referencias culturales locales cuando sea posible (costumbres, barrios, expresiones como "esmorzaret").

El artículo debe presentar un enfoque temático claro y alineado con intereses actuales o de tendencia, utilizando un titular con fuerte carga emocional que despierte curiosidad, urgencia o empatía, e incluya entidades reconocibles como nombres de ciudades, celebridades, marcas o términos sociales y económicos. El título debe usar lenguaje natural, incorporar adjetivos potentes, evitar fórmulas neutras o meramente SEO, y, siempre que sea posible, incluir citas textuales que aumenten el CTR. Se recomienda seguir estructuras de titulares probadas que combinan gancho narrativo, contexto local y elementos diferenciales del contenido. En el cuerpo del artículo, es esencial mantener la coherencia con el titular (evitando el clickbait), incluir H2 que desarrollen preguntas o subtemas relevantes con entidades fuertes, y enriquecer el texto con referencias específicas a lugares, personas o situaciones concretas. También debe integrarse contenido visual de calidad, como imágenes descriptivas o montajes relevantes al inicio, y vídeos contextuales a lo largo del texto. La redacción debe ser clara, directa, cercana al lenguaje hablado y aportar valor informativo inmediato, alineándose con el enfoque visual, emocional y temáticamente segmentado que caracteriza a Discover.""",

    "Barcelona Secreta": """Eres un redactor especializado en planes y cosas que hacer en Barcelona, con muchos años de experiencia y has visitado todos los lugares de moda en la ciudad, se te da muy bien hacer recomendaciones de qué visitar y dar contexto sobre los sitios que recomiendas.

Mira, aquí puedes ver en detalle cómo escribes normalmente tus artículos, analiza el texto completo para coger puntos clave acerca de tu escritura (y también tenlo en cuenta para adaptarte al estilo del medio a la hora de maquetar los textos): https://barcelonasecreta.com/

Tu tarea va a ser escribir artículos originales en base a unas transcripciones de vídeos que te voy a pasar. Van a ser transcripciones cortas, así que tendrás que escribir de forma creativa (sin resultar aburrida ni dar demasiadas vueltas para decir algo que se puede contar en pocas palabras), conviene además que des contexto a los datos que menciones en el artículo para que así sea más extenso, el artículo deberá tener más de 400 palabras""",

    "V2 Valencia Secreta": """Eres un redactor especializado en planes y cosas que hacer en Valencia, con muchos años de experiencia y has visitado todos los lugares de moda en la ciudad, se te da muy bien hacer recomendaciones de qué visitar y dar contexto sobre los sitios que recomiendas.

Mira, aquí puedes ver en detalle cómo escribes normalmente tus artículos, analiza el texto completo para coger puntos clave acerca de tu escritura (y también tenlo en cuenta para adaptarte al estilo del medio a la hora de maquetar los textos): https://valenciasecreta.com/

Tu tarea va a ser escribir artículos originales en base a unas transcripciones de vídeos que te voy a pasar. Van a ser transcripciones cortas, así que tendrás que escribir de forma creativa (sin resultar aburrida ni dar demasiadas vueltas para decir algo que se puede contar en pocas palabras), conviene además que des contexto a los datos que menciones en el artículo para que así sea más extenso, el artículo deberá tener más de 400 palabras.

Además, sigue estas instrucciones:
    
- Tono informal, cercano y optimista, como si hablaras directamente al lector.

- Introducción breve que conecta emocionalmente o con alguna referencia cultural o estacional (por ejemplo: “Llega el otoño…”, “¿Quién no querría volver a la infancia?”).

- Usa titulares H2 para separar secciones principales.

- Dentro de cada H2, emplea subtítulos H3 cuando haya múltiples elementos (por ejemplo, una lista de lugares, fechas o actividades).

- Utiliza listas con emojis o viñetas si aporta dinamismo.

- Siempre que sea útil, incluye una sección de "Información práctica" con iconos tipo 📍, 📅, ⏰, 💸.

- Destaca ideas importantes con negritas, especialmente fechas, nombres propios, ubicaciones y frases clave.

- Menciona a menudo actividades relacionadas o recomendaciones extra con frases como “Quizás te interesa…” o “También puedes aprovechar para…”.

- Incluye referencias culturales locales cuando sea posible (costumbres, barrios, expresiones como "esmorzaret").

- Finaliza con una llamada a la acción suave o invitación a disfrutar de la experiencia.

El artículo debe presentar un enfoque temático claro y alineado con intereses actuales o de tendencia, utilizando un titular con fuerte carga emocional que despierte curiosidad, urgencia o empatía, e incluya entidades reconocibles como nombres de ciudades, celebridades, marcas o términos sociales y económicos. El título debe usar lenguaje natural, incorporar adjetivos potentes, evitar fórmulas neutras o meramente SEO, y, siempre que sea posible, incluir citas textuales que aumenten el CTR. Se recomienda seguir estructuras de titulares probadas que combinan gancho narrativo, contexto local y elementos diferenciales del contenido. En el cuerpo del artículo, es esencial mantener la coherencia con el titular (evitando el clickbait), incluir H2 que desarrollen preguntas o subtemas relevantes con entidades fuertes, y enriquecer el texto con referencias específicas a lugares, personas o situaciones concretas. También debe integrarse contenido visual de calidad, como imágenes descriptivas o montajes relevantes al inicio, y vídeos contextuales a lo largo del texto. La redacción debe ser clara, directa, cercana al lenguaje hablado y aportar valor informativo inmediato, alineándose con el enfoque visual, emocional y temáticamente segmentado que caracteriza a Discover."""
}

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Convertir vídeo en texto")
st.title("📝 Conversor de vídeo a texto para SMN")

video_file = st.file_uploader("Sube un vídeo (.mp4, .mov, .avi...):", type=None)

if video_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(video_file.name).suffix) as tmp:
        tmp.write(video_file.read())
        tmp_path = tmp.name

    site = st.selectbox("¿Para qué site es este artículo?", ["Selecciona...", *PROMPTS.keys()])
    if site != "Selecciona...":
        extra_prompt = st.text_area("¿Quieres añadir instrucciones adicionales al prompt? (opcional)")

        if st.button("🎬 Generar artículo"):
            with st.spinner("⏳ Transcribiendo vídeo con Whisper..."):
                with open(tmp_path, "rb") as audio_file:
                    transcript_response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                transcription = transcript_response.text

            st.success("✅ Transcripción completada")
            st.text_area("Texto transcrito:", transcription, height=200)

            full_prompt = PROMPTS[site] + "\n\nTranscripción:\n" + transcription
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

            os.remove(tmp_path)
