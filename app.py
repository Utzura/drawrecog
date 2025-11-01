# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_drawable_canvas import st_canvas
import colorsys
import re
import datetime

# =========================
# Estilos e interfaz católica
# =========================
st.set_page_config(page_title="✝️ Tablero de Oración y Color", page_icon="🕊️", layout="centered")

st.markdown("""
<style>
  :root{
    --parchment: #F8F3E7;   /* fondo pergamino */
    --ink:       #4A3B2A;   /* texto café oscuro */
    --gold:      #C5A253;   /* dorado */
    --maryblue:  #274B8A;   /* azul mariano */
  }
  html, body, .stApp{
    background: radial-gradient(900px 500px at 10% 0%, #fff9ee 0%, var(--parchment) 60%);
    color: var(--ink) !important;
  }
  h1, h2, h3, h4, h5, h6{
    color: var(--maryblue) !important;
    font-family: "Crimson Text", "Georgia", serif;
    letter-spacing: .3px;
  }
  .stButton>button{
    background: linear-gradient(90deg, var(--gold), #e3c77a) !important;
    color: #3b2d12 !important;
    border: 0 !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 10px rgba(197,162,83,.35);
  }
  .stButton>button:hover{
    filter: brightness(1.05);
  }
  .stExpander, [data-testid="stSidebar"]{
    background: #FAF6EC !important;
    border: 1px solid #eadfc6 !important;
    border-radius: 12px !important;
  }
  .stSlider, .stSelectbox, .stColorPicker{
    color: var(--ink) !important;
  }
  p, label, div, span{
    color: var(--ink) !important;
    font-family: "Inter", system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
  }
  hr{ border: none; border-top: 1px solid #e5d9bd; }
  .blessing{
    padding: 12px 14px; border-left: 4px solid var(--gold); background: #fffdf7; border-radius: 6px;
  }
</style>
""", unsafe_allow_html=True)

# =========================
# Encabezado
# =========================
st.title("✝️ Tablero de Oración y Colores Litúrgicos")
st.markdown("""
**Dibuja en silencio, ora en el corazón.**  
Que cada trazo sea una entrega a Dios. **“Señor, que todo lo que haga te glorifique.”** 🙏
""")

# =========================
# Paleta litúrgica
# =========================
st.subheader("🎨 Colores de la liturgia y su sentido")
st.markdown(
"⚪ **Blanco**: Cristo Resucitado, pureza y gozo · "
"🟩 **Verde**: esperanza y camino cotidiano · "
"🟥 **Rojo**: Espíritu Santo, amor que se entrega · "
"🟪 **Morado**: conversión, espera y misericordia · "
"🩷 **Rosado**: alegría serena en medio de la espera · "
"🖤 **Negro**: duelo y esperanza en la Vida eterna · "
"🟨 **Dorado**: solemnidad y gloria a Dios."
)

# =========================
# Sidebar (ajustes del lienzo)
# =========================
with st.sidebar:
    st.subheader("🕯️ Prepara tu espacio de oración")
    canvas_width = st.slider("Ancho del lienzo", 300, 700, 520, 20)
    canvas_height = st.slider("Alto del lienzo", 220, 600, 320, 20)

    drawing_mode = st.selectbox(
        "Herramienta",
        ("freedraw", "line", "rect", "circle", "polygon", "point", "transform"),
        index=0
    )
    stroke_width = st.slider("Grosor del trazo", 1, 30, 12)

    stroke_color = st.color_picker("Color del trazo (elige tu intención)", "#274B8A")   # azul mariano por defecto
    bg_color = st.color_picker("Color de fondo (tu “altar”)", "#F8F3E7")                # pergamino por defecto

# =========================
# Lienzo
# =========================
canvas_result = st_canvas(
    fill_color="rgba(255,255,255,0.25)",
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color=bg_color,
    height=canvas_height,
    width=canvas_width,
    drawing_mode=drawing_mode,
    key=f"canvas_{canvas_width}_{canvas_height}",
)

st.divider()
st.markdown("🕊️ *“Habla, Señor, que tu siervo escucha.”* (1 Sam 3,9)  Deja que la oración se vuelva trazo y color.")

# =========================
# Funciones espirituales
# =========================
def hex_to_hsv(hex_color: str):
    """Convierte #RRGGBB a HSV (0-360, 0-1, 0-1)."""
    m = re.fullmatch(r"#?([0-9A-Fa-f]{6})", hex_color.strip())
    if not m:
        return 0, 0, 1
    h = m.group(1)
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    hh, ss, vv = colorsys.rgb_to_hsv(r, g, b)  # h ∈ [0,1)
    return int(hh * 360), ss, vv

def color_category(hex_color: str):
    """Clasifica el color en una de las categorías litúrgicas básicas."""
    h, s, v = hex_to_hsv(hex_color)
    # Blanco / Negro por luminosidad
    if v > 0.92 and s < 0.12:
        return "blanco"
    if v < 0.14:
        return "negro"
    # Dorado (amarillos cálidos y brillantes)
    if 40 <= h <= 60 and v > 0.75:
        return "dorado"
    # Verde
    if 75 <= h <= 170:
        return "verde"
    # Rojo (incluye magentas rojizos)
    if h <= 15 or h >= 345:
        return "rojo"
    # Morado
    if 260 <= h <= 305:
        return "morado"
    # Rosado (entre rojo y morado con mucha luz)
    if 305 < h < 345 and v > 0.7:
        return "rosado"
    # Azul Mariano (no litúrgico clásico, pero devocional)
    if 185 <= h <= 250:
        return "azul"
    # Gris / transición si no encaja
    return "neutro"

# Mensajes por color con enfoque en Dios
MEDITACIONES = {
    "blanco": {
        "mensaje": "El Señor te recuerda que **la pureza del corazón** abre camino a su presencia. Pide la gracia de vivir en la **luz de Cristo Resucitado**.",
        "oracion": "Señor Jesús, limpia mi interior y hazme reflejo de tu luz. Amén.",
        "cita": "“Dichosos los limpios de corazón, porque ellos verán a Dios.” (Mt 5,8)"
    },
    "verde": {
        "mensaje": "Dios te invita a **esperar confiado** y perseverar en lo cotidiano. Él hace germinar la semilla en silencio.",
        "oracion": "Señor, fortalece mi esperanza y guía mis pasos cada día. Amén.",
        "cita": "“El Señor es mi pastor, nada me falta.” (Sal 23,1)"
    },
    "rojo": {
        "mensaje": "El Espíritu Santo **enciende el amor** que se entrega. Une tus sacrificios al de Cristo y deja que su fuego purifique.",
        "oracion": "Ven, Espíritu Santo, enciende en mí el fuego de tu amor. Amén.",
        "cita": "“Recibirán la fuerza del Espíritu Santo.” (Hch 1,8)"
    },
    "morado": {
        "mensaje": "Tiempo de **volver al Padre**. En el silencio, Dios te espera con misericordia para sanar y comenzar de nuevo.",
        "oracion": "Padre, dame un corazón humilde y dócil a tu voluntad. Amén.",
        "cita": "“Vuelvan a mí de todo corazón.” (Jl 2,12)"
    },
    "rosado": {
        "mensaje": "Dios te concede una **alegría serena** en medio del camino. Celebra las pequeñas victorias de la gracia.",
        "oracion": "Señor, enséñame a alegrarme en Ti, fuente de todo bien. Amén.",
        "cita": "“Estén siempre alegres en el Señor.” (Flp 4,4)"
    },
    "negro": {
        "mensaje": "En el duelo, **Cristo es esperanza de Vida eterna**. Él hace nuevas todas las cosas.",
        "oracion": "Señor, consuela a los que sufren y fortalécenos en tu promesa. Amén.",
        "cita": "“Yo soy la resurrección y la vida.” (Jn 11,25)"
    },
    "dorado": {
        "mensaje": "Dios merece **toda gloria**. Contempla sus maravillas y ofrécele tu vida como incienso agradable.",
        "oracion": "Dios de majestad, recibe mi alabanza y mi corazón. Amén.",
        "cita": "“Del Señor es la tierra y cuanto la llena.” (Sal 24,1)"
    },
    "azul": {
        "mensaje": "María te toma de la mano. **Aprende de su fe y docilidad**: “Hágase en mí según tu Palabra”.",
        "oracion": "Madre, llévame a Jesús y enséñame a confiar como tú. Amén.",
        "cita": "“Alégrate, llena de gracia, el Señor está contigo.” (Lc 1,28)"
    },
    "neutro": {
        "mensaje": "Dios obra también en los **tiempos de transición**. Permanece fiel: su gracia te sostiene.",
        "oracion": "Señor, aumenta mi fe mientras espero en Ti. Amén.",
        "cita": "“No temas, porque yo estoy contigo.” (Is 41,10)"
    }
}

def generar_reflexion(hex_color: str):
    cat = color_category(hex_color)
    return cat, MEDITACIONES.get(cat, MEDITACIONES["neutro"])

# =========================
# Generar reflexión según color elegido
# =========================
st.markdown("#### 🙏 Pide una palabra de Dios sobre tu oración en color")
if st.button("Generar reflexión espiritual"):
    categoria, info = generar_reflexion(stroke_color)
    etiqueta = {
        "blanco":"⚪ Blanco", "verde":"🟩 Verde", "rojo":"🟥 Rojo", "morado":"🟪 Morado",
        "rosado":"🩷 Rosado", "negro":"🖤 Negro", "dorado":"🟨 Dorado",
        "azul":"🔵 Azul (devocional)", "neutro":"🌫️ Transición"
    }[categoria]

    st.markdown(f"**Color discernido:** {etiqueta}")
    st.markdown(f"**Mensaje:** {info['mensaje']}")
    st.markdown(f"**Oración:** _{info['oracion']}_")
    st.markdown(f"**Palabra de Dios:** “_{info['cita']}_”")
    st.markdown(
        f"<div class='blessing'>Que el Señor te bendiga y te guarde. "
        f"📜 <em>{datetime.date.today().strftime('%d %b %Y')}</em></div>",
        unsafe_allow_html=True
    )

st.divider()
st.markdown("🕯️ *“Todo para mayor gloria de Dios.”* — **San Ignacio de Loyola**")
