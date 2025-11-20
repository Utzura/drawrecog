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
# Session state
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
# Encode image to base64
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
Cada trazo oculta un destino...
""")

# Sidebar
with st.sidebar:
    st.subheader("Herramientas del destino")
    stroke_width = st.slider('Grosor de la pluma', 1, 30, 5)
    stroke_color = st.color_picker("Color de tu energía", "#000000")
    bg_color = st.color_picker("Color del universo", "#FFFFFF")

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
    except:
        client = None

# ============================
# Predicción del destino
# ============================
analyze_button = st.button("🔮 Revela mi futuro")

if canvas_result.image_data is not None and api_key and analyze_button:
    with st.spinner("Consultando al Oráculo..."):

        # Convert canvas → PNG
        input_numpy_array = np.array(canvas_result.image_data)
        input_image = Image.fromarray(input_numpy_array.astype('uint8')).convert('RGBA')
        input_image.save('img.png')

        base64_image = encode_image_to_base64("img.png")
        st.session_state.base64_image = base64_image

        prompt_text = (
            "Eres un oráculo místico. Basado en este dibujo, interpreta el destino del usuario "
            "con símbolos, metáforas y tono enigmático."
        )

        try:
            # ========== NUEVA API RESPONSES ==========
            response = client.responses.create(
                model="gpt-4o-mini",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt_text},
                            {"type": "input_image", "image_url": f"data:image/png;base64,{base64_image}"}
                        ],
                    }
                ],
                max_output_tokens=500,
            )

            content = response.output_text
            st.session_state.full_response = content
            st.session_state.analysis_done = True

        except Exception as e:
            st.error(f"Ocurrió un error en la lectura del destino: {e}")

# ============================
# Mostrar resultado
# ============================
if st.session_state.analysis_done:
    st.divider()
    st.subheader("𓁻 Tu destino revelado 𓁻")
    st.markdown(st.session_state.full_response)

    st.divider()
    st.subheader("¿Quieres saber qué tan probable es este futuro?")

    col1, col2 = st.columns([1, 1])
    want_prob = col1.button("Sí, muéstrame la probabilidad")
    advice_button = col2.button("Escuchar el consejo del destino")

    # ============================
    # CONSEJO
    # ============================
    if advice_button:
        with st.spinner("Consultando sabiduría..."):
            consejo_prompt = (
                f"Basado en esta predicción del futuro: '{st.session_state.full_response}', "
                "da un consejo espiritual breve, profundo y místico."
            )

            try:
                consejo_response = client.responses.create(
                    model="gpt-4o-mini",
                    input=[{"role": "user", "content":[{"type":"input_text","text": consejo_prompt}]}],
                    max_output_tokens=200,
                )
                consejo_texto = consejo_response.output_text.strip()

            except Exception as e:
                consejo_texto = f"No se pudo obtener un consejo: {e}"

        st.subheader("⋆.˚Consejo del destino⋆.˚")
        st.markdown(consejo_texto)

        # TTS Audio
        try:
            tts = gTTS(consejo_texto, lang="es")
            audio_path = "consejo_oraculo.mp3"
            tts.save(audio_path)
            st.audio(open(audio_path, "rb").read(), format="audio/mp3")
        except Exception as e:
            st.error(f"No se pudo generar audio: {e}")

    # ============================
    # PROBABILIDAD
    # ============================
    if want_prob:
        with st.spinner("El Oráculo analiza el destino..."):

            prob_prompt = (
                "Evalúa la probabilidad de la siguiente predicción:\n"
                f"{st.session_state.full_response}\n\n"
                "Devuelve SOLO JSON: "
                "{\"label\":\"ALTO|MEDIO|BAJO\",\"confidence\":0-100,\"reason\":\"texto\"}"
            )

            try:
                prob_resp = client.responses.create(
                    model="gpt-4o-mini",
                    input=[{"role":"user","content":[{"type":"input_text","text":prob_prompt}]}],
                    max_output_tokens=150,
                )

                prob_text = prob_resp.output_text.strip()

                try:
                    prob_json = json.loads(prob_text)
                except:
                    prob_json = {"label":"MEDIO","confidence":50,"reason":"Estimación automática"}

                raw_label = prob_json.get("label","MEDIO").upper()

                if "ALTO" in raw_label:
                    normalized_label = "ALTO"
                elif "BAJO" in raw_label:
                    normalized_label = "BAJO"
                else:
                    normalized_label = "MEDIO"

                confidence = int(float(prob_json.get("confidence",50)))
                confidence = max(0, min(100, confidence))

                angle_map = {"ALTO":160, "MEDIO":90, "BAJO":20}
                servo_angle = angle_map[normalized_label]

                st.session_state.probability_result = {
                    "label": normalized_label,
                    "confidence": confidence,
                    "reason": prob_json.get("reason","")
                }
                st.session_state.servo_angle = servo_angle

                st.success(f"Probabilidad: **{normalized_label}** — Confianza: **{confidence}%**")
                st.markdown(f"**Motivo:** {prob_json.get('reason','')}")

            except Exception as e:
                st.error(f"No se pudo evaluar: {e}")

    # ============================
    # MQTT + SERVO
    # ============================
    if st.session_state.probability_result:

        st.divider()
        st.subheader("Implementación Servo (Arduino)")
        st.markdown(f"""
        **Etiqueta:** `{st.session_state.probability_result['label']}`  
        **Confianza:** `{st.session_state.probability_result['confidence']}%`  
        **Ángulo sugerido:** `{st.session_state.servo_angle}°`  
        """)

        # Slider manual
        new_val = st.slider(
            "Selecciona un valor manual",
            0.0, 100.0,
            st.session_state.slider_value,
            key="manual_slider"
        )
        st.session_state.slider_value = new_val

        colMQ1, colMQ2 = st.columns(2)

        with colMQ1:
            if st.button("Enviar ON al ESP32"):
                ok, err = mqtt_publish("cmqtt_s", {"Act1": "ON"})
                st.success("ON enviado") if ok else st.error(err)

        with colMQ2:
            if st.button("Enviar OFF al ESP32"):
                ok, err = mqtt_publish("cmqtt_s", {"Act1": "OFF"})
                st.success("OFF enviado") if ok else st.error(err)

        # Enviar ángulo sugerido
        if st.button("Enviar ángulo sugerido al ESP32"):
            percent = round((st.session_state.servo_angle / 180) * 100, 2)
            percent = max(0, min(100, percent))
            payload = {"Analog": percent}
            ok, err = mqtt_publish("cmqtt_a", payload)
            st.success(f"Publicado {payload}") if ok else st.error(err)

        # Enviar manual
        if st.button("Enviar valor manual"):
            payload = {"Analog": float(st.session_state.slider_value)}
            ok, err = mqtt_publish("cmqtt_a", payload)
            st.success(f"Publicado {payload}") if ok else st.error(err)
