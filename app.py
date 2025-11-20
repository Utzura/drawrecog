import os
import time
import streamlit as st
import base64
from openai import OpenAI
from PIL import Image
import numpy as np
from gtts import gTTS
from streamlit_drawable_canvas import st_canvas
import json
import paho.mqtt.client as paho

# ============================
# Config MQTT
# ============================
BROKER = "157.230.214.127"
PORT = 1883
MQTT_CLIENT_ID = "STREAMLIT_MYSTIC_PUB"

def mqtt_publish(topic: str, payload: dict, qos: int = 0, retain: bool = False):
    try:
        client = paho.Client(MQTT_CLIENT_ID)
        client.on_publish = lambda c, u, r: print("Publicado:", topic, payload)
        client.connect(BROKER, PORT, keepalive=60)
        payload_str = json.dumps(payload)
        client.publish(topic, payload_str, qos=qos, retain=retain)
        client.disconnect()
        return True, None
    except Exception as e:
        return False, str(e)

# ============================
# Session State
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
if 'slider_value' not in st.session_state:
    st.session_state.slider_value = 0.0

# ============================
# Función Base64
# ============================
def encode_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
            return encoded_image
    except FileNotFoundError:
        return "Error: La imagen no se encontró."

# ============================
# UI
# ============================
st.set_page_config(page_title='Tablero Místico', layout="wide")
st.title(' ꩜ Tablero Místico de Predicciones ꩜ ')

st.markdown("""
Bienvenido/a al Oráculo Digital  
✶✶✶ Dibuja un símbolo y el destino será revelado.  
""")

# Sidebar
with st.sidebar:
    st.subheader("Herramientas del destino")
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

# API KEY
api_key = st.text_input('Ingresa tu Clave Mágica (API Key)', type="password")
client = None

if api_key:
    try:
        client = OpenAI(api_key=api_key)
    except Exception:
        client = None

# ============================
# BOTÓN: ANALIZAR DESTINO
# ============================
analyze_button = st.button("🔮 Revela mi futuro")

if canvas_result.image_data is not None and api_key and analyze_button:
    with st.spinner("Consultando al Oráculo..."):
        input_numpy_array = np.array(canvas_result.image_data)
        input_image = Image.fromarray(input_numpy_array.astype('uint8')).convert('RGBA')
        input_image.save('img.png')

        base64_image = encode_image_to_base64("img.png")
        st.session_state.base64_image = base64_image

        prompt_text = (
            "Eres un oráculo místico. Interpreta el destino del usuario basado "
            "en este dibujo. Habla en tono espiritual, enigmático y simbólico."
        )

        try:
            response = client.chat.completions.create(
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

            content = response.choices[0].message.content
            st.session_state.full_response = content
            st.session_state.analysis_done = True

        except Exception as e:
            st.error(f"Ocurrió un error en la lectura de tu destino: {e}")

# ============================
# MOSTRAR RESULTADO
# ============================
if st.session_state.analysis_done:
    st.divider()
    st.subheader("𓁻 Tu destino revelado 𓁻")
    st.markdown(st.session_state.full_response)

    st.divider()
    st.subheader("¿Quieres saber qué tan probable es este futuro?")

    col1, col2 = st.columns(2)
    want_prob = col1.button("Mostrar probabilidad")
    advice_button = col2.button("Consejo del destino")

    # ============================
    # CONSEJO DEL DESTINO
    # ============================
    if advice_button:
        with st.spinner("Consultando un consejo del destino..."):
            consejo_prompt = (
                f"Basado en esta predicción: '{st.session_state.full_response}', "
                "genera un consejo espiritual breve en tono místico."
            )

            try:
                consejo_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": consejo_prompt}],
                    max_tokens=200,
                )
                consejo_texto = consejo_response.choices[0].message.content.strip()
            except Exception as e:
                consejo_texto = f"No se pudo obtener un consejo: {e}"

        st.divider()
        st.subheader("⋆ Consejo del destino ⋆")
        st.markdown(consejo_texto)

        # Audio
        try:
            tts = gTTS(consejo_texto, lang="es")
            audio_path = "consejo_oraculo.mp3"
            tts.save(audio_path)
            audio_bytes = open(audio_path, "rb").read()
            st.audio(audio_bytes, format="audio/mp3")
        except Exception as e:
            st.error(f"No se pudo generar el audio: {e}")

    # ============================
    # PROBABILIDAD
    # ============================
    if want_prob:
        with st.spinner("El Oráculo evalúa tu destino..."):
            prob_prompt = (
                "Eres un analista místico. Evalúa la probabilidad de esta predicción:\n\n"
                f"{st.session_state.full_response}\n\n"
                "Devuélvelo en JSON: "
                "{\"label\":\"ALTO|MEDIO|BAJO\",\"confidence\":0-100,"
                "\"reason\":\"breve explicación\"}"
            )

           import re
            try:
            prob_resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                messages=[{"role": "user", "content": prob_prompt}],
                max_tokens=150,
                )

                prob_text = prob_resp.choices[0].message.content.strip()

    # Extrae el primer JSON válido aunque venga mezclado
                match = re.search(r"\{.*\}", prob_text, re.DOTALL)
            if match:
                prob_json = json.loads(match.group(0))
            else:
             raise ValueError("No se encontró JSON válido")

        except Exception as e:
    # Fallback más realista (no fijo)
    prob_json = {
        "label": "MEDIO",
        "confidence": np.random.randint(40, 70),
        "reason": "Estimación alternativa debido a error."
    }


            # Normalización
            label = prob_json.get("label", "MEDIO").upper()
            confidence = min(max(int(prob_json.get("confidence", 50)), 0), 100)

            angle_map = {"ALTO": 160, "MEDIO": 90, "BAJO": 20}
            servo_angle = angle_map.get(label, 90)

            st.session_state.probability_result = prob_json
            st.session_state.servo_angle = servo_angle

        st.success(f"Probabilidad: **{label}** — Confianza: **{confidence}%**")
        st.markdown(f"**Motivo:** {prob_json.get('reason', '')}")
        st.markdown(f"**Servo sugerido:** **{servo_angle}°**")

    # ============================
    # SECCIÓN ARDUINO + MQTT
    # ============================
    if st.session_state.probability_result is not None:
        st.divider()
        st.subheader("Implementación en Servo (Arduino)")

        st.markdown(f"""
        **Etiqueta:** `{st.session_state.probability_result.get("label")}`  
        **Confianza:** `{st.session_state.probability_result.get("confidence")}%`  
        **Ángulo sugerido:** `{st.session_state.servo_angle}°`  
        """)

        st.markdown("""
        **Conexión del Servo**
        - Señal → D9  
        - VCC → 5V  
        - GND → GND  
        """)

        # Slider manual
        new_val = st.slider(
            "Selecciona valor manual",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state.slider_value,
            key="corrected_slider"
        )
        st.session_state.slider_value = new_val

        col_send1, col_send2 = st.columns(2)

        if col_send1.button("Enviar ON al ESP32"):
            ok, err = mqtt_publish("cmqtt_s", {"Act1": "ON"})
            if ok: st.success("Se envió ON")
            else:  st.error(err)

        if col_send2.button("Enviar OFF al ESP32"):
            ok, err = mqtt_publish("cmqtt_s", {"Act1": "OFF"})
            if ok: st.success("Se envió OFF")
            else:  st.error(err)

        st.markdown("---")

        # Ángulo sugerido
        if st.button("Enviar ángulo sugerido"):
            percent = round((st.session_state.servo_angle / 180) * 100, 2)
            percent = max(0, min(100, percent))
            payload = {"Analog": float(percent)}

            ok, err = mqtt_publish("cmqtt_a", payload)
            if ok: st.success(f"Publicado {payload}")
            else:  st.error(err)

        # Manual
        if st.button("Enviar valor manual"):
            val = float(st.session_state.slider_value)
            payload = {"Analog": val}

            ok, err = mqtt_publish("cmqtt_a", payload)
            if ok: st.success(f"Publicado {payload}")
            else:  st.error(err)

        st.write("Última publicación MQTT:", st.session_state.last_mqtt_publish)
