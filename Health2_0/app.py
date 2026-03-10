import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import io

# --- 1. COORDENADAS DEL BÚNKER ---
SHEET_ID = "TU_ID_DE_HOJA_AQUÍ" 
URL_LECTURA = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=CONTROL"
URL_ESCRITURA = "https://script.google.com/macros/s/AKfycbxHsIEBnMN3KrIof9bB5BM_-RbLWXa-t2A8JfPmuHgYQiRhqLFdhYcxdymBz_ELMK94SA/exec"

st.set_page_config(page_title="Búnker Health - LDK", layout="wide")

# --- 2. DATA HISTÓRICA (NUESTRO RESPALDO DE SEGURIDAD) ---
@st.cache_data
def get_history():
    data = {
        'Fecha': ['2026-01-02', '2026-02-24', '2026-02-25', '2026-02-26', '2026-03-10'],
        'Glucosa': [110, 122, 112, 112, 111]
    }
    # (Aquí puedes pegar toda la lista larga de fechas que te di antes para que el gráfico sea gigante)
    df_h = pd.DataFrame(data)
    df_h['Fecha'] = pd.to_datetime(df_h['Fecha'])
    return df_h

# --- 3. CARGA Y FUSIÓN DE DATOS ---
def load_full_data():
    # 1. Cargar Historial local
    df_total = get_history()
    
    # 2. Intentar cargar Nube
    try:
        response = requests.get(URL_LECTURA)
        response.encoding = 'utf-8'
        df_cloud = pd.read_csv(io.StringIO(response.text))
        df_cloud['Fecha'] = pd.to_datetime(df_cloud['Fecha'], errors='coerce')
        
        # Unimos las dos bases de datos y quitamos duplicados
        df_total = pd.concat([df_total, df_cloud]).drop_duplicates(subset=['Fecha'], keep='last')
    except:
        st.sidebar.warning("⚠️ Modo Offline: Usando historial local.")
    
    return df_total.sort_values('Fecha')

df = load_full_data()

# --- 4. REGISTRO (TRANSMISOR) ---
with st.sidebar:
    st.header("📝 Registro Diario")
    with st.form("registro_form", clear_on_submit=True):
        fecha_in = st.date_input("Fecha", datetime.now())
        glucosa_in = st.number_input("Glucosa", min_value=50, max_value=300, value=111)
        if st.form_submit_button("📡 ENVIAR A LA NUBE"):
            payload = {"tipo": "SALUD", "fecha": fecha_in.strftime('%Y-%m-%d'), "glucosa": glucosa_in}
            requests.post(URL_ESCRITURA, json=payload)
            st.success("¡Dato en órbita!")
            st.rerun()

# --- 5. EL GRAFICADOR MAESTRO ---
st.title("🛡️ Búnker Health: Visualización Crítica")

if not df.empty:
    # KPIs Rápidos
    df['Glucosa'] = pd.to_numeric(df['Glucosa'])
    ult = df['Glucosa'].iloc[-1]
    prom = df['Glucosa'].tail(8).mean()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Última Medición", f"{ult:.0f} mg/dL")
    c2.metric("Promedio (8d)", f"{prom:.1f} mg/dL")
    c3.metric("Estado de la Red", "📡 ONLINE" if ult > 0 else "OFFLINE")

    # Cálculos de Proyección (Plan 91)
    asintota, k, v_base = 90, 0.08, 122
    f_base = pd.to_datetime('2026-02-24')
    t_fut = np.arange(60)
    v_fut = (v_base - asintota) * np.exp(-k * t_fut) + asintota
    fechas_fut = [f_base + timedelta(days=int(i)) for i in t_fut]

    # --- PLOTLY ---
    fig = go.Figure()
    
    # Línea de Glucosa Real
    fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Glucosa'], name="Realidad",
                             line=dict(color='#00e5ff', width=4), mode='lines+markers'))
    
    # Línea de Plan 91
    fig.add_trace(go.Scatter(x=fechas_fut, y=v_fut, name="Plan 91 (Teórico)",
                             line=dict(color='#ff4081', dash='dash')))

    fig.update_layout(template="plotly_dark", height=500, title="Histórico Consolidado (CSV + Nube)",
                      hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Esperando ráfaga de datos para graficar...")
