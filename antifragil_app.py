import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from datetime import datetime

# ================== CONFIG ==================
st.set_page_config(
    page_title="Centro de Consultas – Antifrágil Inversiones",
    page_icon="🧭",
    layout="wide",
)

# ================== ESTILOS ==================
st.markdown("""
<style>
:root {
  --bg: #0b0f14;
  --panel: #111826;
  --accent: #0EA5E9;
  --text: #E5E7EB;
  --muted: #9CA3AF;
}
html, body, [class*="css"] {
  background-color: var(--bg) !important;
  color: var(--text) !important;
  font-family: "Inter", "Segoe UI", sans-serif;
}
h1 {
  font-size: 2.4rem !important;
  color: var(--text);
  text-align: center;
  font-weight: 800;
}
h2 {
  color: var(--text);
  margin-top: 1.5rem;
  font-weight: 700;
  font-size: 1.4rem;
}
.section-icon {
  font-size: 1.6rem;
  margin-right: 6px;
}
.metric {
  background: var(--panel);
  border: 1px solid #1F2937;
  border-radius: 16px;
  padding: 14px;
  text-align: center;
  height: 100%;
}
.metric .label {
  color: var(--muted);
  font-size: 14px;
}
.metric .value {
  font-weight: 800;
  font-size: 22px;
  margin-top: 4px;
}
.caption {
  color: var(--muted);
  font-size: 13px;
  text-align: center;
}
.badge {
  display: inline-block;
  background: #064E3B;
  color: #34D399;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  margin-left: 8px;
}
hr {
  border-color: #1F2937;
  margin: 1.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# ================== FUNCIONES ==================
def now_str():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

@st.cache_data(ttl=300)
def get_dolares():
    url = "https://dolarapi.com/v1/dolares"
    r = requests.get(url, timeout=12)
    r.raise_for_status()
    data = r.json()
    by = {d["nombre"].lower(): d for d in data}
    def fmt(v):
        try:
            return f"{float(v):,.0f}".replace(",", ".")
        except: return "—"
    out = {
        "oficial": fmt(by.get("oficial", {}).get("venta")),
        "mep": fmt(by.get("mep", {}).get("venta")),
        "ccl": fmt(by.get("contadoconliqui", {}).get("venta")),
        "blue": fmt(by.get("blue", {}).get("venta"))
    }
    return out

@st.cache_data(ttl=300)
def get_merval():
    hist = yf.Ticker("^MERV").history(period="3mo", interval="1d")
    if hist.empty: return None
    last, prev = hist["Close"].iloc[-1], hist["Close"].iloc[-2]
    var_d = (last/prev - 1) * 100
    month_idx = -22 if len(hist) >= 22 else 0
    month = hist["Close"].iloc[month_idx]
    var_m = (last/month - 1) * 100
    return {"last": last, "var_d": var_d, "var_m": var_m}

@st.cache_data(ttl=600)
def get_riesgo_pais():
    try:
        r = requests.get("https://mercados.ambito.com//riesgo-pais/variacion", timeout=12)
        js = r.json()
        val = str(js[-1][1]).replace(",", ".")
        return int(float(val))
    except:
        return None

@st.cache_data(ttl=1800)
def get_bcra_tasa():
    try:
        url = "https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/275"
        r = requests.get(url, timeout=12)
        js = r.json()["results"]
        return float(js[-1]["valor"])
    except:
        return None

# ================== COMPONENTES ==================
def metric(label, value, sub=None):
    sub_html = f"<div class='caption'>{sub}</div>" if sub else ""
    st.markdown(f"""
    <div class='metric'>
      <div class='label'>{label}</div>
      <div class='value'>{value}</div>
      {sub_html}
    </div>
    """, unsafe_allow_html=True)

# ================== UI ==================

st.markdown("""
<h1>🧭 Centro de Consultas – Antifrágil Inversiones <span class="badge">en vivo</span></h1>
<p class="caption">Datos automáticos, actualizados en tiempo real. Sin valores fijos.</p>
""", unsafe_allow_html=True)

col_btn1, col_btn2 = st.columns([0.25, 0.75])
with col_btn1:
    if st.button("🔄 Refrescar ahora"):
        st.cache_data.clear()
        st.experimental_rerun()

# --- DÓLAR ---
st.markdown("<h2><span class='section-icon'>💱</span>Tipos de cambio</h2>", unsafe_allow_html=True)
try:
    fx = get_dolares()
    c1, c2, c3, c4 = st.columns(4)
    metric("Oficial (venta)", fx["oficial"])
    metric("MEP (venta)", fx["mep"])
    metric("CCL (venta)", fx["ccl"])
    metric("Blue (venta)", fx["blue"])
except:
    st.warning("No se pudieron obtener los tipos de cambio.")

# --- BRECHAS ---
st.markdown("<h2><span class='section-icon'>📊</span>Brechas cambiarias</h2>", unsafe_allow_html=True)
try:
    r = requests.get("https://dolarapi.com/v1/dolares", timeout=10).json()
    def find(n): return next((float(x['venta']) for x in r if x['nombre'].lower()==n), None)
    ofi, mep, ccl = find("oficial"), find("mep"), find("contadoconliqui")
    cols = st.columns(3)
    b1 = ((mep/ofi)-1)*100 if mep and ofi else None
    b2 = ((ccl/ofi)-1)*100 if ccl and ofi else None
    b3 = ((ccl/mep)-1)*100 if ccl and mep else None
    with cols[0]: metric("Oficial–MEP", f"{b1:.1f} %" if b1 else "—")
    with cols[1]: metric("Oficial–CCL", f"{b2:.1f} %" if b2 else "—")
    with cols[2]: metric("MEP–CCL", f"{b3:.1f} %" if b3 else "—")
except:
    st.caption("No fue posible calcular las brechas.")

st.markdown("<hr>", unsafe_allow_html=True)

# --- TASAS ---
st.markdown("<h2><span class='section-icon'>🏦</span>Tasa de referencia (BCRA)</h2>", unsafe_allow_html=True)
cols_t = st.columns(2)
tasa_bcra = get_bcra_tasa()
with cols_t[0]:
    metric("Tasa Política Monetaria (TNA)", f"{tasa_bcra:.2f} %" if tasa_bcra else "No disponible")
with cols_t[1]:
    st.markdown("""
    <div class='metric'>
      <div class='label'>Caución 10 días</div>
      <div class='value'>En integración</div>
      <div class='caption'>
        <a href='https://www.byma.com.ar/market-data/' target='_blank'>BYMA</a> ·
        <a href='https://www.mae.com.ar/estadisticas' target='_blank'>MAE</a>
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# --- INDICADORES ---
st.markdown("<h2><span class='section-icon'>📈</span>Indicadores de mercado</h2>", unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
mv = get_merval()
if mv:
    val_fmt = f"{mv['last']:,.0f}".replace(",", ".")
    sub = f"Δ día: {mv['var_d'_]()
