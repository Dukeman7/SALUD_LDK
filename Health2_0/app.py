import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import io

# --- 1. COORDENADAS ---
SHEET_ID = "1MT2EYKUmKmAP8vSBbPElR_DsP45zgrczDTMXe1b9s5Y" 
URL_LECTURA = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet=CONTROL"
URL_ESCRITURA = "https://script.google.com/macros/s/AKfycbxHsIEBnMN3KrIof9bB5BM_-RbLWXa-t2A8JfPmuHgYQiRhqLFdhYcxdymBz_ELMK94SA/exec"

st.set_page_config(page_title="Búnker Health: Meta Junio 28", layout="wide")

def load_data():
    try:
        response = requests.get(URL_LECTURA)
        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
        df.columns = df.columns.str.strip()
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df['Glucosa'] = pd.to_numeric(df['Glucosa'], errors='coerce')
        if 'Peso' in df.columns:
            df['Peso'] = pd.to_numeric(df['Peso'], errors='coerce')
        return df.dropna(subset=['Fecha']).sort_values('Fecha')
    except:
        return pd.DataFrame(columns=['Fecha', 'Glucosa', 'Peso'])

df = load_data()

# --- 2. CÁLCULOS DE PROSPECTIVA (EL CORAZÓN) ---
# Glucosa Plan 91
f_base_g = pd.to_datetime('2026-02-24')
t_fut_g = np.arange(92)
v_fut_g = (122 - 90) * np.exp(-0.08 * t_fut_g) + 90
fechas_g = [f_base_g + timedelta(days=int(i)) for i in t_fut_g]

# Peso Meta Cumpleaños (1 de Marzo -> 28 de Junio)
f_inicio_p = pd.to_datetime('2026-03-01')
f_meta_p = pd.to_datetime('2026-06-28')
dias_total_p = (f_meta_p - f_inicio_p).days
# Generamos la línea lineal 123.5 -> 115
fechas_p = [f_inicio_p + timedelta(days=i) for i in range(dias_total_p + 1)]
proyeccion_p = np.linspace(123.5, 115, len(fechas_p))

# --- 3. INTERFAZ ---
st.title("🛡️ Búnker Health: Operación 28-Junio")

if not df.empty:
    ult_g = df['Glucosa'].iloc[-1]
    ult_p = df['Peso'].dropna().iloc[-1] if 'Peso' in df.columns and not df['Peso'].dropna().empty else 123.5
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Glucosa Actual", f"{ult_g:.0f}", delta=f"{ult_g-90:.0f} pto meta", delta_color="inverse" if ult_g > 130 else "normal")
    c2.metric("Peso Actual", f"{ult_p:.1f} kg", delta=f"{ult_p-115:.1f} kg p/meta")
    c3.metric("Meta Cumpleaños", "115 kg")
    c4.metric("Días para el 28-Jun", (f_meta_p - datetime.now()).days)

    # --- 4. GRAFICADOR MAESTRO ---
    fig = go.Figure()

    # GLUCOSA: Plan 91 (Rosa Tatuada)
    fig.add_trace(go.Scatter(x=fechas_g, y=v_fut_g, name="Meta Glucosa (90)",
                             line=dict(color='#ff4081', dash='dot', width=2)))
    
    # GLUCOSA: Realidad (Cian)
    fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Glucosa'], name="Realidad Glucosa",
                             line=dict(color='#00e5ff', width=4), mode='lines+markers'))

    # PESO: Proyección Cumpleaños (Amarillo Tenue)
    fig.add_trace(go.Scatter(x=fechas_p, y=proyeccion_p, name="Rumbo a 115kg (Jun-28)",
                             line=dict(color='rgba(255, 255, 0, 0.3)', dash='dash', width=2)))

    # PESO: Registro Real (Amarillo Brillante Dash)
    if 'Peso' in df.columns:
        fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Peso'], name="Peso Real (kg)",
                                 line=dict(color='yellow', width=4, dash='dash'),
                                 connectgaps=True, mode='lines+markers',
                                 marker=dict(size=10, symbol='diamond')))

    fig.update_layout(template="plotly_dark", height=600, hovermode="x unified",
                      xaxis_range=[pd.to_datetime('2026-01-01'), f_meta_p + timedelta(days=5)],
                      title="Sincronía de Metas: Proyecto 91 & Objetivo 115kg")
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Esperando conexión con la nube...")

# --- 5. REGISTRO SIDEBAR ---
with st.sidebar:
    st.header("📝 Entrada de Datos")
    with st.form("reg_dual"):
        f_in = st.date_input("Fecha", datetime.now())
        g_in = st.number_input("Glucosa", value=111)
        p_in = st.number_input("Peso", value=123.5, step=0.1)
        if st.form_submit_button("📡 TRANSMITIR"):
            payload = {"tipo":"SALUD", "fecha":f_in.strftime('%Y-%m-%d'), "glucosa":g_in, "peso":p_in}
            requests.post(URL_ESCRITURA, json=payload)
            st.rerun()
