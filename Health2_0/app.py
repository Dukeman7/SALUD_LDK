import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import io

# --- 1. CONFIGURACIÓN DE ENLACE ---
# PEGA AQUÍ TU ID DE GOOGLE SHEET
SHEET_ID = "TU_ID_DE_HOJA_AQUÍ" 
URL_LECTURA = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=CONTROL"
URL_ESCRITURA = "https://script.google.com/macros/s/AKfycby1BwxvJAa-mmMxG87Eid-u-BF2e2L1r9TFQwK1h7Z5q0evmsK5ZmjJ2XH1Tl6jnJIkjQ/exec"

st.set_page_config(page_title="Búnker Health - LDK", layout="wide")

# --- 2. FUNCIÓN DE CARGA ACORAZADA (ANTI-ACENTOS) ---
def load_data():
    try:
        # Intento con requests para forzar el encoding y evitar el error 'ascii'
        response = requests.get(URL_LECTURA)
        response.encoding = 'utf-8' # Forzamos idioma universal
        df_cloud = pd.read_csv(io.StringIO(response.text))
        
        # Limpieza de nombres de columnas
        df_cloud.columns = [c.strip() for c in df_cloud.columns]
        
        if 'Fecha' in df_cloud.columns:
            df_cloud['Fecha'] = pd.to_datetime(df_cloud['Fecha'], errors='coerce')
            df_cloud = df_cloud.dropna(subset=['Fecha'])
            return df_cloud.sort_values('Fecha')
        return pd.DataFrame(columns=['Fecha', 'Glucosa'])
    except Exception as e:
        st.error(f"Falla de sintonía con la nube: {e}")
        return pd.DataFrame(columns=['Fecha', 'Glucosa'])

df = load_data()

# --- 3. REGISTRO DIARIO (EL TRANSMISOR) ---
with st.sidebar:
    st.header("📝 Registro Diario")
    with st.form("registro_form", clear_on_submit=True):
        fecha_input = st.date_input("Fecha de medición", datetime.now())
        glucosa_input = st.number_input("Glucosa (mg/dL)", min_value=50, max_value=300, value=110)
        submit = st.form_submit_button("📡 ENVIAR AL ESPACIO")
        
        if submit:
            payload = {
                "tipo": "SALUD",
                "fecha": fecha_input.strftime('%Y-%m-%d'),
                "glucosa": glucosa_input
            }
            try:
                res = requests.post(URL_ESCRITURA, json=payload, timeout=10)
                if res.status_code == 200:
                    st.success("✅ ¡Dato blindado en la nube!")
                    st.rerun()
                else:
                    st.error("❌ Error en el repetidor de Google.")
            except:
                st.error("❌ Falla de transmisión (Timeout).")

# --- 4. CÁLCULOS Y PROYECCIONES ---
if not df.empty:
    # Aseguramos que Glucosa sea numérica
    df['Glucosa'] = pd.to_numeric(df['Glucosa'], errors='coerce')
    df = df.dropna(subset=['Glucosa'])
    
    # Medias Móviles
    df['MA8'] = df['Glucosa'].rolling(window=8).mean()
    df['MA15'] = df['Glucosa'].rolling(window=15).mean()

    # Proyección Plan 91 (Hito Tatuado)
    asintota, k, v_base = 90, 0.08, 122
    fecha_base = pd.to_datetime('2026-02-24')
    t_fut = np.arange(70) # Extendemos la línea de tiempo
    v_fut = (v_base - asintota) * np.exp(-k * t_fut) + asintota
