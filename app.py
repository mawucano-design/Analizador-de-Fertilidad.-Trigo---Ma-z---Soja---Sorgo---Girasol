# En la sección de configuración del sidebar, quita los inputs de credenciales:
with st.sidebar:
    st.header("⚙️ Configuración Satellital")
    
    cultivo = st.selectbox("Cultivo:", ["TRIGO", "MAÍZ", "SOJA", "SORGO", "GIRASOL"])
    
    analisis_tipo = st.selectbox("Tipo de Análisis:", 
                               ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK", "ANÁLISIS MULTITEMPORAL"])
    
    # ... resto de la configuración
    
    # Mostrar estado de las credenciales
    with st.expander("🔑 Estado de Credenciales Satelitales"):
        if SENTINELHUB_CONFIG:
            st.success("✅ Sentinel Hub: Configurado")
            st.code(f"Instance ID: {SENTINELHUB_CONFIG['instance_id'][:10]}...")
        else:
            st.error("❌ Sentinel Hub: No configurado")
            st.info("Agrega tus credenciales en .streamlit/secrets.toml")

# Función para verificar disponibilidad de datos
def check_satellite_availability():
    """Verificar si hay datos satelitales disponibles"""
    if not SENTINELHUB_CONFIG:
        st.warning("""
        ⚠️ **Modo Simulación Activado**
        
        Para usar datos satelitales reales:
        1. Agrega tus credenciales de Sentinel Hub en `.streamlit/secrets.toml`
        2. Reinicia la aplicación
        
        **Credenciales necesarias:**
        ```toml
        SENTINELHUB_INSTANCE_ID = "tu_instance_id"
        SENTINELHUB_CLIENT_ID = "tu_client_id"  
        SENTINELHUB_CLIENT_SECRET = "tu_client_secret"
        ```
        """)
        return False
    return True

# En el botón de análisis:
if st.button("🚀 EJECUTAR ANÁLISIS CON DATOS SATELITALES", type="primary"):
    if check_satellite_availability():
        # Proceder con análisis satelital real
        resultados, imagenes = analisis_con_imagenes_reales(
            gdf, cultivo, indices_seleccionados, fecha_inicio, fecha_fin
        )
    else:
        # Usar datos simulados como fallback
        st.info("🔄 Usando datos simulados (modo demo)")
        resultados = generar_datos_simulados(gdf, cultivo)
        # Continuar con análisis simulado
