import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN DEL BÚNKER ---
st.set_page_config(page_title="Búnker Health - LDK", layout="wide")

# --- 2. DATA MAESTRA (GLUCOSA REAL) ---
data_glucosa = {
    'Fecha': pd.to_datetime([
        '2026-01-02', '2026-01-04', '2026-01-05', '2026-01-06', '2026-01-07', '2026-01-08', '2026-01-09',
        '2026-01-10', '2026-01-11', '2026-01-12', '2026-01-13', '2026-01-14', '2026-01-15', '2026-01-16',
        '2026-01-17', '2026-01-18', '2026-01-19', '2026-01-20', '2026-01-21', '2026-01-22', '2026-01-23',
        '2026-01-24', '2026-01-25', '2026-01-26', '2026-01-28', '2026-01-29', '2026-01-30', '2026-01-31',
        '2026-02-01', '2026-02-02', '2026-02-03', '2026-02-04', '2026-02-05', '2026-02-06', '2026-02-07',
        '2026-02-08', '2026-02-09', '2026-02-10', '2026-02-11', '2026-02-12', '2026-02-13', '2026-02-14',
        '2026-02-15', '2026-02-16', '2026-02-18', '2026-02-19', '2026-02-20', '2026-02-21', '2026-02-22',
        '2026-02-23', '2026-02-24'
    ]),
    'Glucosa': [
        110, 94, 107, 121, 97, 109, 109, 109, 105, 122, 110, 110, 107, 115, 109, 116, 126, 107, 125, 111, 133,
        112, 116, 115, 96, 107, 109, 101, 116, 111, 107, 105, 107, 100, 103, 105, 103, 110, 118, 107, 113, 115,
        119, 116, 116, 122, 118, 116, 120, 123, 122
    ]
}
df = pd.DataFrame(data_glucosa)

# --- 3. LÓGICA DE PESO (INTERPOLACIÓN DE HITOS) ---
# Hitos discretos (lo que tú controlas)
hitos_peso = {
    '2026-01-01': 127.0,
    '2026-01-25': 123.5,
    '2026-02-13': 125.3,
    '2026-02-24': 125.1
}

df_p = pd.DataFrame(list(hitos_peso.items()), columns=['Fecha', 'Peso'])
df_p['Fecha'] = pd.to_datetime(df_p['Fecha'])
# Rellenamos los días intermedios de forma continua
df_p = df_p.set_index('Fecha').resample('D').interpolate(method='linear').reset_index()

# Unimos la data
df = pd.merge(df, df_p, on='Fecha', how='left')
df['Peso'] = df['Peso'].ffill().bfill() # Limpieza de bordes

# --- 4. CÁLCULOS DE CONTROL (PROMEDIOS Y PROYECCIÓN) ---
df['MA8'] = df['Glucosa'].rolling(window=8).mean()
df['MA15'] = df['Glucosa'].rolling(window=15).mean()
df['MA30'] = df['Glucosa'].rolling(window=30).mean()
df['MA45'] = df['Glucosa'].rolling(window=45).mean()

# Parámetros Proyectados (Plan 91)
asintota = 90
k = 0.08
v_hoy = 122
dias_proy = 45
t
