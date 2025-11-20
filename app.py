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
import re

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
# Session State defaults
# ============================
for key, value in {
    "analysis_done": False,
    "full_response": "",
    "base64_image": "",
    "probability_result": None,
    "servo_angle": None,
    "last_mqtt_publish": "",
    "slider_value": 0.0,
    "last_prompt_text": ""
}.items():
    st.session_state.setdefault(key, value)

# ============================
# Helpers
# ============================
def encode_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as img:
            return base64.b64encode(img.read()).decode("utf-8")
    except:
        return None

def extract_first_json(text: str):
    """
    Extrae el primer objeto JSON válido encontrado en text.
    Devuelve None si no encuentra un JSON bien formado.
    """
    if not text:
        return None
    # Buscar la primera "{" y el correspondiente "}" balanceado
    start = text.find("{")
    if start == -1:
        return None
    stack = []
    for i in range(start, len(text)):
        if text[i] == "{":
            stack.append("{")
        elif text[i] == "}":
            if not stack:
                # cierre sin apertura
                continue
            stack.pop()
            if not stack:
                candidate = text[start:i+1]
                try:
                    return json.loads(candidate)
                except Exception:
                    # intentar continuar buscando si hay otro { más adelante
                    next_start = text.find("{", start+1)
                    if next_start == -1 or next_start <= start:
                        return None
                    start = next_start
                    stack = []
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

        # Texto que el usuario verá (lo guardamos y mostramos)
        prompt_text = (
            "Eres un oráculo místico. Basado en este dibujo, interpreta el destino del usuario "
            "con símbolos, metáforas y un tono enigmático y espiritual. Evita dar instrucciones técnicas; "
            "usa un lenguaje evocador y breve."
        )
        st.session_state.last_prompt_text = prompt_text

        # Llamada correcta al modelo (con tipos correctos)
        try:
            response = client.responses.create(
                model="gpt-4o-mini",
                input=[
                    {"role": "system", "content": [{"type": "input_text", "text":
                        "Eres un oráculo místico. Responde en español."}]},
                    {"role": "user", "content": [
                        {"type": "input_text", "text": prompt_text},
                        {"type": "input_image", "image_url": f"data:image/png;base64,{base64_img}"}
                    ]}
                ],
                max_output_tokens=700,
                temperature=0.7
            )

            # Preferencia: usar output_text si existe
            content = getattr(response, "output_text", None)
            if not content:
                # intentar leer de response.output[*]
                try:
                    parts = response.output
                    # concatenar cualquier text en content entries
                    collected = []
                    for item in parts:
                        for c in item.get("content", []):
                            # algunas respuestas vienen con {"type":"output_text","text": "..."}
                            if isinstance(c, dict) and c.get("type") in ("output_text", "text"):
                                collected.append(c.get("text", ""))
                            elif isinstance(c, dict) and "text" in c:
                                collected.append(c.get("text", ""))
                            elif isinstance(c, str):
                                collected.append(c)
                    content = "\n".join(collected).strip()
                except Exception:
                    content = ""

            st.session_state.full_response = content or "El Oráculo no devolvió texto."
            st.session_state.analysis_done = True

        except Exception as e:
            st.error(f"Ocurrió un error en la lectura del destino: {e}")

# ============================
# MOSTRAR DESTINO
# ============================
if st.session_state.analysis_done:
    st.subheader("Mensaje enviado al Oráculo (prompt):")
    st.markdown(f"> {st.session_state.last_prompt_text}")

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
                "Da un consejo místico en español, breve y en tono inspirador, "
                f"basado en esta predicción:\n\n{st.session_state.full_response}"
            )

            response = client.responses.create(
                model="gpt-4o-mini",
                input=[{"role": "user", "content": [{"type":"input_text","text":prompt}]}],
                max_output_tokens=200,
                temperature=0.6
            )

            consejo = getattr(response, "output_text", None)
            if not consejo:
                # intentar leer fallback
                try:
                    consejo = response.output[0].content[0].text
                except Exception:
                    consejo = "El Oráculo no pudo generar un consejo."

        st.subheader("⋆.˚ Consejo del destino ⋆.˚")
        st.markdown(consejo)

        # TTS
        try:
            tts = gTTS(consejo, lang="es")
            tts.save("consejo.mp3")
            st.audio(open("consejo.mp3", "rb").read(), format="audio/mp3")
        except Exception:
            st.warning("No se pudo generar audio.")

    # ============================
    # PROBABILIDAD (MEJORADA) - DOS PASOS FORZADOS
    # ============================
    if want_prob:
        with st.spinner("Analizando probabilidad..."):
            # Paso 1: pensamiento libre (no usamos la salida)
            try:
                _ = client.responses.create(
                    model="gpt-4o-mini",
                    input=[
                        {"role": "system", "content": [{"type": "input_text", "text":
                            "Piensa internamente sobre la siguiente predicción y prepara una evaluación. NO respondas todavía."}]},
                        {"role": "user", "content": [{"type": "input_text", "text": st.session_state.full_response}]}
                    ],
                    max_output_tokens=200,
                    temperature=0.7
                )
            except Exception:
                # no crítico si falla el paso de pensamiento
                pass

            # Paso 2: FORZAR JSON **SIN POSIBILIDAD DE TEXTO EXTRA**
            prob_prompt = (
                "Responde únicamente con un JSON válido y NADA más. No incluyas comentarios, texto externo, "
                "ni explicaciones. El formato obligatorio es EXACTO:\n"
                "{\"label\": \"ALTO|MEDIO|BAJO\", \"confidence\": <número entre 0 y 100>, \"reason\": \"una frase breve\"}\n\n"
                "Si no puedes evaluar con certeza, devuelve confianza entre 40 y 60. "
                "Cualquier salida que no sea solo el JSON será ignorada."
            )

            try:
                final = client.responses.create(
                    model="gpt-4o-mini",
                    input=[
                        {"role": "system", "content": [{"type": "input_text", "text":
                            "Eres un generador de JSON. Responde SOLO con JSON válido en una sola línea."}]},
                        {"role": "user", "content": [{"type":"input_text","text": prob_prompt}]}
                    ],
                    max_output_tokens=120,
                    temperature=0.0
                )

                raw = getattr(final, "output_text", None) or ""
                if not raw:
                    # intentar extraer de estructura output[]
                    try:
                        parts = final.output
                        collected = []
                        for item in parts:
                            for c in item.get("content", []):
                                if isinstance(c, dict) and c.get("type") in ("output_text", "text"):
                                    collected.append(c.get("text", ""))
                                elif isinstance(c, str):
                                    collected.append(c)
                        raw = "\n".join(collected).strip()
                    except Exception:
                        raw = ""

                # Intentar parsear directo
                prob_json = None
                try:
                    prob_json = json.loads(raw)
                except Exception:
                    prob_json = extract_first_json(raw)

                # Si sigue fallando, reintento ultra-restrictivo
                if prob_json is None:
                    retry = client.responses.create(
                        model="gpt-4o-mini",
                        input=[{"role":"user","content":[{"type":"input_text","text":
                            "RESPONDE AHORA SOLO CON UN JSON VÁLIDO EN UNA LÍNEA: "
                            "{\"label\":\"ALTO|MEDIO|BAJO\",\"confidence\":<0-100>,\"reason\":\"breve\"}"}]}],
                        max_output_tokens=80,
                        temperature=0.0
                    )
                    retry_text = getattr(retry, "output_text", None) or ""
                    if not retry_text:
                        try:
                            parts = retry.output
                            collected = []
                            for item in parts:
                                for c in item.get("content", []):
                                    if isinstance(c, dict) and c.get("type") in ("output_text", "text"):
                                        collected.append(c.get("text", ""))
                                    elif isinstance(c, str):
                                        collected.append(c)
                            retry_text = "\n".join(collected).strip()
                        except Exception:
                            retry_text = ""
                    prob_json = extract_first_json(retry_text)
                    if prob_json is None:
                        try:
                            prob_json = json.loads(retry_text)
                        except Exception:
                            prob_json = None

                # Fallback final si todo falla
                if prob_json is None:
                    prob_json = {"label": "MEDIO", "confidence": 50, "reason": "No se pudo extraer JSON del modelo."}

                # Normalizar y asegurar tipos
                raw_label = str(prob_json.get("label", "MEDIO")).upper()
                if "ALTO" in raw_label:
                    normalized_label = "ALTO"
                elif "BAJO" in raw_label:
                    normalized_label = "BAJO"
                else:
                    normalized_label = "MEDIO"

                try:
                    confidence = int(float(prob_json.get("confidence", 50)))
                except Exception:
                    confidence = 50
                confidence = max(0, min(100, confidence))

                angle_map = {"ALTO": 160, "MEDIO": 90, "BAJO": 20}
                servo_angle = angle_map.get(normalized_label, 90)

                st.session_state.probability_result = {
                    "label": normalized_label,
                    "confidence": confidence,
                    "reason": prob_json.get("reason", "")
                }
                st.session_state.servo_angle = servo_angle

                st.success(f"Probabilidad: **{normalized_label}** — Confianza: **{confidence}%**")
                st.markdown(f"**Motivo:** {prob_json.get('reason', '')}")
                st.markdown(f"**Ángulo sugerido para servo:** **{servo_angle}°**")

            except Exception as e:
                st.error(f"No se pudo evaluar la probabilidad: {e}")

# ============================
# CONTROLES DE ARDUINO + MQTT
# ============================
if st.session_state.probability_result:
    st.divider()
    st.subheader("Servo (Arduino)")

    angle = st.session_state.servo_angle or 90

    st.write(f"Ángulo recomendado: **{angle}°**")

    # Slider manual (0..100)
    new_val = st.slider(
        "Valor manual (0-100)",
        0.0, 100.0,
        value=st.session_state.slider_value,
        key="manual_slider"
    )
    st.session_state.slider_value = new_val

    colA, colB = st.columns(2)

    # ON/OFF
    if colA.button("Enviar ON"):
        ok, err = mqtt_publish("cmqtt_s", {"Act1": "ON"})
        if ok:
            st.success("ON enviado.")
        else:
            st.error(err)

    if colB.button("Enviar OFF"):
        ok, err = mqtt_publish("cmqtt_s", {"Act1": "OFF"})
        if ok:
            st.success("OFF enviado.")
        else:
            st.error(err)

    st.markdown("---")

    # Enviar ángulo sugerido
    if st.button("Enviar ángulo sugerido"):
        percent = round((angle / 180) * 100, 2)
        payload = {"Analog": percent}
        ok, err = mqtt_publish("cmqtt_a", payload)
        if ok:
            st.success(f"Publicado: {payload}")
            st.session_state.last_mqtt_publish = f"Publicado Analog (sugerido): {payload}"
        else:
            st.error(err)

    # Enviar manual
    if st.button("Enviar manual"):
        payload = {"Analog": float(new_val)}
        ok, err = mqtt_publish("cmqtt_a", payload)
        if ok:
            st.success(f"Publicado: {payload}")
            st.session_state.last_mqtt_publish = f"Publicado Analog manual: {payload}"
        else:
            st.error(err)

    st.markdown("**Última publicación MQTT:**")
    st.write(st.session_state.last_mqtt_publish)
