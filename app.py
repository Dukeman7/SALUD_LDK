import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# --- 1. DATA MAESTRA RECALIBRADA (PESO SUAVIZADO) ---
fechas_glucosa = pd.to_datetime([
    '2026-01-02', '2026-01-04', '2026-01-05', '2026-01-06', '2026-01-07', '2026-01-08', '2026-01-09',
    '2026-01-10', '2026-01-11', '2026-01-12', '2026-01-13', '2026-01-14', '2026-01-15', '2026-01-16',
    '2026-01-17', '2026-01-18', '2026-01-19', '2026-01-20', '2026-01-21', '2026-01-22', '2026-01-23',
    '2026-01-24', '2026-01-25', '2026-01-26', '2026-01-28', '2026-01-29', '2026-01-30', '2026-01-31',
    '2026-02-01', '2026-02-02', '2026-02-03', '2026-02-04', '2026-02-05', '2026-02-06', '2026-02-07',
    '2026-02-08', '2026-02-09', '2026-02-10', '2026-02-11', '2026-02-12', '2026-02-13', '2026-02-14',
    '2026-02-15', '2026-02-16', '2026-02-18', '2026-02-19', '2026-02-20', '2026-02-21', '2026-02-22',
    '2026-02-23', '2026-02-24'
])

# Peso simulado continuo basado en tus hitos discretos
peso_hitos = np.linspace(127, 123.5, 24).tolist() + np.linspace(123.5, 125.3, 18).tolist() + np.linspace(125.3, 125.1, 9).tolist()

df = pd.DataFrame({
    'Fecha': fechas_glucosa, 
    'Glucosa': [110, 94, 107, 121, 97, 109, 109, 109, 105, 122, 110, 110, 107, 115, 109, 116, 126, 107, 125, 111, 133, 112, 116, 115, 96, 107, 109, 101, 116, 111, 107, 105, 107, 100, 103, 105, 103, 110, 118, 107, 113, 115, 119, 116, 116, 122, 118, 116, 120, 123, 122],
    # Hitos reales que tú me diste
hitos_peso = {
    '2026-01-01': 127.0,
    '2026-01-25': 123.5,
    '2026-02-13': 125.3,
    '2026-02-24': 125.1
}

# Creamos una serie de tiempo completa y le decimos que 'interpole' (una los puntos)
df_peso = pd.DataFrame(list(hitos_peso.items()), columns=['Fecha', 'Peso'])
df_peso['Fecha'] = pd.to_datetime(df_peso['Fecha'])
df_peso = df_peso.set_index('Fecha').resample('D').interpolate(method='linear')

# Ahora lo unimos a tu data de glucosa
df = pd.merge(df_glucosa, df_peso, on='Fecha', how='left')
df['Peso'] = df['Peso'].ffill().bfill() # Por si falta algún día al inicio/final
})

# --- 2. CÁLCULOS DE TENDENCIA Y PROMEDIOS ---
df['MA8'] = df['Glucosa'].rolling(window=8).mean()
df['MA15'] = df['Glucosa'].rolling(window=15).mean()
df['MA30'] = df['Glucosa'].rolling(window=30).mean()
df['MA45'] = df['Glucosa'].rolling(window=45).mean()

# Parámetros de la curva prospectiva (Fija)
target_asintota = 90
k_factor = 0.08  # Freno logarítmico
v_hoy = 122
dias_proy = 45

# --- 3. ESTIMACIÓN DE HITOS ---
# Glucosa < 99 (Racha de 5 días)
dias_99 = -np.log((99 - target_asintota) / (v_hoy - target_asintota)) / k_factor
fecha_99 = df['Fecha'].max() + timedelta(days=int(dias_99) + 5)

# Glucosa < 90 (Racha de 5 días - Aproximación asintótica)
fecha_90 = df['Fecha'].max() + timedelta(days=60) # Estimación conservadora

# --- 4. INTERFAZ STREAMLIT ---
st.title("🛡️ Búnker Health: Proyecto 91 / Hito 90")

# Fila de KPIs (Promedios actuales)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Promedio 8d", f"{df['MA8'].iloc[-1]:.1f}")
c2.metric("Promedio 15d", f"{df['MA15'].iloc[-1]:.1f}")
c3.metric("Promedio 30d", f"{df['MA30'].iloc[-1]:.1f}")
c4.metric("Promedio 45d", f"{df['MA45'].iloc[-1]:.1f}")

# --- 5. GRÁFICO PROFESIONAL (Últimos 45 días) ---
df_plot = df.tail(45) # Sacrificamos el inicio para ganar detalle
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Glucosa Real
fig.add_trace(go.Scatter(x=df_plot['Fecha'], y=df_plot['Glucosa'], name="Glucosa Real", line=dict(color='#00e5ff', width=3)), secondary_y=False)

# Peso (Continuo)
fig.add_trace(go.Scatter(x=df_plot['Fecha'], y=df_plot['Peso'], name="Peso (kg)", line=dict(color='#ffeb3b', width=2, dash='dot')), secondary_y=True)

# Curva Prospectiva Fija (Hito de Plan 91)
t_futuro = np.arange(dias_proy)
v_futuro = (v_hoy - target_asintota) * np.exp(-k_factor * t_futuro) + target_asintota
fechas_futuras = [df['Fecha'].max() + timedelta(days=int(i)) for i in t_futuro]
fig.add_trace(go.Scatter(x=fechas_futuras, y=v_futuro, name="Hito Plan 91 (Proyección)", line=dict(color='#ff4081', dash='dash')), secondary_y=False)

fig.update_layout(template="plotly_dark", height=600, title="Control Metabólico Multiplataforma")
st.plotly_chart(fig, use_container_width=True)

# --- 6. HITOS DE PESO Y GLUCOSA ---
st.subheader("🎯 Panel de Objetivos Estratégicos")
col_a, col_b = st.columns(2)
with col_a:
    st.write("📅 **Hitos de Peso:**")
    st.write(f"- Meta 115kg (Cumpleaños): **28 de Junio**")
    st.write(f"- Meta 99kg (Diciembre): **15 de Diciembre**")
with col_b:
    st.write("🩺 **Hitos de Glucosa:**")
    st.write(f"- Racha 5 días < 99: **{fecha_99.strftime('%d de Marzo')}**")
    st.write(f"- Racha 5 días < 90: **Abril 2026**")
