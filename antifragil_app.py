import streamlit as st
import requests
import yfinance as yf
from datetime import datetime

# ---- CONFIGURACIÓN ----
st.set_page_config(page_title="Centro de Consultas – Antifrágil Inversiones",
                   page_icon="🧭", layout="wide")

# ---- ESTILOS ----
st.markdown("""
<style>
body, [class*="css"] {
    background-color: #121212 !important;
    color: #f3f3f3 !important;
    font-family: 'Inter', sans-serif;
}
h1 {
    text-align: center;
    font-weight: 800;
    font-size: 2.3rem;
    margin-bottom: 0.8rem;
}
.section-title {
    font-size: 1.5rem;
    font-weight: 700;
    margin-top: 1.8rem;
    margin-bottom: 1rem;
}
.card-container {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 12px;
}
.card {
    background-color: #1c1c1c;
    border-radius: 16px;
    padding: 16px;
    width: 220px;
    text-align: center;
    box-shadow: 0px 0px 8px rgba(0,0,0,0.4);
}
.card h3 {
    margin: 0;
    font-size: 1rem;
    color: #9ca3af;
}
.card .price {
    font-size: 1.6rem;
    font-weight: 700;
    margin-top: 6px;
}
.card .sub {
    font-size: 0.9rem;
    color: #9ca3af;
}
.var-up { color: #22c55e; font-weight: 600; }
.var-down { color: #ef4444; font-weight: 600; }
hr { border: 1px solid #2e2e2e; margin: 1.8rem 0; }
.footer { text-align: center; font-size: 0.8rem; color: #9ca3af; margin-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ---- FUNCIONES ----
def format_num(n):
    try:
        return f"{float(n):,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "—"

def now_str():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

@st.cache_data(ttl=300)
def get_dolar():
    try:
        data = requests.get("https://dolarapi.com/v1/dolares", timeout=10).json()
        d = {i["nombre"].lower(): i for i in data}
        return {
            "oficial": d.get("oficial", {}),
            "mep": d.get("mep", {}),
            "ccl": d.get("contadoconliqui", {}),
            "blue": d.get("blue", {})
        }
    except:
        return None

@st.cache_data(ttl=300)
def get_crypto():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,tether&vs_currencies=usd,ars"
        data = requests.get(url, timeout=10).json()
        return {
            "btc_usd": data["bitcoin"]["usd"],
            "usdt_ars": data["tether"]["ars"]
        }
    except:
        return None

@st.cache_data(ttl=300)
def get_riesgo_pais():
    try:
        data = requests.get("https://mercados.ambito.com//riesgo-pais/variacion", timeout=10).json()
        val = float(str(data[-1][1]).replace(",", "."))
        return int(val)
    except:
        return None

@st.cache_data(ttl=600)
def get_bcra_tasa():
    try:
        data = requests.get("https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/275", timeout=10).json()
        return float(data["results"][-1]["valor"])
    except:
        return None

@st.cache_data(ttl=300)
def get_merval():
    hist = yf.Ticker("^MERV").history(period="1mo")
    if hist.empty: return None
    last, prev = hist["Close"].iloc[-1], hist["Close"].iloc[-2]
    var = (last / prev - 1) * 100
    return {"valor": last, "var": var}

# ---- INTERFAZ ----
st.markdown("<h1>🧭 Centro de Consultas – Antifrágil Inversiones</h1>", unsafe_allow_html=True)

if st.button("🔄 Refrescar datos"):
    st.cache_data.clear()
    st.experimental_rerun()

# --- Tipos de cambio ---
st.markdown("<div class='section-title'>💵 Tipos de cambio</div>", unsafe_allow_html=True)
fx = get_dolar()

if fx:
    st.markdown("<div class='card-container'>", unsafe_allow_html=True)
    for key, color in zip(["oficial", "mep", "ccl", "blue"],
                          ["#9ca3af", "#3b82f6", "#f97316", "#ef4444"]):
        item = fx.get(key, {})
        comp = format_num(item.get("compra"))
        vent = format_num(item.get("venta"))
        var = item.get("variacion")
        if var:
            var_txt = f"<span class='var-up'>+{var}%</span>" if float(var) > 0 else f"<span class='var-down'>{var}%</span>"
        else:
            var_txt = ""
        st.markdown(f"""
        <div class='card' style='border:1px solid {color};'>
            <h3>{key.upper()}</h3>
            <div class='price'>Compra: {comp}</div>
            <div class='price'>Venta: {vent}</div>
            <div class='sub'>{var_txt}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.warning("No se pudieron obtener los tipos de cambio.")

# --- Criptomonedas ---
st.markdown("<div class='section-title'>🪙 Criptomonedas</div>", unsafe_allow_html=True)
crypto = get_crypto()
if crypto:
    st.markdown("<div class='card-container'>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='card' style='border:1px solid #facc15;'>
        <h3>BITCOIN (USD)</h3>
        <div class='price'>{format_num(crypto["btc_usd"])}</div>
    </div>
    <div class='card' style='border:1px solid #8b5cf6;'>
        <h3>TETHER (ARS)</h3>
        <div class='price'>{format_num(crypto["usdt_ars"])}</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.warning("No se pudieron obtener los datos de criptomonedas.")

# --- Tasas BCRA ---
st.markdown("<div class='section-title'>🏦 Tasas de referencia</div>", unsafe_allow_html=True)
tasa = get_bcra_tasa()
st.markdown("<div class='card-container'>", unsafe_allow_html=True)
st.markdown(f"""
<div class='card' style='border:1px solid #8b5cf6;'>
    <h3>Tasa Política Monetaria (TNA)</h3>
    <div class='price'>{format_num(tasa)} %</div>
</div>
<div class='card' style='border:1px solid #9ca3af;'>
    <h3>Caución 10 días</h3>
    <div class='price'>En integración</div>
</div>
""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# --- Indicadores ---
st.markdown("<div class='section-title'>📈 Indicadores de mercado</div>", unsafe_allow_html=True)
merval = get_merval()
riesgo = get_riesgo_pais()
st.markdown("<div class='card-container'>", unsafe_allow_html=True)
if merval:
    st.markdown(f"""
    <div class='card' style='border:1px solid #f97316;'>
        <h3>MERVAL (ARS)</h3>
        <div class='price'>{format_num(merval["valor"])}</div>
        <div class='sub'>{merval["var"]:+.1f}% diario</div>
    </div>
    """, unsafe_allow_html=True)
st.markdown(f"""
<div class='card' style='border:1px solid #ef4444;'>
    <h3>Riesgo País (EMBI+ AR)</h3>
    <div class='price'>{format_num(riesgo)}</div>
</div>
""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# --- FOOTER ---
st.markdown(
    f"<div class='footer'>Actualizado: {now_str()} • Dólar: dolarapi.com • Cripto: CoinGecko • BCRA: api.bcra.gob.ar • Ámbito • Yahoo Finance</div>",
    unsafe_allow_html=True)
