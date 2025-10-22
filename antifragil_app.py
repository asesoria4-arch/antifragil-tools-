import streamlit as st
import requests
from datetime import datetime

# ------------------ CONFIG ------------------
st.set_page_config(
    page_title="Centro de Consultas – Antifrágil Inversiones",
    page_icon="💼",
    layout="wide"
)

# ------------------ ESTILOS (DólarYa-like, centrado, 2 por fila) ------------------
st.markdown("""
<style>
:root{
  --bg:#121212; --panel:#1E1E1E; --text:#f3f3f3; --muted:#bdbdbd; --line:#2e2e2e;
  --grey:#9ca3af; --blue:#3b82f6; --orange:#f97316; --red:#ef4444; --gold:#facc15; --violet:#8b5cf6;
}
html, body, [class*="css"]{ background-color:var(--bg)!important; color:var(--text)!important; font-family:Inter, system-ui, Segoe UI, Roboto, sans-serif;}
h1{ text-align:center; font-weight:800; font-size:2.2rem; margin:0.6rem 0 0.2rem;}
.header-sub{ text-align:center; color:var(--muted); margin:0 0 0.8rem; }
.section-title{ text-align:center; font-size:1.4rem; font-weight:750; margin:1.2rem 0 0.8rem; }
hr{ border:0; border-top:1px solid var(--line); margin:1.2rem 0; }

.grid{ display:grid; grid-template-columns: repeat(2, minmax(230px, 260px)); gap:14px; justify-content:center; }
@media (max-width: 620px){ .grid{ grid-template-columns: repeat(1, minmax(230px, 260px)); } }

.card{ background:var(--panel); border-radius:14px; border:1px solid rgba(255,255,255,.12);
       width:260px; height:200px; padding:16px; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; }
.card h3{ margin:0 0 6px; font-size:1.02rem; color:var(--muted); font-weight:800; letter-spacing:.2px; }
.row{ display:flex; gap:10px; align-items:baseline; }
.tag{ font-size:1.05rem; font-weight:800; }
.sub{ color:var(--muted); font-size:.86rem; margin-top:6px; }
.btnbar{ display:flex; justify-content:center; margin:.4rem 0 .6rem; }
.btn{ background:#202020; border:1px solid var(--line); color:#ddd; padding:6px 10px; border-radius:10px; font-size:.92rem; cursor:pointer; }
</style>
""", unsafe_allow_html=True)

# ------------------ HELPERS ------------------
def now_str(): return datetime.now().strftime("%d/%m/%Y %H:%M")

def fmt_num(n):
    """1 decimal, miles con coma: 12.345,6"""
    try:
        return f"{float(n):,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return None

@st.cache_data(ttl=300)
def fetch_json(url, timeout=12):
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except:
        return None

# ------------------ DATA SOURCES (con fallback suave) ------------------
@st.cache_data(ttl=300)
def get_dolares():
    """
    dolarapi.com/v1/dolares -> lista con objetos: {nombre, compra, venta, variacion?}
    Mapeamos: Oficial / MEP / ContadoConLiqui / Blue
    """
    js = fetch_json("https://dolarapi.com/v1/dolares")
    if not js:
        return None
    by = {x.get("nombre","").lower(): x for x in js}
    def pack(key):
        x = by.get(key, {})
        c, v = x.get("compra"), x.get("venta")
        return {
            "nombre": x.get("nombre"),
            "compra": c, "venta": v,
            "compra_fmt": fmt_num(c), "venta_fmt": fmt_num(v)
        }
    return {
        "oficial": pack("oficial"),
        "mep": pack("mep"),
        "ccl": pack("contadoconliqui"),
        "blue": pack("blue"),
    }

@st.cache_data(ttl=300)
def get_crypto():
    # CoinGecko simple price
    js = fetch_json("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,tether&vs_currencies=usd,ars")
    if not js: return None
    btc_usd = js.get("bitcoin",{}).get("usd")
    usdt_ars = js.get("tether",{}).get("ars")
    return {
        "btc_usd": fmt_num(btc_usd) if btc_usd is not None else None,
        "usdt_ars": fmt_num(usdt_ars) if usdt_ars is not None else None
    }

@st.cache_data(ttl=600)
def get_bcra_tpm_tna():
    # BCRA v2 Variable 275 – si no responde, None (no mostramos número inventado)
    js = fetch_json("https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/275")
    try:
        res = js.get("results") if isinstance(js, dict) else js
        if res and len(res)>0:
            return fmt_num(res[-1]["valor"])
    except:
        pass
    return None

@st.cache_data(ttl=300)
def get_riesgo_pais():
    # Ámbito: lista de listas [[fec, valor,...], ...]
    js = fetch_json("https://mercados.ambito.com//riesgo-pais/variacion")
    try:
        if isinstance(js, list) and js:
            val = float(str(js[-1][1]).replace(",", "."))
            return fmt_num(val)
    except:
        pass
    return None

@st.cache_data(ttl=300)
def get_merval_ars():
    # Yahoo chart (sin yfinance para reducir fallos)
    js = fetch_json("https://query1.finance.yahoo.com/v8/finance/chart/%5EMERV?range=1d&interval=1d")
    try:
        return float(js["chart"]["result"][0]["meta"]["regularMarketPrice"])
    except:
        return None

# ------------------ HEADER ------------------
st.markdown("<h1>💼 Centro de Consultas – Antifrágil Inversiones</h1>", unsafe_allow_html=True)
st.markdown("<div class='header-sub'>Datos en tiempo real – Tipo de cambio, tasas y mercado</div>", unsafe_allow_html=True)
st.markdown("<div class='btnbar'><button class='btn' onclick='location.reload()'>🔄 Refrescar datos</button></div>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# ------------------ SECCIÓN: TIPOS DE CAMBIO (cards cuadradas, compra/venta) ------------------
st.markdown("<div class='section-title'>💵 Tipos de cambio</div>", unsafe_allow_html=True)
fx = get_dolares()

def render_fx_cards():
    if not fx:
        st.warning("No se pudieron obtener los tipos de cambio en este momento.")
        return
    colors = {"oficial":"var(--grey)","mep":"var(--blue)","ccl":"var(--orange)","blue":"var(--red)"}
    st.markdown("<div class='grid'>", unsafe_allow_html=True)
    for key in ["oficial","mep","ccl","blue"]:
        it = fx.get(key)
        if not it: 
            continue
        if not (it["compra_fmt"] and it["venta_fmt"]):
            # Si la API no trae números, no mostramos la card para NO romper el layout visual
            continue
        title = "CCL" if key=="ccl" else key.upper()
        st.markdown(f"""
        <div class='card' style='border:1px solid {colors[key]};'>
          <h3>{title}</h3>
          <div class='row'><div class='tag'>Compra: {it['compra_fmt']}</div></div>
          <div class='row'><div class='tag'>Venta: {it['venta_fmt']}</div></div>
          <div class='sub'>&nbsp;</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

render_fx_cards()

# ------------------ SECCIÓN: CRIPTO ------------------
st.markdown("<div class='section-title'>🪙 Criptomonedas</div>", unsafe_allow_html=True)
crypto = get_crypto()
st.markdown("<div class='grid'>", unsafe_allow_html=True)
if crypto and crypto.get("btc_usd"):
    st.markdown(f"""
    <div class='card' style='border:1px solid var(--gold);'>
      <h3>BITCOIN (USD)</h3>
      <div class='tag' style='font-size:1.25rem;'>{crypto['btc_usd']}</div>
      <div class='sub'>&nbsp;</div>
    </div>
    """, unsafe_allow_html=True)
if crypto and crypto.get("usdt_ars"):
    st.markdown(f"""
    <div class='card' style='border:1px solid var(--violet);'>
      <h3>USDT (ARS)</h3>
      <div class='tag' style='font-size:1.25rem;'>{crypto['usdt_ars']}</div>
      <div class='sub'>&nbsp;</div>
    </div>
    """, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ------------------ SECCIÓN: TASAS ------------------
st.markdown("<div class='section-title'>🏦 Tasas de referencia</div>", unsafe_allow_html=True)
tpm = get_bcra_tpm_tna()
st.markdown("<div class='grid'>", unsafe_allow_html=True)
if tpm:
    st.markdown(f"""
    <div class='card' style='border:1px solid var(--violet);'>
      <h3>BCRA – TPM (TNA)</h3>
      <div class='tag' style='font-size:1.25rem;'>{tpm} %</div>
      <div class='sub'>&nbsp;</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class='card' style='border:1px solid var(--violet);'>
      <h3>BCRA – TPM (TNA)</h3>
      <div class='tag'>En actualización</div>
      <div class='sub'>Fuente: api.bcra.gob.ar</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class='card' style='border:1px solid var(--grey);'>
  <h3>Caución 10 días</h3>
  <div class='tag'>En integración</div>
  <div class='sub'>Fuentes: BYMA / MAE</div>
</div>
""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ------------------ SECCIÓN: INDICADORES (MERVAL ARS / USD CCL / RIESGO) ------------------
st.markdown("<div class='section-title'>📈 Indicadores de mercado</div>", unsafe_allow_html=True)
merval_ars = get_merval_ars()
ccl_venta = None
if fx and fx.get("ccl") and fx["ccl"]["venta"]:
    try: ccl_venta = float(fx["ccl"]["venta"])
    except: ccl_venta = None

st.markdown("<div class='grid'>", unsafe_allow_html=True)

# MERVAL ARS
if merval_ars:
    st.markdown(f"""
    <div class='card' style='border:1px solid var(--orange);'>
      <h3>MERVAL (ARS)</h3>
      <div class='tag' style='font-size:1.25rem;'>{fmt_num(merval_ars)}</div>
      <div class='sub'>&nbsp;</div>
    </div>
    """, unsafe_allow_html=True)

# MERVAL USD
if merval_ars and ccl_venta:
    merval_usd = merval_ars / ccl_venta
    st.markdown(f"""
    <div class='card' style='border:1px solid var(--blue);'>
      <h3>MERVAL (USD CCL)</h3>
      <div class='tag' style='font-size:1.25rem;'>{fmt_num(merval_usd)}</div>
      <div class='sub'>Calculado con CCL (venta)</div>
    </div>
    """, unsafe_allow_html=True)

# RIESGO PAÍS
rp = get_riesgo_pais()
if rp:
    st.markdown(f"""
    <div class='card' style='border:1px solid var(--red);'>
      <h3>Riesgo País</h3>
      <div class='tag' style='font-size:1.25rem;'>{rp}</div>
      <div class='sub'>(EMBI+ Argentina)</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class='card' style='border:1px solid var(--red);'>
      <h3>Riesgo País</h3>
      <div class='tag'>En actualización</div>
      <div class='sub'>Fuente: Ámbito</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ------------------ FOOTER ------------------
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    f"<div style='text-align:center; color:var(--muted);'>Actualizado: {now_str()} • Fuentes: DólarAPI • CoinGecko • BCRA • Ámbito • Yahoo Finance</div>",
    unsafe_allow_html=True
)
