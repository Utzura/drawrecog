import os
import time
import streamlit as st
import base64
from openai import OpenAI
import openai
from PIL import Image
import numpy as np
from gtts import gTTS
from streamlit_drawable_canvas import st_canvas
import json
import paho.mqtt.client as paho

# ============================
# Config MQTT (ajusta si hace falta)
# ============================
BROKER = "157.230.214.127"
PORT = 1883
MQTT_CLIENT_ID = "STREAMLIT_MYSTIC_PUB"

def mqtt_publish(topic: str, payload: dict, qos: int = 0, retain: bool = False):
    """Conecta al broker, publica el mensaje (JSON) y se desconecta."""
    try:
        client = paho.Client(MQTT_CLIENT_ID)
        client.on_publish = lambda c, u, r: print("Publicado:", topic, payload)
        client.connect(BROKER, PORT, keepalive=60)
        # Convertir payload a JSON string
        payload_str = json.dumps(payload)
        client.publish(topic, payload_str, qos=qos, retain=retain)
        client.disconnect()
        return True, None
    except Exception as e:
        return False, str(e)

# ============================
# Variables / session_state inicial
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
if 'last_mqtt_publish' not in st.session_state:
    st.session_state.last_mqtt_publish = ""

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
""")

# Sidebar
with st.sidebar:
    st.subheader("Herramientas de tu destino")
    stroke_width = st.slider('Grosor de la pluma', 1, 30, 5)
    stroke_color = st.color_picker("Color de tu energía", "#000000")
    bg_color = st.color_picker("Color de tu universo", "#FFFFFF")

# Canvas
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color=bg_color,
    height=350,
    width=450,
    drawing_mode="freedraw",
    key="canvas",
)

# API Key
ke = st.text_input('Ingresa tu Clave Mágica (API Key)', type="password")
os.environ['OPENAI_API_KEY'] = ke
api_key = os.environ.get('OPENAI_API_KEY', '')
client = None
if api_key:
    try:
        client = OpenAI(api_key=api_key)
    except Exception:
        client = None

# Botón para análisis
analyze_button = st.button("🔮 Revela mi futuro")

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

# Mostrar resultado
if st.session_state.analysis_done:
    st.divider()
    st.subheader("𓁻 Tu destino revelado 𓁻")
    st.markdown(f"{st.session_state.full_response}")

    st.divider()
    st.subheader("¿Quieres saber qué tan probable es este futuro?")

    col1, col2 = st.columns([1, 1])
    with col1:
        want_prob = st.button("Sí, muéstrame la probabilidad")
    with col2:
        advice_button = st.button("Escuchar el consejo del destino")

    # CONSEJO DEL DESTINO
    if advice_button:
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
                consejo_texto = consejo_response.choices[0].message.content.strip()
            except Exception as e:
                consejo_texto = f"No se pudo obtener un consejo del destino: {e}"

        st.divider()
        st.subheader("⋆.˚Consejo del destino⋆.˚")
        st.markdown(consejo_texto)

        # TTS
        try:
            tts = gTTS(consejo_texto, lang="es")
            audio_path = "consejo_oraculo.mp3"
            tts.save(audio_path)
            audio_file = open(audio_path, "rb")
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/mp3")
        except Exception as e:
            st.error(f"No se pudo generar el audio: {e}")

    # PROBABILIDAD
    if want_prob:
        if not api_key:
            st.error("Necesitas ingresar tu Clave Mágica (API Key) para que el Oráculo calcule la probabilidad.")
        else:
            with st.spinner("El Oráculo está evaluando la probabilidad..."):
                prob_prompt = (
                    "Eres un analista místico. Lee la siguiente predicción y evalúa qué tan probable es que ese futuro "
                    "se cumpla: \n\n"
                    f"Predicción:\n{st.session_state.full_response}\n\n"
                    "Devuélvelo en formato JSON simple: "
                    "{\"label\":\"ALTO|MEDIO|BAJO\",\"confidence\":<porcentaje entre 0 y 100>," 
                    "\"reason\":\"una frase breve explicando por qué\"}. Solo devuelve JSON."
                )
                try:
                    prob_resp = openai.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prob_prompt}],
                        max_tokens=150,
                    )
                    prob_text = prob_resp.choices[0].message.content.strip()

                    try:
                        prob_json = json.loads(prob_text)
                    except Exception:
                        prob_json = {"label": "MEDIO", "confidence": 50, "reason": "Estimación mística automática."}

                    label = prob_json.get("label", "MEDIO")
                    confidence = prob_json.get("confidence", 50)
                    reason = prob_json.get("reason", "")
                    # Normalizar etiqueta del modelo
                    raw_label = str(label).strip().upper()

                    if "ALTO" in raw_label:
                        normalized = "ALTO"
                    elif "MEDIO" in raw_label or "MEDIA" in raw_label:
                        normalized = "MEDIO"
                    elif "BAJO" in raw_label or "BAJA" in raw_label:
                        normalized = "BAJO"
                    else:
                        normalized = "MEDIO"   # fallback razonable

# Usar etiqueta normalizada
                    angle_map = {"ALTO": 160, "MEDIO": 90, "BAJO": 20}
                    servo_angle = angle_map.get(normalized, 90)
                    #angle_map = {"ALTO": 160, "ALTA": 160, "MEDIO": 90, "BAJO": 20, "BAJA": 20}
                    #servo_angle = angle_map.get(str(label).upper(), 90)

                    st.session_state.probability_result = {"label": label, "confidence": confidence, "reason": reason}
                    st.session_state.servo_angle = servo_angle

                    st.success(f"Probabilidad: **{label}** — Confianza: **{confidence}%**")
                    st.markdown(f"**Motivo:** {reason}")
                    st.markdown(f"**Ángulo sugerido para el servo (Arduino):** **{servo_angle}°**")
                    
                except Exception as e:
                    st.error(f"No se pudo evaluar la probabilidad: {e}")

  # Mostrar info Arduino si hay probabilidad
    if st.session_state.probability_result is not None:
        st.divider()
        st.subheader("Implementación en Servo (Arduino)")
        st.markdown(f"""
        **Resumen rápido**
        - Etiqueta: `{st.session_state.probability_result.get("label")}`  
        - Confianza: `{st.session_state.probability_result.get("confidence")}%`  
        - Ángulo sugerido: `{st.session_state.servo_angle}°`  
        """)

        st.markdown("""
        **Cómo conectar el servo**
        1. Señal (amarillo/naranja) → Pin PWM (ej. D9)  
        2. VCC (rojo) → 5V  
        3. GND (negro/marrón) → GND  
        """)

        # ===============================
        # SLIDER CORREGIDO
        # ===============================
        # Este SIEMPRE arranca en 0 y ya no recuerda valores anteriores
        if "slider_value" not in st.session_state:
            st.session_state.slider_value = 0.0

        new_val = st.slider(
            "Selecciona el rango de valores",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state.slider_value,
            key="corrected_slider"
        )

        st.session_state.slider_value = new_val
        values = st.session_state.slider_value
        st.write("Valor seleccionado:", values)

        # ===============================
        # BOTONES MQTT
        # ===============================
        col_send1, col_send2 = st.columns(2)
        with col_send1:
            if st.button("Enviar ON al ESP32"):
                ok, err = mqtt_publish("cmqtt_s", {"Act1": "ON"})
                if ok:
                    st.session_state.last_mqtt_publish = f"Publicado Act1: ON"
                    st.success("Se envió ON al ESP32")
                else:
                    st.error(f"No se pudo publicar: {err}")

        with col_send2:
            if st.button("Enviar OFF al ESP32"):
                ok, err = mqtt_publish("cmqtt_s", {"Act1": "OFF"})
                if ok:
                    st.session_state.last_mqtt_publish = f"Publicado Act1: OFF"
                    st.success("Se envió OFF al ESP32")
                else:
                    st.error(f"No se pudo publicar: {err}")

        st.markdown("---")

        # Enviar ángulo sugerido
        if st.button("Enviar ángulo sugerido al ESP32"):
            analog_value = float(st.session_state.servo_angle)
            ok, err = mqtt_publish("cmqtt_a", {"Analog": analog_value})
            if ok:
                st.session_state.last_mqtt_publish = f"Publicado Analog: {analog_value}"
                st.success(f"Ángulo/valor {analog_value} enviado al ESP32")
            else:
                st.error(f"No se pudo publicar: {err}")

        # Enviar valor manual del slider
        st.markdown("---")
        if st.button("Enviar valor manual al ESP32"):
            ok, err = mqtt_publish("cmqtt_a", {"Analog": float(values)})
            if ok:
                st.session_state.last_mqtt_publish = f"Publicado Analog manual: {values}"
                st.success(f"Valor {values} enviado al ESP32")
            else:
                st.error(f"No se pudo publicar: {err}")

        st.markdown("**Última publicación MQTT:**")
        st.write(st.session_state.last_mqtt_publish)
