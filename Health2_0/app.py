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

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("📝 Registro de Operaciones")
    with st.form("form_salud", clear_on_submit=True):
        f_in = st.date_input("Fecha de Registro", datetime.now())
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
                else: st.error("Error 500: Revisa el Google Script")
            except Exception as e: st.error(f"Falla: {e}")

    st.divider()
    st.header("🔭 Ajuste de Radar (Zoom)")
    hoy = datetime.now()
    prom_7d = df[df['Fecha'] >= (hoy - timedelta(days=7))]['Glucosa'].mean()
    prom_15d = df[df['Fecha'] >= (hoy - timedelta(days=15))]['Glucosa'].mean()
    prom_30d = df[df['Fecha'] >= (hoy - timedelta(days=30))]['Glucosa'].mean()
    f_inicio_zoom = st.date_input("Desde:", value=hoy_dt - timedelta(days=20))
    f_fin_zoom = st.date_input("Hasta:", value=hoy_dt + timedelta(days=20))

# --- 3. LÓGICA DE PROSPECTIVA (EL CEREBRO) ---
# --- RECALIBRACIÓN CUÁNTICA DE GLUCOSA ---
f_base_g = pd.to_datetime('2026-02-24')
meta_glucosa = 95  # Ajustado a tu nueva meta
valor_inicial = 122
suavizado = 0.035   # Menos exigente que 0.08

t_fut_g = np.arange(120) # Ampliamos el horizonte de días
v_fut_g = (valor_inicial - meta_glucosa) * np.exp(-suavizado * t_fut_g) + meta_glucosa
fechas_g = [f_base_g + timedelta(days=int(i)) for i in t_fut_g]

# Configuración de la meta dinámica
f_inicio_p = pd.to_datetime('2026-03-01')
f_meta_p = pd.to_datetime('2026-06-28')
f_final_p = pd.to_datetime('2026-12-28') # Para el gráfico completo
peso_inicio = 123.5
peso_meta_junio = 115.0
peso_meta_final = 99.8

# Cálculo del Peso Ideal HOY (Línea de tendencia)
dias_totales = (f_meta_p - f_inicio_p).days
ritmo_diario = (peso_inicio - peso_meta_junio) / dias_totales
dias_transcurridos = (datetime.now() - f_inicio_p).days
peso_ideal_hoy = peso_inicio - (ritmo_diario * dias_transcurridos)

# --- 4. INTERFAZ ---
st.title("🛡️ Búnker Health: Operación 99.8 kg")

if not df.empty:
    ult_g = df['Glucosa'].iloc[-1]
    df_p = df[df['Peso'] > 0]
    ult_p = df_p['Peso'].iloc[-1] if not df_p.empty else 123.5
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Glucosa", f"{ult_g:.0f}", delta=f"{ult_g-90:.0f} p/meta", delta_color="inverse")
    
    # ¡AQUÍ ESTÁ EL OBJETO BRILLANTE!
    diferencial_dinamico = ult_p - peso_ideal_hoy
    c2.metric(
        label="Peso Actual", 
        value=f"{ult_p:.1f} kg", 
        delta=f"{diferencial_dinamico:.1f} vs ideal", 
        delta_color="inverse"
    )
    
    c3.metric("Meta Junio", "115 kg")
    c4.metric("Meta Dic", "99.8 kg")

    c5, c6, c7 = st.columns(3)
    c5.metric("Promedio 7 días", f"{prom_7d:.1f}" if not np.isnan(prom_7d) else "---")
    c6.metric("Promedio 15 días", f"{prom_15d:.1f}" if not np.isnan(prom_15d) else "---")
    c7.metric("Promedio Mes", f"{prom_30d:.1f}" if not np.isnan(prom_30d) else "---")
    
    # --- 5. GRÁFICO ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=fechas_g, y=v_fut_g, name="Meta Glucosa", line=dict(color='gray', dash='dash')))
    fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Glucosa'], name="Glucosa Real", line=dict(color='#00e5ff', width=3), mode='lines+markers'))
    
    # Línea de Rumbo (Dash brillante)
    fechas_rumbo = [f_inicio_p, f_meta_p, f_final_p]
    pesos_rumbo = [peso_inicio, peso_meta_junio, peso_meta_final]
    fig.add_trace(go.Scatter(x=fechas_rumbo, y=pesos_rumbo, name="Rumbo Meta", 
                             line=dict(color='rgba(255, 255, 0, 0.5)', dash='dash', width=4)))
    
    if not df_p.empty:
        fig.add_trace(go.Scatter(x=df_p['Fecha'], y=df_p['Peso'], name="Peso Real", 
                                 line=dict(color='yellow', width=4), mode='lines+markers',
                                 marker=dict(size=10, symbol='diamond')))

    fig.update_layout(template="plotly_dark", height=600, hovermode="x unified",
                      xaxis=dict(range=[pd.to_datetime(f_inicio_zoom), pd.to_datetime(f_fin_zoom)]))
    st.plotly_chart(fig, use_container_width=True)

st.info(f"💡 El peso ideal para hoy según la meta de junio es: {peso_ideal_hoy:.2f} kg")
