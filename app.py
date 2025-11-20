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
        client.connect(BROKER, PORT, keepalive=60)
        client.publish(topic, json.dumps(payload), qos=qos, retain=retain)
        client.disconnect()
        return True, None
    except Exception as e:
        return False, str(e)

# ============================
# Session State
# ============================
for key, value in {
    "analysis_done": False,
    "full_response": "",
    "base64_image": "",
    "probability_result": None,
    "servo_angle": None,
    "last_mqtt_publish": "",
    "slider_value": 0.0
}.items():
    st.session_state.setdefault(key, value)

# ============================
# Base64 image
# ============================
def encode_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as img:
            return base64.b64encode(img.read()).decode("utf-8")
    except:
        return None

# ============================
# UI
# ============================
st.set_page_config(page_title="Tablero Místico", layout="wide")
st.title("꩜ Tablero Místico de Predicciones ꩜")

st.markdown("""
Dibuja tu destino y deja que el Oráculo revele lo que los trazos esconden.
""")

# Sidebar
with st.sidebar:
    stroke_width = st.slider("Grosor de la pluma", 1, 30, 5)
    stroke_color = st.color_picker("Color del trazo", "#000000")
    bg_color = st.color_picker("Color del fondo", "#FFFFFF")

# Canvas
canvas_result = st_canvas(
    fill_color="rgba(255,165,0,0.3)",
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color=bg_color,
    height=350,
    width=450,
    drawing_mode="freedraw",
    key="canvas",
)

# API Key
api_key = st.text_input("API Key", type="password")
client = OpenAI(api_key=api_key) if api_key else None

# ============================
# ANALIZAR DESTINO
# ============================
if canvas_result.image_data is not None and api_key and st.button("🔮 Revela mi futuro"):
    with st.spinner("Consultando al Oráculo..."):
        # Convert canvas to PNG
        img = Image.fromarray(canvas_result.image_data.astype("uint8")).convert("RGBA")
        img.save("img.png")

        base64_img = encode_image_to_base64("img.png")
        st.session_state.base64_image = base64_img

        # Llamada correcta al modelo
        try:
            response = client.responses.create(
                model="gpt-4o-mini",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text":
                                "Eres un oráculo místico. Interpreta este dibujo con tono enigmático."},
                            {"type": "input_image", "image_url": f"data:image/png;base64,{base64_img}"}
                        ]
                    }
                ]
            )

            out = response.output[0].content[0].text
            st.session_state.full_response = out
            st.session_state.analysis_done = True

        except Exception as e:
            st.error(f"Ocurrió un error en la lectura del destino: {e}")

# ============================
# MOSTRAR DESTINO
# ============================
if st.session_state.analysis_done:
    st.subheader("𓁻 Tu destino revelado 𓁻")
    st.markdown(st.session_state.full_response)

    st.divider()
    st.subheader("¿Deseas saber la probabilidad de este futuro?")

    col1, col2 = st.columns(2)
    want_prob = col1.button("Sí, calcular probabilidad")
    want_advice = col2.button("Consejo del destino")

    # ============================
    # CONSEJO
    # ============================
    if want_advice:
        with st.spinner("Consultando consejo espiritual..."):
            prompt = (
                "Da un consejo místico basado en esta predicción: "
                f"{st.session_state.full_response}"
            )

            response = client.responses.create(
                model="gpt-4o-mini",
                input=[{"role": "user", "content":
                    [{"type":"input_text", "text": prompt}]}]
            )

            consejo = response.output[0].content[0].text

        st.subheader("⋆.˚ Consejo del destino ⋆.˚")
        st.markdown(consejo)

        # TTS
        try:
            tts = gTTS(consejo, lang="es")
            tts.save("consejo.mp3")
            st.audio(open("consejo.mp3", "rb").read())
        except:
            st.warning("No se pudo generar audio.")

    # ============================
    # PROBABILIDAD
    # ============================
    if want_prob:
        with st.spinner("Analizando probabilidad..."):
            prompt = (
                "Evalúa la siguiente predicción y responde SOLO JSON:\n"
                "{\"label\":\"ALTO|MEDIO|BAJO\", \"confidence\":0-100, \"reason\":\"breve\"}\n"
                f"Predicción: {st.session_state.full_response}"
            )

            response = client.responses.create(
                model="gpt-4o-mini",
                input=[{"role":"user", "content":[{"type":"input_text","text":prompt}]}]
            )

            out = response.output[0].content[0].text

        try:
            result = json.loads(out)
        except:
            result = {"label": "MEDIO", "confidence": 50, "reason": "Auto fallback"}

        label = result["label"].upper()
        if "ALTO" in label: label = "ALTO"
        elif "BAJO" in label: label = "BAJO"
        else: label = "MEDIO"

        angle = {"ALTO":160, "MEDIO":90, "BAJO":20}[label]

        st.session_state.probability_result = result
        st.session_state.servo_angle = angle

        st.success(f"Probabilidad: {label} — {result['confidence']}%")
        st.write(f"Motivo: {result['reason']}")
        st.write(f"Ángulo sugerido: {angle}°")

# ============================
# CONTROLES DE ARDUINO + MQTT
# ============================
if st.session_state.probability_result:
    st.divider()
    st.subheader("Servo (Arduino)")

    angle = st.session_state.servo_angle

    st.write(f"Ángulo recomendado: **{angle}°**")

    # Slider
    new_val = st.slider(
        "Valor manual (0-100)",
        0.0, 100.0,
        value=st.session_state.slider_value
    )
    st.session_state.slider_value = new_val

    colA, colB = st.columns(2)

    # ON/OFF
    if colA.button("Enviar ON"):
        ok, err = mqtt_publish("cmqtt_s", {"Act1": "ON"})
        if ok: st.success("ON enviado.")
        else: st.error(err)

    if colB.button("Enviar OFF"):
        ok, err = mqtt_publish("cmqtt_s", {"Act1": "OFF"})
        if ok: st.success("OFF enviado.")
        else: st.error(err)

    st.markdown("---")

    # Sugerido
    if st.button("Enviar ángulo sugerido"):
        percent = round((angle / 180) * 100, 2)
        payload = {"Analog": percent}
        ok, err = mqtt_publish("cmqtt_a", payload)
        if ok: st.success(f"Publicado: {payload}")
        else: st.error(err)

    # Manual
    if st.button("Enviar manual"):
        payload = {"Analog": float(new_val)}
        ok, err = mqtt_publish("cmqtt_a", payload)
        if ok: st.success(f"Publicado: {payload}")
        else: st.error(err)
