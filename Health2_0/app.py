import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import io

# --- 1. COORDENADAS DEL BÚNKER ---
SHEET_ID = "1MT2EYKUmKmAP8vSBbPElR_DsP45zgrczDTMXe1b9s5Y" 
URL_LECTURA = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet=CONTROL"
# PEGA AQUÍ TU ÚLTIMO EXEC (EL QUE TIENE EL APPENDROW DE 3 COLUMNAS)
URL_ESCRITURA = "https://script.google.com/macros/s/AKfycbxHsIEBnMN3KrIof9bB5BM_-RbLWXa-t2A8JfPmuHgYQiRhqLFdhYcxdymBz_ELMK94SA/exec"

st.set_page_config(page_title="Búnker Health LDK - V3.0", layout="wide")

def load_data():
    try:
        response = requests.get(URL_LECTURA)
        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
        df.columns = df.columns.str.strip()
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df['Glucosa'] = pd.to_numeric(df['Glucosa'], errors='coerce')
        df['Peso'] = pd.to_numeric(df['Peso'], errors='coerce')
        return df.dropna(subset=['Fecha']).sort_values('Fecha')
    except:
        return pd.DataFrame(columns=['Fecha', 'Glucosa', 'Peso'])

df = load_data()

# --- 2. TRANSMISOR DUAL (SIDEBAR) ---
with st.sidebar:
    st.header("📝 Registro de Biometría")
    with st.form("registro_dual", clear_on_submit=True):
        f_med = st.date_input("Fecha", datetime.now())
        g_med = st.number_input("Glucosa (mg/dL)", value=111)
        p_med = st.number_input("Peso (kg)", value=122.5, step=0.1)
        
        if st.form_submit_button("📡 DISPARAR A LA NUBE"):
            payload = {
                "tipo": "SALUD",
                "fecha": f_med.strftime('%Y-%m-%d'),
                "glucosa": g_med,
                "peso": p_med
            }
            res = requests.post(URL_ESCRITURA, json=payload)
            if res.status_code == 200:
                st.success("✅ ¡Ráfaga exitosa registrada!")
                st.rerun()

# --- 3. INTERFAZ Y BOTÓN DE PÁNICO ---
st.title("🛡️ Búnker Health: Monitor de Biometría Dual")

if not df.empty:
    ult_g = df['Glucosa'].iloc[-1]
    ult_p = df['Peso'].iloc[-1] if 'Peso' in df.columns else 0
    
    # --- LÓGICA DE ALERTA ---
    if ult_g > 130:
        st.error(f"🚨 ¡ALERTA DE BÚNKER! Glucosa en zona crítica: {ult_g} mg/dL. Activar protocolo de control.")
        delta_color = "inverse"
    else:
        delta_color = "normal"

    c1, c2, c3 = st.columns(3)
    c1.metric("Glucosa Actual", f"{ult_g:.0f} mg/dL", delta=f"{ult_g-100:.0f} s/meta", delta_color=delta_color)
    c2.metric("Peso Actual", f"{ult_p:.1f} kg", delta=f"{ult_p - 127.5 if len(df)>1 else 0:.1f} kg")
    c3.metric("Puntos de Telemetría", len(df))

    # --- 4. GRAFICADOR MAESTRO (CON AMARILLO DASH) ---
    fig = go.Figure()

    # Glucosa Real (Cian Sólido)
    fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Glucosa'], name="Glucosa (Cian)",
                             line=dict(color='#00e5ff', width=4)))

    # Peso (Amarillo Dash)
    if 'Peso' in df.columns:
        fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Peso'], name="Peso (Amarillo Dash)",
                                 line=dict(color='yellow', width=3, dash='dash')))

    fig.update_layout(template="plotly_dark", height=600, hovermode="x unified",
                      title="Análisis de Correlación: Glucosa vs Peso")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("📡 Escaneando... esperando datos desde Google Sheets.")
