import streamlit as st
import pandas as pd
from datetime import datetime

# ------------------ CONFIG & ESTILO ------------------
st.set_page_config(page_title="Antifrágil – Centro de Herramientas", page_icon="🧭", layout="wide")
st.markdown("""
<style>
:root { --primary: #0B7A75; --muted:#6B7280; }
html, body, [class*="css"] { font-family: -apple-system, Inter, Segoe UI, Roboto, sans-serif; }
h1, h2, h3 { letter-spacing:-0.02em; color:#0B7A75; }
.block { background:#fff; border:1px solid #E5E7EB; border-radius:16px; padding:16px 18px; box-shadow:0 2px 10px rgba(0,0,0,.04); }
.badge { display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; background:rgba(11,122,117,.08); color:#0B7A75; font-weight:600; }
.footer { color:var(--muted); font-size:12px; margin-top:24px; }
</style>
""", unsafe_allow_html=True)

def footer():
    st.markdown(f"<div class='footer'>Antifrágil Inversiones • {datetime.now().strftime('%d/%m/%Y %H:%M')} • Info pública, no es recomendación.</div>", unsafe_allow_html=True)

st.title("Centro de Herramientas – Antifrágil Inversiones")
st.markdown("<span class='badge'>MVP – datos de ejemplo (sin APIs)</span>", unsafe_allow_html=True)
st.write("Todo en un solo lugar: Tasas PF, Billeteras, Tipo de cambio e Indicadores clave.")

# ------------------ PESTAÑAS ------------------
tab_pf, tab_bille, tab_fx, tab_ind = st.tabs([
    "🏦 Tasas de Plazo Fijo",
    "👛 Billeteras",
    "💱 Tipo de cambio",
    "📊 Indicadores"
])

# ------------------ 1) TASAS PF ------------------
with tab_pf:
    st.subheader("Tasas de Plazo Fijo (ARS)")
    st.caption("Datos orientativos de ejemplo. Podés reemplazar por APIs/scraping más adelante.")
    pf = pd.DataFrame({
        "Entidad": ["BCRA (referencia)", "Banco Nación", "Banco Galicia", "Banco Macro", "Santander"],
        "TNA (%)": [40.0, 41.5, 42.0, 42.5, 43.0],
        "TEA (%)": [48.8, 50.2, 50.9, 51.6, 52.2],
        "Plazo (días)": [30, 30, 30, 30, 30]
    })
    st.markdown("<div class='block'>", unsafe_allow_html=True)
    st.dataframe(pf, use_container_width=True, hide_index=True)
    st.bar_chart(pf.set_index("Entidad")["TNA (%)"])
    st.markdown("</div>", unsafe_allow_html=True)
    footer()

# ------------------ 2) BILLETERAS ------------------
with tab_bille:
    st.subheader("Tasas de Billeteras Virtuales")
    bille = pd.DataFrame({
        "Billetera": ["Mercado Pago", "Ualá", "Naranja X"],
        "TNA (%)": [35.0, 33.0, 32.0],
        "Notas": ["Fondo MMF ARS", "Fondo MMF ARS", "Fondo MMF ARS"],
        "Actualización": [datetime.now().strftime("%d/%m/%Y")]*3
    })
    st.markdown("<div class='block'>", unsafe_allow_html=True)
    st.dataframe(bille, use_container_width=True, hide_index=True)
    st.bar_chart(bille.set_index("Billetera")["TNA (%)"])
    st.markdown("</div>", unsafe_allow_html=True)
    footer()

# ------------------ 3) TIPO DE CAMBIO ------------------
with tab_fx:
    st.subheader("Tipo de cambio")
    fx = pd.DataFrame({
        "Ticker": ["CCL", "MEP", "Blue", "Oficial"],
        "Compra": [1070, 1030, 1000, 980],
        "Venta": [1090, 1045, 1015, 990],
        "Fuente": ["Demo"]*4,
        "Fecha": [datetime.now().strftime("%d/%m/%Y")]*4
    })
    fx["Spread (%)"] = ((fx["Venta"] - fx["Compra"]) / fx["Compra"] * 100).round(2)
    st.markdown("<div class='block'>", unsafe_allow_html=True)
    st.dataframe(fx, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1: st.metric("CCL (venta)", f"{fx.loc[0,'Venta']:.0f}")
    with col2: st.metric("MEP (venta)", f"{fx.loc[1,'Venta']:.0f}")
    footer()

# ------------------ 4) INDICADORES ------------------
with tab_ind:
    st.subheader("Indicadores: Riesgo País + Variación Merval")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Riesgo País (ejemplo)**")
        rp = pd.DataFrame({
            "Fecha": pd.date_range(end=datetime.now().date(), periods=7),
            "Valor": [1250, 1265, 1288, 1272, 1290, 1305, 1312]
        })
        st.dataframe(rp, use_container_width=True, hide_index=True)
        st.line_chart(rp.set_index("Fecha")["Valor"])
    with col2:
        st.markdown("**Merval – Variación diaria (ejemplo)**")
        mv = pd.DataFrame({
            "Fecha": pd.date_range(end=datetime.now().date(), periods=7),
            "Índice cierre": [1445000,1450000,1462000,1459000,1468000,1475000,1481000],
            "Var día (%)": [-0.85, 0.83, 0.55, -0.21, 0.62, 0.48, 0.41]
        })
        st.dataframe(mv, use_container_width=True, hide_index=True)
        st.bar_chart(mv.set_index("Fecha")["Var día (%)"])
    footer()
