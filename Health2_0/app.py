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
hoy = datetime.now() # Variable maestra de tiempo

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("📝 Registro de Operaciones")
    with st.form("form_salud", clear_on_submit=True):
        f_in = st.date_input("Fecha de Registro", hoy)
        g_in = st.number_input("Glucosa (mg/dL)", value=110)
        p_in = st.text_input("Peso (kg) - Vacío si no toca hoy", value="")
        if st.form_submit_button("📡 TRANSMITIR AL BÚNKER"):
            try:
                p_val = float(p_in.replace(',', '.')) if p_in.strip() != "" else 0
                payload = {"tipo": "SALUD", "fecha": f_in.strftime('%Y-%m-%d'), "glucosa": g_in, "peso": p_val}
                r = requests.post(URL_ESCRITURA, json=payload, timeout=15)
                if r.status_code == 200:
                    st.success("✅ Datos en la Nube")
                    st.cache_data.clear()
                    st.rerun()
                else: st.error("Error 500: Revisa el Script")
            except Exception as e: st.error(f"Falla: {e}")

    st.divider()
    st.header("🔭 Ajuste de Radar (Zoom)")
    # Corregido: usando 'hoy' en lugar de 'hoy_dt'
    f_inicio_zoom = st.date_input("Desde:", value=hoy - timedelta(days=20))
    f_fin_zoom = st.date_input("Hasta:", value=hoy + timedelta(days=20))

# --- 3. LÓGICA DE PROSPECTIVA Y PROMEDIOS ---
# Curva Glucosa Suavizada
f_base_g = pd.to_datetime('2026-02-24')
meta_g = 95
v_ini_g = 122
suavizado = 0.035
t_fut_g = np.arange(120)
v_fut_g = (v_ini_g - meta_g) * np.exp(-suavizado * t_fut_g) + meta_g
fechas_g = [f_base_g + timedelta(days=int(i)) for i in t_fut_g]

# Meta Peso Dinámica
f_ini_p, f_meta_p, f_fin_p = pd.to_datetime('2026-03-01'), pd.to_datetime('2026-06-28'), pd.to_datetime('2026-12-28')
p_ini, p_meta_j, p_meta_d = 123.5, 115.0, 99.8
ritmo = (p_ini - p_meta_j) / (f_meta_p - f_ini_p).days
peso_ideal_hoy = p_ini - (ritmo * (hoy - f_ini_p).days)

# Promedios de Glucosa
if not df.empty:
    p7 = df[df['Fecha'] >= (hoy - timedelta(days=7))]['Glucosa'].mean()
    p15 = df[df['Fecha'] >= (hoy - timedelta(days=15))]['Glucosa'].mean()
    p30 = df[df['Fecha'] >= (hoy - timedelta(days=30))]['Glucosa'].mean()

# --- 4. INTERFAZ ---
st.title("🛡️ Búnker Health: Operación 99.8 kg")

if not df.empty:
    ult_g = df['Glucosa'].iloc[-1]
    df_p = df[df['Peso'] > 0]
    ult_p = df_p['Peso'].iloc[-1] if not df_p.empty else 123.5
    
    # Fila 1: Métricas Principales
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Última Glucosa", f"{ult_g:.0f}", delta=f"{ult_g-meta_g:.0f} vs meta", delta_color="inverse")
    c2.metric("Peso Actual", f"{ult_p:.1f} kg", delta=f"{ult_p - peso_ideal_hoy:.1f} vs ideal", delta_color="inverse")
    c3.metric("Meta Junio", f"{p_meta_j} kg")
    c4.metric("Meta Dic", f"{p_meta_d} kg")

    # Fila 2: Los Promedios "Preciosos"
    st.write("### 📊 Tendencias de Glucosa")
    c5, c6, c7 = st.columns(3)
    c5.metric("Promedio 7 días", f"{p7:.1f}" if not np.isnan(p7) else "---")
    c6.metric("Promedio 15 días", f"{p15:.1f}" if not np.isnan(p15) else "---")
    c7.metric("Promedio Mes", f"{p30:.1f}" if not np.isnan(p30) else "---")
    
    # --- 5. GRÁFICO ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=fechas_g, y=v_fut_g, name=f"Meta ({meta_g})", line=dict(color='gray', dash='dash')))
    fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Glucosa'], name="Real", line=dict(color='#00e5ff', width=3), mode='lines+markers'))
    
    f_rumbo = [f_ini_p, f_meta_p, f_fin_p]
    p_rumbo = [p_ini, p_meta_j, p_meta_d]
    fig.add_trace(go.Scatter(x=f_rumbo, y=p_rumbo, name="Rumbo Meta", line=dict(color='rgba(255, 255, 0, 0.4)', dash='dash', width=4)))
    
    if not df_p.empty:
        fig.add_trace(go.Scatter(x=df_p['Fecha'], y=df_p['Peso'], name="Peso Real", line=dict(color='yellow', width=4), mode='lines+markers', marker=dict(size=10, symbol='diamond')))

    fig.update_layout(template="plotly_dark", height=600, hovermode="x unified",
                      xaxis=dict(range=[pd.to_datetime(f_inicio_zoom), pd.to_datetime(f_fin_zoom)]))
    st.plotly_chart(fig, use_container_width=True)

st.info(f"💡 Peso ideal para hoy: {peso_ideal_hoy:.2f} kg | Meta Glucosa: {meta_g} mg/dL")
