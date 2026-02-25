import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DEL BÚNKER ---
st.set_page_config(page_title="Búnker Health - LDK", layout="wide")

# 1. DATA MAESTRA (Glucosa + Peso procesado)
fechas = pd.to_datetime([
    '2026-01-02', '2026-01-04', '2026-01-05', '2026-01-06', '2026-01-07', '2026-01-08', '2026-01-09',
    '2026-01-10', '2026-01-11', '2026-01-12', '2026-01-13', '2026-01-14', '2026-01-15', '2026-01-16',
    '2026-01-17', '2026-01-18', '2026-01-19', '2026-01-20', '2026-01-21', '2026-01-22', '2026-01-23',
    '2026-01-24', '2026-01-25', '2026-01-26', '2026-01-28', '2026-01-29', '2026-01-30', '2026-01-31',
    '2026-02-01', '2026-02-02', '2026-02-03', '2026-02-04', '2026-02-05', '2026-02-06', '2026-02-07',
    '2026-02-08', '2026-02-09', '2026-02-10', '2026-02-11', '2026-02-12', '2026-02-13', '2026-02-14',
    '2026-02-15', '2026-02-16', '2026-02-18', '2026-02-19', '2026-02-20', '2026-02-21', '2026-02-22',
    '2026-02-23', '2026-02-24'
])

glucosa = [
    110, 94, 107, 121, 97, 109, 109, 109, 105, 122, 110, 110, 107, 115, 109, 116, 126, 107, 125, 111, 133,
    112, 116, 115, 96, 107, 109, 101, 116, 111, 107, 105, 107, 100, 103, 105, 103, 110, 118, 107, 113, 115,
    119, 116, 116, 122, 118, 116, 120, 123, 122
]

peso = [
    125.6, 124.344, 125.463, 124.459, 125.206, 126.333, 127.217, 128.362, 127.977, 128.105, 
    128.361, 127.334, 128.480, 129.122, 128.864, 129.637, 130.415, 130.285, 130.545, 129.109, 
    128.722, 128.722, 129.366, 129.366, 128.978, 128.849, 127.431, 126.921, 126.160, 125.655, 
    124.399, 124.772, 123.774, 124.145, 124.021, 124.269, 125.512, 124.131, 124.379, 124.379, 
    125.623, 124.367, 124.367, 123.745, 122.384, 122.873, 122.259, 122.137, 122.137, 122.503, 
    122.748
]

df = pd.DataFrame({'Fecha': fechas, 'Glucosa': glucosa, 'Peso': peso})

# --- LÓGICA DE PREDICCIÓN (Asintótica) ---
# Meta: 100 mg/dL | Asíntota: 90 mg/dL | k: 0.1
target = 100
asintota = 90
k = 0.1
v_last = df['Glucosa'].iloc[-1]

# Cálculo de t (días para llegar al target): target = (v_last - asintota) * e^(-kt) + asintota
dias_para_100 = -np.log((target - asintota) / (v_last - asintota)) / k
fecha_exito = df['Fecha'].max() + timedelta(days=int(dias_para_100))

# --- INTERFAZ ---
st.title("📊 Proyecto 90: Control de Mando LDK")
st.markdown(f"**CONATEL Countdown:** 91 Días restantes")

# Métricas Principales
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Glucosa Actual", f"{v_last} mg/dL", "-1 pt")
with col2:
    st.metric("Peso Actual", f"{df['Peso'].iloc[-1]:.2f} kg", "Bajando")
with col3:
    st.success(f"🎯 Meta 100 mg/dL: **{fecha_exito.strftime('%d de Marzo')}**")

# --- GRÁFICO DOBLE EJE ---
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Glucosa (Eje Principal)
fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Glucosa'], name="Glucosa (mg/dL)",
                         line=dict(color='#00e5ff', width=3)), secondary_y=False)

# Peso (Eje Secundario)
fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Peso'], name="Peso (kg)",
                         line=dict(color='#ffeb3b', width=2, dash='dot')), secondary_y=True)

# Proyección Asíntotica
t_future = np.arange(30)
v_future = (v_last - asintota) * np.exp(-k * t_future) + asintota
dates_future = [df['Fecha'].max() + timedelta(days=int(i)) for i in t_future]

fig.add_trace(go.Scatter(x=dates_future, y=v_future, name="Tendencia a 90",
                         line=dict(color='#ff4081', dash='dash')), secondary_y=False)

fig.update_layout(template="plotly_dark", title="Sincronía Glucosa vs Peso")
st.plotly_chart(fig, use_container_width=True)

# Cálculo de IMC (Tarea de la noche)
altura = 1.70 # Cambia esto por tu altura real
imc = df['Peso'].iloc[-1] / (altura**2)
st.info(f"💡 **Cálculo de IMC:** Su índice actual es **{imc:.1f}**. Vamos por el rango saludable.")
