import os
import streamlit as st
import base64
from openai import OpenAI
import openai
from PIL import Image
import numpy as np
from streamlit_drawable_canvas import st_canvas

# ============================
# Variables
# ============================
Expert = " "
profile_imgenh = " "

# ============================
# Inicializar session_state
# ============================
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'full_response' not in st.session_state:
    st.session_state.full_response = ""
if 'base64_image' not in st.session_state:
    st.session_state.base64_image = ""
if 'probability_result' not in st.session_state:
    st.session_state.probability_result = None
if 'servo_angle' not in st.session_state:
    st.session_state.servo_angle = None

# ============================
# Función para convertir imagen a Base64
# ============================
def encode_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
            return encoded_image
    except FileNotFoundError:
        return "Error: La imagen no se encontró en la ruta especificada."

# ============================
# Interfaz principal
# ============================
st.set_page_config(page_title='Tablero Místico', layout="wide")
st.title(' ꩜ Tablero Místico de Predicciones ꩜ ')

st.markdown("""
Bienvenido/a al Oráculo Digital
✶✶✶ Lo que traces aquí no será un simple dibujo...  
Cada línea, cada trazo y cada forma revelará algo oculto en tu mente, y con ello... tu destino.  

Dibuja sin pensar y cuando estés listo, pide al tablero que revele lo que el futuro guarda para ti.
✩₊˚.⋆☾𓃦☽⋆⁺₊✧
""")

# ============================
# Panel lateral
# ============================
with st.sidebar:
    st.subheader("Herramientas de tu destino")
    stroke_width = st.slider('Grosor de la pluma', 1, 30, 5)
    stroke_color = st.color_picker("Color de tu energía", "#000000")
    bg_color = st.color_picker("Color de tu universo", "#FFFFFF")

# ============================
# Canvas para dibujar
# ============================
drawing_mode = "freedraw"
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color=bg_color,
    height=350,
    width=450,
    drawing_mode=drawing_mode,
    key="canvas",
)

# ============================
# API Key
# ============================
ke = st.text_input('Ingresa tu Clave Mágica (API Key)', type="password")
os.environ['OPENAI_API_KEY'] = ke
api_key = os.environ.get('OPENAI_API_KEY', '')
client = None
if api_key:
    try:
        client = OpenAI(api_key=api_key)
    except Exception:
        client = None

# ============================
# Botón para análisis
# ============================
analyze_button = st.button("Revela mi futuro")

if canvas_result.image_data is not None and api_key and analyze_button:
    with st.spinner("Consultando al Oráculo..."):
        input_numpy_array = np.array(canvas_result.image_data)
        input_image = Image.fromarray(input_numpy_array.astype('uint8')).convert('RGBA')
        input_image.save('img.png')

        base64_image = encode_image_to_base64("img.png")
        st.session_state.base64_image = base64_image

        prompt_text = (
            "Eres un oráculo místico. Basado en este dibujo, interpreta el destino del usuario. "
            "Habla en tono enigmático y espiritual, como si estuvieras revelando un secreto profundo sobre su futuro. "
            "Predice con metáforas, símbolos y un aire de misterio."
        )

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
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                            },
                        ],
                    }
                ],
                max_tokens=500,
            )

            if response.choices[0].message.content is not None:
                full_response += response.choices[0].message.content
                message_placeholder.markdown(full_response)

            st.session_state.full_response = full_response
            st.session_state.analysis_done = True

        except Exception as e:
            st.error(f"Ocurrió un error en la lectura de tu destino: {e}")

# ============================
# Mostrar resultado
# ============================
if st.session_state.analysis_done:
    st.divider()
    st.subheader("𓁻 Tu destino revelado 𓁻")
    st.markdown(f"{st.session_state.full_response}")

    # Generar consejo del destino
    with st.spinner("Consultando un consejo del destino..."):
        consejo_prompt = (
            f"Basado en esta predicción del futuro: '{st.session_state.full_response}', "
            "genera un consejo espiritual y enigmático. "
            "El consejo debe ser breve, inspirador y sonar como una guía del destino. "
            "Usa metáforas y un tono místico."
        )

        try:
            consejo_response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": consejo_prompt}],
                max_tokens=200,
            )
            consejo_texto = consejo_response.choices[0].message.content
        except Exception as e:
            consejo_texto = f"No se pudo obtener un consejo del destino: {e}"

    st.divider()
    st.subheader("⋆.˚Consejo del destino⋆.˚")
    st.markdown(consejo_texto)

    # -------------------------
    # NUEVO: Preguntar si quiere saber probabilidad
    # -------------------------
    st.divider()
    st.subheader("¿Quieres saber qué tan probable es este futuro?")

    # Botones para preguntar al usuario
    col1, col2 = st.columns([1, 1])
    with col1:
        want_prob = st.button("Sí, muéstrame la probabilidad")
    with col2:
        skip_prob = st.button("No, gracias")

    if skip_prob:
        st.info("Como prefieras. El Oráculo permanece a tu servicio si cambias de opinión.")

    if want_prob:
        if not api_key:
            st.error("Necesitas ingresar tu Clave Mágica (API Key) para que el Oráculo calcule la probabilidad.")
        else:
            with st.spinner("El Oráculo está evaluando la probabilidad..."):
                # Prompt para clasificar probabilidad en Alto/Medio/Bajo y dar porcentaje estimado
                prob_prompt = (
                    "Eres un analista místico. Lee la siguiente predicción y evalúa qué tan probable es que ese futuro "
                    "se cumpla: \n\n"
                    f"Predicción:\n{st.session_state.full_response}\n\n"
                    "Devuélvelo en formato JSON simple: {\"label\":\"ALTO|MEDIO|BAJO\",\"confidence\":<porcentaje entre 0 y 100>,"
                    "\"reason\":\"una frase breve explicando por qué\"}. Solo devuelve JSON."
                )
                try:
                    prob_resp = openai.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prob_prompt}],
                        max_tokens=150,
                    )
                    prob_text = prob_resp.choices[0].message.content.strip()

                    # Intento de parse simple del JSON (sin dependencia json.loads para tolerancia)
                    import json
                    try:
                        prob_json = json.loads(prob_text)
                    except Exception:
                        # Si el asistente no devolvió puro JSON, extraer manualmente buscando label y numbers
                        prob_json = {"label": "MEDIO", "confidence": 50, "reason": "Estimación mística automatica."}

                    label = prob_json.get("label", "MEDIO")
                    confidence = prob_json.get("confidence", 50)
                    reason = prob_json.get("reason", "")

                    # Mapear etiqueta a ángulo de servo
                    # Alto -> ángulo grande (ej. 160), Medio -> 90, Bajo -> 20
                    angle_map = {"ALTO": 160, "ALTO.": 160, "ALTA": 160, "MEDIO": 90, "MEDIO.": 90, "BAJO": 20, "BAJA": 20}
                    servo_angle = angle_map.get(str(label).upper(), 90)

                    # Guardar en session_state
                    st.session_state.probability_result = {"label": label, "confidence": confidence, "reason": reason}
                    st.session_state.servo_angle = servo_angle

                    st.success(f"Probabilidad: **{label}** — Confianza: **{confidence}%**")
                    st.markdown(f"**Motivo:** {reason}")
                    st.markdown(f"**Ángulo sugerido para el servo (Arduino):** **{servo_angle}°**")
                except Exception as e:
                    st.error(f"No se pudo evaluar la probabilidad: {e}")

    # Si ya se calculó la probabilidad, mostrar instrucciones Arduino
    if st.session_state.probability_result is not None:
        st.divider()
        st.subheader("Implementación en Servo (Arduino)")

        st.markdown("""
        **Resumen rápido**
        - Etiqueta: `{label}`  
        - Confianza: `{conf}%`  
        - Ángulo sugerido: `{angle}°`  
        """.format(
            label=st.session_state.probability_result.get("label"),
            conf=st.session_state.probability_result.get("confidence"),
            angle=st.session_state.servo_angle
        ))

        st.markdown("""
        **Cómo conectar el servo**
        1. Señal (cable amarillo/naranja) -> Pin digital PWM (ej. D9).  
        2. VCC (rojo) -> 5V (o alimentación externa 5V recomendada si el servo consume corriente).  
        3. GND (marrón/negro) -> GND de Arduino (y GND común si usas fuente externa).  
        **IMPORTANTE:** si usas una fuente externa para el servo, conecta las tierras (GND) entre Arduino y la fuente.
        """)

        st.markdown("**Sketch de Arduino (sube esto al Arduino)**")
        arduino_code =_
