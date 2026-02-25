import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os

# --- 1. CONFIGURACIÓN DEL BÚNKER ---
st.set_page_config(page_title="Búnker Health - LDK", layout="wide")

# --- 2. GESTIÓN DE DATOS (EL MOTOR DE SEGUIMIENTO) ---
FILE_NAME = "glucosa_seguimiento.csv"

# Data Maestra inicial (la que ya validamos)
data_inicial = {
    'Fecha': [
        '2026-01-02', '2026-01-04', '2026-01-05', '2026-01-06', '2026-01-07', '2026-01-08', '2026-01-09',
        '2026-01-10', '2026-01-11', '2026-01-12', '2026-01-13', '2026-01-14', '2026-01-15', '2026-01-16',
        '2026-01-17', '2026-01-18', '2026-01-19', '2026-01-20', '2026-01-21', '2026-01-22', '2026-01-23',
        '2026-01-24', '2026-01-25', '2026-01-26', '2026-01-28', '2026-01-29', '2026-01-30', '2026-01-31',
        '2026-02-01', '2026-02-02', '2026-02-03', '2026-02-04', '2026-02-05', '2026-02-06', '2026-02-07',
        '2026-02-08', '2026-02-09', '2026-02-10', '2026-02-11', '2026-02-12', '2026-02-13', '2026-02-14',
        '2026-02-15', '2026-02-16', '2026-02-18', '2026-02-19', '2026-02-20', '2026-02-21', '2026-02-22',
        '2026-02-23', '2026-02-24', '2026-02-25'
    ],
    'Glucosa': [
        110, 94, 107, 121, 97, 109, 109, 109, 105, 122, 110, 110, 107, 115, 109, 116, 126, 107, 125, 111, 133,
        112, 116, 115, 96, 107, 109, 101, 116, 111, 107, 105, 107, 100, 103, 105, 103, 110, 118, 107, 113, 115,
        119, 116, 116, 122, 118, 116, 120, 123, 122, 112
    ]
}

def load_data():
    if os.path.exists(FILE_NAME):
        return pd.read_csv(FILE_NAME, parse_dates=['Fecha'])
    else:
        df_init = pd.DataFrame(data_inicial)
        df_init['Fecha'] = pd.to_datetime(df_init['Fecha'])
        df_init.to_csv(FILE_NAME, index=False)
        return df_init

df = load_data()

# --- 3. VENTANA DE SEGUIMIENTO (SIDEBAR) ---
with st.sidebar:
    st.header("📝 Registro Diario")
    with st.form("registro_form", clear_on_submit=True):
        fecha_input = st.date_input("Fecha de medición", datetime.now())
        glucosa_input = st.number_input("Glucosa (mg/dL)", min_value=50, max_value=300, value=112)
        submit = st.form_submit_button("Guardar en el Búnker")
        
        if submit:
            nueva_fila = pd.DataFrame({'Fecha': [pd.to_datetime(fecha_input)], 'Glucosa': [glucosa_input]})
            df = pd.concat([df, nueva_fila]).drop_duplicates(subset=['Fecha'], keep='last').sort_values('Fecha')
            df.to_csv(FILE_NAME, index=False)
            st.success("¡Dato guardado!")
            st.rerun()

# --- 4. CÁLCULOS DE CONTROL ---
df['MA8'] = df['Glucosa'].rolling(window=8).mean()
df['MA15'] = df['Glucosa'].rolling(window=15).mean()
df['MA30'] = df['Glucosa'].rolling(window=30).mean()

# Proyección FIJA (Tatuada el 24-Feb en 122)
asintota = 90
k = 0.08
v_base = 122
fecha_base = pd.to_datetime('2026-02-24')
t_fut = np.arange(45)
v_fut = (v_base - asintota) * np.exp(-k * t_fut) + asintota
fechas_fut = [fecha_base + timedelta(days=int(i)) for i in t_fut]

# --- 5. INTERFAZ ---
st.title("🛡️ Búnker Health: Proyecto 91")
st.markdown(f"**Bitácora Activa:** {df['Fecha'].max().strftime('%d-%m-%Y')} | Glucosa: {df['Glucosa'].iloc[-1]}")

# KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Última Lectura", df['Glucosa'].iloc[-1], f"{df['Glucosa'].iloc[-1] - df['Glucosa'].iloc[-2] if len(df)>1 else 0}", delta_color="inverse")
c2.metric("Promedio 8d", f"{df['MA8'].iloc[-1]:.1f}")
c3.metric("Promedio 15d", f"{df['MA15'].iloc[-1]:.1f}")
c4.metric("Días Restantes 91", (pd.to_datetime('2026-05-26') - datetime.now()).days)

# Gráfico
fig = go.Figure()
df_vis = df.tail(45)

# Glucosa Real (Cyan)
fig.add_trace(go.Scatter(x=df_vis['Fecha'], y=df_vis['Glucosa'], name="Glucosa Real", 
                         line=dict(color='#00e5ff', width=4), mode='lines+markers'))

# Hito Tatuado (Rosa)
fig.add_trace(go.Scatter(x=fechas_fut, y=v_fut, name="Plan 91 (Hito Fijo)", 
                         line=dict(color='#ff4081', dash='dash', width=2)))

fig.update_layout(template="plotly_dark", height=600, hovermode="x unified", title="Seguimiento vs Hito Proyectado")
st.plotly_chart(fig, use_container_width=True)

# Sección de Luisito
if df['Glucosa'].iloc[-1] < 100:
    st.balloons()
    st.success("¡OBJETIVO LUISITO ALCANZADO! Por debajo de 100.")
