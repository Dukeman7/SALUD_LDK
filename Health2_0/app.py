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

st.set_page_config(page_title="Búnker LDK: Radar Health V4.0", layout="wide")

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

# --- 3. LÓGICA DE PROSPECTIVA Y SEMÁFORO ---
# Glucosa Suavizada
f_base_g, meta_g, v_ini_g, suavizado = pd.to_datetime('2026-02-24'), 95, 122, 0.035
t_fut_g = np.arange(120)
v_fut_g = (v_ini_g - meta_g) * np.exp(-suavizado * t_fut_g) + meta_g
fechas_g = [f_base_g + timedelta(days=int(i)) for i in t_fut_g]

# Meta Diaria de Glucosa (Cálculo exacto para hoy)
dias_g = (hoy - f_base_g).days
meta_glucosa_hoy = (v_ini_g - meta_g) * np.exp(-suavizado * dias_g) + meta_g

# Meta Peso Dinámica
f_ini_p, f_meta_p, f_fin_p = pd.to_datetime('2026-03-01'), pd.to_datetime('2026-06-28'), pd.to_datetime('2026-12-28')
p_ini, p_meta_j, p_meta_d = 123.5, 115.0, 99.8
ritmo = (p_ini - p_meta_j) / (f_meta_p - f_ini_p).days
peso_ideal_hoy = p_ini - (ritmo * (hoy - f_ini_p).days)

# Promedios
p7 = p15 = p30 = np.nan
if not df.empty:
    p7 = df[df['Fecha'] >= (hoy - timedelta(days=7))]['Glucosa'].mean()
    p15 = df[df['Fecha'] >= (hoy - timedelta(days=15))]['Glucosa'].mean()
    p30 = df[df['Fecha'] >= (hoy - timedelta(days=30))]['Glucosa'].mean()

# --- 4. INTERFAZ V4.0 ---
st.title("🛡️ Búnker Health V4.0: Operación 99.8 kg")

if not df.empty:
    ult_g = df['Glucosa'].iloc[-1]
    df_p = df[df['Peso'] > 0]
    ult_p = df_p['Peso'].iloc[-1] if not df_p.empty else 123.5
    
    # MÉTRICAS TOP
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Última Glucosa", f"{ult_g:.0f}", delta=f"{ult_g - meta_glucosa_hoy:+.1f} vs hoy", delta_color="inverse")
    c2.metric("Peso Actual", f"{ult_p:.1f} kg", delta=f"{ult_p - peso_ideal_hoy:+.1f} vs ideal", delta_color="inverse")
    c3.metric("Meta Junio", f"{p_meta_j} kg")
    c4.metric("Meta Dic", f"{p_meta_d} kg")

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

    # --- 5. GRÁFICO ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=fechas_g, y=v_fut_g, name="Curva Meta Glucosa", line=dict(color='gray', dash='dash')))
    fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Glucosa'], name="Real", line=dict(color='#00e5ff', width=3), mode='lines+markers'))
    fig.add_trace(go.Scatter(x=[f_ini_p, f_meta_p, f_fin_p], y=[p_ini, p_meta_j, p_meta_d], name="Rumbo Meta", line=dict(color='rgba(255, 255, 0, 0.4)', dash='dash', width=4)))
    if not df_p.empty:
        fig.add_trace(go.Scatter(x=df_p['Fecha'], y=df_p['Peso'], name="Peso Real", line=dict(color='yellow', width=4), mode='lines+markers', marker=dict(size=10, symbol='diamond')))

    fig.update_layout(template="plotly_dark", height=600, margin=dict(l=20, r=20, t=20, b=20), xaxis=dict(range=[pd.to_datetime(f_inicio_zoom), pd.to_datetime(f_fin_zoom)]))
    st.plotly_chart(fig, use_container_width=True)

st.info(f"🎯 **ESTADO DEL BÚNKER:** Peso Ideal Hoy: {peso_ideal_hoy:.2f} kg | Meta Glucosa Hoy: {meta_glucosa_hoy:.1f} mg/dL")
