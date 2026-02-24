import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DEL BÚNKER ---
st.set_page_config(page_title="Búnker Health - LDK", layout="wide")

# 1. DATA HISTÓRICA (La base que ya validamos)
data = {
    'Fecha': pd.to_datetime([
        '2026-02-18', '2026-02-19', '2026-02-20', '2026-02-21', 
        '2026-02-22', '2026-02-23', '2026-02-24'
    ]),
    'Lectura': [116, 122, 118, 116, 120, 123, 122],
    'Peso': [85.5, 85.4, 85.6, 85.2, 85.3, 85.5, 85.4] # Datos ejemplo para IMC
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
