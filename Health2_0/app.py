import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests

# --- 1. CONFIGURACIÓN DE ENLACE (LAS COORDENADAS) ---
# Sustituye con tu ID de hoja (el chorizo de letras de la URL del Sheet)
SHEET_ID = "TU_ID_DE_HOJA_AQUÍ" 
URL_LECTURA = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=CONTROL"
URL_ESCRITURA = "https://script.google.com/macros/s/AKfycbzDBcvqqtowBetmsHEsXxsIxhicjP0DU2rsDs6LxlHt48aDo5VKuGOSLrty8IMzxd5I9Q/exec"

st.set_page_config(page_title="Búnker Health - LDK", layout="wide")

# --- 2. MOTOR DE CARGA (DIRECTO DESDE LA NUBE) ---
def load_data():
    try:
        # Sintonizamos la frecuencia de Google Sheets
        df_cloud = pd.read_csv(URL_LECTURA)
        df_cloud['Fecha'] = pd.to_datetime(df_cloud['Fecha'])
        return df_cloud.sort_values('Fecha')
    except Exception as e:
        st.error(f"Falla de sintonía con la nube: {e}")
        # Retorno de emergencia si falla el enlace
        return pd.DataFrame(columns=['Fecha', 'Glucosa'])

def load_data():
    try:
        # Añadimos encoding='utf-8' para que acepte acentos y Ñs
        df_cloud = pd.read_csv(URL_LECTURA, encoding='utf-8')
        df_cloud['Fecha'] = pd.to_datetime(df_cloud['Fecha'])
        return df_cloud.sort_values('Fecha')
    except Exception as e:
        # Si el error persiste, probamos con este bypass:
        try:
             # A veces Google envía la data con un encoding diferente
             df_cloud = pd.read_csv(URL_LECTURA, encoding='latin-1')
             df_cloud['Fecha'] = pd.to_datetime(df_cloud['Fecha'])
             return df_cloud.sort_values('Fecha')
        except:
             st.error(f"Falla de sintonía con la nube: {e}")
             return pd.DataFrame(columns=['Fecha', 'Glucosa'])

# --- 4. CÁLCULOS Y PROYECCIONES ---
if not df.empty:
    df['MA8'] = df['Glucosa'].rolling(window=8).mean()
    df['MA15'] = df['Glucosa'].rolling(window=15).mean()

    # Proyección Plan 91
    asintota, k, v_base = 90, 0.08, 122
    fecha_base = pd.to_datetime('2026-02-24')
    t_fut = np.arange(60)
    v_fut = (v_base - asintota) * np.exp(-k * t_fut) + asintota
    fechas_fut = [fecha_base + timedelta(days=int(i)) for i in t_fut]

    # --- 5. INTERFAZ ---
    st.title("🛡️ Búnker Health: Proyecto 91")
    st.markdown(f"**Bitácora Activa:** {df['Fecha'].max().strftime('%d-%m-%Y')} | Glucosa: **{df['Glucosa'].iloc[-1]}**")

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Última Lectura", df['Glucosa'].iloc[-1], delta_color="inverse")
    c2.metric("Promedio 8d", f"{df['MA8'].iloc[-1]:.1f}" if not df['MA8'].isnull().all() else "---")
    c3.metric("Meta 91", "90 mg/dL")
    c4.metric("Días Restantes", (pd.to_datetime('2026-05-26') - datetime.now()).days)

    # Gráfico Dark
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Glucosa'], name="Glucosa Real", 
                             line=dict(color='#00e5ff', width=4), mode='lines+markers'))
    fig.add_trace(go.Scatter(x=fechas_fut, y=v_fut, name="Hito Teórico (Plan 91)", 
                             line=dict(color='#ff4081', dash='dash', width=2)))

    fig.update_layout(template="plotly_dark", height=500, margin=dict(l=10, r=10, t=40, b=10),
                      hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("📡 Buscando señales en la nube... Asegúrate de tener datos en tu Google Sheet.")
