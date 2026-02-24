import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os

# 1. Configuración de Archivo de Datos
DB_FILE = "glucosa_historico.csv"

def cargar_datos():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        return df.sort_values('Fecha')
    else:
        # Si no existe, creamos uno con tu data inicial
        return pd.DataFrame(columns=['Fecha', 'Lectura'])

# 2. Configuración de la App
st.set_page_config(page_title="Búnker Health - Glucosa Pro", layout="wide")
st.title("📊 Monitor Metabólico de Alta Precisión")

df = cargar_datos()

# 3. Sidebar: Registro
st.sidebar.header("📥 Registro de Lectura")
fecha_ingreso = st.sidebar.date_input("Fecha", datetime.now())
valor_ingreso = st.sidebar.number_input("mg/dL", min_value=50, max_value=300, value=110)

if st.sidebar.button("💾 Guardar en Búnker"):
    nueva_fila = pd.DataFrame({'Fecha': [pd.to_datetime(fecha_ingreso)], 'Lectura': [valor_ingreso]})
    df = pd.concat([df, nueva_fila]).drop_duplicates().sort_values('Fecha')
    df.to_csv(DB_FILE, index=False)
    st.sidebar.success("¡Data Blindada!")
    st.rerun()

# 4. Cálculos de Promedios Móviles (Blindado)
if not df.empty:
    # Solo calculamos si hay suficientes datos para evitar columnas vacías
    df['MA8'] = df['Lectura'].rolling(window=8, min_periods=1).mean()
    df['MA15'] = df['Lectura'].rolling(window=15, min_periods=1).mean()
    df['MA30'] = df['Lectura'].rolling(window=30, min_periods=1).mean()
    df['MA45'] = df['Lectura'].rolling(window=45, min_periods=1).mean()

# 5. Visualización Pro con Plotly
fig = go.Figure()

if not df.empty:
    # Lecturas Reales
    fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Lectura'], mode='markers', name='Lectura Diaria', 
                             marker=dict(color='#00e5ff', size=8, opacity=0.5)))

    # Líneas de Promedio (Verificando si la columna existe antes de usarla)
    colores = {'MA8': '#ffeb3b', 'MA15': '#ff9800', 'MA30': '#f44336', 'MA45': '#9c27b0'}
    for ma in colores.keys():
        if ma in df.columns:  # <--- ESTE ES EL BLINDAJE
            fig.add_trace(go.Scatter(x=df['Fecha'], y=df[ma], mode='lines', name=f'Promedio {ma[2:]} días',
                                     line=dict(color=colores[ma], width=2)))

# Meta Ideal (Línea Horizontal en 100)
fig.add_hline(y=100, line_dash="dash", line_color="green", annotation_text="Meta < 100")

fig.update_layout(template="plotly_dark", height=600, title="Evolución y Promedios Móviles")
st.plotly_chart(fig, use_container_width=True)

# 6. Tabla de Control
st.subheader("📋 Histórico de Combate")
st.dataframe(df.sort_values('Fecha', ascending=False), use_container_width=True)
