import streamlit as st
import requests
from datetime import datetime

# ============== CONFIG ==============
st.set_page_config(
    page_title="Centro de Consultas – Antifrágil Inversiones",
    page_icon="💼",
    layout="wide",
)

# ============== ESTILOS ==============
st.markdown("""
<style>
:root{
  --bg:#121212; --panel:#1E1E1E; --text:#f3f3f3; --muted:#bdbdbd;
  --grey:#9ca3af; --blue:#3b82f6; --orange:#f97316; --red:#ef4444;
  --gold:#facc15; --violet:#8b5cf6; --line:#2e2e2e;
}
html, body, [class*="css"]{ background-color:var(--bg)!important; color:var(--text)!important; font-family:Inter, system-ui, Segoe UI, Roboto, sans-serif;}

h1{ text-align:center; font-weight:800; font-size:2.3rem; margin:0.6rem 0 0.2rem;}
.header-sub{ text-align:center; color:var(--muted); margin:0 0 0.6rem; }

.section-title{ text-align:center; font-size:1.5rem; font-weight:700; margin:1.4rem 0 0.8rem; }
hr{ border:0; border-top:1px solid var(--line); margin:1.5rem 0; }

.grid { display:grid; grid-template-columns: repeat(2, 240px); gap:14px; justify-content:center; }
@media (max-width: 620px){ .grid{ grid-template-columns: repeat(1, 240px);} }

.card { background:var(--panel); border:1px solid rgba(255,255,255,.1); border-radius:14px;
        width:240px; height:200px; padding:16px; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center; }
.card h3{ margin:0 0 6px; font-size:1.05rem; color:var(--muted); font-weight:700; }
.row { display:flex; gap:10px; }
.tag { font-size:0.86rem; font-weight:700; }
.small { color:var(--muted); font-size:0.85rem; margin-top:6px; }
.buttonbar { display:flex; justify-content:center; margin:6px 0 10px; }
.btn { background:#222; border:1px solid var(--line); color:#ddd; padding:6px 10px; border-radius:10px; font-size:0.9rem; }
</style>
""", unsafe_allow_html=True)

# ============== UTILS ==============
def now_str(): return datetime.now().strftime("%d/%m/%Y %H:%M")

def fmt_num(n):
    """ 1 decimal, miles con coma y decimales con punto: 12.345,6 """
    try:
        return f"{float(n):,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return None

@st.cache_data(ttl=300)
def fetch_json(url):
    try:
        r = requests.get(url, timeout=12)
        r.raise_for_status()
        return r.json()
    except:
        return None

# ============== DATA SOURCES ==============
@st.cache_data(ttl=300)
def get_dolares():
    """
    DólarAPI: lista de objetos con campos:
    {"nombre":"Oficial","compra":xxx,"venta":yyy, ...}
    """
    data = fetch_json("https://dolarapi.com/v1/dolares")
    if not data:
        return None
    by = {d["nombre"].lower(): d for d in data if "nombre" in d}
    def pack(k):
        x = by.get(k, {})
        return {
            "nombre": x.get("nombre"),
            "compra": x.get("compra"),
            "venta": x.get("venta"),
            "compra_fmt": fmt_num(x.get("compra")),
            "venta_fmt": fmt_num(x.get("venta")),
        }
    return {
        "oficial": pack("oficial"),
        "mep": pack("mep"),
        "ccl": pack("contadoconliqui"),
        "blue": pack("blue"),
    }

@st.cache_data(ttl=300)
def get_crypto():
    js = fetch_json("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,tether&vs_currencies=usd,ars")
    if not js: return None
    return {
        "btc_usd": fmt_num(js.get("bitcoin", {}).get("usd")),
        "usdt_ars": fmt_num(js.get("tether", {}).get("ars")),
    }

@st.cache_data(ttl=600)
def get_bcra_tpm_tna():
    # BCRA v2 variable 275 – si falla, None
    js = fetch_json("https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/275")
    try:
        res = js.get("results") if isinstance(js, dict) else js
        if not res: return None
        val = res[-1]["valor"]
        return fmt_num(val)
    except:
        return None

@st.cache_data(ttl=300)
def get_riesgo_pais():
    # Ámbito: lista de listas [[fecha, valor, ...], ...]
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
    # Yahoo chart endpoint simple (evita dependencia externa)
    js = fetch_json("https://query1.finance.yahoo.com/v8/finance/chart/%5EMERV?range=1d&interval=1d")
    try:
        last = js["chart"]["result"][0]["meta"]["regularMarketPrice"]
        return float(last)
    except:
        return None

# ============== HEADER ==============
st.markdown("<h1>💼 Centro de Consultas – Antifrágil Inversiones</h1>", unsafe_allow_html=True)
st.markdown("<div class='header-sub'>Datos en tiempo real – Tipo de cambio, tasas y mercado</div>", unsafe_allow_html=True)
st.markdown("<div class='buttonbar'><button class='btn' onclick='window.location.reload()'>🔄 Refrescar datos</button></div>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# ============== SECCIÓN: TIPOS DE CAMBIO (cards cuadradas, compra+venta) ==============
st.markdown("<div class='section-title'>💵 Tipos de cambio</div>", unsafe_allow_html=True)
fx = get_dolares()

def render_fx_grid():
    if not fx:
        st.warning("No se pudieron obtener los tipos de cambio en este momento.")
        return
    # colores por tipo
    colors = {
        "oficial": "var(--grey)",
        "mep": "var(--blue)",
        "ccl": "var(--orange)",
        "blue": "var(--red)",
    }
    # grid 2 por fila
    st.markdown("<div class='grid'>", unsafe_allow_html=True)
    for key in ["oficial", "mep", "ccl", "blue"]:
        item = fx.get(key)
        if not item: 
            continue
        compra = item["compra_fmt"]
        venta  = item["venta_fmt"]
        if not (compra and venta):
            # si una API viene vacía, no mostramos card
            continue
        title = key.upper() if key != "ccl" else "CCL"
        st.markdown(f"""
        <div class='card' style='border:1px solid {colors[key]};'>
          <h3>{title}</h3>
          <div class='row'>
            <div class='tag'>Compra:&nbsp;{compra}</div>
          </div>
          <div class='row' style='margin-top:4px;'>
            <div class='tag'>Venta:&nbsp;{venta}</div>
          </div>
          <div class='small'>&nbsp;</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

render_fx_grid()

# ============== SECCIÓN: CRIPTOS (BTC/USDT) ==============
st.markdown("<div class='section-title'>🪙 Criptomonedas</div>", unsafe_allow_html=True)
crypto = get_crypto()
def render_crypto_grid():
    st.markdown("<div class='grid'>", unsafe_allow_html=True)
    if crypto and crypto.get("btc_usd"):
        st.markdown(f"""
        <div class='card' style='border:1px solid var(--gold);'>
          <h3>BITCOIN (USD)</h3>
          <div class='tag' style='font-size:1.3rem;'>{crypto['btc_usd']}</div>
          <div class='small'>&nbsp;</div>
        </div>
        """, unsafe_allow_html=True)
    if crypto and crypto.get("usdt_ars"):
        st.markdown(f"""
        <div class='card' style='border:1px solid var(--violet);'>
          <h3>USDT (ARS)</h3>
          <div class='tag' style='font-size:1.3rem;'>{crypto['usdt_ars']}</div>
          <div class='small'>&nbsp;</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
render_crypto_grid()

# ============== SECCIÓN: TASAS (BCRA + Caución) ==============
st.markdown("<div class='section-title'>🏦 Tasas de referencia</div>", unsafe_allow_html=True)
tpm = get_bcra_tpm_tna()
st.markdown("<div class='grid'>", unsafe_allow_html=True)
if tpm:
    st.markdown(f"""
    <div class='card' style='border:1px solid var(--violet);'>
      <h3>BCRA – TPM (TNA)</h3>
      <div class='tag' style='font-size:1.3rem;'>{tpm} %</div>
      <div class='small'>&nbsp;</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class='card' style='border:1px solid var(--violet);'>
      <h3>BCRA – TPM (TNA)</h3>
      <div class='tag'>No disponible</div>
      <div class='small'>Fuente: api.bcra.gob.ar</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"""
<div class='card' style='border:1px solid var(--grey);'>
  <h3>Caución 10 días</h3>
  <div class='tag'>En integración</div>
  <div class='small'>Fuentes: BYMA / MAE</div>
</div>
""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ============== SECCIÓN: INDICADORES (MERVAL ARS / USD CCL / Riesgo país) ==============
st.markdown("<div class='section-title'>📈 Indicadores de mercado</div>", unsafe_allow_html=True)
merval_ars = get_merval_ars()
ccl_venta = None
if fx and fx.get("ccl") and fx["ccl"]["venta"]:
    try:
        ccl_venta = float(fx["ccl"]["venta"])
    except:
        ccl_venta = None

st.markdown("<div class='grid'>", unsafe_allow_html=True)

# MERVAL ARS
if merval_ars:
    st.markdown(f"""
    <div class='card' style='border:1px solid var(--orange);'>
      <h3>MERVAL (ARS)</h3>
      <div class='tag' style='font-size:1.3rem;'>{fmt_num(merval_ars)}</div>
      <div class='small'>&nbsp;</div>
    </div>
    """, unsafe_allow_html=True)

# MERVAL USD (CCL)
if merval_ars and ccl_venta:
    merval_usd = merval_ars / ccl_venta
    st.markdown(f"""
    <div class='card' style='border:1px solid var(--blue);'>
      <h3>MERVAL (USD CCL)</h3>
      <div class='tag' style='font-size:1.3rem;'>{fmt_num(merval_usd)}</div>
      <div class='small'>Calculado con CCL (venta)</div>
    </div>
    """, unsafe_allow_html=True)

# Riesgo País
rp = get_riesgo_pais()
if rp:
    st.markdown(f"""
    <div class='card' style='border:1px solid var(--red);'>
      <h3>Riesgo País</h3>
      <div class='tag' style='font-size:1.3rem;'>{rp}</div>
      <div class='small'>(EMBI+ Argentina)</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class='card' style='border:1px solid var(--red);'>
      <h3>Riesgo País</h3>
      <div class='tag'>No disponible</div>
      <div class='small'>Fuente: Ámbito</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ============== FOOTER ==============
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    f"<div style='text-align:center; color:var(--muted);'>Actualizado: {now_str()} • Fuentes: DólarAPI • CoinGecko • BCRA • Ámbito • Yahoo Finance</div>",
    unsafe_allow_html=True
)
