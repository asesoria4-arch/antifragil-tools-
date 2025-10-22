import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ===========================
# CONFIGURACIÓN DE PÁGINA
# ===========================
st.set_page_config(page_title="Centro de Consultas – Antifrágil Inversiones", page_icon="💼", layout="centered")

# ===========================
# ESTILO GLOBAL
# ===========================
st.markdown("""
    <style>
    body {background-color: #121212 !important;}
    .main {background-color: #121212;}
    div[data-testid="stMetricValue"] {font-size: 22px; font-weight: bold;}
    .card {
        background-color: #1E1E1E;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        color: white;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 0 10px rgba(0,0,0,0.3);
        width: 190px; height: 190px;
        display: flex; flex-direction: column; justify-content: center;
    }
    .section-title {
        font-size: 22px; font-weight: 700; margin-top: 25px;
        display: flex; align-items: center; gap: 10px;
    }
    .subtitle {
        font-size: 13px; color: #bdbdbd;
    }
    </style>
""", unsafe_allow_html=True)

# ===========================
# ENCABEZADO
# ===========================
st.markdown("<h1 style='text-align:center;'>💼 Centro de Consultas – Antifrágil Inversiones</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray;'>Datos en tiempo real – Tipo de cambio, tasas y mercado</p>", unsafe_allow_html=True)
st.markdown("---")

if st.button("🔄 Refrescar datos"):
    st.experimental_rerun()

# ===========================
# FUNCIONES AUXILIARES
# ===========================
@st.cache_data(ttl=600)
def get_json(url):
    try:
        return requests.get(url, timeout=10).json()
    except:
        return None

def fmt_num(value):
    if value is None:
        return "—"
    try:
        return f"{float(value):,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "—"

# ===========================
# DATOS
# ===========================
# Tipos de cambio
dolar_data = get_json("https://dolarapi.com/v1/dolares")
d = {d["casa"]: d for d in dolar_data} if dolar_data else {}

# Criptos
crypto_data = get_json("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,tether&vs_currencies=usd,ars")
btc_usd = crypto_data.get("bitcoin", {}).get("usd", None)
usdt_ars = crypto_data.get("tether", {}).get("ars", None)

# Tasas y riesgo
tasa_data = get_json("https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/275")
riesgo_data = get_json("https://mercados.ambito.com//riesgo-pais/variacion")

# MERVAL
merval_ars = 0
merval_usd = 0
try:
    merval = get_json("https://query1.finance.yahoo.com/v8/finance/chart/%5EMERV?range=1d&interval=1d")
    merval_ars = merval["chart"]["result"][0]["meta"]["regularMarketPrice"]
except:
    merval_ars = None

ccl_val = d.get("CCL", {}).get("venta", None)
if merval_ars and ccl_val:
    merval_usd = merval_ars / float(ccl_val)

# ===========================
# SECCIÓN 1: TIPOS DE CAMBIO
# ===========================
st.markdown("<div class='section-title'>💵 Tipos de cambio</div>", unsafe_allow_html=True)
cols = st.columns(4, gap="large")

cards = [
    ("OFICIAL", d.get("oficial", {}).get("compra"), d.get("oficial", {}).get("venta")),
    ("MEP", d.get("mep", {}).get("compra"), d.get("mep", {}).get("venta")),
    ("CCL", d.get("ccl", {}).get("compra"), d.get("ccl", {}).get("venta")),
    ("BLUE", d.get("blue", {}).get("compra"), d.get("blue", {}).get("venta")),
]

for i, (nombre, compra, venta) in enumerate(cards):
    with cols[i % 4]:
        st.markdown(f"""
        <div class='card'>
            <div class='subtitle'>{nombre}</div>
            <b>Compra:</b> {fmt_num(compra)}<br>
            <b>Venta:</b> {fmt_num(venta)}
        </div>
        """, unsafe_allow_html=True)

# ===========================
# SECCIÓN 2: CRIPTOS
# ===========================
st.markdown("<div class='section-title'>🪙 Criptomonedas</div>", unsafe_allow_html=True)
cols = st.columns(2, gap="large")

with cols[0]:
    st.markdown(f"""
        <div class='card'>
            <div class='subtitle'>Bitcoin (USD)</div>
            <b>{fmt_num(btc_usd)}</b>
        </div>
        """, unsafe_allow_html=True)

with cols[1]:
    st.markdown(f"""
        <div class='card'>
            <div class='subtitle'>Tether (ARS)</div>
            <b>{fmt_num(usdt_ars)}</b>
        </div>
        """, unsafe_allow_html=True)

# ===========================
# SECCIÓN 3: TASAS
# ===========================
st.markdown("<div class='section-title'>🏦 Tasas de referencia</div>", unsafe_allow_html=True)
cols = st.columns(2, gap="large")

tasa_bcra = None
try:
    if tasa_data and len(tasa_data["results"]) > 0:
        tasa_bcra = tasa_data["results"][-1]["valor"]
except:
    tasa_bcra = None

with cols[0]:
    st.markdown(f"""
        <div class='card'>
            <div class='subtitle'>Tasa Política Monetaria (TNA)</div>
            <b>{fmt_num(tasa_bcra)}%</b>
        </div>
        """, unsafe_allow_html=True)

with cols[1]:
    st.markdown(f"""
        <div class='card'>
            <div class='subtitle'>Caución 10 días</div>
            <b>En integración</b>
        </div>
        """, unsafe_allow_html=True)

# ===========================
# SECCIÓN 4: MERCADO
# ===========================
st.markdown("<div class='section-title'>📈 Indicadores de mercado</div>", unsafe_allow_html=True)
cols = st.columns(2, gap="large")

with cols[0]:
    st.markdown(f"""
        <div class='card'>
            <div class='subtitle'>MERVAL (ARS)</div>
            <b>{fmt_num(merval_ars)}</b>
        </div>
        """, unsafe_allow_html=True)

with cols[1]:
    st.markdown(f"""
        <div class='card'>
            <div class='subtitle'>MERVAL (USD CCL)</div>
            <b>{fmt_num(merval_usd)}</b>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Riesgo país
rp = None
try:
    rp = riesgo_data.get("valor", None)
except:
    rp = None

st.markdown(f"""
    <div style='text-align:center; color:{"#ff4b4b" if not rp else "white"}'>
    <b>Riesgo País (EMBI+AR):</b> {fmt_num(rp)}
    </div>
""", unsafe_allow_html=True)

# ===========================
# FOOTER
# ===========================
st.markdown("---")
st.markdown(
    f"<div class='subtitle' style='text-align:center;'>Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')} • "
    "Fuentes: dolarapi.com | CoinGecko | BCRA | Ámbito | Yahoo Finance</div>",
    unsafe_allow_html=True
)
