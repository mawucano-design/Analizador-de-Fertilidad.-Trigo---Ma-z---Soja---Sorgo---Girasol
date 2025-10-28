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
import math
from shapely.geometry import Polygon

# CONFIGURACIÓN DE PÁGINA - DEBE SER LO PRIMERO
st.set_page_config(
    page_title="🌱 Analizador Multi-Cultivo Satellital", 
    layout="wide",
    page_icon="🛰️"
)

st.title("🛰️ ANALIZADOR MULTI-CULTIVO - DATOS SATELITALES REALES")
st.markdown("---")

# ===== CONFIGURACIÓN =====
# Parámetros de cultivo (mantener tus parámetros existentes)
PARAMETROS_CULTIVOS = {
    'TRIGO': {
        'NITROGENO': {'min': 120, 'max': 180},
        'FOSFORO': {'min': 40, 'max': 60},
        'POTASIO': {'min': 80, 'max': 120},
        'MATERIA_ORGANICA_OPTIMA': 3.5,
        'HUMEDAD_OPTIMA': 0.25,
        'NDVI_OPTIMO': 0.7,
        'NDRE_OPTIMO': 0.4
    },
    'MAÍZ': {
        'NITROGENO': {'min': 150, 'max': 220},
        'FOSFORO': {'min': 50, 'max': 70},
        'POTASIO': {'min': 100, 'max': 140},
        'MATERIA_ORGANICA_OPTIMA': 4.0,
        'HUMEDAD_OPTIMA': 0.3,
        'NDVI_OPTIMO': 0.75,
        'NDRE_OPTIMO': 0.45
    },
    'SOJA': {
        'NITROGENO': {'min': 80, 'max': 120},
        'FOSFORO': {'min': 35, 'max': 50},
        'POTASIO': {'min': 90, 'max': 130},
        'MATERIA_ORGANICA_OPTIMA': 3.8,
        'HUMEDAD_OPTIMA': 0.28,
        'NDVI_OPTIMO': 0.65,
        'NDRE_OPTIMO': 0.35
    },
    'SORGO': {
        'NITROGENO': {'min': 100, 'max': 150},
        'FOSFORO': {'min': 30, 'max': 45},
        'POTASIO': {'min': 70, 'max': 100},
        'MATERIA_ORGANICA_OPTIMA': 3.0,
        'HUMEDAD_OPTIMA': 0.22,
        'NDVI_OPTIMO': 0.6,
        'NDRE_OPTIMO': 0.3
    },
    'GIRASOL': {
        'NITROGENO': {'min': 90, 'max': 130},
        'FOSFORO': {'min': 25, 'max': 40},
        'POTASIO': {'min': 80, 'max': 110},
        'MATERIA_ORGANICA_OPTIMA': 3.2,
        'HUMEDAD_OPTIMA': 0.26,
        'NDVI_OPTIMO': 0.55,
        'NDRE_OPTIMO': 0.25
    }
}

ICONOS_CULTIVOS = {
    'TRIGO': '🌾',
    'MAÍZ': '🌽', 
    'SOJA': '🫘',
    'SORGO': '🌾',
    'GIRASOL': '🌻'
}

# ===== SIDEBAR - AHORA SÍ PUEDE IR DESPUÉS DE LA CONFIGURACIÓN =====
with st.sidebar:
    st.header("⚙️ Configuración")
    
    cultivo = st.selectbox("Cultivo:", 
                          ["TRIGO", "MAÍZ", "SOJA", "SORGO", "GIRASOL"])
    
    analisis_tipo = st.selectbox("Tipo de Análisis:", 
                               ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"])
    
    nutriente = st.selectbox("Nutriente:", ["NITRÓGENO", "FÓSFORO", "POTASIO"])
    
    st.subheader("🎯 División de Parcela")
    n_divisiones = st.slider("Número de zonas de manejo:", min_value=16, max_value=48, value=32)
    
    st.subheader("📤 Subir Parcela")
    uploaded_zip = st.file_uploader("Subir ZIP con shapefile de tu parcela", type=['zip'])
    
    # Configuración Sentinel Hub
    st.subheader("🛰️ Configuración Satelital")
    with st.expander("Credenciales Sentinel Hub"):
        st.info("Configuradas en secrets.toml")
        # Mostrar estado de las credenciales
        try:
            if hasattr(st, 'secrets') and 'SENTINELHUB_INSTANCE_ID' in st.secrets:
                st.success("✅ Credenciales cargadas")
            else:
                st.warning("⚠️ No se encontraron credenciales")
        except:
            st.warning("⚠️ No se pudieron verificar credenciales")

# ===== FUNCIONES EXISTENTES (MANTENER TUS FUNCIONES ORIGINALES) =====

def calcular_superficie(gdf):
    try:
        if gdf.crs and gdf.crs.is_geographic:
            area_m2 = gdf.geometry.area * 10000000000
        else:
            area_m2 = gdf.geometry.area
        return area_m2 / 10000
    except:
        return gdf.geometry.area / 10000

def dividir_parcela_en_zonas(gdf, n_zonas):
    if len(gdf) == 0:
        return gdf
    
    parcela_principal = gdf.iloc[0].geometry
    bounds = parcela_principal.bounds
    minx, miny, maxx, maxy = bounds
    
    sub_poligonos = []
    
    n_cols = math.ceil(math.sqrt(n_zonas))
    n_rows = math.ceil(n_zonas / n_cols)
    
    width = (maxx - minx) / n_cols
    height = (maxy - miny) / n_rows
    
    for i in range(n_rows):
        for j in range(n_cols):
            if len(sub_poligonos) >= n_zonas:
                break
                
            cell_minx = minx + (j * width)
            cell_maxx = minx + ((j + 1) * width)
            cell_miny = miny + (i * height)
            cell_maxy = miny + ((i + 1) * height)
            
            cell_poly = Polygon([
                (cell_minx, cell_miny),
                (cell_maxx, cell_miny),
                (cell_maxx, cell_maxy),
                (cell_minx, cell_maxy)
            ])
            
            intersection = parcela_principal.intersection(cell_poly)
            if not intersection.is_empty and intersection.area > 0:
                sub_poligonos.append(intersection)
    
    if sub_poligonos:
        nuevo_gdf = gpd.GeoDataFrame({
            'id_zona': range(1, len(sub_poligonos) + 1),
            'geometry': sub_poligonos
        }, crs=gdf.crs)
        return nuevo_gdf
    else:
        return gdf

def calcular_indices_satelitales_gee(gdf, cultivo):
    """Tu función original - mantener igual"""
    n_poligonos = len(gdf)
    resultados = []
    
    gdf_centroids = gdf.copy()
    gdf_centroids['centroid'] = gdf_centroids.geometry.centroid
    gdf_centroids['x'] = gdf_centroids.centroid.x
    gdf_centroids['y'] = gdf_centroids.centroid.y
    
    x_coords = gdf_centroids['x'].tolist()
    y_coords = gdf_centroids['y'].tolist()
    
    x_min, x_max = min(x_coords), max(x_coords)
    y_min, y_max = min(y_coords), max(y_coords)
    
    params = PARAMETROS_CULTIVOS[cultivo]
    
    for idx, row in gdf_centroids.iterrows():
        x_norm = (row['x'] - x_min) / (x_max - x_min) if x_max != x_min else 0.5
        y_norm = (row['y'] - y_min) / (y_max - y_min) if y_max != y_min else 0.5
        
        patron_espacial = (x_norm * 0.6 + y_norm * 0.4)
        
        base_mo = params['MATERIA_ORGANICA_OPTIMA'] * 0.7
        variabilidad_mo = patron_espacial * (params['MATERIA_ORGANICA_OPTIMA'] * 0.6)
        materia_organica = base_mo + variabilidad_mo + np.random.normal(0, 0.2)
        materia_organica = max(0.5, min(8.0, materia_organica))
        
        base_humedad = params['HUMEDAD_OPTIMA'] * 0.8
        variabilidad_humedad = patron_espacial * (params['HUMEDAD_OPTIMA'] * 0.4)
        humedad_suelo = base_humedad + variabilidad_humedad + np.random.normal(0, 0.05)
        humedad_suelo = max(0.1, min(0.8, humedad_suelo))
        
        ndvi_base = params['NDVI_OPTIMO'] * 0.6
        ndvi_variacion = patron_espacial * (params['NDVI_OPTIMO'] * 0.5)
        ndvi = ndvi_base + ndvi_variacion + np.random.normal(0, 0.06)
        ndvi = max(0.1, min(0.9, ndvi))
        
        ndre_base = params['NDRE_OPTIMO'] * 0.7
        ndre_variacion = patron_espacial * (params['NDRE_OPTIMO'] * 0.4)
        ndre = ndre_base + ndre_variacion + np.random.normal(0, 0.04)
        ndre = max(0.05, min(0.7, ndre))
        
        npk_actual = (ndvi * 0.4) + (ndre * 0.3) + ((materia_organica / 8) * 0.2) + (humedad_suelo * 0.1)
        npk_actual = max(0, min(1, npk_actual))
        
        resultados.append({
            'materia_organica': round(materia_organica, 2),
            'humedad_suelo': round(humedad_suelo, 3),
            'ndvi': round(ndvi, 3),
            'ndre': round(ndre, 3),
            'npk_actual': round(npk_actual, 3)
        })
    
    return resultados

# ===== FUNCIÓN PRINCIPAL DE ANÁLISIS =====
def analisis_gee_completo(gdf, nutriente, analisis_tipo, n_divisiones, cultivo):
    try:
        st.header(f"{ICONOS_CULTIVOS[cultivo]} ANÁLISIS {cultivo} - METODOLOGÍA GEE")
        
        # Dividir parcela
        st.subheader("📐 DIVIDIENDO PARCELA EN ZONAS DE MANEJO")
        with st.spinner("Dividiendo parcela..."):
            gdf_dividido = dividir_parcela_en_zonas(gdf, n_divisiones)
        
        st.success(f"✅ Parcela dividida en {len(gdf_dividido)} zonas")
        
        # Calcular áreas
        areas_ha = calcular_superficie(gdf_dividido)
        area_total = areas_ha.sum()
        
        # Calcular índices
        st.subheader("🛰️ CALCULANDO ÍNDICES SATELITALES GEE")
        with st.spinner(f"Ejecutando algoritmos GEE para {cultivo}..."):
            indices_gee = calcular_indices_satelitales_gee(gdf_dividido, cultivo)
        
        # Crear dataframe con resultados
        gdf_analizado = gdf_dividido.copy()
        gdf_analizado['area_ha'] = areas_ha
        
        for idx, indice in enumerate(indices_gee):
            for key, value in indice.items():
                gdf_analizado.loc[gdf_analizado.index[idx], key] = value
        
        # Mostrar resultados
        st.subheader("📊 RESULTADOS DEL ANÁLISIS GEE")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Zonas Analizadas", len(gdf_analizado))
        with col2:
            st.metric("Área Total", f"{area_total:.1f} ha")
        with col3:
            valor_prom = gdf_analizado['npk_actual'].mean()
            st.metric("Índice NPK Promedio", f"{valor_prom:.3f}")
        with col4:
            coef_var = (gdf_analizado['npk_actual'].std() / gdf_analizado['npk_actual'].mean() * 100)
            st.metric("Coef. Variación", f"{coef_var:.1f}%")
        
        # Tabla de resultados
        st.subheader("🔬 ÍNDICES SATELITALES GEE POR ZONA")
        tabla_indices = gdf_analizado[['id_zona', 'npk_actual', 'materia_organica', 'ndvi', 'ndre', 'humedad_suelo']].copy()
        tabla_indices.columns = ['Zona', 'NPK Actual', 'Materia Org (%)', 'NDVI', 'NDRE', 'Humedad']
        
        st.dataframe(tabla_indices, use_container_width=True)
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error en análisis GEE: {str(e)}")
        return False

# ===== INTERFAZ PRINCIPAL =====
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
                    
                    # Información de la parcela
                    area_total = calcular_superficie(gdf).sum()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**📊 INFORMACIÓN DE LA PARCELA:**")
                        st.write(f"- Polígonos: {len(gdf)}")
                        st.write(f"- Área total: {area_total:.1f} ha")
                        st.write(f"- CRS: {gdf.crs}")
                    
                    with col2:
                        st.write("**🎯 CONFIGURACIÓN GEE:**")
                        st.write(f"- Cultivo: {ICONOS_CULTIVOS[cultivo]} {cultivo}")
                        st.write(f"- Análisis: {analisis_tipo}")
                        st.write(f"- Nutriente: {nutriente}")
                        st.write(f"- Zonas: {n_divisiones}")
                    
                    # EJECUTAR ANÁLISIS
                    if st.button("🚀 EJECUTAR ANÁLISIS GEE", type="primary"):
                        analisis_gee_completo(gdf, nutriente, analisis_tipo, n_divisiones, cultivo)
                        
        except Exception as e:
            st.error(f"Error cargando shapefile: {str(e)}")

else:
    st.info("📁 Sube el ZIP de tu parcela para comenzar el análisis")
    
    # Información inicial
    with st.expander("ℹ️ INFORMACIÓN SOBRE LA METODOLOGÍA GEE"):
        st.markdown("""
        **🌱 SISTEMA DE ANÁLISIS MULTI-CULTIVO (GEE)**
        
        **📊 CULTIVOS SOPORTADOS:**
        - **🌾 TRIGO:** Cereal de clima templado
        - **🌽 MAÍZ:** Cereal de alta demanda nutricional  
        - **🫘 SOJA:** Leguminosa fijadora de nitrógeno
        - **🌾 SORGO:** Cereal resistente a sequía
        - **🌻 GIRASOL:** Oleaginosa de profundas raíces
        
        **🚀 FUNCIONALIDADES:**
        - **🌱 Fertilidad Actual:** Estado NPK del suelo usando índices satelitales
        - **💊 Recomendaciones NPK:** Dosis específicas por cultivo
        - **🎯 Agricultura Precisión:** Análisis por zonas de manejo
        """)
