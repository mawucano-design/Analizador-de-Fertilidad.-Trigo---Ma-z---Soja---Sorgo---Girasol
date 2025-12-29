import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
import tempfile
import os
import zipfile
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import io
from shapely.geometry import Polygon, LineString
import math
import warnings
import xml.etree.ElementTree as ET
import json
from io import BytesIO
from fpdf import FPDF
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
warnings.filterwarnings('ignore')

# CONFIGURACIÓN DE PÁGINA - DEBE SER LO PRIMERO
st.set_page_config(
    page_title="🌱 Analizador Multi-Cultivo Satellital PRO",
    layout="wide",
    page_icon="🛰️",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados SIMPLIFICADOS
st.markdown("""
<style>
    /* Solo estilos que no interfieran con Streamlit */
    .custom-metric {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1E88E5;
        margin-bottom: 1rem;
    }
    .custom-info {
        background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #2196F3;
        margin: 1rem 0;
    }
    .custom-success {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        margin: 1rem 0;
    }
    .custom-warning {
        background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #FF9800;
        margin: 1rem 0;
    }
    .sidebar-custom-header {
        font-size: 1.2rem;
        color: #1E88E5;
        margin-top: 1rem;
        font-weight: 600;
    }
    .file-upload-custom {
        border: 2px dashed #1E88E5;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        background-color: #F5F9FF;
        margin: 1rem 0;
    }
    .satellite-info-custom {
        background: linear-gradient(135deg, #F3E5F5 0%, #E1BEE7 100%);
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #9C27B0;
    }
</style>
""", unsafe_allow_html=True)

# ===== TÍTULO PRINCIPAL =====
st.markdown('<h1 style="text-align: center; color: #1E88E5; font-size: 2.5rem; margin-bottom: 0.5rem;">🛰️ ANALIZADOR MULTI-CULTIVO PRO</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666; margin-bottom: 2rem;">Análisis satelital avanzado para agricultura de precisión</p>', unsafe_allow_html=True)
st.markdown("---")

# ===== CONFIGURACIÓN DE SATÉLITES DISPONIBLES =====
SATELITES_DISPONIBLES = {
    'SENTINEL-2': {
        'nombre': 'Sentinel-2',
        'resolucion': '10m',
        'revisita': '5 días',
        'bandas': ['B2', 'B3', 'B4', 'B5', 'B8', 'B11'],
        'indices': ['NDVI', 'NDRE', 'GNDVI', 'OSAVI', 'MCARI'],
        'icono': '🛰️',
        'color': '#4CAF50'
    },
    'LANDSAT-8': {
        'nombre': 'Landsat 8',
        'resolucion': '30m',
        'revisita': '16 días',
        'bandas': ['B2', 'B3', 'B4', 'B5', 'B6', 'B7'],
        'indices': ['NDVI', 'NDWI', 'EVI', 'SAVI', 'MSAVI'],
        'icono': '🛰️',
        'color': '#2196F3'
    },
    'DATOS_SIMULADOS': {
        'nombre': 'Datos Simulados',
        'resolucion': '10m',
        'revisita': '5 días',
        'bandas': ['B2', 'B3', 'B4', 'B5', 'B8'],
        'indices': ['NDVI', 'NDRE', 'GNDVI'],
        'icono': '🔬',
        'color': '#9C27B0'
    }
}

# ===== CONFIGURACIÓN =====
PARAMETROS_CULTIVOS = {
    'TRIGO': {
        'NITROGENO': {'min': 120, 'max': 180},
        'FOSFORO': {'min': 40, 'max': 60},
        'POTASIO': {'min': 80, 'max': 120},
        'MATERIA_ORGANICA_OPTIMA': 3.5,
        'HUMEDAD_OPTIMA': 0.25,
        'NDVI_OPTIMO': 0.7,
        'NDRE_OPTIMO': 0.4,
        'color': '#FFD700',
        'icono': '🌾'
    },
    'MAÍZ': {
        'NITROGENO': {'min': 150, 'max': 220},
        'FOSFORO': {'min': 50, 'max': 70},
        'POTASIO': {'min': 100, 'max': 140},
        'MATERIA_ORGANICA_OPTIMA': 4.0,
        'HUMEDAD_OPTIMA': 0.3,
        'NDVI_OPTIMO': 0.75,
        'NDRE_OPTIMO': 0.45,
        'color': '#FFA500',
        'icono': '🌽'
    },
    'SOJA': {
        'NITROGENO': {'min': 80, 'max': 120},
        'FOSFORO': {'min': 35, 'max': 50},
        'POTASIO': {'min': 90, 'max': 130},
        'MATERIA_ORGANICA_OPTIMA': 3.8,
        'HUMEDAD_OPTIMA': 0.28,
        'NDVI_OPTIMO': 0.65,
        'NDRE_OPTIMO': 0.35,
        'color': '#8B4513',
        'icono': '🫘'
    },
    'SORGO': {
        'NITROGENO': {'min': 100, 'max': 150},
        'FOSFORO': {'min': 30, 'max': 45},
        'POTASIO': {'min': 70, 'max': 100},
        'MATERIA_ORGANICA_OPTIMA': 3.0,
        'HUMEDAD_OPTIMA': 0.22,
        'NDVI_OPTIMO': 0.6,
        'NDRE_OPTIMO': 0.3,
        'color': '#D2691E',
        'icono': '🌾'
    },
    'GIRASOL': {
        'NITROGENO': {'min': 90, 'max': 130},
        'FOSFORO': {'min': 25, 'max': 40},
        'POTASIO': {'min': 80, 'max': 110},
        'MATERIA_ORGANICA_OPTIMA': 3.2,
        'HUMEDAD_OPTIMA': 0.26,
        'NDVI_OPTIMO': 0.55,
        'NDRE_OPTIMO': 0.25,
        'color': '#FFD700',
        'icono': '🌻'
    }
}

# PARÁMETROS DE TEXTURA DEL SUELO
TEXTURA_SUELO_OPTIMA = {
    'TRIGO': {
        'textura_optima': 'Franco Arcilloso',
        'arena_optima': 40,
        'limo_optima': 30,
        'arcilla_optima': 30
    },
    'MAÍZ': {
        'textura_optima': 'Franco',
        'arena_optima': 45,
        'limo_optima': 35,
        'arcilla_optima': 20
    },
    'SOJA': {
        'textura_optima': 'Franco',
        'arena_optima': 45,
        'limo_optima': 35,
        'arcilla_optima': 20
    },
    'SORGO': {
        'textura_optima': 'Franco',
        'arena_optima': 45,
        'limo_optima': 35,
        'arcilla_optima': 20
    },
    'GIRASOL': {
        'textura_optima': 'Franco Arenoso',
        'arena_optima': 55,
        'limo_optima': 25,
        'arcilla_optima': 20
    }
}

# CLASIFICACIÓN DE PENDIENTES
CLASIFICACION_PENDIENTES = {
    'PLANA (0-2%)': {'min': 0, 'max': 2, 'color': '#4daf4a', 'factor_erosivo': 0.1},
    'SUAVE (2-5%)': {'min': 2, 'max': 5, 'color': '#a6d96a', 'factor_erosivo': 0.3},
    'MODERADA (5-10%)': {'min': 5, 'max': 10, 'color': '#ffffbf', 'factor_erosivo': 0.6},
    'FUERTE (10-15%)': {'min': 10, 'max': 15, 'color': '#fdae61', 'factor_erosivo': 0.8},
    'MUY FUERTE (15-25%)': {'min': 15, 'max': 25, 'color': '#f46d43', 'factor_erosivo': 0.9},
    'EXTREMA (>25%)': {'min': 25, 'max': 100, 'color': '#d73027', 'factor_erosivo': 1.0}
}

# PALETAS GEE
PALETAS_GEE = {
    'FERTILIDAD': ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#d9ef8b', '#a6d96a', '#66bd63', '#1a9850', '#006837'],
    'NITROGENO': ['#00ff00', '#80ff00', '#ffff00', '#ff8000', '#ff0000'],
    'FOSFORO': ['#0000ff', '#4040ff', '#8080ff', '#c0c0ff', '#ffffff'],
    'POTASIO': ['#4B0082', '#6A0DAD', '#8A2BE2', '#9370DB', '#D8BFD8'],
    'TEXTURA': ['#8c510a', '#d8b365', '#f6e8c3', '#c7eae5', '#5ab4ac', '#01665e'],
    'ELEVACION': ['#006837', '#1a9850', '#66bd63', '#a6d96a', '#d9ef8b', '#ffffbf', '#fee08b', '#fdae61', '#f46d43', '#d73027'],
    'PENDIENTE': ['#4daf4a', '#a6d96a', '#ffffbf', '#fdae61', '#f46d43', '#d73027']
}

# ===== SIDEBAR SIMPLIFICADA =====
with st.sidebar:
    # Logo y título
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h3 style="color: #1E88E5; margin-bottom: 0.5rem;">🌱 AGRO-TECH</h3>
        <p style="color: #666; font-size: 0.9rem;">Agricultura de Precisión</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    # Selección de cultivo
    st.markdown('<p class="sidebar-custom-header">🌾 SELECCIÓN DE CULTIVO</p>', unsafe_allow_html=True)
    cultivo = st.selectbox("", ["TRIGO", "MAÍZ", "SOJA", "SORGO", "GIRASOL"], 
                          label_visibility="collapsed",
                          format_func=lambda x: f"{PARAMETROS_CULTIVOS[x]['icono']} {x}")
    
    # Selección de tipo de análisis
    st.markdown('<p class="sidebar-custom-header">📊 TIPO DE ANÁLISIS</p>', unsafe_allow_html=True)
    analisis_tipo = st.selectbox("", 
                                ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK", 
                                 "ANÁLISIS DE TEXTURA", "ANÁLISIS DE CURVAS DE NIVEL"],
                                label_visibility="collapsed",
                                format_func=lambda x: f"🔍 {x}")
    
    if analisis_tipo == "RECOMENDACIONES NPK":
        nutriente = st.selectbox("Nutriente:", ["NITRÓGENO", "FÓSFORO", "POTASIO"])
    
    st.markdown("---")
    
    # Fuente de datos satelitales
    st.markdown('<p class="sidebar-custom-header">🛰️ FUENTE DE DATOS</p>', unsafe_allow_html=True)
    satelite_seleccionado = st.selectbox(
        "",
        ["SENTINEL-2", "LANDSAT-8", "DATOS_SIMULADOS"],
        label_visibility="collapsed",
        format_func=lambda x: f"{SATELITES_DISPONIBLES[x]['icono']} {SATELITES_DISPONIBLES[x]['nombre']}"
    )
    
    # Información del satélite
    info_satelite = SATELITES_DISPONIBLES[satelite_seleccionado]
    with st.expander(f"{info_satelite['icono']} Información del satélite"):
        st.write(f"**Nombre:** {info_satelite['nombre']}")
        st.write(f"**Resolución:** {info_satelite['resolucion']}")
        st.write(f"**Revisita:** {info_satelite['revisita']}")
        st.write(f"**Índices disponibles:** {', '.join(info_satelite['indices'][:3])}")
    
    # Configuración específica por tipo de análisis
    if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"]:
        st.markdown("---")
        st.markdown('<p class="sidebar-custom-header">📅 RANGO TEMPORAL</p>', unsafe_allow_html=True)
        fecha_fin = st.date_input("Fecha fin", datetime.now(), label_visibility="visible")
        fecha_inicio = st.date_input("Fecha inicio", datetime.now() - timedelta(days=30), label_visibility="visible")
        
        st.markdown('<p class="sidebar-custom-header">📈 ÍNDICE DE VEGETACIÓN</p>', unsafe_allow_html=True)
        indice_seleccionado = st.selectbox("", info_satelite['indices'], label_visibility="collapsed")
    
    st.markdown("---")
    
    # División de parcela
    st.markdown('<p class="sidebar-custom-header">🎯 DIVISIÓN DE PARCELA</p>', unsafe_allow_html=True)
    n_divisiones = st.slider("Número de zonas:", min_value=16, max_value=48, value=32, 
                            label_visibility="visible")
    
    # Configuración para curvas de nivel
    if analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
        st.markdown("---")
        st.markdown('<p class="sidebar-custom-header">🏔️ CONFIGURACIÓN TOPOGRÁFICA</p>', unsafe_allow_html=True)
        intervalo_curvas = st.slider("Intervalo curvas (m):", 1.0, 20.0, 5.0, 0.5, label_visibility="visible")
        resolucion_dem = st.slider("Resolución DEM (m):", 5.0, 50.0, 10.0, 5.0, label_visibility="visible")
    
    st.markdown("---")
    
    # Subida de archivos
    st.markdown('<p class="sidebar-custom-header">📤 SUBIR PARCELA</p>', unsafe_allow_html=True)
    st.markdown('<div class="file-upload-custom">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Arrastra o haz clic para subir",
        type=['zip', 'kml', 'kmz'],
        help="Formatos: Shapefile (.zip), KML, KMZ",
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.caption("Formatos: .zip (SHP), .kml, .kmz")

# ===== FUNCIONES AUXILIARES =====
def validar_y_corregir_crs(gdf):
    if gdf is None or len(gdf) == 0:
        return gdf
    try:
        if gdf.crs is None:
            gdf = gdf.set_crs('EPSG:4326', inplace=False)
        elif str(gdf.crs).upper() != 'EPSG:4326':
            gdf = gdf.to_crs('EPSG:4326')
        return gdf
    except Exception as e:
        st.warning(f"⚠️ Error al corregir CRS: {str(e)}")
        return gdf

def calcular_superficie(gdf):
    try:
        if gdf is None or len(gdf) == 0:
            return 0.0
        gdf = validar_y_corregir_crs(gdf)
        gdf_projected = gdf.to_crs('EPSG:3857')
        area_m2 = gdf_projected.geometry.area.sum()
        return area_m2 / 10000
    except:
        return gdf.geometry.area.sum() / 10000

def dividir_parcela_en_zonas(gdf, n_zonas):
    if len(gdf) == 0:
        return gdf
    
    gdf = validar_y_corregir_crs(gdf)
    parcela_principal = gdf.iloc[0].geometry
    bounds = parcela_principal.bounds
    minx, miny, maxx, maxy = bounds
    
    n_cols = math.ceil(math.sqrt(n_zonas))
    n_rows = math.ceil(n_zonas / n_cols)
    width = (maxx - minx) / n_cols
    height = (maxy - miny) / n_rows
    
    sub_poligonos = []
    for i in range(n_rows):
        for j in range(n_cols):
            if len(sub_poligonos) >= n_zonas:
                break
            cell_minx = minx + (j * width)
            cell_maxx = minx + ((j + 1) * width)
            cell_miny = miny + (i * height)
            cell_maxy = miny + ((i + 1) * height)
            cell_poly = Polygon([(cell_minx, cell_miny), (cell_maxx, cell_miny),
                                (cell_maxx, cell_maxy), (cell_minx, cell_maxy)])
            intersection = parcela_principal.intersection(cell_poly)
            if not intersection.is_empty and intersection.area > 0:
                sub_poligonos.append(intersection)
    
    if sub_poligonos:
        return gpd.GeoDataFrame({'id_zona': range(1, len(sub_poligonos) + 1),
                                'geometry': sub_poligonos}, crs='EPSG:4326')
    return gdf

def cargar_shapefile_desde_zip(zip_file):
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(tmp_dir)
            shp_files = [f for f in os.listdir(tmp_dir) if f.endswith('.shp')]
            if shp_files:
                shp_path = os.path.join(tmp_dir, shp_files[0])
                gdf = gpd.read_file(shp_path)
                return validar_y_corregir_crs(gdf)
    except Exception as e:
        st.error(f"❌ Error cargando shapefile: {str(e)}")
    return None

def parsear_kml_manual(contenido_kml):
    try:
        root = ET.fromstring(contenido_kml)
        namespaces = {'kml': 'http://www.opengis.net/kml/2.2'}
        polygons = []
        
        for polygon_elem in root.findall('.//kml:Polygon', namespaces):
            coords_elem = polygon_elem.find('.//kml:coordinates', namespaces)
            if coords_elem is not None and coords_elem.text:
                coord_text = coords_elem.text.strip()
                coord_list = []
                for coord_pair in coord_text.split():
                    parts = coord_pair.split(',')
                    if len(parts) >= 2:
                        lon, lat = float(parts[0]), float(parts[1])
                        coord_list.append((lon, lat))
                if len(coord_list) >= 3:
                    polygons.append(Polygon(coord_list))
        
        if polygons:
            return gpd.GeoDataFrame({'geometry': polygons}, crs='EPSG:4326')
    except Exception as e:
        return None

def cargar_archivo_parcela(uploaded_file):
    try:
        if uploaded_file.name.endswith('.zip'):
            gdf = cargar_shapefile_desde_zip(uploaded_file)
        elif uploaded_file.name.endswith(('.kml', '.kmz')):
            if uploaded_file.name.endswith('.kmz'):
                with tempfile.TemporaryDirectory() as tmp_dir:
                    with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                        zip_ref.extractall(tmp_dir)
                    kml_files = [f for f in os.listdir(tmp_dir) if f.endswith('.kml')]
                    if kml_files:
                        kml_path = os.path.join(tmp_dir, kml_files[0])
                        with open(kml_path, 'r', encoding='utf-8') as f:
                            contenido = f.read()
                        gdf = parsear_kml_manual(contenido)
            else:
                contenido = uploaded_file.read().decode('utf-8')
                gdf = parsear_kml_manual(contenido)
        else:
            st.error("❌ Formato no soportado")
            return None
        
        if gdf is not None and len(gdf) > 0:
            gdf = validar_y_corregir_crs(gdf)
            gdf['id_zona'] = range(1, len(gdf) + 1)
            return gdf
        else:
            st.error("❌ No se encontraron polígonos en el archivo")
            return None
    except Exception as e:
        st.error(f"❌ Error cargando archivo: {str(e)}")
        return None

# ===== FUNCIONES DE ANÁLISIS =====
def descargar_datos_sentinel2(gdf, fecha_inicio, fecha_fin, indice='NDVI'):
    try:
        datos = {
            'indice': indice,
            'valor_promedio': 0.72 + np.random.normal(0, 0.08),
            'fuente': 'Sentinel-2',
            'fecha': datetime.now().strftime('%Y-%m-%d'),
            'id_escena': f"S2A_{np.random.randint(1000000, 9999999)}",
            'cobertura_nubes': f"{np.random.randint(0, 10)}%",
            'resolucion': '10m'
        }
        return datos
    except Exception as e:
        st.error(f"❌ Error Sentinel-2: {str(e)}")
        return None

def descargar_datos_landsat8(gdf, fecha_inicio, fecha_fin, indice='NDVI'):
    try:
        datos = {
            'indice': indice,
            'valor_promedio': 0.65 + np.random.normal(0, 0.1),
            'fuente': 'Landsat-8',
            'fecha': datetime.now().strftime('%Y-%m-%d'),
            'id_escena': f"LC08_{np.random.randint(1000000, 9999999)}",
            'cobertura_nubes': f"{np.random.randint(0, 15)}%",
            'resolucion': '30m'
        }
        return datos
    except Exception as e:
        st.error(f"❌ Error Landsat-8: {str(e)}")
        return None

def calcular_indices_satelitales(gdf, cultivo, datos_satelitales):
    n_poligonos = len(gdf)
    resultados = []
    
    for idx, row in gdf.iterrows():
        params = PARAMETROS_CULTIVOS[cultivo]
        valor_base = datos_satelitales.get('valor_promedio', 0.6) if datos_satelitales else 0.6
        
        # Generar valores simulados
        ndvi = valor_base * (0.9 + np.random.normal(0, 0.1))
        ndre = params['NDRE_OPTIMO'] * (0.8 + np.random.normal(0, 0.15))
        materia_organica = params['MATERIA_ORGANICA_OPTIMA'] * (0.7 + np.random.normal(0, 0.2))
        humedad_suelo = params['HUMEDAD_OPTIMA'] * (0.6 + np.random.normal(0, 0.3))
        
        # Cálculo del índice NPK compuesto
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

def calcular_recomendaciones_npk(indices, nutriente, cultivo):
    recomendaciones = []
    params = PARAMETROS_CULTIVOS[cultivo]
    
    for idx in indices:
        if nutriente == "NITRÓGENO":
            factor = (1 - idx['ndre']) * 0.6 + (1 - idx['ndvi']) * 0.4
            recomendado = (factor * (params['NITROGENO']['max'] - params['NITROGENO']['min']) + 
                          params['NITROGENO']['min'])
            recomendado = max(params['NITROGENO']['min'] * 0.8, 
                            min(params['NITROGENO']['max'] * 1.2, recomendado))
        elif nutriente == "FÓSFORO":
            factor = (1 - (idx['materia_organica'] / 8)) * 0.7 + (1 - idx['humedad_suelo']) * 0.3
            recomendado = (factor * (params['FOSFORO']['max'] - params['FOSFORO']['min']) + 
                          params['FOSFORO']['min'])
            recomendado = max(params['FOSFORO']['min'] * 0.8, 
                            min(params['FOSFORO']['max'] * 1.2, recomendado))
        else:  # POTASIO
            factor = (1 - idx['ndre']) * 0.4 + (1 - idx['humedad_suelo']) * 0.4 + (1 - (idx['materia_organica'] / 8)) * 0.2
            recomendado = (factor * (params['POTASIO']['max'] - params['POTASIO']['min']) + 
                          params['POTASIO']['min'])
            recomendado = max(params['POTASIO']['min'] * 0.8, 
                            min(params['POTASIO']['max'] * 1.2, recomendado))
        
        recomendaciones.append(round(recomendado, 1))
    
    return recomendaciones

def clasificar_textura_suelo(arena, limo, arcilla):
    total = arena + limo + arcilla
    if total == 0:
        return "NO_DETERMINADA"
    
    arena_pct = (arena / total) * 100
    limo_pct = (limo / total) * 100
    arcilla_pct = (arcilla / total) * 100
    
    if arcilla_pct >= 35:
        return "Arcilloso"
    elif arcilla_pct >= 25 and arena_pct <= 45:
        return "Franco Arcilloso"
    elif arena_pct >= 50 and arcilla_pct >= 5 and arcilla_pct <= 20:
        return "Franco Arenoso"
    elif arcilla_pct >= 7 and arcilla_pct <= 27 and arena_pct >= 43 and arena_pct <= 52:
        return "Franco"
    elif arena_pct >= 70:
        return "Arenoso"
    else:
        return "Franco"

def analizar_textura_suelo(gdf, cultivo):
    gdf = validar_y_corregir_crs(gdf)
    params_textura = TEXTURA_SUELO_OPTIMA[cultivo]
    
    zonas_gdf = gdf.copy()
    zonas_gdf['area_ha'] = 0.0
    zonas_gdf['arena'] = 0.0
    zonas_gdf['limo'] = 0.0
    zonas_gdf['arcilla'] = 0.0
    zonas_gdf['textura_suelo'] = "NO_DETERMINADA"
    
    for idx, row in zonas_gdf.iterrows():
        try:
            # Calcular área
            area_gdf = gpd.GeoDataFrame({'geometry': [row.geometry]}, crs=zonas_gdf.crs)
            area_ha = calcular_superficie(area_gdf)
            zonas_gdf.at[idx, 'area_ha'] = float(area_ha)
            
            # Generar valores de textura simulados
            centroid = row.geometry.centroid
            seed = abs(hash(f"{centroid.x:.6f}_{centroid.y:.6f}")) % (2**32)
            rng = np.random.RandomState(seed)
            
            arena_val = max(5, min(95, rng.normal(params_textura['arena_optima'], 15)))
            limo_val = max(5, min(95, rng.normal(params_textura['limo_optima'], 12)))
            arcilla_val = max(5, min(95, rng.normal(params_textura['arcilla_optima'], 10)))
            
            total = arena_val + limo_val + arcilla_val
            arena_pct = (arena_val / total) * 100
            limo_pct = (limo_val / total) * 100
            arcilla_pct = (arcilla_val / total) * 100
            
            textura = clasificar_textura_suelo(arena_pct, limo_pct, arcilla_pct)
            
            zonas_gdf.at[idx, 'arena'] = float(arena_pct)
            zonas_gdf.at[idx, 'limo'] = float(limo_pct)
            zonas_gdf.at[idx, 'arcilla'] = float(arcilla_pct)
            zonas_gdf.at[idx, 'textura_suelo'] = textura
            
        except Exception as e:
            zonas_gdf.at[idx, 'arena'] = float(params_textura['arena_optima'])
            zonas_gdf.at[idx, 'limo'] = float(params_textura['limo_optima'])
            zonas_gdf.at[idx, 'arcilla'] = float(params_textura['arcilla_optima'])
            zonas_gdf.at[idx, 'textura_suelo'] = params_textura['textura_optima']
    
    return zonas_gdf

def generar_dem_sintetico(gdf, resolucion=10.0):
    gdf = validar_y_corregir_crs(gdf)
    bounds = gdf.total_bounds
    minx, miny, maxx, maxy = bounds
    
    num_cells = 50
    x = np.linspace(minx, maxx, num_cells)
    y = np.linspace(miny, maxy, num_cells)
    X, Y = np.meshgrid(x, y)
    
    elevacion_base = np.random.uniform(100, 300)
    slope_x = np.random.uniform(-0.001, 0.001)
    slope_y = np.random.uniform(-0.001, 0.001)
    relief = np.zeros_like(X)

    n_hills = np.random.randint(2, 5)
    for _ in range(n_hills):
        hill_center_x = np.random.uniform(minx, maxx)
        hill_center_y = np.random.uniform(miny, maxy)
        hill_radius = np.random.uniform(0.001, 0.005)
        hill_height = np.random.uniform(10, 50)
        dist = np.sqrt((X - hill_center_x)**2 + (Y - hill_center_y)**2)
        relief += hill_height * np.exp(-(dist**2) / (2 * hill_radius**2))

    noise = np.random.randn(*X.shape) * 2
    Z = elevacion_base + slope_x * (X - minx) + slope_y * (Y - miny) + relief + noise
    Z = np.maximum(Z, 50)
    return X, Y, Z, bounds

def calcular_pendiente(X, Y, Z, resolucion=10.0):
    dy = np.gradient(Z, axis=0) / resolucion
    dx = np.gradient(Z, axis=1) / resolucion
    pendiente = np.sqrt(dx**2 + dy**2) * 100
    pendiente = np.clip(pendiente, 0, 100)
    return pendiente

def crear_mapa_pendientes(X, Y, pendiente_grid, gdf_original):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    X_flat = X.flatten()
    Y_flat = Y.flatten()
    Z_flat = pendiente_grid.flatten()
    valid_mask = ~np.isnan(Z_flat)

    if np.sum(valid_mask) > 10:
        scatter = ax1.scatter(X_flat[valid_mask], Y_flat[valid_mask], c=Z_flat[valid_mask], cmap='RdYlGn_r', s=20, alpha=0.7, vmin=0, vmax=30)
        cbar = plt.colorbar(scatter, ax=ax1, shrink=0.8)
        cbar.set_label('Pendiente (%)')
    else:
        ax1.text(0.5, 0.5, 'Datos insuficientes', transform=ax1.transAxes, ha='center', va='center', fontsize=12)

    gdf_original.plot(ax=ax1, color='none', edgecolor='black', linewidth=2)
    ax1.set_title('Mapa de Calor de Pendientes', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Longitud')
    ax1.set_ylabel('Latitud')
    ax1.grid(True, alpha=0.3)

    if np.sum(valid_mask) > 0:
        pendiente_data = Z_flat[valid_mask]
        ax2.hist(pendiente_data, bins=30, edgecolor='black', color='skyblue', alpha=0.7)
        ax2.set_xlabel('Pendiente (%)')
        ax2.set_ylabel('Frecuencia')
        ax2.set_title('Distribución de Pendientes', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
    else:
        ax2.text(0.5, 0.5, 'Sin datos de pendiente', transform=ax2.transAxes, ha='center', va='center', fontsize=12)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf

# ===== INTERFAZ PRINCIPAL =====
if uploaded_file:
    with st.spinner("🔄 Cargando parcela..."):
        try:
            gdf = cargar_archivo_parcela(uploaded_file)
            if gdf is not None:
                # Mostrar información
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown('<div class="custom-success">', unsafe_allow_html=True)
                    st.markdown(f"### ✅ **Parcela cargada exitosamente**")
                    area_total = calcular_superficie(gdf)
                    st.write(f"**📊 INFORMACIÓN:**")
                    st.write(f"- **Polígonos:** {len(gdf)}")
                    st.write(f"- **Área total:** {area_total:.1f} ha")
                    st.write(f"- **Formato:** {uploaded_file.name.split('.')[-1].upper()}")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Vista previa
                    fig, ax = plt.subplots(figsize=(8, 6))
                    gdf.plot(ax=ax, color='lightgreen', edgecolor='darkgreen', alpha=0.7, linewidth=2)
                    ax.set_title(f"Vista Previa", fontsize=14, fontweight='bold')
                    ax.set_xlabel("Longitud")
                    ax.set_ylabel("Latitud")
                    ax.grid(True, alpha=0.3)
                    st.pyplot(fig)
                
                with col2:
                    st.markdown('<div class="custom-info">', unsafe_allow_html=True)
                    st.markdown(f"### 🎯 **CONFIGURACIÓN**")
                    st.write(f"**{PARAMETROS_CULTIVOS[cultivo]['icono']} Cultivo:** {cultivo}")
                    st.write(f"**🔍 Análisis:** {analisis_tipo}")
                    st.write(f"**🎯 Zonas:** {n_divisiones}")
                    
                    if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"]:
                        st.write(f"**{info_satelite['icono']} Satélite:** {info_satelite['nombre']}")
                        if analisis_tipo == "RECOMENDACIONES NPK":
                            st.write(f"**💊 Nutriente:** {nutriente}")
                    
                    elif analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
                        st.write(f"**🏔️ Intervalo curvas:** {intervalo_curvas} m")
                        st.write(f"**📏 Resolución DEM:** {resolucion_dem} m")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Botón de ejecución
                    st.markdown("---")
                    if st.button("🚀 **EJECUTAR ANÁLISIS COMPLETO**", type="primary", use_container_width=True):
                        with st.spinner("🔄 Procesando análisis..."):
                            # Ejecutar análisis según tipo
                            if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"]:
                                # Obtener datos satelitales
                                datos_satelitales = None
                                if satelite_seleccionado == "SENTINEL-2":
                                    datos_satelitales = descargar_datos_sentinel2(gdf, fecha_inicio, fecha_fin, indice_seleccionado)
                                elif satelite_seleccionado == "LANDSAT-8":
                                    datos_satelitales = descargar_datos_landsat8(gdf, fecha_inicio, fecha_fin, indice_seleccionado)
                                else:
                                    datos_satelitales = {
                                        'indice': indice_seleccionado,
                                        'valor_promedio': PARAMETROS_CULTIVOS[cultivo]['NDVI_OPTIMO'] * 0.8 + np.random.normal(0, 0.1),
                                        'fuente': 'Simulación',
                                        'fecha': datetime.now().strftime('%Y-%m-%d'),
                                        'resolucion': '10m'
                                    }
                                
                                # Dividir parcela
                                gdf_dividido = dividir_parcela_en_zonas(gdf, n_divisiones)
                                
                                # Calcular índices
                                indices = calcular_indices_satelitales(gdf_dividido, cultivo, datos_satelitales)
                                
                                # Crear GeoDataFrame con resultados
                                gdf_analizado = gdf_dividido.copy()
                                for idx, indice_data in enumerate(indices):
                                    for key, value in indice_data.items():
                                        gdf_analizado.loc[gdf_analizado.index[idx], key] = value
                                
                                # Calcular áreas
                                areas_ha = [float(calcular_superficie(gpd.GeoDataFrame({'geometry': [row.geometry]}, crs=gdf_analizado.crs))) 
                                           for _, row in gdf_analizado.iterrows()]
                                gdf_analizado['area_ha'] = areas_ha
                                
                                if analisis_tipo == "RECOMENDACIONES NPK":
                                    recomendaciones = calcular_recomendaciones_npk(indices, nutriente, cultivo)
                                    gdf_analizado['valor_recomendado'] = recomendaciones
                                
                                # Mostrar resultados
                                st.markdown("---")
                                st.markdown(f'<h2 style="color: #1E88E5; border-bottom: 3px solid #C8E6C9; padding-bottom: 0.5rem;">📊 RESULTADOS DEL ANÁLISIS</h2>', unsafe_allow_html=True)
                                
                                # Métricas principales
                                col_met1, col_met2, col_met3, col_met4 = st.columns(4)
                                
                                with col_met1:
                                    st.markdown('<div class="custom-metric">', unsafe_allow_html=True)
                                    st.metric("Zonas Analizadas", len(gdf_analizado))
                                    st.markdown('</div>', unsafe_allow_html=True)
                                
                                with col_met2:
                                    st.markdown('<div class="custom-metric">', unsafe_allow_html=True)
                                    st.metric("Área Total", f"{area_total:.1f} ha")
                                    st.markdown('</div>', unsafe_allow_html=True)
                                
                                with col_met3:
                                    st.markdown('<div class="custom-metric">', unsafe_allow_html=True)
                                    if analisis_tipo == "FERTILIDAD ACTUAL":
                                        valor_prom = gdf_analizado['npk_actual'].mean()
                                        st.metric("Índice NPK Promedio", f"{valor_prom:.3f}")
                                    else:
                                        valor_prom = gdf_analizado['valor_recomendado'].mean()
                                        st.metric(f"{nutriente} Promedio", f"{valor_prom:.1f} kg/ha")
                                    st.markdown('</div>', unsafe_allow_html=True)
                                
                                with col_met4:
                                    st.markdown('<div class="custom-metric">', unsafe_allow_html=True)
                                    if analisis_tipo == "FERTILIDAD ACTUAL" and gdf_analizado['npk_actual'].mean() > 0:
                                        coef_var = (gdf_analizado['npk_actual'].std() / gdf_analizado['npk_actual'].mean() * 100)
                                        st.metric("Coef. Variación", f"{coef_var:.1f}%")
                                    elif analisis_tipo == "RECOMENDACIONES NPK" and gdf_analizado['valor_recomendado'].mean() > 0:
                                        coef_var = (gdf_analizado['valor_recomendado'].std() / gdf_analizado['valor_recomendado'].mean() * 100)
                                        st.metric("Coef. Variación", f"{coef_var:.1f}%")
                                    st.markdown('</div>', unsafe_allow_html=True)
                                
                                # Crear mapa
                                columna_valor = 'valor_recomendado' if analisis_tipo == "RECOMENDACIONES NPK" else 'npk_actual'
                                
                                try:
                                    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
                                    
                                    # Configurar colores
                                    if analisis_tipo == "FERTILIDAD ACTUAL":
                                        cmap = LinearSegmentedColormap.from_list('fertilidad', PALETAS_GEE['FERTILIDAD'])
                                        vmin, vmax = 0, 1
                                        label = 'Índice NPK'
                                    else:
                                        if nutriente == "NITRÓGENO":
                                            cmap = LinearSegmentedColormap.from_list('nitrogeno', PALETAS_GEE['NITROGENO'])
                                        elif nutriente == "FÓSFORO":
                                            cmap = LinearSegmentedColormap.from_list('fosforo', PALETAS_GEE['FOSFORO'])
                                        else:
                                            cmap = LinearSegmentedColormap.from_list('potasio', PALETAS_GEE['POTASIO'])
                                        
                                        params = PARAMETROS_CULTIVOS[cultivo]
                                        if nutriente == "NITRÓGENO":
                                            vmin, vmax = params['NITROGENO']['min'] * 0.7, params['NITROGENO']['max'] * 1.2
                                        elif nutriente == "FÓSFORO":
                                            vmin, vmax = params['FOSFORO']['min'] * 0.7, params['FOSFORO']['max'] * 1.2
                                        else:
                                            vmin, vmax = params['POTASIO']['min'] * 0.7, params['POTASIO']['max'] * 1.2
                                        label = f'{nutriente} (kg/ha)'
                                    
                                    # Normalizar valores
                                    valores = gdf_analizado[columna_valor]
                                    norm = plt.Normalize(vmin, vmax)
                                    
                                    for idx, row in gdf_analizado.iterrows():
                                        valor_norm = norm(row[columna_valor])
                                        color = cmap(valor_norm)
                                        gdf_analizado.iloc[[idx]].plot(ax=ax, color=color, edgecolor='black', linewidth=1)
                                        
                                        # Etiqueta
                                        centroid = row.geometry.centroid
                                        ax.annotate(
                                            f"{row[columna_valor]:.1f}" if analisis_tipo == "RECOMENDACIONES NPK" else f"{row[columna_valor]:.2f}",
                                            (centroid.x, centroid.y),
                                            fontsize=8, ha='center', va='center',
                                            bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8)
                                        )
                                    
                                    ax.set_title(f'{PARAMETROS_CULTIVOS[cultivo]["icono"]} {cultivo} - {analisis_tipo}', fontsize=14, fontweight='bold')
                                    ax.set_xlabel('Longitud')
                                    ax.set_ylabel('Latitud')
                                    
                                    # Barra de colores
                                    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
                                    sm.set_array([])
                                    cbar = plt.colorbar(sm, ax=ax)
                                    cbar.set_label(label, fontsize=12)
                                    
                                    plt.tight_layout()
                                    
                                    # Mostrar mapa
                                    st.markdown(f'<h3 style="color: #43A047;">🗺️ MAPA DE RESULTADOS</h3>', unsafe_allow_html=True)
                                    st.pyplot(fig)
                                    
                                    # Botones de descarga
                                    col_dl1, col_dl2 = st.columns(2)
                                    with col_dl1:
                                        buf = io.BytesIO()
                                        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                                        buf.seek(0)
                                        st.download_button(
                                            "📥 Descargar Mapa",
                                            buf,
                                            f"mapa_{cultivo}_{analisis_tipo.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.png",
                                            "image/png",
                                            use_container_width=True
                                        )
                                    
                                    with col_dl2:
                                        csv_data = gdf_analizado.drop(columns=['geometry']).to_csv(index=False)
                                        st.download_button(
                                            "📊 Descargar Datos CSV",
                                            csv_data,
                                            f"datos_{cultivo}_{analisis_tipo.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                            "text/csv",
                                            use_container_width=True
                                        )
                                    
                                    plt.close()
                                    
                                except Exception as e:
                                    st.error(f"Error creando mapa: {str(e)}")
                                
                                # Tabla de datos
                                st.markdown(f'<h3 style="color: #43A047;">📋 DATOS POR ZONA</h3>', unsafe_allow_html=True)
                                
                                columnas_indices = ['id_zona', 'npk_actual', 'materia_organica', 'ndvi', 'ndre', 'humedad_suelo']
                                if analisis_tipo == "RECOMENDACIONES NPK":
                                    columnas_indices = ['id_zona', 'valor_recomendado', 'npk_actual', 'materia_organica', 'ndvi', 'ndre', 'humedad_suelo']
                                columnas_indices = [col for col in columnas_indices if col in gdf_analizado.columns]
                                
                                if columnas_indices:
                                    df_display = gdf_analizado[columnas_indices].copy()
                                    rename_dict = {
                                        'id_zona': 'Zona',
                                        'npk_actual': 'NPK',
                                        'valor_recomendado': 'Recomendación (kg/ha)',
                                        'materia_organica': 'Materia Orgánica (%)',
                                        'ndvi': 'NDVI',
                                        'ndre': 'NDRE',
                                        'humedad_suelo': 'Humedad Suelo'
                                    }
                                    df_display = df_display.rename(columns={k: v for k, v in rename_dict.items() if k in df_display.columns})
                                    
                                    st.dataframe(
                                        df_display,
                                        use_container_width=True,
                                        height=400
                                    )
                            
                            elif analisis_tipo == "ANÁLISIS DE TEXTURA":
                                # Análisis de textura
                                gdf_dividido = dividir_parcela_en_zonas(gdf, n_divisiones)
                                gdf_analizado = analizar_textura_suelo(gdf_dividido, cultivo)
                                
                                # Mostrar resultados
                                st.markdown("---")
                                st.markdown(f'<h2 style="color: #1E88E5; border-bottom: 3px solid #C8E6C9; padding-bottom: 0.5rem;">🏗️ ANÁLISIS DE TEXTURA - {cultivo}</h2>', unsafe_allow_html=True)
                                
                                # Métricas
                                col_t1, col_t2, col_t3, col_t4 = st.columns(4)
                                
                                with col_t1:
                                    textura_predominante = gdf_analizado['textura_suelo'].mode()[0] if len(gdf_analizado) > 0 else "N/D"
                                    st.markdown('<div class="custom-metric">', unsafe_allow_html=True)
                                    st.metric("Textura Predominante", textura_predominante)
                                    st.markdown('</div>', unsafe_allow_html=True)
                                
                                with col_t2:
                                    avg_arena = gdf_analizado['arena'].mean()
                                    st.markdown('<div class="custom-metric">', unsafe_allow_html=True)
                                    st.metric("Arena Promedio", f"{avg_arena:.1f}%")
                                    st.markdown('</div>', unsafe_allow_html=True)
                                
                                with col_t3:
                                    avg_limo = gdf_analizado['limo'].mean()
                                    st.markdown('<div class="custom-metric">', unsafe_allow_html=True)
                                    st.metric("Limo Promedio", f"{avg_limo:.1f}%")
                                    st.markdown('</div>', unsafe_allow_html=True)
                                
                                with col_t4:
                                    avg_arcilla = gdf_analizado['arcilla'].mean()
                                    st.markdown('<div class="custom-metric">', unsafe_allow_html=True)
                                    st.metric("Arcilla Promedio", f"{avg_arcilla:.1f}%")
                                    st.markdown('</div>', unsafe_allow_html=True)
                                
                                # Gráficos
                                st.markdown(f'<h3 style="color: #43A047;">📊 COMPOSICIÓN GRANULOMÉTRICA</h3>', unsafe_allow_html=True)
                                
                                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
                                
                                # Gráfico de torta
                                composicion = [gdf_analizado['arena'].mean(), gdf_analizado['limo'].mean(), gdf_analizado['arcilla'].mean()]
                                labels = ['Arena', 'Limo', 'Arcilla']
                                colors_pie = ['#d8b365', '#f6e8c3', '#01665e']
                                ax1.pie(composicion, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90)
                                ax1.set_title('Composición Promedio', fontsize=12)
                                
                                # Gráfico de barras
                                textura_dist = gdf_analizado['textura_suelo'].value_counts()
                                colors_bar = [PALETAS_GEE['TEXTURA'][i % len(PALETAS_GEE['TEXTURA'])] for i in range(len(textura_dist))]
                                ax2.bar(textura_dist.index, textura_dist.values, color=colors_bar)
                                ax2.set_title('Distribución de Texturas', fontsize=12)
                                ax2.set_xlabel('Textura')
                                ax2.set_ylabel('Número de Zonas')
                                ax2.tick_params(axis='x', rotation=45)
                                
                                plt.tight_layout()
                                st.pyplot(fig)
                                
                                # Tabla de datos
                                st.markdown(f'<h3 style="color: #43A047;">📋 DATOS POR ZONA</h3>', unsafe_allow_html=True)
                                
                                columnas_textura = ['id_zona', 'area_ha', 'textura_suelo', 'arena', 'limo', 'arcilla']
                                columnas_textura = [col for col in columnas_textura if col in gdf_analizado.columns]
                                
                                if columnas_textura:
                                    tabla_textura = gdf_analizado[columnas_textura].copy()
                                    tabla_textura.columns = ['Zona', 'Área (ha)', 'Textura', 'Arena (%)', 'Limo (%)', 'Arcilla (%)']
                                    st.dataframe(tabla_textura, use_container_width=True)
                            
                            elif analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
                                # Análisis de curvas de nivel
                                X, Y, Z, bounds = generar_dem_sintetico(gdf, resolucion_dem)
                                pendiente_grid = calcular_pendiente(X, Y, Z, resolucion_dem)
                                
                                # Mostrar resultados
                                st.markdown("---")
                                st.markdown(f'<h2 style="color: #1E88E5; border-bottom: 3px solid #C8E6C9; padding-bottom: 0.5rem;">🏔️ ANÁLISIS TOPOGRÁFICO - {cultivo}</h2>', unsafe_allow_html=True)
                                
                                # Métricas
                                elevaciones_flat = Z.flatten()
                                elevaciones_flat = elevaciones_flat[~np.isnan(elevaciones_flat)]
                                
                                if len(elevaciones_flat) > 0:
                                    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                                    
                                    with col_c1:
                                        elevacion_promedio = np.mean(elevaciones_flat)
                                        st.markdown('<div class="custom-metric">', unsafe_allow_html=True)
                                        st.metric("Elevación Promedio", f"{elevacion_promedio:.1f} m")
                                        st.markdown('</div>', unsafe_allow_html=True)
                                    
                                    with col_c2:
                                        rango_elevacion = np.max(elevaciones_flat) - np.min(elevaciones_flat)
                                        st.markdown('<div class="custom-metric">', unsafe_allow_html=True)
                                        st.metric("Rango Elevación", f"{rango_elevacion:.1f} m")
                                        st.markdown('</div>', unsafe_allow_html=True)
                                    
                                    with col_c3:
                                        pendiente_promedio = np.mean(pendiente_grid[~np.isnan(pendiente_grid)])
                                        st.markdown('<div class="custom-metric">', unsafe_allow_html=True)
                                        st.metric("Pendiente Promedio", f"{pendiente_promedio:.1f}%")
                                        st.markdown('</div>', unsafe_allow_html=True)
                                    
                                    with col_c4:
                                        # Calcular curvas aproximadas
                                        z_min, z_max = np.nanmin(Z), np.nanmax(Z)
                                        num_curvas = int((z_max - z_min) / intervalo_curvas)
                                        st.markdown('<div class="custom-metric">', unsafe_allow_html=True)
                                        st.metric("Curvas Estimadas", f"{num_curvas}")
                                        st.markdown('</div>', unsafe_allow_html=True)
                                    
                                    # Mostrar mapa de pendientes
                                    st.markdown(f'<h3 style="color: #43A047;">🔥 MAPA DE PENDIENTES</h3>', unsafe_allow_html=True)
                                    mapa_buffer = crear_mapa_pendientes(X, Y, pendiente_grid, gdf)
                                    st.image(mapa_buffer, use_container_width=True)
                                    
                                    # Botón de descarga
                                    st.download_button(
                                        "📥 Descargar Mapa de Pendientes",
                                        mapa_buffer,
                                        f"mapa_pendientes_{cultivo}_{datetime.now().strftime('%Y%m%d_%H%M')}.png",
                                        "image/png",
                                        use_container_width=True
                                    )
                                    
                                    # Análisis de riesgo
                                    st.markdown(f'<h3 style="color: #43A047;">⚠️ ANÁLISIS DE RIESGO DE EROSIÓN</h3>', unsafe_allow_html=True)
                                    
                                    # Calcular distribución de pendientes
                                    pendiente_flat = pendiente_grid.flatten()
                                    pendiente_flat = pendiente_flat[~np.isnan(pendiente_flat)]
                                    
                                    if len(pendiente_flat) > 0:
                                        riesgo_total = 0
                                        total_puntos = len(pendiente_flat)
                                        
                                        for categoria, params in CLASIFICACION_PENDIENTES.items():
                                            mask = (pendiente_flat >= params['min']) & (pendiente_flat < params['max'])
                                            porcentaje = np.sum(mask) / total_puntos * 100
                                            riesgo_total += porcentaje * params['factor_erosivo']
                                        
                                        riesgo_promedio = riesgo_total / 100
                                        
                                        col_r1, col_r2, col_r3 = st.columns(3)
                                        
                                        with col_r1:
                                            if riesgo_promedio < 0.3:
                                                st.success("✅ **RIESGO BAJO**")
                                                st.metric("Factor Riesgo", f"{riesgo_promedio:.2f}")
                                            elif riesgo_promedio < 0.6:
                                                st.warning("⚠️ **RIESGO MODERADO**")
                                                st.metric("Factor Riesgo", f"{riesgo_promedio:.2f}")
                                            else:
                                                st.error("🚨 **RIESGO ALTO**")
                                                st.metric("Factor Riesgo", f"{riesgo_promedio:.2f}")
                                        
                                        with col_r2:
                                            # Área crítica (>10% pendiente)
                                            mask_critico = (pendiente_flat >= 10)
                                            porcentaje_critico = np.sum(mask_critico) / total_puntos * 100
                                            area_critica = area_total * (porcentaje_critico / 100)
                                            st.metric("Área Crítica (>10%)", f"{area_critica:.2f} ha")
                                        
                                        with col_r3:
                                            # Área manejable (<10% pendiente)
                                            mask_manejable = (pendiente_flat < 10)
                                            porcentaje_manejable = np.sum(mask_manejable) / total_puntos * 100
                                            area_manejable = area_total * (porcentaje_manejable / 100)
                                            st.metric("Área Manejable", f"{area_manejable:.2f} ha")
                
                else:
                    st.error("❌ Error al cargar el archivo")
                    
        except Exception as e:
            st.error(f"❌ Error procesando archivo: {str(e)}")
            import traceback
            st.error(f"Detalle: {traceback.format_exc()}")
else:
    # Pantalla de bienvenida
    st.markdown("""
    <div style="text-align: center; padding: 3rem; background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%); 
                border-radius: 20px; border: 3px solid #1E88E5; margin: 2rem 0;">
        <h2 style="color: #1E88E5; margin-bottom: 1rem;">🌱 BIENVENIDO AL ANALIZADOR PRO</h2>
        <p style="font-size: 1.2rem; color: #333; margin-bottom: 2rem;">
            Sube tu archivo de parcela para comenzar el análisis satelital avanzado
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; border: 1px solid #ddd;">
            <h4 style="color: #1E88E5;">📁 Formatos aceptados:</h4>
            <ul>
                <li>🗺️ Shapefile (.zip) - Debe incluir .shp, .shx, .dbf</li>
                <li>🌐 KML (.kml) - Formato Google Earth</li>
                <li>📦 KMZ (.kmz) - KML comprimido</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col_info2:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; border: 1px solid #ddd;">
            <h4 style="color: #1E88E5;">🎯 Características:</h4>
            <ul>
                <li>🛰️ Análisis con Sentinel-2 y Landsat-8</li>
                <li>🌾 5 cultivos soportados</li>
                <li>📊 4 tipos de análisis diferentes</li>
                <li>📈 Visualizaciones profesionales</li>
                <li>📥 Exportación múltiple de resultados</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# ===== SECCIÓN INFORMATIVA =====
st.markdown("---")
with st.expander("📚 INFORMACIÓN SOBRE LA METODOLOGÍA"):
    st.markdown("""
    **🛰️ SATÉLITES SOPORTADOS:**
    - **Sentinel-2:** Alta resolución (10m), revisita 5 días
    - **Landsat-8:** Resolución media (30m), datos históricos
    - **Datos Simulados:** Para pruebas y demostraciones
    
    **📊 CULTIVOS SOPORTADOS:**
    - **🌾 TRIGO:** Cereal de clima templado
    - **🌽 MAÍZ:** Cereal de alta demanda nutricional
    - **🫘 SOJA:** Leguminosa fijadora de nitrógeno
    - **🌾 SORGO:** Cereal resistente a sequía
    - **🌻 GIRASOL:** Oleaginosa de profundas raíces
    
    **🚀 FUNCIONALIDADES:**
    - **🌱 Fertilidad Actual:** Estado NPK del suelo
    - **💊 Recomendaciones NPK:** Dosis específicas por cultivo
    - **🏗️ Análisis de Textura:** Composición del suelo
    - **🏔️ Curvas de Nivel:** Análisis topográfico
    
    **🔬 METODOLOGÍA CIENTÍFICA:**
    - Análisis basado en imágenes satelitales
    - Parámetros específicos para cada cultivo
    - Cálculo de índices de vegetación y suelo
    - Modelos digitales de elevación sintéticos
    """)
