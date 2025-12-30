import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time

# ============================================
# CONFIGURACIÓN INICIAL (DEBE SER LA PRIMERA LÍNEA)
# ============================================
st.set_page_config(
    page_title="AgTech - Fertilidad Multicultivos",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# INICIALIZACIÓN DE SESSION STATE
# ============================================
def init_session_state():
    """Inicializa todas las variables de estado de la sesión"""
    default_states = {
        # Estado de la aplicación
        'app_initialized': False,
        'current_step': 0,
        'data_loaded': False,
        'calculations_done': False,
        
        # Datos
        'df_raw': None,
        'df_processed': None,
        'df_results': None,
        
        # Parámetros y configuraciones
        'selected_crop': '',
        'selected_soil': '',
        'fertilizer_params': {},
        'calculation_params': {},
        
        # UI State
        'show_results': False,
        'show_export': False,
        'sidebar_collapsed': False,
        
        # Control de renderizado
        'last_rerun': time.time(),
        'render_count': 0
    }
    
    for key, value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ============================================
# FUNCIONES DE UTILIDAD CON MANEJO SEGURO
# ============================================
def safe_rerun():
    """Ejecuta un rerun seguro con protección contra loops infinitos"""
    current_time = time.time()
    if current_time - st.session_state.last_rerun > 1:  # Mínimo 1 segundo entre reruns
        st.session_state.last_rerun = current_time
        st.rerun()

def safe_empty_container(container_key):
    """Maneja contenedores vacíos de forma segura"""
    if container_key not in st.session_state:
        st.session_state[container_key] = st.empty()
    return st.session_state[container_key]

# ============================================
# COMPONENTES DE UI CON CLAVES ESTABLES
# ============================================
def create_navigation():
    """Crea navegación con claves únicas y estables"""
    with st.sidebar:
        st.title("🌱 Navegación")
        
        # Usar índices numéricos como claves para estabilidad
        nav_options = {
            "🏠 Inicio": 0,
            "📊 Cargar Datos": 1,
            "⚙️ Configurar": 2,
            "🧮 Calcular": 3,
            "📈 Resultados": 4,
            "💾 Exportar": 5
        }
        
        # Crear botones de navegación
        for option, idx in nav_options.items():
            if st.button(option, key=f"nav_btn_{idx}", use_container_width=True):
                st.session_state.current_step = idx
                safe_rerun()
        
        st.divider()
        
        # Botones de acción con claves únicas
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Reiniciar", key="btn_reset", type="secondary"):
                reset_application()
        
        with col2:
            if st.button("ℹ️ Ayuda", key="btn_help"):
                st.session_state.show_help = not st.session_state.get('show_help', False)
                safe_rerun()

def create_data_upload_section():
    """Sección para carga de datos con manejo seguro"""
    with st.container():
        st.header("📊 Carga de Datos")
        
        # Usar un contenedor específico para el uploader
        upload_container = safe_empty_container("upload_container")
        
        with upload_container:
            uploaded_file = st.file_uploader(
                "Selecciona archivo CSV o Excel",
                type=['csv', 'xlsx', 'xls'],
                key="file_uploader_unique"
            )
            
            if uploaded_file is not None:
                try:
                    # Leer archivo según extensión
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    # Validar datos
                    if not df.empty:
                        st.session_state.df_raw = df
                        st.session_state.data_loaded = True
                        st.success(f"✅ Datos cargados: {len(df)} registros, {len(df.columns)} columnas")
                        
                        # Mostrar vista previa
                        with st.expander("Vista previa de datos"):
                            st.dataframe(df.head(), use_container_width=True)
                    else:
                        st.error("El archivo está vacío")
                        
                except Exception as e:
                    st.error(f"Error al cargar archivo: {str(e)}")

def create_parameters_section():
    """Sección de parámetros con estado persistente"""
    with st.container():
        st.header("⚙️ Configuración de Parámetros")
        
        # Dividir en columnas para mejor organización
        col1, col2 = st.columns(2)
        
        with col1:
            # Cultivos con clave estable
            crops = ["Maíz", "Soja", "Trigo", "Girasol", "Sorgo"]
            st.session_state.selected_crop = st.selectbox(
                "🌾 Cultivo",
                crops,
                index=crops.index(st.session_state.selected_crop) if st.session_state.selected_crop in crops else 0,
                key="crop_select_fixed"
            )
            
            # Tipo de suelo
            soil_types = ["Arcilloso", "Franco", "Arenoso"]
            st.session_state.selected_soil = st.selectbox(
                "🌍 Tipo de Suelo",
                soil_types,
                index=soil_types.index(st.session_state.selected_soil) if st.session_state.selected_soil in soil_types else 0,
                key="soil_select_fixed"
            )
        
        with col2:
            # Parámetros numéricos con valores por defecto
            if 'nitrogen' not in st.session_state.fertilizer_params:
                st.session_state.fertilizer_params = {
                    'nitrogen': 50.0,
                    'phosphorus': 30.0,
                    'potassium': 20.0,
                    'organic_matter': 2.5
                }
            
            st.session_state.fertilizer_params['nitrogen'] = st.number_input(
                "Nitrógeno (kg/ha)",
                min_value=0.0,
                max_value=200.0,
                value=float(st.session_state.fertilizer_params['nitrogen']),
                step=1.0,
                key="nitrogen_input"
            )
            
            st.session_state.fertilizer_params['phosphorus'] = st.number_input(
                "Fósforo (kg/ha)",
                min_value=0.0,
                max_value=150.0,
                value=float(st.session_state.fertilizer_params['phosphorus']),
                step=1.0,
                key="phosphorus_input"
            )

def create_calculation_section():
    """Sección de cálculos con protección contra errores"""
    with st.container():
        st.header("🧮 Cálculos de Fertilidad")
        
        # Verificar que hay datos cargados
        if not st.session_state.data_loaded:
            st.warning("Primero carga los datos en la sección 'Cargar Datos'")
            return
        
        # Botón de cálculo con protección
        calculate_container = safe_empty_container("calculate_container")
        
        with calculate_container:
            if st.button("🚀 Ejecutar Cálculos", key="btn_calculate", type="primary", use_container_width=True):
                with st.spinner("Calculando..."):
                    try:
                        # Simular cálculo
                        time.sleep(1)  # Para demostración
                        
                        # Generar resultados de ejemplo
                        results = {
                            'Recomendación': 'Aplicar fertilizante balanceado',
                            'Dosis N': f"{st.session_state.fertilizer_params['nitrogen']} kg/ha",
                            'Dosis P': f"{st.session_state.fertilizer_params['phosphorus']} kg/ha",
                            'Costo estimado': '$ 450/ha',
                            'Rendimiento esperado': '85-95 qq/ha'
                        }
                        
                        st.session_state.df_results = pd.DataFrame([results])
                        st.session_state.calculations_done = True
                        st.session_state.show_results = True
                        
                        st.success("✅ Cálculos completados")
                        safe_rerun()
                        
                    except Exception as e:
                        st.error(f"Error en cálculo: {str(e)}")

def create_results_section():
    """Muestra resultados con manejo seguro de actualizaciones"""
    if not st.session_state.get('show_results', False):
        return
    
    with st.container():
        st.header("📈 Resultados")
        
        # Contenedor para resultados
        results_container = safe_empty_container("results_container")
        
        with results_container:
            if st.session_state.df_results is not None:
                # Mostrar tabla de resultados
                st.dataframe(
                    st.session_state.df_results,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Mostrar métricas
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Cultivo", st.session_state.selected_crop)
                with col2:
                    st.metric("Suelo", st.session_state.selected_soil)
                with col3:
                    st.metric("Estado", "Completado")
                
                # Gráfico de ejemplo
                try:
                    chart_data = pd.DataFrame({
                        'Nutriente': ['N', 'P', 'K', 'OM'],
                        'Valor': [
                            st.session_state.fertilizer_params['nitrogen'],
                            st.session_state.fertilizer_params['phosphorus'],
                            st.session_state.fertilizer_params.get('potassium', 20),
                            st.session_state.fertilizer_params.get('organic_matter', 2.5)
                        ]
                    })
                    
                    st.bar_chart(chart_data.set_index('Nutriente'))
                except:
                    pass  # Si falla el gráfico, continuar sin él

def create_export_section():
    """Sección de exportación con manejo seguro de archivos"""
    if not st.session_state.get('calculations_done', False):
        return
    
    with st.container():
        st.header("💾 Exportar Resultados")
        
        export_container = safe_empty_container("export_container")
        
        with export_container:
            # Formato de exportación
            export_format = st.radio(
                "Formato de exportación",
                ["CSV", "Excel", "JSON"],
                horizontal=True,
                key="export_format_radio"
            )
            
            # Botón de exportación
            if st.session_state.df_results is not None:
                if export_format == "CSV":
                    csv = st.session_state.df_results.to_csv(index=False)
                    st.download_button(
                        label="📥 Descargar CSV",
                        data=csv,
                        file_name=f"resultados_fertilidad_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key="download_csv_unique"
                    )
                elif export_format == "Excel":
                    # Para Excel necesitamos un buffer
                    import io
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        st.session_state.df_results.to_excel(writer, index=False, sheet_name='Resultados')
                    
                    st.download_button(
                        label="📥 Descargar Excel",
                        data=buffer.getvalue(),
                        file_name=f"resultados_fertilidad_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_excel_unique"
                    )

# ============================================
# FUNCIONES DE CONTROL DE LA APLICACIÓN
# ============================================
def reset_application():
    """Reinicia la aplicación de forma segura"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session_state()
    safe_rerun()

def render_current_step():
    """Renderiza el paso actual de forma segura"""
    steps = [
        render_home,           # Paso 0
        create_data_upload_section,  # Paso 1
        create_parameters_section,   # Paso 2
        create_calculation_section,  # Paso 3
        create_results_section,      # Paso 4
        create_export_section        # Paso 5
    ]
    
    if 0 <= st.session_state.current_step < len(steps):
        steps[st.session_state.current_step]()
    else:
        st.session_state.current_step = 0
        safe_rerun()

def render_home():
    """Página de inicio"""
    with st.container():
        st.title("🌱 AgTech - Fertilidad Multicultivos")
        st.markdown("---")
        
        st.markdown("""
        ### 🚀 Bienvenido al Sistema de Análisis de Fertilidad
        
        Esta aplicación te permite:
        
        - 📊 **Cargar y analizar** datos de suelos y cultivos
        - ⚙️ **Configurar parámetros** específicos para cada cultivo
        - 🧮 **Calcular recomendaciones** de fertilización
        - 📈 **Visualizar resultados** en tiempo real
        - 💾 **Exportar reportes** en múltiples formatos
        
        ### 📋 Pasos recomendados:
        1. Navega a **Cargar Datos** para importar tu información
        2. Configura los parámetros en **Configurar**
        3. Ejecuta los cálculos en **Calcular**
        4. Revisa los resultados en **Resultados**
        5. Exporta tus datos en **Exportar**
        """)
        
        # Indicador de estado
        with st.expander("Estado actual de la aplicación", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Datos cargados", "✅" if st.session_state.data_loaded else "❌")
            with col2:
                st.metric("Cálculos realizados", "✅" if st.session_state.calculations_done else "❌")
            with col3:
                st.metric("Paso actual", st.session_state.current_step)

# ============================================
# MAIN APP - ESTRUCTURA PRINCIPAL
# ============================================
def main():
    """Función principal de la aplicación"""
    
    # Inicializar estado
    init_session_state()
    
    # Incrementar contador de renderizado
    st.session_state.render_count = st.session_state.get('render_count', 0) + 1
    
    # Marcar aplicación como inicializada
    if not st.session_state.app_initialized:
        st.session_state.app_initialized = True
    
    # Sidebar con navegación
    create_navigation()
    
    # Contenido principal
    main_container = st.container()
    
    with main_container:
        try:
            render_current_step()
        except Exception as e:
            st.error(f"Error al renderizar: {str(e)}")
            if st.button("Reintentar", key="retry_button"):
                safe_rerun()
    
    # Footer
    st.markdown("---")
    st.caption(f"AgTech Fertilidad v1.0 • Renderizado: {st.session_state.render_count} • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ============================================
# PUNTO DE ENTRADA PROTEGIDO
# ============================================
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Página de error amigable
        st.error("⚠️ Ocurrió un error inesperado")
        st.exception(e)
        
        if st.button("🔄 Reiniciar Aplicación", key="error_reset"):
            reset_application()
