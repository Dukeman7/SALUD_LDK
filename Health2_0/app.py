import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import requests
import io

# --- 1. COORDENADAS DEL BÚNKER ---
SHEET_ID = "1MT2EYKUmKmAP8vSBbPElR_DsP45zgrczDTMXe1b9s5Y"
URL_LECTURA = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet=CONTROL"
URL_ESCRITURA = "https://script.google.com/macros/s/AKfycbwWXvFy3wkSRT1BhTmCMi6cPyRsq7KQ80BZvOxzPk6bRaj27yfHkQTO-J6trH6IgtGFhw/exec"

st.set_page_config(page_title="Búnker Health V4.0: Operación 99.8 kg", layout="wide")

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
    except Exception:
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
                    st.error("Error 500: Revisa el Script")
            except Exception as e:
                st.error(f"Falla: {e}")

    st.divider()
    st.header("🔭 Ajuste de Radar (Zoom)")
    f_inicio_zoom = st.date_input("Desde:", value=date(2026, 10, 1))
    f_fin_zoom = st.date_input("Hasta:", value=date(2026, 12, 31))

# --- 3. LÓGICA DE PROSPECTIVA V4.0 ---
# A. Curva Meta Glucosa
f_base_g = pd.to_datetime("2026-01-01")
f_fin_anio = pd.to_datetime("2026-12-31")
dias_anio = (f_fin_anio - f_base_g).days + 1
fechas_g = [f_base_g + timedelta(days=int(i)) for i in range(dias_anio)]
v_ini_g = 115.0
meta_final_g = 95.0
suavizado = 0.012
v_fut_g = [(v_ini_g - meta_final_g) * np.exp(-suavizado * i) + meta_final_g for i in range(dias_anio)]

dias_g_hoy = max(0, (pd.to_datetime(hoy.date()) - f_base_g).days)
meta_glucosa_hoy = (v_ini_g - meta_final_g) * np.exp(-suavizado * dias_g_hoy) + meta_final_g

# B. Rumbo Meta Peso (Anual original hacia 99.8 kg)
p_ini_anio = 125.6
p_meta_dic = 99.8
pendiente_anual = (p_ini_anio - p_meta_dic) / (dias_anio - 1)
fechas_rumbo = fechas_g
rumbo_meta = [p_ini_anio - (pendiente_anual * i) for i in range(dias_anio)]
peso_ideal_hoy = p_ini_anio - (pendiente_anual * dias_g_hoy)

# Promedios
p7 = p15 = p30 = np.nan
if not df.empty:
    p7 = df[df['Fecha'] >= (hoy - timedelta(days=7))]['Glucosa'].mean()
    p15 = df[df['Fecha'] >= (hoy - timedelta(days=15))]['Glucosa'].mean()
    p30 = df[df['Fecha'] >= (hoy - timedelta(days=30))]['Glucosa'].mean()

# --- 4. INTERFAZ V4.0 ---
st.title("🛡️ Búnker Health V4.0: Operación 99.8 kg")

if not df.empty:
    ult_g = df['Glucosa'].dropna().iloc[-1]
    df_p = df[df['Peso'] > 0].copy()
    ult_p = df_p['Peso'].iloc[-1] if not df_p.empty else 130.9
    ult_f_p = df_p['Fecha'].iloc[-1] if not df_p.empty else pd.to_datetime(hoy.date())

    # MÉTRICAS TOP
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Última Glucosa", f"{ult_g:.0f}", delta=f"{ult_g - meta_glucosa_hoy:+.1f} vs hoy", delta_color="inverse")
    c2.metric("Peso Actual", f"{ult_p:.1f} kg", delta=f"{ult_p - peso_ideal_hoy:+.1f} vs ideal", delta_color="inverse")
    c3.metric("Meta Junio", "115.0 kg")
    c4.metric("Meta Dic", "99.8 kg")

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
            if p7 < p15:
                st.success(f"🟢 Mejora Semanal: {var:.1%}")
            elif abs(var) <= 0.05:
                st.warning("🟠 Estable (Variación < 5%)")
            else:
                st.error("🔴 Alerta: Tendencia al alza")
    with ct2:
        if not np.isnan(p15) and not np.isnan(p30):
            var2 = (p15 - p30) / p30
            if p15 < p30:
                st.success(f"🟢 Quincena Positiva: {var2:.1%}")
            elif abs(var2) <= 0.05:
                st.warning("🟠 Quincena Estable")
            else:
                st.error("🔴 Tendencia mensual subiendo")

    # --- 5. GRÁFICO V4.0 ---
    fig = go.Figure()

    # Curva Meta Glucosa (Gris Dash)
    fig.add_trace(go.Scatter(
        x=fechas_g, y=v_fut_g, name="Curva Meta Glucosa",
        line=dict(color='gray', dash='dash', width=1.8)
    ))

    # Glucosa Real (Cian)
    df_g = df.dropna(subset=['Glucosa'])
    fig.add_trace(go.Scatter(
        x=df_g['Fecha'], y=df_g['Glucosa'], name="Real",
        line=dict(color='#00e5ff', width=2.5), mode='lines+markers',
        marker=dict(size=6)
    ))

    # Rumbo Meta Anual (Amarilla punteada)
    fig.add_trace(go.Scatter(
        x=fechas_rumbo, y=rumbo_meta, name="Rumbo Meta",
        line=dict(color='#b5a600', dash='dash', width=2.5)
    ))

    # Peso Real (Amarilla gruesa continua)
    if not df_p.empty:
        fig.add_trace(go.Scatter(
            x=df_p['Fecha'], y=df_p['Peso'], name="Peso Real",
            line=dict(color='#ffee00', width=4), mode='lines+markers',
            marker=dict(size=9, symbol='diamond', color='#ffee00')
        ))

    # NUEVA TRAZA: Verde Agua Punteada desde último peso real hasta 31 Dic (119.9 kg)
    fig.add_trace(go.Scatter(
        x=[ult_f_p, pd.to_datetime("2026-12-31")],
        y=[ult_p, 119.9],
        name="Meta 31 Dic (119.9 kg)",
        mode="lines+markers+text",
        line=dict(color="#00FFD1", width=3, dash="dash"),
        marker=dict(size=9, symbol="star", color="#00FFD1"),
        text=["", "119.9 kg"],
        textposition="top left",
        textfont=dict(color="#00FFD1", size=12)
    ))

    fig.update_layout(
        template="plotly_dark",
        height=580,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(range=[pd.to_datetime(f_inicio_zoom), pd.to_datetime(f_fin_zoom)])
    )
    st.plotly_chart(fig, use_container_width=True)

st.info(f"🎯 **ESTADO DEL BÚNKER:** Peso Ideal Hoy: {peso_ideal_hoy:.2f} kg | Meta Glucosa Hoy: {meta_glucosa_hoy:.1f} mg/dL | Objetivo 31 Dic: 119.9 kg")
