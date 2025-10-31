import os
import streamlit as st
import base64
from openai import OpenAI
import openai
from PIL import Image
import numpy as np
from streamlit_drawable_canvas import st_canvas

Expert = " "
profile_imgenh = " "

# Función para codificar la imagen en base64
def encode_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
            return encoded_image
    except FileNotFoundError:
        return "Error: La imagen no se encontró en la ruta especificada."

# Configuración de la página
st.set_page_config(page_title='Tablero Inteligente 🎨', layout='wide')

# Título centrado y colorido
st.markdown(
    "<h1 style='text-align: center; color: #4CAF50;'>Tablero Inteligente 🎨</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<h4 style='text-align: center; color: #555555;'>Dibuja un boceto en el panel y presiona 'Analizar'</h4>",
    unsafe_allow_html=True
)
st.markdown("---")

# Sidebar con información
with st.sidebar:
    st.header("📝 Acerca de")
    st.write("Esta aplicación muestra la capacidad que tiene una máquina de interpretar un boceto.")
    st.write("Dibuja en el panel principal y la IA describirá tu dibujo en español.")

# Canvas para dibujar
stroke_width = st.sidebar.slider('🖌️ Ancho de línea', 1, 30, 5)
stroke_color = "#000000"
bg_color = '#FFFFFF'

canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color=bg_color,
    height=300,
    width=400,
    drawing_mode="freedraw",
    key="canvas",
)

# Vista previa del dibujo
if canvas_result.image_data is not None:
    st.subheader("👁️ Vista previa de tu dibujo")
    preview_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
    st.image(preview_img, use_column_width=False, width=300)

# API Key input
ke = st.text_input('🔑 Ingresa tu Clave de OpenAI', type="password")
os.environ['OPENAI_API_KEY'] = ke
api_key = os.environ.get('OPENAI_API_KEY', None)

# Inicializar cliente OpenAI
if api_key:
    client = OpenAI(api_key=api_key)

# Botón de análisis
analyze_button = st.button("🔍 Analiza la imagen")

# Lógica de análisis
if canvas_result.image_data is not None and api_key and analyze_button:
    with st.spinner("Analizando ..."):
        input_numpy_array = np.array(canvas_result.image_data)
        input_image = Image.fromarray(input_numpy_array.astype('uint8'),'RGBA')
        input_image.save('img.png')

        base64_image = encode_image_to_base64("img.png")
        prompt_text = "Describe in Spanish briefly the image"

        try:
            full_response = ""
            message_placeholder = st.empty()
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                        ],
                    }
                ],
                max_tokens=500,
            )
            if response.choices[0].message.content is not None:
                full_response += response.choices[0].message.content
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

            if Expert == profile_imgenh:
                st.session_state.mi_respuesta = response.choices[0].message.content

        except Exception as e:
            st.error(f"❌ Ocurrió un error: {e}")

# Mensaje de advertencia si no hay API Key
elif analyze_button:
    if not api_key:
        st.warning("🔑 Por favor ingresa tu API key.")

