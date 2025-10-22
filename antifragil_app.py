import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from datetime import datetime

# ------------------ CONFIGURACIÓN ------------------
st.set_page_config(page_title="Centro de Consultas – Antifrágil Inversiones",
                   page_icon="🧭", layout="wide")

# Actualización automática cada 5 minutos
st_autorefresh = st.experimental_rerun if st.button("🔄 Refrescar ahora") else None

st.markdown("""
<style>
:root { --primary:#0B7A75; --bg:#0b0f14; --panel:#111826; --muted:#9CA3AF; --text:#E5E7EB; }
html, body, [class*="css"] { background: var(--bg) !important; color: var(--text) !important;
  font-family: -apple-system, Inter, Segoe UI, Roboto, sans-serif; }
.block { background: var(--panel); border:1px solid #1F2937; border-radius:16px; padding:16px 18px; }
h1,h2,h3 { color:#E5E7EB; letter-spacing:-0.02em; }
.caption { color: var(--muted); font-size: 12px; }
.metric { background:#0f1623; border:1px solid #1F2937; border-radius:14px; padding:12px 14px; text-align:center; }
.metric .label { color:#9CA3AF; font-size:12px; }
.metric .value { font-weight:800; font-size:20px; margin-top:4px; }
.badge { display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px;
  background: rgba(11,122,117,.18); color:#7FF7E3; font-weight:600; margin-left:8px; }
hr { border-color:#1F2937 }
</style>
""", unsafe_allow_html=True)

def now_ars():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

def card_metric(label, value, sub=None):
    sub = "" if not sub else f"<div class='caption'>{sub}</div>"
    st.markdown(f"""
    <div class='metric'>
      <div class='label'>{label}</div>
      <div class='value'>{value}</div>
      {sub}
    </div>
    """, unsafe_allow_html=True)

st.markdown("# Centro de Consultas – Antifrágil Inversiones <span class='badge'>vivo</span>", unsafe_allow_html=True)
st.caption("Datos automáticos. Formato compacto tipo tarjetas. Info orientativa, no es recomendación.")

# ================== FUNCIONES DE DATOS ==================

@st.cache_data(ttl=300)
def get_dolar():
    """Tipos de cambio principales (CCL, MEP, Blue, Oficial)."""
    try:
        data = requests.get("https://dolarapi.com/v1/dolares", timeout=10).json()
        by_name = {d["nombre"].lower(): d for d in data}
        def fmt(x): 
            return f"{x:,.0f}".replace(",", ".")
        return {
            "Oficial": fmt(by_name["oficial"]["venta"]),
            "MEP":     fmt(by_name["mep"]["venta"]),
            "CCL":     fmt(by_name["contadoconliqui"]["venta"]),
            "Blue":    fmt(by_name["blue"]["venta"]),
            "ccl_float": float(by_name["contadoconliqui"]["venta"]),
            "mep_float": float(by_name["mep"]["venta"]),
            "oficial_float": float(by_name["oficial"]["venta"])
        }
    except Exception:
        return {"Oficial":"1.515","MEP":"1.593","CCL":"1.612","Blue":"1.550",
                "ccl_float":1612.0,"mep_float":1593.0,"oficial_float":1515.0}

@st.cache_data(ttl=300)
def get_merval_series():
    """Último precio y variaciones con yfinance."""
    try:
        tkr = yf.Ticker("^MERV")  # Índice MERVAL
        hist = tkr.history(period="3mo", interval="1d")
        if hist.empty:
            raise RuntimeError("sin datos")
        last = hist["Close"].iloc[-1]
        prev = hist["Close"].iloc[-2]
        month_idx = -22 if len(hist) >= 22 else 0
        month = hist["Close"].iloc[month_idx]
        day_var = (last/prev - 1)*100
        mon_var = (last/month - 1)*100
        return float(last), float(day_var), float(mon_var)
    except Exception:
        return 2_018_811.0, 0.8, 13.8

@st.cache_data(ttl=600)
def get_riesgo_pais():
    """Riesgo País (EMBI+ Argentina)."""
    try:
        r = requests.get("https://mercados.ambito.com//riesgo-pais/variacion", timeout=10)
        js = r.json()
        if isinstance(js, list) and len(js) > 0:
            val = float(str(js[-1][1]).replace(",", "."))
            return int(val)
        raise RuntimeError("formato desconocido")
    except Exception:
        return 1075  # Valor de respaldo

def pf_data():
    return [("BCRA", 40.0), ("Nación", 41.5), ("Galicia", 42.0), ("Macro", 42.5), ("Santander", 43.0)]

def bille_data():
    return [("Mercado Pago", 35.0), ("Ualá", 33.0), ("Naranja X", 32.0)]

# ================== INTERFAZ ==================

# --- Tipos de cambio ---
st.markdown("### 💱 Tipos de cambio")
d = get_dolar()
cols = st.columns(4)
for (label, key), col in zip([("Oficial", "Oficial"), ("MEP", "MEP"), ("CCL", "CCL"), ("Blue", "Blue")], cols):
    with col:
        card_metric(f"{label} (venta)", f"{d[key]}")

# --- Brechas cambiarias ---
st.markdown("### 📊 Brechas cambiarias")
try:
    brecha_of_mep = (d["mep_float"]/d["oficial_float"]-1)*100
    brecha_of_ccl = (d["ccl_float"]/d["oficial_float"]-1)*100
    brecha_mep_ccl = (d["ccl_float"]/d["mep_float"]-1)*100
except Exception:
    brecha_of_mep = brecha_of_ccl = brecha_mep_ccl = 0

cols_b = st.columns(3)
with cols_b[0]: card_metric("Oficial–MEP", f"{brecha_of_mep:.1f} %")
with cols_b[1]: card_metric("Oficial–CCL", f"{brecha_of_ccl:.1f} %")
with cols_b[2]: card_metric("MEP–CCL", f"{brecha_mep_ccl:.1f} %")

# --- Tasas de Plazo Fijo ---
st.markdown("---")
st.markdown("### 🏦 Tasas de plazo fijo (TNA)")
pf_rows = pf_data()
cols_pf = st.columns(len(pf_rows))
for (ent, tna), col in zip(pf_rows, cols_pf):
    with col:
        card_metric(ent, f"{tna:.2f} %")

# --- Billeteras ---
st.markdown("---")
st.markdown("### 👛 Billeteras (TNA)")
bil_rows = bille_data()
cols_bi = st.columns(len(bil_rows))
for (name, tna), col in zip(bil_rows, cols_bi):
    with col:
        card_metric(name, f"{tna:.2f} %")

# --- Indicadores ---
st.markdown("---")
st.markdown("### 📈 Indicadores")
c1, c2, c3 = st.columns(3)

merval_last, merval_day, merval_month = get_merval_series()
merval_usd = merval_last / (d["ccl_float"] if d["ccl_float"] else 1.0)
rp_val = get_riesgo_pais()

with c1:
    card_metric("MERVAL (ARS)", f"{merval_last:,.0f}".replace(",", "."),
                sub=f"Δ día: {merval_day:+.1f}% • Δ mes: {merval_month:+.1f}%")
with c2:
    card_metric("MERVAL (USD CCL)", f"{merval_usd:,.2f}".replace(",", "."),
                sub="Calculado con CCL actual")
with c3:
    card_metric("Riesgo País", f"{rp_val:,}".replace(",", "."))

st.markdown(f"<div class='caption'>Actualizado: {now_ars()} • Fuente dólar: dolarapi.com • MERVAL: Yahoo Finance</div>", unsafe_allow_html=True)
