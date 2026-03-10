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
# Asegúrate de usar tu último EXEC aquí
URL_ESCRITURA = "https://script.google.com/macros/s/AKfycbxHsIEBnMN3KrIof9bB5BM_-RbLWXa-t2A8JfPmuHgYQiRhqLFdhYcxdymBz_ELMK94SA/exec"

st.set_page_config(page_title="Búnker Health LDK - Proyecto 91", layout="wide")

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

# --- 2. TRANSMISOR (SIDEBAR) ---
with st.sidebar:
    st.header("📝 Registro de Biometría")
    with st.form("registro_dual", clear_on_submit=True):
        f_med = st.date_input("Fecha", datetime.now())
        g_med = st.number_input("Glucosa (mg/dL)", value=111)
        p_med = st.number_input("Peso (kg)", value=122.5, step=0.1)
        
        if st.form_submit_button("📡 DISPARAR A LA NUBE"):
            payload = {"tipo": "SALUD", "fecha": f_med.strftime('%Y-%m-%d'), "glucosa": g_med, "peso": p_med}
            requests.post(URL_ESCRITURA, json=payload)
            st.success("✅ ¡Dato en órbita!")
            st.rerun()

# --- 3. CÁLCULOS DEL CORAZÓN (PROYECTO 91) ---
asintota, k, v_base = 90, 0.08, 122
f_base = pd.to_datetime('2026-02-24')
t_fut = np.arange(92) # Los 91 días del proyecto
v_fut = (v_base - asintota) * np.exp(-k * t_fut) + asintota
fechas_fut = [f_base + timedelta(days=int(i)) for i in t_fut]

# --- 4. INTERFAZ Y MONITOR DE PÁNICO ---
st.title("🛡️ Búnker Health: Monitor Proyecto 91")

if not df.empty:
    ult_g = df['Glucosa'].iloc[-1]
    ult_p = df['Peso'].iloc[-1] if 'Peso' in df.columns and not df['Peso'].isnull().all() else 122.5
    
    # Alerta de Pánico
    if ult_g > 130:
        st.error(f"🚨 ALERTA: Glucosa en {ult_g}. ¡Revisar suministros y dieta!")
        d_color = "inverse"
    else:
        d_color = "normal"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Glucosa", f"{ult_g:.0f}", delta=f"{ult_g-90:.0f} pto meta", delta_color=d_color)
    c2.metric("Peso", f"{ult_p:.1f} kg")
    c3.metric("Días Restantes", (f_base + timedelta(days=91) - datetime.now()).days)
    c4.metric("Puntos", len(df))

    # --- 5. EL GRAFICADOR MAESTRO ---
    fig = go.Figure()

    # Plan 91 - LA TATUADA (Rosa)
    fig.add_trace(go.Scatter(x=fechas_fut, y=v_fut, name="Plan 91 (Hito Tatuado)",
                             line=dict(color='#ff4081', dash='dot', width=2)))

    # Glucosa Real (Cian)
    fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Glucosa'], name="Realidad Glucosa",
                             line=dict(color='#00e5ff', width=4), mode='lines+markers'))

    # Peso Real (Amarillo Dash) - Con conexión de puntos distantes
    if 'Peso' in df.columns:
        fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Peso'], name="Peso (kg)",
                                 line=dict(color='yellow', width=3, dash='dash'),
                                 connectgaps=True, mode='lines+markers'))

    fig.update_layout(template="plotly_dark", height=600, hovermode="x unified",
                      title="Sincronía Biométrica: Glucosa vs Peso vs Plan 91")
    st.plotly_chart(fig, use_container_width=True)
