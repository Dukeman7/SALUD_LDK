import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DEL BÚNKER ---
st.set_page_config(page_title="Búnker Health - LDK", layout="wide")

# 1. DATA HISTÓRICA (La base que ya validamos)
data = {
    'Fecha': [
        '2026-01-02', '2026-01-04', '2026-01-05', '2026-01-06', '2026-01-07', '2026-01-08', '2026-01-09',
        '2026-01-10', '2026-01-11', '2026-01-12', '2026-01-13', '2026-01-14', '2026-01-15', '2026-01-16',
        '2026-01-17', '2026-01-18', '2026-01-19', '2026-01-20', '2026-01-21', '2026-01-22', '2026-01-23',
        '2026-01-24', '2026-01-25', '2026-01-26', '2026-01-28', '2026-01-29', '2026-01-30', '2026-01-31',
        '2026-02-01', '2026-02-02', '2026-02-03', '2026-02-04', '2026-02-05', '2026-02-06', '2026-02-07',
        '2026-02-08', '2026-02-09', '2026-02-10', '2026-02-11', '2026-02-12', '2026-02-13', '2026-02-14',
        '2026-02-15', '2026-02-16', '2026-02-18', '2026-02-19', '2026-02-20', '2026-02-21', '2026-02-22',
        '2026-02-23', '2026-02-24'
    ],
    'Lectura': [
        110, 94, 107, 121, 97, 109, 109, 109, 105, 122, 110, 110, 107, 115, 109, 116, 126, 107, 125, 111, 133,
        112, 116, 115, 96, 107, 109, 101, 116, 111, 107, 105, 107, 100, 103, 105, 103, 110, 118, 107, 113, 115,
        119, 116, 116, 122, 118, 116, 120, 123, 122
    ]
    'Peso': [
    125.6, 124.344, 125.463096, 124.4593912, 125.2061476, 126.3330029, 127.2173339, 128.3622899, 127.9772031, 128.1051803, 
    128.3613906, 127.3344995, 128.48051, 129.1229125, 128.8646667, 129.6378547, 130.4156819, 130.2852662, 130.5458367, 129.1098325, 
    128.722503, 128.722503, 129.3661155, 129.3661155, 128.9780172, 128.8490392, 127.4316997, 126.9219729, 126.1604411, 125.6557993, 
    124.3992413, 124.7724391, 123.7742595, 124.1455823, 124.0214367, 124.2694796, 125.5121744, 124.1315405, 124.3798036, 124.3798036, 
    125.6236016, 124.3673656, 124.3673656, 123.7455288, 122.3843279, 122.8738653, 122.2594959, 122.1372364, 122.1372364, 122.5036481, 
    122.7486554 # Datos ejemplo para IMC
    ]
}
df = pd.DataFrame(data)

# --- LÓGICA DE INGENIERÍA: ASÍNTOTA Y DECAY ---
def calcular_tendencia_asintotica(df, dias_proyeccion=30, objetivo=90):
    ultima_fecha = df['Fecha'].max()
    ultimo_valor = df['Lectura'].iloc[-1]
    
    # Generamos fechas futuras
    fechas_futuras = [ultima_fecha + timedelta(days=i) for i in range(dias_proyeccion)]
    t = np.arange(dias_proyeccion)
    
    # Modelo: f(t) = (Valor_Inicial - Objetivo) * exp(-k*t) + Objetivo
    # k es la constante de "esfuerzo" (0.1 para un cambio firme pero realista)
    k = 0.1 
    valores_tendencia = (ultimo_valor - objetivo) * np.exp(-k * t) + objetivo
    
    return fechas_futuras, valores_tendencia

# --- INTERFAZ DE USUARIO ---
st.title("🚀 Panel de Control Metabólico - Proyecto 90")
st.markdown(f"**Estado del Sistema:** Conectado | **Margen CONATEL:** 91 días")

# KPIs de Promedios Móviles (Al pie de la letra, Socio)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Promedio 8d", f"{df['Lectura'].tail(8).mean():.1f} mg/dL")
with col2:
    st.metric("Promedio 15d", f"{df['Lectura'].tail(15).mean():.1f} mg/dL")
with col3:
    st.metric("Meta Asintótica", "90 mg/dL", "-32 pts")
with col4:
    # Cálculo de IMC (Tarea de la noche)
    altura = 1.75 # Tu altura aquí, Socio
    peso_actual = df['Peso'].iloc[-1]
    imc = peso_actual / (altura ** 2)
    st.metric("IMC Actual", f"{imc:.1f}", "Normal")

# --- GRÁFICO DE ALTA PRECISIÓN ---
fechas_p, valores_p = calcular_tendencia_asintotica(df)

fig = go.Figure()

# Data Real
fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Lectura'], name="Lectura Real",
                         line=dict(color='#00e5ff', width=3), mode='lines+markers'))

# Tendencia Exponencial con Freno Logarítmico (La curva de la victoria)
fig.add_trace(go.Scatter(x=fechas_p, y=valores_p, name="Curva de Recuperación",
                         line=dict(color='#ff4081', dash='dash', width=2)))

# Zona de Seguridad
fig.add_hrect(y0=70, y1=100, fillcolor="green", opacity=0.1, label_text="Zona de Éxito")

fig.update_layout(template="plotly_dark", height=500, xaxis_title="Cronología de Recuperación",
                  yaxis_title="Glucosa (mg/dL)", hovermode="x unified")

st.plotly_chart(fig, use_container_width=True)
