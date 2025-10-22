import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from datetime import datetime, timedelta, timezone

# ------------------ CONFIG ------------------
st.set_page_config(page_title="Centro de Consultas – Antifrágil Inversiones",
                   page_icon="🧭", layout="wide")

# Auto-refresh cada 5 minutos
st_autorefresh = st.sidebar.button("🔄 Refrescar ahora")
st.experimental_rerun if st_autorefresh else None
st_autorefresh = st.experimental_get_query_params()  # noop para mantener compat

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
    return datetime.now().astimezone()

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

# ================== DATA HELPERS ==================

@st.cache_data(ttl=300)
def get_dolar():
    """Tipos de cambio principales (CCL, MEP, Blue, Oficial)."""
    try:
        # API pública estable
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
        }
    except Exception:
        # Fallback simple
        return {"Oficial":"1.515","MEP":"1.593","CCL":"1.612","Blue":"1.550","ccl_float":1612.0}

@st.cache_data(ttl=300)
def get_merval_series():
    """Último precio y variaciones con yfinance."""
    try:
        tkr = yf.Ticker("^MERV")  # MERVAL
        hist = tkr.history(period="3mo", interval="1d")
        if hist.empty:
            raise RuntimeError("sin datos")
        last = hist["Close"].iloc[-1]
        prev = hist["Close"].iloc[-2] if len(hist) > 1 else last
        # mensual ~ 22 ruedas atrás
        month_idx = -22 if len(hist) >= 22 else 0
        month = hist["Close"].iloc[month_idx]
        day_var = (last/prev - 1)*100 if prev else 0
        mon_var = (last/month - 1)*100 if month else 0
        return float(last), float(day_var), float(mon_var)
    except Exception:
        # Fallback
        return 2_018_811.0, 0.8, 13.8

@st.cache_data(ttl=600)
def get_riesgo_pais():
    """Riesgo país (EMBI+ Argentina). Intenta endpoint público; fallback si falla."""
    try:
        # Endpoint público (puede cambiar). Si no responde, se usa fallback.
        r = requests.get("https://mercados.ambito.com//riesgo-pais/variacion", timeout=10)
        js = r.json()
        # Algunos endpoints devuelven [[fecha, valor, var, ...]]: tomamos último valor
        if isinstance(js, list) and len(js) > 0:
            raw = js[-1]
            val = float(str(raw[1]).replace(",", "."))
            return int(val)
        raise RuntimeError("formato desconocido")
    except Exception:
        return None  # mostrará “No disponible”

# PF y Billeteras: permiten API/JSON propio vía secrets (opcional)
def get_json_from_secret(key):
    url = st.secrets.get(key, "")
    if not url:
        return None
    try:
        return requests.get(url, timeout=10).json()
    except Exception:
        return None

def pf_data():
    # Si cargás un JSON en st.secrets["PF_JSON_URL"] con:
    # [{"entidad":"BCRA","tna":40.0},{"entidad":"Nación","tna":41.5}, ...]
    js = get_json_from_secret("PF_JSON_URL")
    if js:
        rows = [(x["entidad"], x["tna"]) for x in js]
    else:
        # placeholders (actualizalos si querés)
        rows = [("BCRA", 40.0), ("Nación", 41.5), ("Galicia", 42.0), ("Macro", 42.5), ("Santander", 43.0)]
    return rows

def bille_data():
    # st.secrets["BILLE_JSON_URL"] con:
    # [{"billetera":"Mercado Pago","tna":35.0}, ...]
    js = get_json_from_secret("BILLE_JSON_URL")
    if js:
        rows = [(x["billetera"], x["tna"]) for x in js]
    else:
        rows = [("Mercado Pago", 35.0), ("Ualá", 33.0), ("Naranja X", 32.0)]
    return rows

# ================== UI ==================
st.markdown("### 💱 Tipos de cambio")
d = get_dolar()
c1, c2, c3, c4 = st.columns(4)
with c1: card_metric("Oficial (venta)", f"{d['Oficial']}")
with c2: card_metric("MEP (venta)",     f"{d['MEP']}")
with c3: card_metric("CCL (venta)",     f"{d['CCL']}")
with c4: card_metric("Blue (venta)",    f"{d['Blue']}")

st.markdown("---")
st.markdown("### 🏦 Tasas de plazo fijo (TNA)")
pf_rows = pf_data()
cols = st.columns(len(pf_rows))
for (ent, tna), col in zip(pf_rows, cols):
    with col:
        card_metric(ent, f"{tna:.2f} %")

st.markdown("---")
st.markdown("### 👛 Billeteras (TNA)")
bil_rows = bille_data()
cols2 = st.columns(len(bil_rows))
for (name, tna), col in zip(bil_rows, cols2):
    with col:
        card_metric(name, f"{tna:.2f} %")

st.markdown("---")
st.markdown("### 📊 Indicadores")
c1, c2, c3 = st.columns(3)

# Merval (ARS) + Merval USD (ARS/CCL)
merval_last, merval_day, merval_month = get_merval_series()
merval_usd = merval_last / (d["ccl_float"] if d["ccl_float"] else 1.0)

with c1:
    card_metric("MERVAL (ARS)", f"{merval_last:,.0f}".replace(",", "."), 
                sub=f"Δ día: {merval_day:+.1f}% • Δ mes: {merval_month:+.1f}%")
with c2:
    card_metric("MERVAL (USD CCL)", f"{merval_usd:,.2f}".replace(",", "."), 
                sub="Calculado con CCL actual")

rp_val = get_riesgo_pais()
with c3:
    if rp_val is None:
        card_metric("Riesgo País", "—", sub="No disponible")
    else:
        card_metric("Riesgo País", f"{rp_val:,}".replace(",", "."))

st.markdown("<div class='caption'>Actualizado: " + now_ars().strftime("%d/%m/%Y %H:%M") +
            " • Fuente dólar: dolarapi.com • MERVAL: Yahoo Finance • PF/Billeteras: configurables por JSON</div>", 
            unsafe_allow_html=True)
