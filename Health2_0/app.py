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
URL_ESCRITURA = "https://script.google.com/macros/s/AKfycbwWXvFy3wkSRT1BhTmCMi6cPyRsq7KQ80BZvOxzPk6bRaj27yfHkQTO-J6trH6IgtGFhw/exec"

st.set_page_config(page_title="Búnker LDK: Radar Health", layout="wide")

# Función de carga con caché para no saturar la nube
@st.cache_data(ttl=60)
def load_data():
    try:
        response = requests.get(URL_LECTURA, timeout=10)
        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
        df.columns = df.columns.str.strip()
        for col in ['Glucosa', 'Peso']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        return df.dropna(subset=['Fecha']).sort_values('Fecha')
    except:
        return pd.DataFrame(columns=['Fecha', 'Glucosa', 'Peso'])

df = load_data()

# --- 2. SIDEBAR: REGISTRO Y ZOOM ---
with st.sidebar:
    st.header("📝 Registro de Operaciones")
    with st.form("form_salud", clear_on_submit=True):
        f_in = st.date_input("Fecha de Registro", datetime.now())
        g_in = st.number_input("Glucosa (mg/dL)", value=110)
        p_in = st.text_input("Peso (kg) - Vacío si no toca hoy", value="")
        
        if st.form_submit_button("📡 TRANSMITIR AL BÚNKER"):
            try:
                # Lógica: Si peso está vacío mandamos 0, el Script debe ignorar ceros
                p_val = float(p_in.replace(',', '.')) if p_in.strip() != "" else 0
                payload = {
                    "tipo": "SALUD", 
                    "fecha": f_in.strftime('%Y-%m-%d'), 
                    "glucosa": g_in, 
                    "peso": p_val
                }
                r = requests.post(URL_ESCRITURA, json=payload, timeout=15)
                if r.status_code == 200:
                    st.success("✅ Datos en la Nube")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(f"Error 500: Revisa el Google Script")
            except Exception as e:
                st.error(f"Falla: {e}")

    st.divider()
    st.header("🔭 Ajuste de Radar (Zoom)")
    hoy = datetime.now()
    # WISH LIST: -20 días y +20 días
    f_inicio_zoom = st.date_input("Desde:", value=hoy - timedelta(days=20))
    f_fin_zoom = st.date_input("Hasta:", value=hoy + timedelta(days=20))

# --- 3. CÁLCULOS Y PROSPECTIVAS ---
# Curva Glucosa (Meta 90)
fechas_g = [pd.to_datetime('2026-02-24') + timedelta(days=i) for i in range(92)]
v_fut_g = (122 - 90) * np.exp(-0.08 * np.arange(92)) + 90
# Rumbo Peso (Meta 99.8)
fechas_p_meta = [pd.to_datetime('2026-03-01'), pd.to_datetime('2026-06-28'), pd.to_datetime('2026-12-28')]
pesos_p_meta = [123.5, 115.0, 99.8]

# --- 4. INTERFAZ ---
st.title("🛡️ Búnker Health: Operación 99.8 kg")

if not df.empty:
    # Métricas principales
    ult_g = df['Glucosa'].iloc[-1]
    df_p = df[df['Peso'] > 0] # Solo fechas con peso registrado
    ult_p = df_p['Peso'].iloc[-1] if not df_p.empty else 123.5
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Glucosa", f"{ult_g:.0f}", delta=f"{ult_g-90:.0f} p/meta", delta_color="inverse")
    c2.metric("Peso Actual", f"{ult_p:.1f} kg")
    c3.metric("Meta Junio", "115 kg")
    c4.metric("Meta Dic", "99.8 kg")

    # --- 5. EL GRÁFICO DEL RADAR ---
    fig = go.Figure()
    
    # Glucosa: Meta vs Real
    fig.add_trace(go.Scatter(x=fechas_g, y=v_fut_g, name="Meta Glucosa", line=dict(color='gray', dash='dash')))
    fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Glucosa'], name="Glucosa Real", line=dict(color='#00e5ff', width=3), mode='lines+markers'))
    
    # Peso: Meta vs Real
    fig.add_trace(go.Scatter(
        x=fechas_p_meta, 
        y=pesos_p_meta, 
        name="Rumbo 99.8", 
        line=dict(
            color='rgba(255, 255, 0, 0.3)', # Amarillo puro al 30% de brillo
            dash='dash', # guiones
            width=4 #Más gruesa
        )
    ))
    if not df_p.empty:
        fig.add_trace(go.Scatter(x=df_p['Fecha'], y=df_p['Peso'], name="Peso (kg)", 
                                 line=dict(color='yellow', width=4), mode='lines+markers',
                                 marker=dict(size=10, symbol='diamond')))

    fig.update_layout(
        template="plotly_dark", height=600, 
        hovermode="x unified",
        xaxis=dict(range=[pd.to_datetime(f_inicio_zoom), pd.to_datetime(f_fin_zoom)])
    )
    st.plotly_chart(fig, use_container_width=True)

st.info("💡 Consejo: Si el peso no se registra hoy, deja el campo vacío y dale a Transmitir.")
