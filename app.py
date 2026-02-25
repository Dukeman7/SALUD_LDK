import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN DEL BÚNKER ---
st.set_page_config(page_title="Búnker Health - LDK", layout="wide")

# --- 2. DATA MAESTRA (¡ACTUALIZADA CON EL 112!) ---
data_glucosa = {
    'Fecha': pd.to_datetime([
        '2026-01-02', '2026-01-04', '2026-01-05', '2026-01-06', '2026-01-07', '2026-01-08', '2026-01-09',
        '2026-01-10', '2026-01-11', '2026-01-12', '2026-01-13', '2026-01-14', '2026-01-15', '2026-01-16',
        '2026-01-17', '2026-01-18', '2026-01-19', '2026-01-20', '2026-01-21', '2026-01-22', '2026-01-23',
        '2026-01-24', '2026-01-25', '2026-01-26', '2026-01-28', '2026-01-29', '2026-01-30', '2026-01-31',
        '2026-02-01', '2026-02-02', '2026-02-03', '2026-02-04', '2026-02-05', '2026-02-06', '2026-02-07',
        '2026-02-08', '2026-02-09', '2026-02-10', '2026-02-11', '2026-02-12', '2026-02-13', '2026-02-14',
        '2026-02-15', '2026-02-16', '2026-02-18', '2026-02-19', '2026-02-20', '2026-02-21', '2026-02-22',
        '2026-02-23', '2026-02-24', '2026-02-25' # <--- ¡EL DÍA DE LA VICTORIA!
    ]),
    'Glucosa': [
        110, 94, 107, 121, 97, 109, 109, 109, 105, 122, 110, 110, 107, 115, 109, 116, 126, 107, 125, 111, 133,
        112, 116, 115, 96, 107, 109, 101, 116, 111, 107, 105, 107, 100, 103, 105, 103, 110, 118, 107, 113, 115,
        119, 116, 116, 122, 118, 116, 120, 123, 122, 112  # <--- ¡EL 112 MÁGICO!
    ]
}
df = pd.DataFrame(data_glucosa)

# --- 3. LÓGICA DE PESO (TATUAJE DE HOY) ---
hitos_peso = {
    '2026-01-01': 127.0,
    '2026-01-25': 123.5,
    '2026-02-13': 125.3,
    '2026-02-24': 125.1,
    '2026-02-25': 125.0  # Ligera baja por el pollo asado
}
df_p = pd.DataFrame(list(hitos_peso.items()), columns=['Fecha', 'Peso'])
df_p['Fecha'] = pd.to_datetime(df_p['Fecha'])
df_p = df_p.set_index('Fecha').resample('D').interpolate(method='linear').reset_index()
df = pd.merge(df, df_p, on='Fecha', how='left')
df['Peso'] = df['Peso'].ffill().bfill()

# --- 4. CÁLCULOS DE CONTROL ---
df['MA8'] = df['Glucosa'].rolling(window=8).mean()
df['MA15'] = df['Glucosa'].rolling(window=15).mean()
df['MA30'] = df['Glucosa'].rolling(window=30).mean()

# --- PROYECCIÓN FIJA "PLAN 91" (Tatuada el 24-Feb en 122) ---
asintota = 90
k = 0.08
v_base = 122  # Punto de partida del hito
fecha_base = pd.to_datetime('2026-02-24')
dias_proy = 45
t_fut = np.arange(dias_proy)
v_fut = (v_base - asintota) * np.exp(-k * t_fut) + asintota
fechas_fut = [fecha_base + timedelta(days=int(i)) for i in t_fut]

# --- 5. INTERFAZ ---
st.title("🛡️ Búnker Health: ¡Efecto Tai Chi! 🧘‍♂️")
st.markdown(f"**CONATEL:** Bendiciones de César recibidas | **Glucosa:** -10 pts vs ayer")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Glucosa Hoy", "112", "-10")
c2.metric("Promedio 8d", f"{df['MA8'].iloc[-1]:.1f}")
c3.metric("Promedio 15d", f"{df['MA15'].iloc[-1]:.1f}")
c4.metric("Desviación vs Hito", f"{112 - v_fut[1]:.1f}", "¡BAJO LA CURVA!", delta_color="inverse")

# Gráfico
fig = make_subplots(specs=[[{"secondary_y": True}]])
df_vis = df.tail(45)

fig.add_trace(go.Scatter(x=df_vis['Fecha'], y=df_vis['Glucosa'], name="Glucosa Real", 
                         line=dict(color='#00e5ff', width=4)), secondary_y=False)

fig.add_trace(go.Scatter(x=fechas_fut, y=v_fut, name="Hito Fijo (Plan 91)", 
                         line=dict(color='#ff4081', dash='dash', width=2)), secondary_y=False)

fig.add_trace(go.Scatter(x=df_vis['Fecha'], y=df_vis['Peso'], name="Peso (kg)", 
                         line=dict(color='#ffeb3b', width=2, dash='dot')), secondary_y=True)

fig.update_layout(template="plotly_dark", height=600, hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

st.success(f"🚀 **Análisis del Búnker:** Estás navegando por DEBAJO de la curva proyectada. Si mantienes este ritmo, el 99 de Luisito (18 de Marzo) está asegurado.")
