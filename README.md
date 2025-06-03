
# 📝 Video to Article - Generador de artículos desde vídeos para SMN

Este proyecto permite a los editores de medios como **Valencia Secreta** y **Barcelona Secreta** generar artículos listos para publicar a partir de vídeos subidos. El sistema transcribe automáticamente el vídeo usando **Whisper**, y genera el artículo usando **ChatGPT** con estilos adaptados según el medio.

---

## 🚀 ¿Qué hace esta app?

- ✅ Transcribe vídeos automáticamente (.mp4, .mov, .avi, etc.)
- ✍️ Genera artículos listos para publicar (con títulos, negritas, estilo periodístico)
- 📋 Permite añadir instrucciones editoriales personalizadas
- 🔒 Protegida con contraseña para uso interno
- 📄 Exporta a HTML, Markdown o permite copiar directamente

---

## 🔗 Nota sobre LucidLink

LucidLink no permite acceder a archivos mediante enlaces públicos o sin autenticación por seguridad (modelo de cero conocimiento).  
Por tanto, si quieres usar un vídeo que está almacenado en LucidLink:

1. Asegúrate de tener instalado el cliente de escritorio de LucidLink.
2. Inicia sesión y monta tu Filespace como si fuera una unidad en tu equipo.
3. Sube el archivo desde esa ruta usando la opción de subida directa.

---

## ▶️ Contraseña

🔐 Al iniciar, la app te pedirá una contraseña. Usa: `SECRETMEDIA`

---

## 📦 Requisitos (solo para desarrolladores)

- Python 3.9 o superior
- Cuenta en OpenAI con acceso a `whisper-1` y `gpt-4`
- Streamlit y dependencias del proyecto

---

## 🛠 Instalación local (solo para desarrolladores)

1. Clona este repositorio:

```bash
git clone https://github.com/TU_USUARIO/video-to-article.git
cd video-to-article
```

2. Crea un entorno virtual (opcional pero recomendado):

```bash
python -m venv venv
venv\Scripts\activate
```

3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

4. Crea un archivo `.env` con tus claves de API:

```
WHISPER_API_KEY=tu_clave_openai_para_whisper
CHATGPT_API_KEY=tu_clave_openai_para_chatgpt
```

---

## ▶️ Ejecutar la app (solo para desarrolladores)

```bash
streamlit run app.py
```

🔐 Al iniciar, la app te pedirá una contraseña. Usa: `SECRETMEDIA`

---

## 🌐 Despliegue en Streamlit Cloud (opcional, solo para desarrolladores)

1. Sube este repositorio a GitHub (como privado).
2. Ve a [https://streamlit.io/cloud](https://streamlit.io/cloud) y crea una app nueva conectada al repo.
3. En la configuración de **Secrets** o **Environment Variables**, añade:

```
WHISPER_API_KEY = tu_clave
CHATGPT_API_KEY = tu_clave
```

4. Lanza la app. ¡Listo para usar!

---

## ✅ TODOs futuros

- [ ] Añadir opción de seleccionar el autor del artículo
- [ ] Integración con la API de WordPress
- [ ] Mejorar la detección de idioma y permitir traducción cruzada

---

## 🧠 Autores y contacto

Desarrollado para uso interno en el equipo de SMN.

Para soporte técnico, contactar con Jakub Motyka (jakub.motyka@feverup.com).
