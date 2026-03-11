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

st.set_page_config(page_title="Búnker LDK: Control de Radar", layout="wide")

# Función de carga ultra-robusta
@st.cache_data(ttl=60) # Refresca cada minuto
def load_data():
    try:
        response = requests.get(URL_LECTURA, timeout=10)
        content = response.content.decode('utf-8')
        df = pd.read_csv(io.StringIO(content))
        df.columns = df.columns.str.strip()
        for col in ['Glucosa', 'Peso']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        return df.dropna(subset=['Fecha']).sort_values('Fecha')
    except:
        return pd.DataFrame(columns=['Fecha', 'Glucosa', 'Peso'])

df = load_data()

# --- 2. BARRA LATERAL: ÚNICA Y FUNCIONAL ---
with st.sidebar:
    st.header("📝 Registro de Hoy")
    with st.form("reg_v35", clear_on_submit=True):
        f_in = st.date_input("Fecha de hoy", datetime.now())
        g_in = st.number_input("Glucosa", value=111)
        p_in = st.text_input("Peso (kg)", value="123.5") 
        enviar = st.form_submit_button("📡 TRANSMITIR AL BÚNKER")
        
        if enviar:
            try:
                p_val = float(p_in.replace(',', '.'))
                payload = {"tipo":"SALUD", "fecha":f_in.strftime('%Y-%m-%d'), "glucosa":g_in, "peso":p_val}
                r = requests.post(URL_ESCRITURA, json=payload, timeout=15)
                if r.status_code == 200:
                    st.success("✅ Transmisión Exitosa")
                    st.cache_data.clear() # Forzamos recarga
                    st.rerun()
                else:
                    st.error(f"Error en servidor: {r.status_code}")
            except Exception as e:
                st.error(f"Falla de conexión: {e}")
    
    st.divider()
    st.header("🔭 Ajuste de Radar (Zoom)")
    # Fechas por defecto: últimos 30 días hasta fin de año
    hoy = datetime.now()
    inicio_defecto = hoy - timedelta(days=30)
    fin_defecto = datetime(2026, 12, 31)
    
    fecha_inicio = st.date_input("Ver desde:", value=inicio_defecto)
    fecha_fin = st.date_input("Ver hasta:", value=fin_defecto)

# --- 3. PROSPECTIVAS (Lógica Cuántica) ---
fechas_g = [pd.to_datetime('2026-02-24') + timedelta(days=i) for i in range(92)]
v_fut_g = (122 - 90) * np.exp(-0.08 * np.arange(92)) + 90
fechas_proy = [pd.to_datetime('2026-03-01'), pd.to_datetime('2026-06-28'), pd.to_datetime('2026-12-28')]
pesos_proy = [123.5, 115.0, 99.8]

# --- 4. INTERFAZ PRINCIPAL ---
st.title("🛡️ Búnker Health: Operación 99.8 kg")

if not df.empty:
    ult_g = df['Glucosa'].iloc[-1]
    df_p = df.dropna(subset=['Peso'])
    ult_p = df_p['Peso'].iloc[-1] if not df_p.empty else 123.5
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Última Glucosa", f"{ult_g:.0f}", delta=f"{ult_g-90:.0f} vs meta", delta_color="inverse")
    c2.metric("Peso Actual", f"{ult_p:.1f} kg")
    c3.metric("Meta Junio", "115 kg")
    c4.metric("Meta Diciembre", "99.8 kg")

    # --- 5. GRÁFICO ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=fechas_g, y=v_fut_g, name="Curva Meta Glucosa", line=dict(color='#ff4081', dash='dot')))
    fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Glucosa'], name="Realidad Glucosa", line=dict(color='#00e5ff', width=3), mode='lines+markers'))
    fig.add_trace(go.Scatter(x=fechas_proy, y=pesos_proy, name="Rumbo a 99.8", line=dict(color='rgba(255, 255, 0, 0.3)', dash='dash')))
    
    if not df_p.empty:
        fig.add_trace(go.Scatter(x=df_p['Fecha'], y=df_p['Peso'], name="Peso Real",
                                 line=dict(color='yellow', width=3), mode='lines+markers',
                                 marker=dict(size=10, symbol='diamond')))

    fig.update_layout(template="plotly_dark", height=600, hovermode="x unified",
                      xaxis=dict(range=[pd.to_datetime(fecha_inicio), pd.to_datetime(fecha_fin)]))
    st.plotly_chart(fig, use_container_width=True)

# --- 6. CAJA FUERTE (Sin Kaleido para evitar errores) ---
st.divider()
st.subheader("📁 Caja Fuerte del Búnker")
st.info("💡 Usa el botón de la cámara (arriba a la derecha del gráfico) para descargar la captura instantánea.")
