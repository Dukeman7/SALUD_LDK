import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os

# 1. DATA MAESTRA (Hardcoded para que nunca falle)
data_inicial = {
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
}

DB_FILE = "glucosa_historico.csv"

def cargar_datos():
    df_base = pd.DataFrame(data_inicial)
    df_base['Fecha'] = pd.to_datetime(df_base['Fecha'])
    
    if os.path.exists(DB_FILE):
        df_csv = pd.read_csv(DB_FILE)
        df_csv['Fecha'] = pd.to_datetime(df_csv['Fecha'])
        df_final = pd.concat([df_base, df_csv]).drop_duplicates(subset=['Fecha'], keep='last')
    else:
        df_final = df_base
        
    return df_final.sort_values('Fecha')

# --- APP STREAMLIT ---
st.set_page_config(page_title="Búnker Health", layout="wide")
df = cargar_datos()

# Cálculos de Promedios Móviles
df['MA8'] = df['Lectura'].rolling(window=8, min_periods=1).mean()
df['MA15'] = df['Lectura'].rolling(window=15, min_periods=1).mean()
df['MA30'] = df['Lectura'].rolling(window=30, min_periods=1).mean()
df['MA45'] = df['Lectura'].rolling(window=45, min_periods=1).mean()

# Gráfico
fig = go.Figure()
fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Lectura'], mode='lines+markers', name='Diario', line=dict(color='#00e5ff', width=1)))

colores = {'MA8': '#ffeb3b', 'MA15': '#ff9800', 'MA30': '#f44336', 'MA45': '#9c27b0'}
for ma in colores:
    fig.add_trace(go.Scatter(x=df['Fecha'], y=df[ma], mode='lines', name=f'Promedio {ma[2:]}d', line=dict(color=colores[ma])))

# Línea de Tendencia Planificada (Meta)
# Desde hoy (122) hacia el 15 de Marzo (100)
fig.add_trace(go.Scatter(
    x=[df['Fecha'].max(), pd.to_datetime('2026-03-15')],
    y=[df['Lectura'].iloc[-1], 100],
    mode='lines', name='Ruta a Meta', line=dict(color='#00ff41', dash='dot', width=3)
))

fig.update_layout(template="plotly_dark", title="Control de Navegación Metabólica", hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# Registro
with st.sidebar:
    st.header("📥 Entrada")
    f = st.date_input("Fecha", datetime.now())
    v = st.number_input("Valor", 50, 300, 110)
    if st.button("Guardar"):
        new = pd.DataFrame({'Fecha': [pd.to_datetime(f)], 'Lectura': [v]})
        new.to_csv(DB_FILE, mode='a', header=not os.path.exists(DB_FILE), index=False)
        st.success("Registrado")
        st.rerun()
