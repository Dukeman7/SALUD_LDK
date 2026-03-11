# --- AJUSTE DINÁMICO DE RADAR EN SIDEBAR ---
with st.sidebar:
    st.header("🔭 Ventana de Observación")
    
    hoy = datetime.now()
    # Tu solicitud: 20 días atrás y 20 días adelante
    inicio_radar = hoy - timedelta(days=20)
    fin_radar = hoy + timedelta(days=20)
    
    fecha_inicio = st.date_input("Ver desde:", value=inicio_radar)
    fecha_fin = st.date_input("Ver hasta:", value=fin_radar)

    st.divider()
    st.header("📝 Registro")
    with st.form("reg_v4", clear_on_submit=True):
        f_in = st.date_input("Fecha", hoy)
        g_in = st.number_input("Glucosa", value=110)
        # El peso es opcional: si no lo cambias, enviamos 0 o None
        p_in = st.text_input("Peso (kg) - Dejar vacío si no toca hoy", value="") 
        
        if st.form_submit_button("📡 TRANSMITIR"):
            try:
                # Si el peso está vacío, mandamos 0 para que el script lo ignore
                p_val = float(p_in.replace(',', '.')) if p_in.strip() != "" else 0
                payload = {
                    "tipo": "SALUD", 
                    "fecha": f_in.strftime('%Y-%m-%d'), 
                    "glucosa": g_in, 
                    "peso": p_val
                }
                r = requests.post(URL_ESCRITURA, json=payload, timeout=15)
                if r.status_code == 200:
                    st.success("✅ Recibido en la Nube")
                    st.rerun()
                else:
                    st.error(f"Error 500: Revisa si la Hoja de Google está abierta o bloqueada.")
            except Exception as e:
                st.error(f"Error de formato: {e}")
