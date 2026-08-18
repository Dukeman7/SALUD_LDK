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

st.set_page_config(page_title="Búnker LDK: Radar Health V3.0", layout="wide")

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
hoy = datetime.now()

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
    f_inicio_zoom = st.date_input("Desde:", value=hoy - timedelta(days=20))
    f_fin_zoom = st.date_input("Hasta:", value=hoy + timedelta(days=20))

# --- 3. LÓGICA DE PROSPECTIVA V3.0 ---
# A. Glucosa: Exponencial Decay desde hoy (122 mg/dL inicial)
f_base_g = hoy
v_ini_g = 122
meta_final_g = 95
suavizado = 0.025 
t_fut_g = np.arange(136) # 135 días hasta diciembre
v_fut_g = (v_ini_g - meta_final_g) * np.exp(-suavizado * t_fut_g) + meta_final_g
fechas_g = [f_base_g + timedelta(days=int(i)) for i in t_fut_g]

# Meta de Glucosa exacta para hoy
dias_g = (hoy - f_base_g).days
meta_glucosa_hoy = (v_ini_g - meta_final_g) * np.exp(-suavizado * dias_g) + meta_final_g

# B. Peso: Tres Rutas de Descenso desde 129.8 kg
p_actual = 129.8
dias_restantes = 135
fechas_peso = [hoy + timedelta(days=i) for i in range(dias_restantes)]

linea_amarilla = [p_actual - (0.150 * i) for i in range(dias_restantes)] # 150g/día
linea_blanca   = [p_actual - (0.110 * i) for i in range(dias_restantes)] # 110g/día
linea_roja     = [p_actual - (0.075 * i) for i in range(dias_restantes)] # 75g/día

# Peso ideal teórico para hoy usando la ruta blanca como referencia central
peso_ideal_hoy = p_actual - (0.110 * (hoy - hoy).days)

# Promedios
p7 = p15 = p30 = np.nan
if not df.empty:
    p7 = df[df['Fecha'] >= (hoy - timedelta(days=7))]['Glucosa'].mean()
    p15 = df[df['Fecha'] >= (hoy - timedelta(days=15))]['Glucosa'].mean()
    p30 = df[df['Fecha'] >= (hoy - timedelta(days=30))]['Glucosa'].mean()

# --- 4. INTERFAZ V3.0 ---
st.title("🛡️ Búnker Health V3.0: Operación 99.8 kg")

if not df.empty:
    ult_g = df['Glucosa'].iloc[-1]
    df_p = df[df['Peso'] > 0]
    ult_p = df_p['Peso'].iloc[-1] if not df_p.empty else 129.8
    
    # MÉTRICAS TOP
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Última Glucosa", f"{ult_g:.0f}", delta=f"{ult_g - meta_glucosa_hoy:+.1f} vs hoy", delta_color="inverse")
    c2.metric("Peso Actual", f"{ult_p:.1f} kg", delta=f"{ult_p - peso_ideal_hoy:+.1f} vs ideal", delta_color="inverse")
    c3.metric("Meta Diciembre", "99.8 kg")
    c4.metric("Días Restantes", f"{dias_restantes} días")

    # PROMEDIOS Y SEMÁFORO
    st.write("### 📊 Tendencias y 🚦 Semáforo Táctico")
    c5, c6, c7 = st.columns(3)
    c5.metric("Promedio 7d", f"{p7:.1f}" if not np.isnan(p7) else "---")
    c6.metric("Promedio 15d", f"{p15:.1f}" if not np.isnan(p15) else "---")
    c7.metric("Promedio Mes", f"{p30:.1f}" if not np.isnan(p30) else "---")

    ct1, ct2 = st.columns(2)
    with ct1:
        if not np.isnan(p7) and not np.isnan(p15):
            var = (p7 - p15) / p15
            if p7 < p15: st.success(f"🟢 Mejora Semanal: {var:.1%}")
            elif abs(var) <= 0.05: st.warning(f"🟠 Estable (Variación < 5%)")
            else: st.error(f"🔴 Alerta: Tendencia al alza")
    with ct2:
        if not np.isnan(p15) and not np.isnan(p30):
            var2 = (p15 - p30) / p30
            if p15 < p30: st.success(f"🟢 Quincena Positiva: {var2:.1%}")
            elif abs(var2) <= 0.05: st.warning(f"🟠 Quincena Estable")
            else: st.error(f"🔴 Tendencia mensual subiendo")

    # --- 5. GRÁFICO V3.0 ---
    fig = go.Figure()

    # Glucosa Exponencial (Gris Dash)
    fig.add_trace(go.Scatter(x=fechas_g, y=v_fut_g, name="Meta Glucosa (Exp)", 
                             line=dict(color='gray', dash='dash', width=2)))

    # Rutas de Peso (Nuevas Dash)
    fig.add_trace(go.Scatter(x=fechas_peso, y=linea_amarilla, name="Ruta Amarilla (150g/d)", 
                             line=dict(color='yellow', dash='dash', width=2)))
    fig.add_trace(go.Scatter(x=fechas_peso, y=linea_blanca, name="Ruta Blanca (110g/d)", 
                             line=dict(color='white', dash='dash', width=2)))
    fig.add_trace(go.Scatter(x=fechas_peso, y=linea_roja, name="Ruta Roja (75g/d)", 
                             line=dict(color='red', dash='dash', width=2)))

    # Datos Reales
    if not df.empty:
        fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Glucosa'], name="Glucosa Real", 
                                 line=dict(color='#00e5ff', width=3), mode='lines+markers'))
    if not df_p.empty:
        fig.add_trace(go.Scatter(x=df_p['Fecha'], y=df_p['Peso'], name="Peso Real", 
                                 line=dict(color='#00ff00', width=4), mode='lines+markers', 
                                 marker=dict(size=10, symbol='diamond')))

    fig.update_layout(
        template="plotly_dark", 
        title="Radar de Recuperación V3.0", 
        height=600, 
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(range=[pd.to_datetime(f_inicio_zoom), pd.to_datetime(f_fin_zoom)])
    )
    st.plotly_chart(fig, use_container_width=True)

st.info(f"🎯 **ESTADO DEL BÚNKER:** Meta Glucosa Hoy: {meta_glucosa_hoy:.1f} mg/dL | Rumbo a Diciembre activo")
