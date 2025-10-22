import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from datetime import datetime

# --- CONFIG ---
st.set_page_config(
    page_title="Centro de Consultas – Antifrágil Inversiones",
    page_icon="🧭",
    layout="wide",
)

# --- ESTILOS ---
st.markdown("""
<style>
:root {
  --bg: #0b0f14;
  --panel: #111826;
  --text: #E5E7EB;
  --muted: #9CA3AF;
  --blue: #2563EB;
  --red: #DC2626;
  --orange: #F97316;
  --violet: #8B5CF6;
  --grey: #6B7280;
}
html, body, [class*="css"] {
  background-color: var(--bg) !important;
  color: var(--text) !important;
  font-family: "Inter", "Segoe UI", sans-serif;
}
h1 { font-size:2.4rem !important; text-align:center; font-weight:800; }
h2 { margin-top:1.5rem; font-weight:700; font-size:1.4rem; }
.card-row { display:flex; gap:12px; flex-wrap:wrap; }
.card { background:var(--panel); border:1px solid #1F2937; border-radius:16px; flex:1 1 22%; min-width:200px; padding:14px; text-align:center;}
.label { color:var(--muted); font-size:14px; }
.value { font-size:22px; font-weight:800; margin-top:4px; }
.sub { color:var(--muted); font-size:13px; margin-top:4px; }
.badge { display:inline-block; background:#064E3B; color:#34D399; font-size:12px; padding:4px 10px; border-radius:999px; margin-left:8px; }
hr { border-color:#1F2937; margin:1.5rem 0; }
</style>
""", unsafe_allow_html=True)

def now_str():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

def card(label, value, sub=None, color=None):
    clr = ""
    if color:
        clr = f"style='color:{color};'"
    sub_html = f"<div class='sub'>{sub}</div>" if sub else ""
    st.markdown(f"""
      <div class='card' {clr}>
        <div class='label'>{label}</div>
        <div class='value'>{value}</div>
        {sub_html}
      </div>
    """, unsafe_allow_html=True)

# --- DATOS ---
@st.cache_data(ttl=300)
def get_dolares():
    url="https://dolarapi.com/v1/dolares"
    r=requests.get(url,timeout=12); r.raise_for_status()
    data=r.json()
    by={d["nombre"].lower():d for d in data}
    def fmt(v):
        try: return f"{float(v):,.0f}".replace(",","." )
        except: return "—"
    return {
      "Oficial": fmt(by.get("oficial",{}).get("venta")),
      "MEP": fmt(by.get("mep",{}).get("venta")),
      "CCL": fmt(by.get("contadoconliqui",{}).get("venta")),
      "Blue": fmt(by.get("blue",{}).get("venta")),
      "of_float": float(by.get("oficial",{}).get("venta") or 0),
      "mep_float": float(by.get("mep",{}).get("venta") or 0),
      "ccl_float": float(by.get("contadoconliqui",{}).get("venta") or 0),
    }

@st.cache_data(ttl=300)
def get_crypto():
    # ejemplo con CoinGecko
    try:
        r=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,tether&vs_currencies=usd,ars",timeout=12)
        r.raise_for_status()
        js=r.json()
        btc_usd = js["bitcoin"]["usd"]
        usdt_ars = js["tether"]["ars"]
        return {"BTC_USD": btc_usd, "USDT_ARS": usdt_ars}
    except:
        return {"BTC_USD": None, "USDT_ARS": None}

@st.cache_data(ttl=300)
def get_merval():
    hist = yf.Ticker("^MERV").history(period="3mo", interval="1d")
    if hist.empty: return None
    last=float(hist["Close"].iloc[-1]); prev=float(hist["Close"].iloc[-2])
    var_d = (last/prev-1)*100
    m_idx=-22 if len(hist)>=22 else 0; month=float(hist["Close"].iloc[m_idx])
    var_m=(last/month-1)*100 if month else 0
    return {"last": last, "var_d":var_d, "var_m":var_m}

@st.cache_data(ttl=600)
def get_riesgo_pais():
    try:
        r=requests.get("https://mercados.ambito.com//riesgo-pais/variacion",timeout=12)
        r.raise_for_status()
        js=r.json()
        val=str(js[-1][1]).replace(",","." )
        return int(float(val))
    except:
        return None

@st.cache_data(ttl=1800)
def get_bcra_tasa():
    try:
        url="https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/275"
        r=requests.get(url,timeout=12); r.raise_for_status()
        js=r.json()["results"]
        return float(js[-1]["valor"])
    except:
        return None

# --- INTERFAZ ---
st.markdown(f"<h1>🧭 Centro de Consultas – Antifrágil Inversiones <span class='badge'>en vivo</span></h1>", unsafe_allow_html=True)

if st.button("🔄 Refrescar ahora"):
    st.cache_data.clear()
    st.experimental_rerun()

# --- Sección 1: Tipos de cambio ---
st.markdown("<h2><span class='section-icon'>💱</span>Tipos de cambio</h2>", unsafe_allow_html=True)
fx=get_dolares()
# mostrar 4 por fila:
with st.container():
    card("Oficial (venta)", fx["Oficial"], color="var(--grey)")
    card("MEP (venta)", fx["MEP"], color="var(--blue)")
    card("CCL (venta)", fx["CCL"], color="var(--orange)")
    card("Blue (venta)", fx["Blue"], color="var(--red)")

# Brechas
st.markdown("<h2><span class='section-icon'>📊</span>Brechas cambiarias</h2>", unsafe_allow_html=True)
ofv=fx["of_float"]; mepv=fx["mep_float"]; cclv=fx["ccl_float"]
try:
    b1=(mepv/ofv-1)*100; b2=(cclv/ofv-1)*100; b3=(cclv/mepv-1)*100
    with st.container():
        card("Oficial–MEP", f"{b1:.1f} %", color="var(--blue)")
        card("Oficial–CCL", f"{b2:.1f} %", color="var(--orange)")
        card("MEP–CCL", f"{b3:.1f} %", color="var(--violet)")
except:
    st.caption("Brechas no calculables en este momento.")

st.markdown("<hr>", unsafe_allow_html=True)

# Sección 2: Tasas BCRA + Caución placeholder
st.markdown("<h2><span class='section-icon'>🏦</span>Tasa de referencia (BCRA)</h2>", unsafe_allow_html=True)
cols=st.columns(2)
t_bcra=get_bcra_tasa()
with cols[0]:
    card("Tasa Política Monetaria (TNA)", f"{t_bcra:.2f} %" if t_bcra else "No disponible", color="var(--violet)")
with cols[1]:
    card("Caución 10 días", "En integración", sub="Fuente: BYMA / MAE", color="var(--grey)")

st.markdown("<hr>", unsafe_allow_html=True)

# Sección 3: Criptos
st.markdown("<h2><span class='section-icon'>🪙</span>Criptomonedas</h2>", unsafe_allow_html=True)
crypto=get_crypto()
with st.container():
    card("Bitcoin (USD)", f"{crypto['BTC_USD']:.2f}" if crypto['BTC_USD'] else "No disponible", color="var(--blue)")
    card("Tether (ARS)", f"{crypto['USDT_ARS']:.2f}" if crypto['USDT_ARS'] else "No disponible", color="var(--grey)")

st.markdown("<hr>", unsafe_allow_html=True)

# Sección 4: Indicadores de mercado
st.markdown("<h2><span class='section-icon'>📈</span>Indicadores de mercado</h2>", unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
mv=get_merval()
if mv:
    card("MERVAL (ARS)", f"{mv['last']:,.0f}".replace(",", "."), sub=f"Δ día: {mv['var_d']:+.1f}% • Δ mes: {mv['var_m']:+.1f}%", color="var(--orange)")
    fx2=get_dolares()
    if fx2["ccl_float"]:
        card("MERVAL (USD CCL)", f"{mv['last']/fx2['ccl_float']:.2f}".replace(",", "."), color="var(--blue)")
else:
    card("MERVAL (ARS)", "No disponible", color="var(--grey)")
rp=get_riesgo_pais()
card("Riesgo País (EMBI+ AR)", f"{rp:,}".replace(",", ".") if rp else "No disponible", color="var(--red)")

# Footer
st.markdown(f"<div class='caption'>Actualizado: {now_str()} • Dólar: dolarapi.com • BCRA: api.bcra.gob.ar • MERVAL: Yahoo Finance • Cripto: CoinGecko • Riesgo País: Ámbito</div>", unsafe_allow_html=True)
