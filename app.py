import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Búnker Health - Monitor de Glucosa", layout="wide")

st.title("📊 Monitor de Control Metabólico - Luis")
st.markdown("---")

# 1. Base de Datos (Simulando lo que tienes en Excel)
# Aquí puedes cargar tu archivo: df = pd.read_excel("tus_datos.xlsx")
data = {
    'Fecha': pd.to_datetime(['2026-02-21', '2026-02-22', '2026-02-23', '2026-02-24']),
    'Lectura': [116, 120, 123, 122]
}
df = pd.DataFrame(data)

# 2. Sidebar para agregar nueva lectura
st.sidebar.header("📥 Nueva Entrada")
nueva_fecha = st.sidebar.date_input("Fecha", datetime.now())
nuevo_valor = st.sidebar.number_input("Valor Glucosa (mg/dL)", min_value=50, max_value=300, value=110)

if st.sidebar.button("Registrar Lectura"):
    # Aquí iría la lógica para guardar en el Excel/CSV
    st.sidebar.success(f"Registrado: {nuevo_valor} mg/dL")

# 3. Definición de la Meta (Tendencia Planificada)
# Digamos que tu meta es bajar de 122 a 100 en 15 días
meta_inicio = 122
meta_objetivo = 100
dias_plan = 15

# 4. Creación del Gráfico
fig = go.Figure()

# Línea de Datos Reales
fig.add_trace(go.Scatter(
    x=df['Fecha'], y=df['Lectura'],
    mode='lines+markers',
    name='Glucosa Real',
    line=dict(color='#00e5ff', width=3),
    marker=dict(size=10)
))

# Línea de Tendencia Planificada (Meta)
fig.add_trace(go.Scatter(
    x=[df['Fecha'].max(), df['Fecha'].max() + pd.Timedelta(days=dias_plan)],
    y=[meta_inicio, meta_objetivo],
    mode='lines',
    name='Ruta Objetivo (Meta)',
    line=dict(color='#ff4081', dash='dash', width=2)
))

# Zonas de Alerta
fig.add_hrect(y0=70, y1=100, fillcolor="green", opacity=0.1, line_width=0, annotation_text="Zona Óptima")
fig.add_hrect(y0=100, y1=125, fillcolor="yellow", opacity=0.1, line_width=0, annotation_text="Pre-Alerta")
fig.add_hrect(y0=125, y1=200, fillcolor="red", opacity=0.1, line_width=0, annotation_text="Crítico")

fig.update_layout(
    title="Análisis de Tendencia vs Meta",
    xaxis_title="Fecha",
    yaxis_title="mg/dL",
    template="plotly_dark",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# 5. Indicadores Rápidos
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Última Lectura", f"{df['Lectura'].iloc[-1]}", "1.2%", delta_color="inverse")
with col2:
    st.metric("Promedio 7 días", "118", "-2.5%")
with col3:
    st.metric("Distancia a Meta", f"{df['Lectura'].iloc[-1] - meta_objetivo} pts")
