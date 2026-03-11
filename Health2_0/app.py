import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import io

# --- 1. COORDENADAS DEL BÚNKER ---
SHEET_ID = "1MT2EYKUmKmAP8vSBbPElR_DsP45zgrczDTMXe1b9s5Y" 
URL_LECTURA = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet=CONTROL"
URL_ESCRITURA = "https://script.google.com/macros/s/AKfycbwWXvFy3wkSRT1BhTmCMi6cPyRsq7KQ80BZvOxzPk6bRaj27yfHkQTO-J6trH6IgtGFhw/exec"

st.set_page_config(page_title="Búnker LDK: Radar Health V4.0", layout="wide")

@st.cache_data(ttl=60)
def load_data():
    try:
        response = requests.get(URL_LECTURA, timeout=10)
        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
        df.columns = df.columns.str.strip()
        for col in ['Glucosa', 'Peso']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        return df.dropna(subset=['Fecha']).sort_values('Fecha')
    except:
        return pd.DataFrame(columns=['Fecha', 'Glucosa', 'Peso'])

df = load_data()
hoy = datetime.now()

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("📝 Registro de Operaciones")
    with st.form("form_salud", clear_on_submit=True):
        f_in = st.date_input("Fecha de Registro", hoy)
        g_in = st.number_input("Glucosa (mg/dL)", value=110)
        p_in = st.text_input("Peso (kg) - Vacío si no toca hoy", value="")
        if st.form_submit_button("📡 TRANSMITIR AL BÚNKER"):
            try:
                p_val = float(p_in.replace(',', '.')) if p_in.strip() != "" else 0
                payload = {"tipo": "SALUD", "fecha": f_in.strftime('%Y-%m-%d'), "glucosa": g_in, "peso": p_val}
                r = requests.post(URL_ESCRITURA, json=payload, timeout=15)
                if r.status_code == 200:
                    st.success("✅ Datos en la Nube")
                    st.cache_data.clear()
                    st.rerun()
                else: st.error("Error 500: Revisa el Script")
            except Exception as e: st.error(f"Falla: {e}")

    st.divider()
    st.header("🔭 Ajuste de Radar (Zoom)")
    f_inicio_zoom = st.date_
