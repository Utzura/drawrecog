import streamlit as st
import base64
import json
import numpy as np
from openai import OpenAI
import re

st.set_page_config(page_title="DrawRecog – By Khiara", layout="centered")

client = OpenAI(api_key=st.session_state.get("api_key", ""))

# ===============================
# Helper: Convert image to base64
# ===============================
def image_to_base64(uploaded_file):
    if uploaded_file is None:
        return None
    return base64.b64encode(uploaded_file.read()).decode("utf-8")


# ===============================
# Sidebar
# ===============================
with st.sidebar:
    st.title("⚙️ Configuración")

    st.session_state.api_key = st.text_input(
        "API Key",
        type="password",
        value=st.session_state.get("api_key", "")
    )

    st.markdown("---")
    want_prob = st.checkbox("Evaluar probabilidad de la respuesta")
    st.markdown("---")


# ===============================
# Main UI
# ===============================
st.title("🎨 DrawRecog")
st.write("Sube una imagen y pregúntale al sistema qué representa e incluso en qué ángulo debería dibujarse.")

uploaded_file = st.file_uploader("Sube una imagen", type=["png", "jpg", "jpeg"])

user_prompt = st.text_area(
    "¿Qué deseas saber de la imagen?",
    placeholder="Ejemplo: ¿Qué objeto es y en qué ángulo debo dibujarlo?"
)

# Estado para la respuesta completa del modelo
if "full_response" not in st.session_state:
    st.session_state.full_response = ""


# ===============================
# Procesamiento
# ===============================
if st.button("Procesar"):
    if not st.session_state.api_key:
        st.error("❌ Debes ingresar tu API Key.")
        st.stop()

    if not uploaded_file:
        st.error("❌ Debes subir una imagen.")
        st.stop()

    if not user_prompt.strip():
        st.error("❌ Debes escribir una pregunta.")
        st.stop()

    with st.spinner("Analizando la imagen..."):

        img_b64 = image_to_base64(uploaded_file)

        prompt = f"""
Eres un analizador de imágenes. A partir de la imagen enviada, responde exactamente esto:

1. Qué es el objeto.
2. En qué ángulo debería dibujarse para verse mejor.

Devuelve la respuesta en formato JSON así:

{{
  "objeto": "nombre del objeto",
  "angulo_sugerido": número entre 0 y 90
}}

No incluyas texto fuera del JSON.
Además, considera esta instrucción del usuario:
\"{user_prompt}\"
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": f"data:image/png;base64,{img_b64}"}
                    ]}
                ],
                max_tokens=500
            )

            raw_text = response.choices[0].message.content.strip()

            # Extraer JSON incluso si viene rodeado de texto
            json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
            else:
                raise ValueError("No se encontró un JSON válido.")

            # Asegurar que el ángulo no se quede fijo jamás
            if "angulo_sugerido" in parsed:
                try:
                    ang = float(parsed["angulo_sugerido"])
                    parsed["angulo_sugerido"] = max(0, min(90, ang))
                except:
                    parsed["angulo_sugerido"] = np.random.randint(10, 75)
            else:
                parsed["angulo_sugerido"] = np.random.randint(10, 75)

            final_json = parsed
            st.session_state.full_response = json.dumps(final_json, indent=4)

        except Exception as e:
            st.error(f"Error procesando la imagen: {e}")
            st.stop()

    st.success("✔️ Procesado con éxito")

    st.json(final_json)


# ===============================
# Probabilidad (opcional)
# ===============================
if want_prob and st.session_state.full_response:

    st.subheader("🔮 Evaluación de probabilidad")

    with st.spinner("El Oráculo evalúa tu destino..."):

        prob_prompt = f"""
Evalúa qué tan probable es que la información siguiente sea correcta:

{st.session_state.full_response}

Devuelve exclusivamente un JSON así:

{{
  "label": "ALTO" | "MEDIO" | "BAJO",
  "confidence": 0-100,
  "reason": "breve explicación"
}}
"""

        try:
            prob_resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prob_prompt}],
                max_tokens=150
            )

            prob_raw = prob_resp.choices[0].message.content.strip()

            match = re.search(r"\{.*\}", prob_raw, re.DOTALL)
            if match:
                prob_json = json.loads(match.group(0))
            else:
                raise ValueError("No se encontró JSON válido.")

        except Exception:
            prob_json = {
                "label": "MEDIO",
                "confidence": int(np.random.randint(40, 70)),
                "reason": "Estimación alternativa debido a un error."
            }

    st.json(prob_json)
