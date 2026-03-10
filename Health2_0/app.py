import streamlit as st
import pandas as pd
import requests

# --- CONFIGURACIÓN DE ENLACE ---
# ID de la hoja donde pegaste la data de hoy
URL_GSHEET = "https://docs.google.com/spreadsheets/d/TU_ID_DE_HOJA/gviz/tq?tqx=out:csv&sheet=CONTROL"
URL_WEBHOOK = "TU_URL_DE_APPS_SCRIPT" # El que guarda la data

def load_data_from_cloud():
    try:
        # Leemos la nube directamente
        df_cloud = pd.read_csv(URL_GSHEET)
        df_cloud['Fecha'] = pd.to_datetime(df_cloud['Fecha'])
        return df_cloud
    except:
        st.error("⚠️ Falla de enlace con la base de datos.")
        return pd.DataFrame(columns=['Fecha', 'Glucosa'])

df = load_data_from_cloud()

# --- REGISTRO DIARIO (CON ENVÍO A LA NUBE) ---
with st.sidebar:
    with st.form("registro_salud"):
        f_med = st.date_input("Fecha", datetime.now())
        g_med = st.number_input("Glucosa", value=110)
        if st.form_submit_button("Guardar en Nube"):
            payload = {
                "tipo": "SALUD",
                "fecha": f_med.strftime('%Y-%m-%d'),
                "glucosa": g_med
            }
            # Disparamos el dato al espacio
            requests.post(URL_WEBHOOK, json=payload)
            st.success("✅ ¡Dato blindado en la nube!")
            st.rerun()
