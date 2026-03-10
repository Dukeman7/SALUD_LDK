import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import io

# --- 1. COORDENADAS ---
# Asegúrate de que este ID sea el correcto
SHEET_ID = "1MT2EYKUmKmAP8vSBbPElR_DsP45zgrczDTMXe1b9s5Y" 
URL_LECTURA = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=CONTROL"
URL_ESCRITURA = "https://script.google.com/macros/s/AKfycbxHsIEBnMN3KrIof9bB5BM_-RbLWXa-t2A8JfPmuHgYQiRhqLFdhYcxdymBz_ELMK94SA/exec"

st.set_page_config(page_title="Búnker Health - LDK", layout="wide")

# --- 2. EL RECEPTOR DE NUBE ---
def load_data_from_google():
    try:
        # Usamos el formato de exportación directa para saltar el error de 'Fecha'
        export_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet=CONTROL"
        response = requests.get(export_url)
        
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
            
            # Limpieza profunda de nombres de columnas
            df.columns = df.columns.str.strip()
            
            # Forzamos la conversión
            if 'Fecha' in df.columns:
                df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
                df['Glucosa'] = pd.to_numeric(df['Glucosa'], errors='coerce')
                df = df.dropna(subset=['Fecha', 'Glucosa']).sort_values('Fecha')
                return df
            else:
                st.error(f"⚠️ Columnas detectadas: {list(df.columns)}")
        return pd.DataFrame(columns=['Fecha', 'Glucosa'])
    except Exception as e:
        st.error(f"Falla de sintonía: {e}")
        return pd.DataFrame(columns=['Fecha', 'Glucosa'])

df = load_data_from_google()

# --- 3. TRANSMISOR (SIDEBAR) ---
with st.sidebar:
    st.header("📝 Registro Diario")
    with st.form("registro_form", clear_on_submit=True):
        fecha_in = st.date_input("Fecha", datetime.now())
        glucosa_in = st.number_input("Glucosa", min_value=50, max_value=300, value=111)
        if st.form_submit_button("📡 ENVIAR A LA NUBE"):
            payload = {"tipo": "SALUD", "fecha": fecha_in.strftime('%Y-%m-%d'), "glucosa": glucosa_in}
            res = requests.post(URL_ESCRITURA, json=payload)
            if res.status_code == 200:
                st.success("¡Dato en órbita!")
                st.rerun()

# --- 4. GRAFICADOR Y CONTROL ---
st.title("🛡️ Búnker Health: Monitor de Nube")

if not df.empty and len(df) > 1:
    # KPIs con la data REAL de Google
    ult = df['Glucosa'].iloc[-1]
    dif = ult - df['Glucosa'].iloc[-2]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Última Medición", f"{ult:.0f} mg/dL", delta=f"{dif:.0f}", delta_color="inverse")
    c2.metric("Puntos en el Radar", len(df))
    c3.metric("Promedio Total", f"{df['Glucosa'].mean():.1f}")

    # Proyección Plan 91
    asintota, k, v_base = 90, 0.08, 122
    f_base = pd.to_datetime('2026-02-24')
    t_fut = np.arange(70)
    v_fut = (v_base - asintota) * np.exp(-k * t_fut) + asintota
    fechas_fut = [f_base + timedelta(days=int(i)) for i in t_fut]

    # Plotly
    fig = go.Figure()
    # Data de Google Sheet (Cian)
    fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Glucosa'], name="Historial Real (Google)",
                             line=dict(color='#00e5ff', width=3), mode='lines+markers'))
    # Plan 91 (Rosa)
    fig.add_trace(go.Scatter(x=fechas_fut, y=v_fut, name="Plan 91",
                             line=dict(color='#ff4081', dash='dash')))

    fig.update_layout(template="plotly_dark", height=550, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("📡 Escaneando... Si el gráfico no aparece, asegúrate de que la Google Sheet tenga los 65 puntos que pegamos esta mañana.")
