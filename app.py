import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
import tempfile
import os
import zipfile
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io

from satellite_processor import SatelliteProcessor
import config

# Configuración de página
st.set_page_config(
    page_title="🌱 Analizador Multi-Cultivo Satellital", 
    layout="wide",
    page_icon="🛰️"
)

st.title("🛰️ ANALIZADOR MULTI-CULTIVO - DATOS SATELITALES REALES")
st.markdown("---")

# Sidebar mejorado
with st.sidebar:
    st.header("⚙️ Configuración Satellital")
    
    cultivo = st.selectbox("Cultivo:", 
                          ["TRIGO", "MAÍZ", "SOJA", "SORGO", "GIRASOL"])
    
    analisis_tipo = st.selectbox("Tipo de Análisis:", 
                               ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK", "ANÁLISIS MULTITEMPORAL"])
    
    nutriente = st.selectbox("Nutriente:", ["NITRÓGENO", "FÓSFORO", "POTASIO"])
    
    # Selector de índices satelitales
    st.subheader("📊 Índices Satelitales")
    indices_seleccionados = st.multiselect(
        "Seleccionar índices:",
        ["NDVI", "NDRE", "GNDVI", "OSAVI", "MCARI"],
        default=["NDVI", "NDRE"]
    )
    
    # Selector de fecha
    st.subheader("📅 Rango Temporal")
    fecha_fin = st.date_input("Fecha fin", datetime.now())
    fecha_inicio = st.date_input("Fecha inicio", datetime.now() - timedelta(days=30))
    
    st.subheader("🎯 División de Parcela")
    n_divisiones = st.slider("Número de zonas de manejo:", min_value=16, max_value=48, value=32)
    
    st.subheader("📤 Subir Parcela")
    uploaded_zip = st.file_uploader("Subir ZIP con shapefile de tu parcela", type=['zip'])

    # Configuración APIs
    st.subheader("🔑 Configuración APIs")
    with st.expander("Configurar credenciales satelitales"):
        sentinel_instance = st.text_input("Sentinel Hub Instance ID", type="password")
        sentinel_client = st.text_input("Sentinel Hub Client ID", type="password")
        sentinel_secret = st.text_input("Sentinel Hub Client Secret", type="password")

# Inicializar procesador satelital
@st.cache_resource
def get_satellite_processor():
    return SatelliteProcessor(config)

# Función principal mejorada con datos reales
def analisis_con_imagenes_reales(gdf, cultivo, indices, fecha_inicio, fecha_fin):
    """Ejecutar análisis con imágenes satelitales reales"""
    
    st.header(f"🛰️ PROCESANDO IMÁGENES SATELITALES - {cultivo}")
    
    with st.spinner("Descargando datos de Sentinel-2..."):
        processor = get_satellite_processor()
        
        # Descargar datos satelitales
        satellite_data = processor.download_sentinel2_data(
            gdf, 
            fecha_inicio.strftime('%Y-%m-%d'), 
            fecha_fin.strftime('%Y-%m-%d'),
            indices=[idx.lower() for idx in indices]
        )
        
        if satellite_data is not None:
            st.success("✅ Datos satelitales descargados exitosamente")
            
            # Calcular estadísticas zonales
            with st.spinner("Calculando estadísticas por zona..."):
                statistics = processor.calculate_zonal_statistics(gdf, satellite_data)
                
            # Integrar con análisis existente
            resultados = integrar_datos_reales_simulados(statistics, cultivo)
            
            return resultados, satellite_data
        else:
            st.error("❌ No se pudieron descargar datos satelitales")
            st.info("🔑 Verifica tus credenciales de Sentinel Hub o usa datos simulados")
            
            # Fallback a datos simulados
            return generar_datos_simulados(gdf, cultivo), None

def integrar_datos_reales_simulados(statistics_real, cultivo):
    """Integrar datos satelitales reales con parámetros de cultivo"""
    # Aquí combinas los datos reales con tu lógica existente
    resultados = []
    
    for stats in statistics_real:
        # Usar NDVI real como base
        ndvi_real = stats['mean']
        
        # Ajustar otros parámetros basados en NDVI real
        resultado = {
            'ndvi_real': ndvi_real,
            'npk_actual_ajustado': ajustar_npk_por_ndvi(ndvi_real, cultivo),
            'materia_organica_estimada': estimar_materia_organica(ndvi_real),
            'recomendacion_nitrogeno': calcular_n_recomendado(ndvi_real, cultivo)
        }
        resultados.append(resultado)
    
    return resultados

# ... (mantener tus funciones existentes pero adaptarlas)

# INTERFAZ PRINCIPAL MEJORADA
if uploaded_zip:
    with st.spinner("Cargando parcela..."):
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
                    zip_ref.extractall(tmp_dir)
                
                shp_files = [f for f in os.listdir(tmp_dir) if f.endswith('.shp')]
                if shp_files:
                    shp_path = os.path.join(tmp_dir, shp_files[0])
                    gdf = gpd.read_file(shp_path)
                    
                    st.success(f"✅ **Parcela cargada:** {len(gdf)} polígono(s)")
                    
                    # Mostrar información de la parcela
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.info("**📊 PARCELA**")
                        st.write(f"- Polígonos: {len(gdf)}")
                        st.write(f"- Área: {calcular_superficie(gdf).sum():.1f} ha")
                    
                    with col2:
                        st.info("**🛰️ SATELITAL**")
                        st.write(f"- Índices: {', '.join(indices_seleccionados)}")
                        st.write(f"- Período: {fecha_inicio} a {fecha_fin}")
                    
                    with col3:
                        st.info("**🌱 CULTIVO**")
                        st.write(f"- Cultivo: {cultivo}")
                        st.write(f"- Análisis: {analisis_tipo}")
                    
                    # Botón de análisis mejorado
                    if st.button("🚀 EJECUTAR ANÁLISIS CON DATOS SATELITALES", type="primary"):
                        resultados, imagenes = analisis_con_imagenes_reales(
                            gdf, cultivo, indices_seleccionados, fecha_inicio, fecha_fin
                        )
                        
                        # Continuar con tu análisis existente pero con datos reales
                        if resultados:
                            analisis_gee_completo_mejorado(
                                gdf, nutriente, analisis_tipo, n_divisiones, 
                                cultivo, resultados, imagenes
                            )
                        
        except Exception as e:
            st.error(f"Error cargando shapefile: {str(e)}")

else:
    # Pantalla de bienvenida mejorada
    st.info("📁 Sube el ZIP de tu parcela para comenzar el análisis satelital")
    
    with st.expander("🚀 GUÍA RÁPIDA - ANÁLISIS SATELITAL"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **📋 REQUISITOS:**
            1. Shapefile de tu parcela en ZIP
            2. Credenciales de Sentinel Hub
            3. Conexión a internet
            
            **🛰️ DATOS DISPONIBLES:**
            - **Sentinel-2:** 10m resolución, 5 días revisita
            - **Landsat-8:** 30m resolución, 16 días revisita
            - **Índices:** NDVI, NDRE, GNDVI, OSAVI, MCARI
            """)
        
        with col2:
            st.markdown("""
            **🌱 CULTIVOS SOPORTADOS:**
            - Trigo, Maíz, Soja, Sorgo, Girasol
            
            **📊 ANÁLISIS:**
            - Fertilidad actual con datos reales
            - Recomendaciones NPK precisas
            - Análisis multitemporal
            - Mapas de prescripción
            """)
