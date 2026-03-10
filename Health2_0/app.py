import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import io

# --- 1. COORDENADAS ---
SHEET_ID = "1MT2EYKUmKmAP8vSBbPElR_DsP45zgrczDTMXe1b9s5Y" 
URL_LECTURA = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet=CONTROL"
URL_ESCRITURA = "https://script.google.com/macros/s/AKfycbxHsIEBnMN3KrIof9bB5BM_-RbLWXa-t2A8JfPmuHgYQiRhqLFdhYcxdymBz_ELMK94SA/exec"

st.set_page_config(page_title="Búnker LDK: Control de Radar", layout="wide")

def load_data():
    try:
        response = requests.get(URL_LECTURA)
        content = response.content.decode('utf-8')
        df = pd.read_csv(io.StringIO(content))
        df.columns = df.columns.str.strip()
        for col in ['Glucosa', 'Peso']:
            if col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        return df.dropna(subset=['Fecha']).sort_values('Fecha')
    except:
        return pd.DataFrame(columns=['Fecha', 'Glucosa', 'Peso'])

df = load_data()

# --- 2. BARRA LATERAL: REGISTRO Y AJUSTE DE VENTANA ---
with st.sidebar:
    st.header("📝 Registro de Biometría")
    with st.form("reg_v35"):
        f_in = st.date_input("Fecha de hoy", datetime.now())
        g_in = st.number_input("Glucosa", value=111)
        p_in = st.text_input("Peso (kg)", value="123.5") 
        if st.form_submit_button("📡 TRANSMITIR"):
            p_val = float(p_in.replace(',', '.'))
            payload = {"tipo":"SALUD", "fecha":f_in.strftime('%Y-%m-%d'), "glucosa":g_in, "peso":p_val}
            requests.post(URL_ESCRITURA, json=payload)
            st.rerun()
    
    st.divider()
    st.header("🔭 Ajuste de Radar (Zoom)")
    # Definimos los límites del slider basados en el Proyecto 91 y el fin de año
    min_date = datetime(2026, 1, 1)
    max_date = datetime(2026, 12, 31)
    
    fecha_inicio = st.date_input("Ver desde:", min_date)
    fecha_fin = st.date_input("Ver hasta:", max_date)

# --- 3. PROSPECTIVAS ---
f_base_g = pd.to_datetime('2026-02-24')
t_fut_g = np.arange(92)
v_fut_g = (122 - 90) * np.exp(-0.08 * t_fut_g) + 90
fechas_g = [f_base_g + timedelta(days=int(i)) for i in t_fut_g]

f_inicio_p = pd.to_datetime('2026-03-01')
f_meta_p = pd.to_datetime('2026-06-28')
f_final_p = pd.to_datetime('2026-12-28')
fechas_proy = [f_inicio_p, f_meta_p, f_final_p]
pesos_proy = [123.5, 115.0, 99.8]

# --- 4. INTERFAZ ---
st.title("🛡️ Búnker Health: Operación 99.8 kg")

if not df.empty:
    ult_g = df['Glucosa'].iloc[-1]
    df_p = df.dropna(subset=['Peso'])
    ult_p = df_p['Peso'].iloc[-1] if not df_p.empty else 123.5
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Glucosa", f"{ult_g:.0f}", delta=f"{ult_g-90:.0f} p/meta", delta_color="inverse" if ult_g > 130 else "normal")
    c2.metric("Peso Actual", f"{ult_p:.1f} kg")
    c3.metric("Meta Junio", "115 kg")
    c4.metric("Meta Diciembre", "99.8 kg")

    # --- 5. GRAFICADOR CON RANGO DINÁMICO ---
    fig = go.Figure()
    
    # Glucosa
    fig.add_trace(go.Scatter(x=fechas_g, y=v_fut_g, name="Meta Glucosa (90)", line=dict(color='#ff4081', dash='dot')))
    fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Glucosa'], name="Realidad Glucosa", line=dict(color='#00e5ff', width=3), mode='lines+markers'))
    
    # Peso Prospectiva
    fig.add_trace(go.Scatter(x=fechas_proy, y=pesos_proy, name="Rumbo a 99.8", line=dict(color='rgba(255, 255, 0, 0.2)', dash='dash')))
    
    # Peso Real
    if not df_p.empty:
        fig.add_trace(go.Scatter(x=df_p['Fecha'], y=df_p['Peso'], name="Peso Real (kg)",
                                 line=dict(color='yellow', width=3), mode='lines+markers',
                                 marker=dict(size=12, symbol='diamond', line=dict(width=2, color='white'))))

    # APLICAMOS LOS LÍMITES DEL SIDEBAR
    fig.update_layout(
        template="plotly_dark", 
        height=600, 
        hovermode="x unified",
        xaxis=dict(range=[fecha_inicio, fecha_fin]) # Aquí ocurre la magia
    )
    st.plotly_chart(fig, use_container_width=True)
# --- SEGMENTO DE CAJA FUERTE: GUARDAR GRÁFICA ---
st.divider()
st.subheader("📁 Caja Fuerte del Búnker")

# Convertimos la figura a una imagen estática (requiere que el usuario la descargue)
try:
    # Generamos el nombre del archivo con la fecha de hoy
    nombre_archivo = f"Bunker_Health_LDK_{datetime.now().strftime('%Y-%m-%d')}.png"
    
    # Plotly permite descargar directamente desde el gráfico, 
    # pero este botón es para el registro formal del búnker:
    st.download_button(
        label="📸 GUARDAR CAPTURA DEL RADAR (.PNG)",
        data=fig.to_image(format="png", width=1200, height=600, scale=2),
        file_name=nombre_archivo,
        mime="image/png",
        help="Guarda una imagen de alta resolución de la situación actual del Búnker."
    )
    st.caption("Nota: La primera vez puede tardar unos segundos en procesar la imagen.")
except Exception as e:
    st.info("💡 Para activar la descarga automática de imágenes, asegúrate de tener instalada la librería 'kaleido' (pip install kaleido).")
else:
    st.info("📡 Escaneando la nube... asegúrate de que la hoja CONTROL tenga datos.")
