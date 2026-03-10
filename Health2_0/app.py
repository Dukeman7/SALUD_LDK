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

st.set_page_config(page_title="Búnker LDK: Objetivo 104", layout="wide")

def load_data():
    try:
        response = requests.get(URL_LECTURA)
        # Leemos el texto y reemplazamos comas por puntos antes de procesar
        raw_text = response.content.decode('utf-8').replace(',', '.')
        df = pd.read_csv(io.StringIO(raw_text))
        df.columns = df.columns.str.strip()
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df['Glucosa'] = pd.to_numeric(df['Glucosa'], errors='coerce')
        if 'Peso' in df.columns:
            df['Peso'] = pd.to_numeric(df['Peso'], errors='coerce')
        return df.dropna(subset=['Fecha']).sort_values('Fecha')
    except:
        return pd.DataFrame(columns=['Fecha', 'Glucosa', 'Peso'])

df = load_data()

# --- 2. PROSPECTIVAS ---
# Glucosa Plan 91
f_base_g = pd.to_datetime('2026-02-24')
t_fut_g = np.arange(92)
v_fut_g = (122 - 90) * np.exp(-0.08 * t_fut_g) + 90
fechas_g = [f_base_g + timedelta(days=int(i)) for i in t_fut_g]

# Peso: Meta Cumpleaños (Jun-28) y Meta Navidad (Dic-28)
f_inicio_p = pd.to_datetime('2026-03-01')
f_meta_p = pd.to_datetime('2026-06-28')
f_final_p = pd.to_datetime('2026-12-28')
fechas_proy = [f_inicio_p, f_meta_p, f_final_p]
pesos_proy = [123.5, 115.0, 104.0] # La ruta del éxito

# --- 3. MONITOR Y KPIs ---
st.title("🛡️ Búnker Health: Destino 104 kg")

if not df.empty:
    ult_g = df['Glucosa'].iloc[-1]
    # Buscamos el último peso que no sea nulo
    df_p = df.dropna(subset=['Peso'])
    ult_p = df_p['Peso'].iloc[-1] if not df_p.empty else 123.5
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Glucosa", f"{ult_g:.0f}", delta=f"{ult_g-90:.0f} p/meta", delta_color="inverse" if ult_g > 130 else "normal")
    c2.metric("Peso Actual", f"{ult_p:.1f} kg", delta=f"{ult_p-115:.1f} kg p/meta")
    c3.metric("Meta Junio", "115 kg")
    c4.metric("Diciembre", "104 kg")

    # --- 4. EL GRAFICADOR MAESTRO ---
    fig = go.Figure()

    # GLUCOSA
    fig.add_trace(go.Scatter(x=fechas_g, y=v_fut_g, name="Plan 91 (Glucosa)", line=dict(color='#ff4081', dash='dot')))
    fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Glucosa'], name="Realidad Glucosa", line=dict(color='#00e5ff', width=4), mode='lines+markers'))

    # PESO: PROSPECTIVA LARGO PLAZO (Amarillo Tenue)
    fig.add_trace(go.Scatter(x=fechas_proy, y=pesos_proy, name="Ruta de Peso 2026", line=dict(color='rgba(255, 255, 0, 0.2)', dash='dash', width=2)))

    # PESO: REGISTRO REAL (Amarillo Diamante)
    if not df_p.empty:
        fig.add_trace(go.Scatter(x=df_p['Fecha'], y=df_p['Peso'], name="Peso Real (kg)",
                                 line=dict(color='yellow', width=3), 
                                 mode='lines+markers',
                                 marker=dict(size=12, symbol='diamond', line=dict(width=2, color='white'))))

    fig.update_layout(template="plotly_dark", height=600, hovermode="x unified",
                      xaxis_range=[pd.to_datetime('2026-01-01'), f_final_p + timedelta(days=5)])
    st.plotly_chart(fig, use_container_width=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("📝 Registro de Biometría")
    with st.form("reg_v3"):
        f_in = st.date_input("Fecha", datetime.now())
        g_in = st.number_input("Glucosa", value=111)
        # Importante: Aquí puedes poner el peso con punto o coma, el código lo limpiará
        p_in = st.text_input("Peso (kg)", value="123.5") 
        if st.form_submit_button("📡 TRANSMITIR"):
            peso_float = float(p_in.replace(',', '.'))
            payload = {"tipo":"SALUD", "fecha":f_in.strftime('%Y-%m-%d'), "glucosa":g_in, "peso":peso_float}
            requests.post(URL_ESCRITURA, json=payload)
            st.rerun()
