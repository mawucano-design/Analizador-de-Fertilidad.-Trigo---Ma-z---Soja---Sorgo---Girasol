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
from matplotlib.path import Path
import io
from shapely.geometry import Polygon, LineString, Point
import math
import warnings
import xml.etree.ElementTree as ET
import base64
import json
from io import BytesIO
from fpdf import FPDF, HTMLMixin
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ROW_HEIGHT
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import geojson
from scipy.interpolate import griddata, interp1d
from scipy.spatial import Delaunay
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# CONFIGURACIÓN DE PÁGINA - DEBE SER LO PRIMERO
st.set_page_config(
    page_title="🌱 Analizador Multi-Cultivo Satellital PRO",
    layout="wide",
    page_icon="🛰️",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #43A047;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #C8E6C9;
        padding-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #F5F5F5;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1E88E5;
        margin-bottom: 1rem;
    }
    .export-button {
        background-color: #4CAF50;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        border: none;
        cursor: pointer;
        margin-right: 0.5rem;
    }
    .export-button:hover {
        background-color: #45a049;
    }
    .stButton > button {
        width: 100%;
        margin-top: 0.5rem;
    }
    .stDownloadButton > button {
        width: 100%;
        background-color: #2196F3;
        color: white;
    }
    .success-box {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #4CAF50;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #FFF3E0;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #FF9800;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #2196F3;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("🛰️ ANALIZADOR MULTI-CULTIVO PRO - SENTINEL-2 & LANDSAT-8")
st.markdown("---")

# ===== CONFIGURACIÓN DE SATÉLITES DISPONIBLES =====
SATELITES_DISPONIBLES = {
    'SENTINEL-2': {
        'nombre': 'Sentinel-2',
        'resolucion': '10m',
        'revisita': '5 días',
        'bandas': ['B2', 'B3', 'B4', 'B5', 'B8', 'B11'],
        'indices': ['NDVI', 'NDRE', 'GNDVI', 'OSAVI', 'MCARI', 'NDWI', 'EVI'],
        'icono': '🛰️'
    },
    'LANDSAT-8': {
        'nombre': 'Landsat 8',
        'resolucion': '30m',
        'revisita': '16 días',
        'bandas': ['B2', 'B3', 'B4', 'B5', 'B6', 'B7'],
        'indices': ['NDVI', 'NDWI', 'EVI', 'SAVI', 'MSAVI', 'GCI'],
        'icono': '🛰️'
    },
    'DATOS_SIMULADOS': {
        'nombre': 'Datos Simulados',
        'resolucion': '10m',
        'revisita': '5 días',
        'bandas': ['B2', 'B3', 'B4', 'B5', 'B8'],
        'indices': ['NDVI', 'NDRE', 'GNDVI', 'NDWI'],
        'icono': '🔬'
    }
}

# ===== CONFIGURACIÓN DE PARÁMETROS =====
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

# PARÁMETROS DE TEXTURA DEL SUELO
TEXTURA_SUELO_OPTIMA = {
    'TRIGO': {'textura_optima': 'Franco Arcilloso', 'arena_optima': 40, 'limo_optima': 30, 'arcilla_optima': 30},
    'MAÍZ': {'textura_optima': 'Franco', 'arena_optima': 45, 'limo_optima': 35, 'arcilla_optima': 20},
    'SOJA': {'textura_optima': 'Franco', 'arena_optima': 45, 'limo_optima': 35, 'arcilla_optima': 20},
    'SORGO': {'textura_optima': 'Franco', 'arena_optima': 45, 'limo_optima': 35, 'arcilla_optima': 20},
    'GIRASOL': {'textura_optima': 'Franco Arenoso', 'arena_optima': 55, 'limo_optima': 25, 'arcilla_optima': 20}
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

# RECOMENDACIONES POR TIPO DE TEXTURA
RECOMENDACIONES_TEXTURA = {
    'Franco': {
        'propiedades': ["Equilibrio arena-limo-arcilla", "Buena aireación y drenaje", "CIC Intermedia-alta"],
        'limitantes': ["Puede compactarse", "Erosión en pendientes"],
        'manejo': ["Mantener coberturas", "Evitar tránsito excesivo", "Fertilización eficiente"]
    },
    'Franco Arcilloso': {
        'propiedades': ["Alta retención de agua", "Buena fertilidad natural"],
        'limitantes': ["Riesgo de encharcamiento", "Compactación fácil"],
        'manejo': ["Implementar drenajes", "Subsolado previo", "Incorporar materia orgánica"]
    },
    'Franco Arenoso': {
        'propiedades': ["Excelente drenaje", "Buen desarrollo radicular"],
        'limitantes': ["Riesgo de lixiviación", "Estrés hídrico"],
        'manejo': ["Uso de coberturas leguminosas", "Riego suplementario", "Fertilización fraccionada"]
    }
}

# ICONOS Y COLORES
ICONOS_CULTIVOS = {'TRIGO': '🌾', 'MAÍZ': '🌽', 'SOJA': '🫘', 'SORGO': '🌾', 'GIRASOL': '🌻'}
COLORES_CULTIVOS = {'TRIGO': '#FFD700', 'MAÍZ': '#FFA500', 'SOJA': '#8B4513', 'SORGO': '#D2691E', 'GIRASOL': '#FFD700'}

# PALETAS GEE
PALETAS_GEE = {
    'FERTILIDAD': ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#d9ef8b', '#a6d96a', '#66bd63', '#1a9850', '#006837'],
    'NITROGENO': ['#00ff00', '#80ff00', '#ffff00', '#ff8000', '#ff0000'],
    'FOSFORO': ['#0000ff', '#4040ff', '#8080ff', '#c0c0ff', '#ffffff'],
    'POTASIO': ['#4B0082', '#6A0DAD', '#8A2BE2', '#9370DB', '#D8BFD8']
}

# ===== CLASE PDF MEJORADA CON CSS =====
class ImprovedPDF(FPDF, HTMLMixin):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'REPORTE DE ANÁLISIS AGRÍCOLA', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')
    
    def add_color_section(self, title, color='#1E88E5'):
        self.set_fill_color(int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L', True)
        self.set_text_color(0, 0, 0)
        self.ln(5)

# ===== SIDEBAR =====
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Selección de cultivo
    cultivo = st.selectbox("Cultivo:", ["TRIGO", "MAÍZ", "SOJA", "SORGO", "GIRASOL"])
    
    # Selección de tipo de análisis
    analisis_tipo = st.selectbox("Tipo de Análisis:", 
                                 ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK", 
                                  "ANÁLISIS DE TEXTURA", "ANÁLISIS DE CURVAS DE NIVEL",
                                  "BATCH PROCESSING", "COMPARATIVA HISTÓRICA"])
    
    # Configuración específica por tipo de análisis
    if analisis_tipo == "RECOMENDACIONES NPK":
        nutriente = st.selectbox("Nutriente:", ["NITRÓGENO", "FÓSFORO", "POTASIO"])
    
    # Fuente de datos satelitales
    st.subheader("🛰️ Fuente de Datos")
    satelite_seleccionado = st.selectbox("Satélite:", ["SENTINEL-2", "LANDSAT-8", "DATOS_SIMULADOS"])
    
    # Información del satélite seleccionado
    if satelite_seleccionado in SATELITES_DISPONIBLES:
        info = SATELITES_DISPONIBLES[satelite_seleccionado]
        with st.expander(f"ℹ️ Info {info['nombre']}"):
            st.write(f"**Resolución:** {info['resolucion']}")
            st.write(f"**Revisita:** {info['revisita']}")
            st.write(f"**Índices:** {', '.join(info['indices'])}")
    
    # Configuración temporal para análisis satelital
    if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK", "COMPARATIVA HISTÓRICA"]:
        st.subheader("📅 Rango Temporal")
        fecha_fin = st.date_input("Fecha fin", datetime.now())
        fecha_inicio = st.date_input("Fecha inicio", datetime.now() - timedelta(days=30))
        
        if analisis_tipo == "COMPARATIVA HISTÓRICA":
            fecha_historica = st.date_input("Fecha histórica", datetime.now() - timedelta(days=365))
    
    # División de parcela
    st.subheader("🎯 División de Parcela")
    n_divisiones = st.slider("Número de zonas:", 16, 64, 32)
    
    # Configuración específica para curvas de nivel
    if analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
        st.subheader("🏔️ Configuración Topográfica")
        intervalo_curvas = st.slider("Intervalo curvas (m):", 1.0, 20.0, 5.0, 0.5)
        resolucion_dem = st.slider("Resolución DEM (m):", 5.0, 50.0, 10.0, 5.0)
        generar_perfiles = st.checkbox("Generar perfiles topográficos", value=True)
        calcular_volumen = st.checkbox("Calcular volumen de tierra", value=False)
    
    # Subida de archivos
    st.subheader("📤 Subir Parcela(s)")
    
    if analisis_tipo == "BATCH PROCESSING":
        uploaded_files = st.file_uploader("Subir múltiples archivos", 
                                         type=['zip', 'kml', 'kmz'],
                                         accept_multiple_files=True,
                                         help="Puedes subir varios archivos a la vez")
    else:
        uploaded_file = st.file_uploader("Subir archivo de parcela", 
                                        type=['zip', 'kml', 'kmz'],
                                        help="Formatos: Shapefile (.zip), KML, KMZ")
    
    # Botón para procesar
    st.markdown("---")
    if st.button("🚀 EJECUTAR ANÁLISIS", type="primary", use_container_width=True):
        st.session_state['ejecutar_analisis'] = True
    else:
        st.session_state['ejecutar_analisis'] = False

# ===== FUNCIONES AUXILIARES =====
def validar_y_corregir_crs(gdf):
    """Valida y corrige el sistema de coordenadas a EPSG:4326"""
    if gdf is None or len(gdf) == 0:
        return gdf
    
    try:
        if gdf.crs is None:
            gdf = gdf.set_crs('EPSG:4326', inplace=False)
        elif str(gdf.crs).upper() != 'EPSG:4326':
            gdf = gdf.to_crs('EPSG:4326')
        return gdf
    except Exception as e:
        st.warning(f"⚠️ Error corrigiendo CRS: {str(e)}")
        return gdf

def calcular_superficie(gdf):
    """Calcula la superficie en hectáreas"""
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
    """Divide la parcela en zonas regulares"""
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
    """Carga un shapefile desde un archivo ZIP"""
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
    """Parsea manualmente un archivo KML"""
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
        st.error(f"❌ Error parseando KML: {str(e)}")
    return None

def cargar_archivo_parcela(uploaded_file):
    """Carga un archivo de parcela (SHP, KML, KMZ)"""
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

# ===== FUNCIONES DE ANÁLISIS SATELITAL =====
def descargar_datos_sentinel2(gdf, fecha_inicio, fecha_fin, indice='NDVI'):
    """Simula la descarga de datos Sentinel-2"""
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
    """Simula la descarga de datos Landsat-8"""
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
    """Calcula índices satelitales para cada zona"""
    n_poligonos = len(gdf)
    resultados = []
    
    for idx, row in gdf.iterrows():
        # Simulación de valores basados en parámetros del cultivo
        params = PARAMETROS_CULTIVOS[cultivo]
        valor_base = datos_satelitales.get('valor_promedio', 0.6) if datos_satelitales else 0.6
        
        # Generar valores simulados con variabilidad espacial
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
    """Calcula recomendaciones de NPK basadas en índices"""
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

# ===== FUNCIONES DE TEXTURA DEL SUELO =====
def clasificar_textura_suelo(arena, limo, arcilla):
    """Clasifica la textura del suelo basándose en el triángulo textural"""
    total = arena + limo + arcilla
    if total == 0:
        return "NO_DETERMINADA"
    
    arena_pct = (arena / total) * 100
    limo_pct = (limo / total) * 100
    arcilla_pct = (arcilla / total) * 100
    
    if arcilla_pct >= 40:
        return "Arcilloso"
    elif arcilla_pct >= 25 and arena_pct <= 45:
        return "Franco Arcilloso"
    elif arcilla_pct >= 20 and arena_pct >= 45:
        return "Franco Arcilloso Arenoso"
    elif arcilla_pct >= 7 and arcilla_pct <= 27 and arena_pct >= 43 and arena_pct <= 52:
        return "Franco"
    elif arena_pct >= 70:
        return "Arenoso"
    elif limo_pct >= 80:
        return "Limososo"
    else:
        return "Franco"

def analizar_textura_suelo(gdf, cultivo):
    """Analiza la textura del suelo para cada zona"""
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
            
            # Generar valores de textura simulados con variabilidad
            centroid = row.geometry.centroid
            seed = abs(hash(f"{centroid.x:.6f}_{centroid.y:.6f}")) % (2**32)
            rng = np.random.RandomState(seed)
            
            # Valores basados en textura óptima del cultivo
            arena_val = max(5, min(95, rng.normal(params_textura['arena_optima'], 15)))
            limo_val = max(5, min(95, rng.normal(params_textura['limo_optima'], 12)))
            arcilla_val = max(5, min(95, rng.normal(params_textura['arcilla_optima'], 10)))
            
            # Normalizar a 100%
            total = arena_val + limo_val + arcilla_val
            arena_pct = (arena_val / total) * 100
            limo_pct = (limo_val / total) * 100
            arcilla_pct = (arcilla_val / total) * 100
            
            # Clasificar textura
            textura = clasificar_textura_suelo(arena_pct, limo_pct, arcilla_pct)
            
            zonas_gdf.at[idx, 'arena'] = float(arena_pct)
            zonas_gdf.at[idx, 'limo'] = float(limo_pct)
            zonas_gdf.at[idx, 'arcilla'] = float(arcilla_pct)
            zonas_gdf.at[idx, 'textura_suelo'] = textura
            
        except Exception as e:
            # Valores por defecto en caso de error
            zonas_gdf.at[idx, 'arena'] = float(params_textura['arena_optima'])
            zonas_gdf.at[idx, 'limo'] = float(params_textura['limo_optima'])
            zonas_gdf.at[idx, 'arcilla'] = float(params_textura['arcilla_optima'])
            zonas_gdf.at[idx, 'textura_suelo'] = params_textura['textura_optima']
    
    return zonas_gdf

# ===== FUNCIONES DE CURVAS DE NIVEL MEJORADAS =====
def generar_dem_sintetico(gdf, resolucion=10.0):
    """Genera un Modelo Digital de Elevación sintético"""
    gdf = validar_y_corregir_crs(gdf)
    bounds = gdf.total_bounds
    minx, miny, maxx, maxy = bounds
    
    # Crear una malla regular
    num_cells = 100  # Mayor resolución para mejor detalle
    x = np.linspace(minx, maxx, num_cells)
    y = np.linspace(miny, maxy, num_cells)
    X, Y = np.meshgrid(x, y)
    
    # Elevación base
    elevacion_base = np.random.uniform(100, 300)
    
    # Pendiente general
    slope_x = np.random.uniform(-0.001, 0.001)
    slope_y = np.random.uniform(-0.001, 0.001)
    
    # Terreno ondulado con múltiples características
    Z = elevacion_base + slope_x * (X - minx) + slope_y * (Y - miny)
    
    # Añadir colinas
    n_hills = np.random.randint(3, 8)
    for _ in range(n_hills):
        hill_center_x = np.random.uniform(minx, maxx)
        hill_center_y = np.random.uniform(miny, maxy)
        hill_radius = np.random.uniform(0.001, 0.01)
        hill_height = np.random.uniform(20, 80)
        dist = np.sqrt((X - hill_center_x)**2 + (Y - hill_center_y)**2)
        Z += hill_height * np.exp(-(dist**2) / (2 * hill_radius**2))
    
    # Añadir valles
    n_valleys = np.random.randint(2, 5)
    for _ in range(n_valleys):
        valley_center_x = np.random.uniform(minx, maxx)
        valley_center_y = np.random.uniform(miny, maxy)
        valley_radius = np.random.uniform(0.002, 0.015)
        valley_depth = np.random.uniform(10, 40)
        dist = np.sqrt((X - valley_center_x)**2 + (Y - valley_center_y)**2)
        Z -= valley_depth * np.exp(-(dist**2) / (2 * valley_radius**2))
    
    # Ruido fractal para mayor realismo
    from scipy import ndimage
    noise = np.random.randn(num_cells, num_cells) * 5
    noise = ndimage.gaussian_filter(noise, sigma=2)
    Z += noise
    
    # Asegurar valores positivos
    Z = np.maximum(Z, 50)
    
    # Máscara fuera del polígono
    mask = np.zeros_like(X, dtype=bool)
    for i in range(num_cells):
        for j in range(num_cells):
            point = Point(X[i, j], Y[i, j])
            if not gdf.geometry.iloc[0].contains(point):
                Z[i, j] = np.nan
                mask[i, j] = True
    
    return X, Y, Z, bounds, mask

def calcular_pendiente(X, Y, Z, resolucion=10.0):
    """Calcula la pendiente en porcentaje"""
    dy = np.gradient(Z, axis=0) / resolucion
    dx = np.gradient(Z, axis=1) / resolucion
    pendiente = np.sqrt(dx**2 + dy**2) * 100
    pendiente = np.clip(pendiente, 0, 100)
    return pendiente

def generar_curvas_nivel(X, Y, Z, intervalo=5.0, gdf_original=None):
    """Genera curvas de nivel a intervalos regulares"""
    curvas = []
    elevaciones = []
    
    try:
        if gdf_original is not None:
            z_min, z_max = np.nanmin(Z), np.nanmax(Z)
            niveles = np.arange(z_min, z_max, intervalo)
            
            # Crear contornos usando matplotlib
            from matplotlib import contours
            import matplotlib._contour as _contour
            
            # Crear objeto contorno
            contorno = plt.contour(X, Y, Z, levels=niveles)
            
            for i, nivel in enumerate(contorno.levels):
                for path in contorno.collections[i].get_paths():
                    vertices = path.vertices
                    if len(vertices) > 1:
                        # Crear LineString desde los vértices
                        linea = LineString(vertices)
                        
                        # Recortar con el polígono original
                        if gdf_original is not None:
                            interseccion = gdf_original.geometry.iloc[0].intersection(linea)
                            if not interseccion.is_empty:
                                if interseccion.geom_type == 'LineString':
                                    curvas.append(interseccion)
                                    elevaciones.append(nivel)
                                elif interseccion.geom_type == 'MultiLineString':
                                    for parte in interseccion.geoms:
                                        curvas.append(parte)
                                        elevaciones.append(nivel)
                        else:
                            curvas.append(linea)
                            elevaciones.append(nivel)
            
            plt.close()
            
    except Exception as e:
        # Método de respaldo simple
        if gdf_original is not None:
            bounds = gdf_original.total_bounds
            for i in range(5):
                y = bounds[1] + (i + 1) * ((bounds[3] - bounds[1]) / 6)
                linea = LineString([(bounds[0], y), (bounds[2], y)])
                curvas.append(linea)
                elevaciones.append(100 + i * 50)
    
    return curvas, elevaciones

def generar_perfil_topografico(X, Y, Z, punto_inicio, punto_fin, num_puntos=100):
    """Genera un perfil topográfico entre dos puntos"""
    try:
        # Convertir puntos a índices
        def encontrar_indice_mas_cercano(x, y, X, Y):
            distancias = (X - x)**2 + (Y - y)**2
            idx = np.unravel_index(np.nanargmin(distancias), X.shape)
            return idx
        
        idx_inicio = encontrar_indice_mas_cercano(punto_inicio[0], punto_inicio[1], X, Y)
        idx_fin = encontrar_indice_mas_cercano(punto_fin[0], punto_fin[1], X, Y)
        
        # Crear línea de muestreo
        i_vals = np.linspace(idx_inicio[0], idx_fin[0], num_puntos)
        j_vals = np.linspace(idx_inicio[1], idx_fin[1], num_puntos)
        
        # Interpolación bilineal
        from scipy.interpolate import RegularGridInterpolator
        
        # Crear interpolador excluyendo NaN
        mask = ~np.isnan(Z)
        if np.sum(mask) > 10:
            rows, cols = np.where(mask)
            points = np.column_stack((rows, cols))
            values = Z[mask]
            
            # Interpolación
            interp = RegularGridInterpolator((np.arange(Z.shape[0]), np.arange(Z.shape[1])), 
                                            Z, method='linear', bounds_error=False, fill_value=np.nan)
            
            # Puntos a interpolar
            puntos_interp = np.column_stack((i_vals, j_vals))
            z_interp = interp(puntos_interp)
            
            # Calcular distancias reales
            x_coords = X[i_vals.astype(int), j_vals.astype(int)]
            y_coords = Y[i_vals.astype(int), j_vals.astype(int)]
            
            # Calcular distancia acumulada (en metros, aproximando grados a metros)
            dx = np.diff(x_coords) * 111320  # 1 grado lon ≈ 111,320 m
            dy = np.diff(y_coords) * 111320  # 1 grado lat ≈ 111,320 m
            distancias = np.sqrt(dx**2 + dy**2)
            distancias_acum = np.insert(np.cumsum(distancias), 0, 0)
            
            return distancias_acum, z_interp, (x_coords, y_coords)
        
    except Exception as e:
        st.warning(f"No se pudo generar perfil: {e}")
    
    return None, None, None

def calcular_volumen_tierra(X, Y, Z, elevacion_referencia):
    """Calcula el volumen de tierra a mover"""
    try:
        # Máscara para valores válidos
        mask = ~np.isnan(Z)
        
        if np.sum(mask) == 0:
            return 0, 0
        
        # Calcular diferencia de elevación
        diferencia = Z[mask] - elevacion_referencia
        
        # Calcular área de cada celda (aproximación)
        dx = np.abs(X[0, 1] - X[0, 0]) * 111320  # Convertir a metros
        dy = np.abs(Y[1, 0] - Y[0, 0]) * 111320  # Convertir a metros
        area_celda = dx * dy
        
        # Volumen (positivo = excavación, negativo = relleno)
        volumen_excavacion = np.sum(diferencia[diferencia > 0]) * area_celda
        volumen_relleno = np.abs(np.sum(diferencia[diferencia < 0])) * area_celda
        
        # Área total
        area_total = np.sum(mask) * area_celda
        
        return volumen_excavacion, volumen_relleno, area_total
    except Exception as e:
        st.warning(f"Error cálculo volumen: {e}")
        return 0, 0, 0

def crear_mapa_pendientes_interactivo(X, Y, pendiente_grid, gdf_original):
    """Crea un mapa interactivo de pendientes usando Plotly"""
    try:
        # Crear figura
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Mapa de Pendientes', 'Distribución de Pendientes'),
            specs=[[{"type": "scatter"}, {"type": "histogram"}]]
        )
        
        # Mapa de calor de pendientes
        fig.add_trace(
            go.Contour(
                x=X[0, :],
                y=Y[:, 0],
                z=pendiente_grid,
                colorscale='RdYlGn_r',
                zmin=0,
                zmax=30,
                line_width=0,
                contours=dict(
                    start=0,
                    end=30,
                    size=5,
                    coloring='heatmap'
                ),
                colorbar=dict(title="Pendiente (%)"),
                hoverinfo="x+y+z"
            ),
            row=1, col=1
        )
        
        # Añadir polígono original
        if gdf_original is not None:
            geom = gdf_original.geometry.iloc[0]
            if geom.geom_type == 'Polygon':
                x_coords, y_coords = geom.exterior.xy
                fig.add_trace(
                    go.Scatter(
                        x=list(x_coords),
                        y=list(y_coords),
                        mode='lines',
                        line=dict(color='black', width=2),
                        name='Parcela',
                        fill='toself',
                        fillcolor='rgba(0,0,0,0.1)'
                    ),
                    row=1, col=1
                )
        
        # Histograma de pendientes
        pendiente_flat = pendiente_grid.flatten()
        pendiente_flat = pendiente_flat[~np.isnan(pendiente_flat)]
        
        if len(pendiente_flat) > 0:
            fig.add_trace(
                go.Histogram(
                    x=pendiente_flat,
                    nbinsx=30,
                    marker_color='skyblue',
                    name='Pendientes'
                ),
                row=1, col=2
            )
        
        # Actualizar layout
        fig.update_layout(
            title_text=f"Análisis de Pendientes",
            height=500,
            showlegend=True
        )
        
        fig.update_xaxes(title_text="Longitud", row=1, col=1)
        fig.update_yaxes(title_text="Latitud", row=1, col=1)
        fig.update_xaxes(title_text="Pendiente (%)", row=1, col=2)
        fig.update_yaxes(title_text="Frecuencia", row=1, col=2)
        
        return fig
        
    except Exception as e:
        st.warning(f"No se pudo crear mapa interactivo: {e}")
        return None

# ===== FUNCIONES DE VISUALIZACIÓN 3D MEJORADAS =====
def crear_visualizacion_3d(X, Y, Z, gdf_original=None):
    """Crea una visualización 3D interactiva del terreno"""
    try:
        # Crear figura 3D
        fig = go.Figure(data=[
            go.Surface(
                x=X,
                y=Y,
                z=Z,
                colorscale='Viridis',
                opacity=0.9,
                contours=dict(
                    z=dict(
                        show=True,
                        usecolormap=True,
                        highlightcolor="limegreen",
                        project=dict(z=True)
                    )
                )
            )
        ])
        
        # Añadir polígono si está disponible
        if gdf_original is not None:
            geom = gdf_original.geometry.iloc[0]
            if geom.geom_type == 'Polygon':
                x_coords, y_coords = geom.exterior.xy
                # Crear puntos en 3D (elevación mínima)
                z_coords = np.ones(len(x_coords)) * np.nanmin(Z) - 5
                
                fig.add_trace(go.Scatter3d(
                    x=list(x_coords),
                    y=list(y_coords),
                    z=list(z_coords),
                    mode='lines',
                    line=dict(color='red', width=4),
                    name='Límite Parcela'
                ))
        
        # Actualizar layout
        fig.update_layout(
            title='Modelo 3D del Terreno',
            scene=dict(
                xaxis_title='Longitud',
                yaxis_title='Latitud',
                zaxis_title='Elevación (m)',
                aspectratio=dict(x=2, y=1, z=0.5),
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            height=600,
            margin=dict(l=0, r=0, b=0, t=40)
        )
        
        return fig
        
    except Exception as e:
        st.warning(f"No se pudo crear visualización 3D: {e}")
        return None

# ===== FUNCIONES DE EXPORTACIÓN MEJORADAS =====
def exportar_a_geojson(gdf, nombre_base="parcela"):
    """Exporta GeoDataFrame a GeoJSON"""
    try:
        gdf = validar_y_corregir_crs(gdf)
        geojson_data = gdf.to_json()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"{nombre_base}_{timestamp}.geojson"
        return geojson_data, nombre_archivo
    except Exception as e:
        st.error(f"❌ Error exportando GeoJSON: {str(e)}")
        return None, None

def exportar_curvas_geojson(curvas, elevaciones):
    """Exporta curvas de nivel a GeoJSON"""
    try:
        features = []
        for i, (curva, elev) in enumerate(zip(curvas, elevaciones)):
            if curva.geom_type == 'LineString':
                coords = list(curva.coords)
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[c[0], c[1]] for c in coords]
                    },
                    "properties": {
                        "id": i+1,
                        "elevacion": float(elev),
                        "tipo": "curva_nivel"
                    }
                }
                features.append(feature)
        
        feature_collection = {
            "type": "FeatureCollection",
            "features": features
        }
        
        return json.dumps(feature_collection, indent=2)
        
    except Exception as e:
        st.error(f"❌ Error exportando curvas: {str(e)}")
        return None

def generar_resumen_ejecutivo(gdf_analizado, analisis_tipo, cultivo, area_total):
    """Genera un resumen ejecutivo para el reporte"""
    try:
        resumen = f"# RESUMEN EJECUTIVO\n\n"
        resumen += f"**Fecha:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        resumen += f"**Cultivo:** {cultivo}\n"
        resumen += f"**Tipo de Análisis:** {analisis_tipo}\n"
        resumen += f"**Área Total:** {area_total:.2f} ha\n"
        resumen += f"**Número de Zonas:** {len(gdf_analizado)}\n\n"
        
        if analisis_tipo == "FERTILIDAD ACTUAL":
            if 'npk_actual' in gdf_analizado.columns:
                npk_prom = gdf_analizado['npk_actual'].mean()
                if npk_prom < 0.3:
                    estado = "MUY BAJA"
                    recomendacion = "Se requiere intervención inmediata con fertilización balanceada."
                elif npk_prom < 0.5:
                    estado = "BAJA"
                    recomendacion = "Recomendada fertilización según análisis específico."
                elif npk_prom < 0.7:
                    estado = "ADECUADA"
                    recomendacion = "Mantener prácticas actuales de manejo."
                else:
                    estado = "ÓPTIMA"
                    recomendacion = "Excelente condición, continuar con manejo actual."
                
                resumen += f"**Estado de Fertilidad:** {estado} (Índice NPK: {npk_prom:.3f})\n"
                resumen += f"**Recomendación Principal:** {recomendacion}\n\n"
        
        elif analisis_tipo == "ANÁLISIS DE TEXTURA":
            if 'textura_suelo' in gdf_analizado.columns:
                textura_pred = gdf_analizado['textura_suelo'].mode()[0] if len(gdf_analizado) > 0 else "N/D"
                resumen += f"**Textura Predominante:** {textura_pred}\n"
                resumen += f"**Composición Promedio:** Arena: {gdf_analizado['arena'].mean():.1f}%, "
                resumen += f"Limo: {gdf_analizado['limo'].mean():.1f}%, "
                resumen += f"Arcilla: {gdf_analizado['arcilla'].mean():.1f}%\n\n"
        
        elif analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
            resumen += "**Análisis Topográfico Completo:**\n"
            resumen += "- Generación de Modelo Digital de Elevación\n"
            resumen += "- Cálculo de pendientes y curvas de nivel\n"
            resumen += "- Análisis de riesgo de erosión\n"
            resumen += "- Perfiles topográficos y cálculo de volumen\n\n"
        
        resumen += "**Metodología:** Análisis basado en datos satelitales y modelos predictivos.\n"
        resumen += "**Precisión:** Los resultados deben validarse con análisis de suelo de laboratorio.\n"
        
        return resumen
        
    except Exception as e:
        return f"# RESUMEN EJECUTIVO\n\nError generando resumen: {str(e)}"

def generar_grafico_estadisticas_embebido(gdf_analizado, analisis_tipo, cultivo):
    """Genera gráficos estadísticos para embebir en reportes"""
    try:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        
        if analisis_tipo == "FERTILIDAD ACTUAL" and 'npk_actual' in gdf_analizado.columns:
            # Histograma de NPK
            axes[0].hist(gdf_analizado['npk_actual'], bins=20, edgecolor='black', alpha=0.7)
            axes[0].axvline(gdf_analizado['npk_actual'].mean(), color='red', linestyle='--', label='Promedio')
            axes[0].set_xlabel('Índice NPK')
            axes[0].set_ylabel('Frecuencia')
            axes[0].set_title('Distribución de Fertilidad')
            axes[0].legend()
            axes[0].grid(True, alpha=0.3)
            
            # Boxplot por zonas
            sample_zones = gdf_analizado.head(10) if len(gdf_analizado) > 10 else gdf_analizado
            axes[1].bar(range(len(sample_zones)), sample_zones['npk_actual'])
            axes[1].set_xlabel('Zona')
            axes[1].set_ylabel('Índice NPK')
            axes[1].set_title('Fertilidad por Zona (Top 10)')
            axes[1].set_xticks(range(len(sample_zones)))
            axes[1].set_xticklabels([f"Z{int(i)}" for i in sample_zones['id_zona']], rotation=45)
            axes[1].grid(True, alpha=0.3)
        
        elif analisis_tipo == "ANÁLISIS DE TEXTURA":
            # Gráfico de composición
            composicion = [gdf_analizado['arena'].mean(), 
                          gdf_analizado['limo'].mean(), 
                          gdf_analizado['arcilla'].mean()]
            labels = ['Arena', 'Limo', 'Arcilla']
            colors = ['#d8b365', '#f6e8c3', '#01665e']
            axes[0].pie(composicion, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            axes[0].set_title('Composición Promedio del Suelo')
            
            # Distribución de texturas
            textura_counts = gdf_analizado['textura_suelo'].value_counts()
            axes[1].bar(textura_counts.index, textura_counts.values, color='skyblue')
            axes[1].set_xlabel('Textura')
            axes[1].set_ylabel('Número de Zonas')
            axes[1].set_title('Distribución de Texturas')
            axes[1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Convertir a bytes
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        return buf
        
    except Exception as e:
        st.warning(f"No se pudo generar gráfico: {e}")
        return None

def generar_reporte_pdf_completo(gdf_analizado, cultivo, analisis_tipo, area_total,
                                nutriente=None, satelite=None, indice=None,
                                mapa_buffer=None, estadisticas=None, recomendaciones=None,
                                grafico_buffer=None, resumen_ejecutivo=None,
                                datos_curvas=None, datos_volumen=None):
    """Genera un reporte PDF completo con todas las mejoras"""
    try:
        pdf = ImprovedPDF()
        pdf.add_page()
        
        # Encabezado con logo
        pdf.set_font('Arial', 'B', 20)
        pdf.cell(0, 15, 'ANALIZADOR MULTI-CULTIVO PRO', 0, 1, 'C')
        pdf.set_font('Arial', 'I', 12)
        pdf.cell(0, 10, 'Reporte de Análisis Agrícola', 0, 1, 'C')
        pdf.ln(10)
        
        # Resumen Ejecutivo
        pdf.add_color_section('RESUMEN EJECUTIVO', '#1E88E5')
        if resumen_ejecutivo:
            pdf.set_font('Arial', '', 11)
            for linea in resumen_ejecutivo.split('\n'):
                if linea.startswith('# '):
                    pdf.set_font('Arial', 'B', 14)
                    pdf.cell(0, 8, linea[2:], 0, 1)
                    pdf.set_font('Arial', '', 11)
                elif linea.startswith('**'):
                    # Texto en negrita
                    partes = linea.split('**')
                    for i, parte in enumerate(partes):
                        if i % 2 == 1:  # Parte entre **
                            pdf.set_font('Arial', 'B', 11)
                            pdf.cell(pdf.get_string_width(parte) + 1, 8, parte)
                        else:
                            pdf.set_font('Arial', '', 11)
                            pdf.cell(pdf.get_string_width(parte) + 1, 8, parte)
                    pdf.ln(8)
                else:
                    pdf.multi_cell(0, 8, linea)
        pdf.ln(10)
        
        # Información General
        pdf.add_color_section('INFORMACIÓN GENERAL', '#43A047')
        pdf.set_font('Arial', '', 11)
        
        info_data = [
            ("Cultivo", cultivo),
            ("Área Total", f"{area_total:.2f} ha"),
            ("Zonas Analizadas", str(len(gdf_analizado))),
            ("Tipo de Análisis", analisis_tipo),
            ("Fecha", datetime.now().strftime("%d/%m/%Y %H:%M"))
        ]
        
        if satelite:
            info_data.append(("Satélite", satelite))
        if indice:
            info_data.append(("Índice", indice))
        if nutriente:
            info_data.append(("Nutriente", nutriente))
        
        # Crear tabla de información
        col_width = 80
        for label, value in info_data:
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(col_width, 8, f"{label}:")
            pdf.set_font('Arial', '', 11)
            pdf.cell(0, 8, str(value))
            pdf.ln()
        
        pdf.ln(10)
        
        # Estadísticas Principales
        if estadisticas and len(estadisticas) > 0:
            pdf.add_color_section('ESTADÍSTICAS PRINCIPALES', '#FF9800')
            pdf.set_font('Arial', '', 11)
            
            for key, value in estadisticas.items():
                pdf.cell(0, 8, f"• {key}: {value}", 0, 1)
            
            pdf.ln(5)
        
        # Gráfico Estadístico
        if grafico_buffer:
            try:
                pdf.add_color_section('GRÁFICOS ESTADÍSTICOS', '#9C27B0')
                temp_img_path = "temp_grafico.png"
                with open(temp_img_path, "wb") as f:
                    f.write(grafico_buffer.getvalue())
                pdf.image(temp_img_path, x=10, w=190)
                pdf.ln(5)
                if os.path.exists(temp_img_path):
                    os.remove(temp_img_path)
            except Exception as e:
                pdf.cell(0, 8, f"Error al incluir gráfico: {str(e)[:50]}", 0, 1)
        
        # Mapa de Resultados
        if mapa_buffer:
            try:
                pdf.add_color_section('MAPA DE RESULTADOS', '#E91E63')
                temp_img_path = "temp_mapa.png"
                with open(temp_img_path, "wb") as f:
                    f.write(mapa_buffer.getvalue())
                pdf.image(temp_img_path, x=10, w=190)
                pdf.ln(5)
                if os.path.exists(temp_img_path):
                    os.remove(temp_img_path)
            except Exception as e:
                pdf.cell(0, 8, f"Error al incluir mapa: {str(e)[:50]}", 0, 1)
        
        # Datos de Curvas de Nivel (si aplica)
        if datos_curvas and analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
            pdf.add_color_section('DATOS TOPOGRÁFICOS', '#009688')
            pdf.set_font('Arial', '', 10)
            
            if 'estadisticas_pendiente' in datos_curvas:
                stats = datos_curvas['estadisticas_pendiente']
                pdf.cell(0, 8, f"• Pendiente Promedio: {stats.get('promedio', 0):.1f}%", 0, 1)
                pdf.cell(0, 8, f"• Pendiente Máxima: {stats.get('max', 0):.1f}%", 0, 1)
                pdf.cell(0, 8, f"• Pendiente Mínima: {stats.get('min', 0):.1f}%", 0, 1)
            
            if datos_volumen:
                pdf.cell(0, 8, f"• Volumen Excavación: {datos_volumen[0]:,.0f} m³", 0, 1)
                pdf.cell(0, 8, f"• Volumen Relleno: {datos_volumen[1]:,.0f} m³", 0, 1)
                pdf.cell(0, 8, f"• Área Total: {datos_volumen[2]:,.0f} m²", 0, 1)
            
            pdf.ln(5)
        
        # Tabla de Datos (resumen)
        pdf.add_color_section('RESUMEN DE ZONAS', '#795548')
        pdf.set_font('Arial', '', 9)
        
        if gdf_analizado is not None and not gdf_analizado.empty:
            # Seleccionar columnas relevantes
            columnas_mostrar = ['id_zona', 'area_ha']
            if 'npk_actual' in gdf_analizado.columns:
                columnas_mostrar.append('npk_actual')
            if 'valor_recomendado' in gdf_analizado.columns:
                columnas_mostrar.append('valor_recomendado')
            if 'textura_suelo' in gdf_analizado.columns:
                columnas_mostrar.append('textura_suelo')
            
            columnas_mostrar = [col for col in columnas_mostrar if col in gdf_analizado.columns]
            
            if columnas_mostrar:
                # Cabecera de tabla
                col_widths = [190 // len(columnas_mostrar)] * len(columnas_mostrar)
                
                # Encabezados
                pdf.set_font('Arial', 'B', 9)
                headers = [col.replace('_', ' ').upper() for col in columnas_mostrar]
                for i, header in enumerate(headers):
                    pdf.cell(col_widths[i], 8, header[:15], border=1)
                pdf.ln()
                
                # Datos (primeras 15 filas)
                pdf.set_font('Arial', '', 9)
                for _, row in gdf_analizado.head(15).iterrows():
                    for i, col in enumerate(columnas_mostrar):
                        if col in gdf_analizado.columns:
                            valor = row[col]
                            if isinstance(valor, float):
                                if col in ['npk_actual']:
                                    texto = f"{valor:.3f}"
                                elif col == 'area_ha':
                                    texto = f"{valor:.2f}"
                                else:
                                    texto = f"{valor:.1f}"
                            else:
                                texto = str(valor)[:12]
                            pdf.cell(col_widths[i], 8, texto, border=1)
                    pdf.ln()
                
                pdf.ln(5)
        
        # Recomendaciones
        if recomendaciones and len(recomendaciones) > 0:
            pdf.add_color_section('RECOMENDACIONES', '#F44336')
            pdf.set_font('Arial', '', 11)
            
            for i, rec in enumerate(recomendaciones, 1):
                pdf.multi_cell(0, 8, f"{i}. {rec}")
                pdf.ln(2)
        
        # Metadatos Técnicos
        pdf.add_color_section('METADATOS TÉCNICOS', '#607D8B')
        pdf.set_font('Arial', '', 9)
        
        metadatos = [
            ("Generado por", "Analizador Multi-Cultivo PRO v3.0"),
            ("Sistema de coordenadas", "EPSG:4326 (WGS84)"),
            ("Método de análisis", "Satelital + Modelos Predictivos"),
            ("Fecha generación", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ("Contacto", "soporte@agriculturadeprecision.com")
        ]
        
        for label, value in metadatos:
            pdf.cell(0, 6, f"• {label}: {value}", 0, 1)
        
        # Footer personalizado
        pdf.set_y(-20)
        pdf.set_font('Arial', 'I', 8)
        pdf.cell(0, 10, "© 2024 Agricultura de Precisión - Todos los derechos reservados", 0, 0, 'C')
        
        # Generar PDF
        pdf_output = BytesIO()
        pdf_output.write(pdf.output(dest='S').encode('latin-1'))
        pdf_output.seek(0)
        
        return pdf_output
        
    except Exception as e:
        st.error(f"❌ Error generando PDF: {str(e)}")
        import traceback
        st.error(f"Detalle: {traceback.format_exc()}")
        return None

def generar_reporte_docx_completo(gdf_analizado, cultivo, analisis_tipo, area_total,
                                 nutriente=None, satelite=None, indice=None,
                                 mapa_buffer=None, estadisticas=None, recomendaciones=None,
                                 grafico_buffer=None, resumen_ejecutivo=None):
    """Genera un reporte DOCX completo"""
    try:
        doc = Document()
        
        # Configuración de página
        section = doc.sections[0]
        section.left_margin = Cm(2)
        section.right_margin = Cm(2)
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        
        # Título
        title = doc.add_heading('ANALIZADOR MULTI-CULTIVO PRO', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        subtitle = doc.add_heading('Reporte de Análisis Agrícola', 1)
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Fecha
        fecha_para = doc.add_paragraph()
        fecha_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fecha_run = fecha_para.add_run(datetime.now().strftime('%d/%m/%Y %H:%M'))
        fecha_run.italic = True
        
        doc.add_paragraph()
        
        # Resumen Ejecutivo
        doc.add_heading('RESUMEN EJECUTIVO', level=1)
        if resumen_ejecutivo:
            for linea in resumen_ejecutivo.split('\n'):
                if linea.strip():
                    if linea.startswith('# '):
                        heading = doc.add_heading(linea[2:], level=2)
                    elif linea.startswith('**'):
                        # Texto en negrita
                        para = doc.add_paragraph()
                        partes = linea.split('**')
                        for i, parte in enumerate(partes):
                            if i % 2 == 1:  # Parte entre **
                                run = para.add_run(parte)
                                run.bold = True
                            else:
                                para.add_run(parte)
                    else:
                        doc.add_paragraph(linea)
        
        doc.add_paragraph()
        
        # Información General
        doc.add_heading('INFORMACIÓN GENERAL', level=1)
        info_table = doc.add_table(rows=1, cols=2)
        info_table.style = 'Light Shading Accent 1'
        
        info_data = [
            ("Cultivo", cultivo),
            ("Área Total", f"{area_total:.2f} ha"),
            ("Zonas Analizadas", str(len(gdf_analizado))),
            ("Tipo de Análisis", analisis_tipo)
        ]
        
        if satelite:
            info_data.append(("Satélite", satelite))
        if indice:
            info_data.append(("Índice", indice))
        if nutriente:
            info_data.append(("Nutriente", nutriente))
        
        for label, value in info_data:
            row = info_table.add_row()
            row.cells[0].text = label
            row.cells[1].text = str(value)
        
        doc.add_paragraph()
        
        # Estadísticas
        if estadisticas and len(estadisticas) > 0:
            doc.add_heading('ESTADÍSTICAS PRINCIPALES', level=1)
            for key, value in estadisticas.items():
                p = doc.add_paragraph(style='List Bullet')
                run_key = p.add_run(f"{key}: ")
                run_key.bold = True
                p.add_run(str(value))
        
        # Gráfico
        if grafico_buffer:
            try:
                doc.add_heading('GRÁFICOS ESTADÍSTICOS', level=1)
                temp_img_path = "temp_grafico_docx.png"
                with open(temp_img_path, "wb") as f:
                    f.write(grafico_buffer.getvalue())
                doc.add_picture(temp_img_path, width=Inches(6.0))
                doc.add_paragraph()
                if os.path.exists(temp_img_path):
                    os.remove(temp_img_path)
            except Exception as e:
                doc.add_paragraph(f'Error al incluir gráfico: {str(e)[:50]}')
        
        # Mapa
        if mapa_buffer:
            try:
                doc.add_heading('MAPA DE RESULTADOS', level=1)
                temp_img_path = "temp_mapa_docx.png"
                with open(temp_img_path, "wb") as f:
                    f.write(mapa_buffer.getvalue())
                doc.add_picture(temp_img_path, width=Inches(6.0))
                doc.add_paragraph()
                if os.path.exists(temp_img_path):
                    os.remove(temp_img_path)
            except Exception as e:
                doc.add_paragraph(f'Error al incluir mapa: {str(e)[:50]}')
        
        # Tabla de datos
        doc.add_heading('RESUMEN DE ZONAS', level=1)
        if gdf_analizado is not None and not gdf_analizado.empty:
            columnas_mostrar = ['id_zona', 'area_ha']
            if 'npk_actual' in gdf_analizado.columns:
                columnas_mostrar.append('npk_actual')
            if 'valor_recomendado' in gdf_analizado.columns:
                columnas_mostrar.append('valor_recomendado')
            if 'textura_suelo' in gdf_analizado.columns:
                columnas_mostrar.append('textura_suelo')
            
            columnas_mostrar = [col for col in columnas_mostrar if col in gdf_analizado.columns]
            
            if columnas_mostrar:
                tabla = doc.add_table(rows=1, cols=len(columnas_mostrar))
                tabla.style = 'Table Grid'
                
                # Encabezados
                for i, col in enumerate(columnas_mostrar):
                    tabla.cell(0, i).text = col.replace('_', ' ').upper()
                
                # Datos
                for idx, row in gdf_analizado.head(10).iterrows():
                    row_cells = tabla.add_row().cells
                    for i, col in enumerate(columnas_mostrar):
                        if col in gdf_analizado.columns:
                            valor = row[col]
                            if isinstance(valor, float):
                                if col in ['npk_actual']:
                                    row_cells[i].text = f"{valor:.3f}"
                                else:
                                    row_cells[i].text = f"{valor:.2f}"
                            else:
                                row_cells[i].text = str(valor)
        
        doc.add_paragraph()
        
        # Recomendaciones
        if recomendaciones and len(recomendaciones) > 0:
            doc.add_heading('RECOMENDACIONES', level=1)
            for rec in recomendaciones:
                p = doc.add_paragraph(style='List Bullet')
                p.add_run(rec)
        
        # Metadatos
        doc.add_heading('METADATOS TÉCNICOS', level=1)
        metadatos = [
            ("Generado por", "Analizador Multi-Cultivo PRO"),
            ("Versión", "3.0"),
            ("Fecha generación", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ("Sistema de coordenadas", "EPSG:4326 (WGS84)")
        ]
        
        for key, value in metadatos:
            p = doc.add_paragraph()
            run_key = p.add_run(f"{key}: ")
            run_key.bold = True
            p.add_run(value)
        
        # Guardar documento
        docx_output = BytesIO()
        doc.save(docx_output)
        docx_output.seek(0)
        
        return docx_output
        
    except Exception as e:
        st.error(f"❌ Error generando DOCX: {str(e)}")
        return None

# ===== FUNCIÓN PRINCIPAL DE ANÁLISIS =====
def ejecutar_analisis_completo(gdf, analisis_tipo, cultivo, n_divisiones, **kwargs):
    """Ejecuta el análisis completo según el tipo seleccionado"""
    resultados = {
        'exitoso': False,
        'gdf_analizado': None,
        'area_total': 0,
        'datos_adicionales': {},
        'mapa_buffer': None,
        'grafico_buffer': None
    }
    
    try:
        # Validar y corregir CRS
        gdf = validar_y_corregir_crs(gdf)
        
        # Calcular área total
        area_total = calcular_superficie(gdf)
        resultados['area_total'] = area_total
        
        # Dividir parcela en zonas
        gdf_dividido = dividir_parcela_en_zonas(gdf, n_divisiones)
        
        if analisis_tipo == "FERTILIDAD ACTUAL":
            # Análisis de fertilidad actual
            satelite = kwargs.get('satelite', 'SENTINEL-2')
            indice = kwargs.get('indice', 'NDVI')
            fecha_inicio = kwargs.get('fecha_inicio', datetime.now() - timedelta(days=30))
            fecha_fin = kwargs.get('fecha_fin', datetime.now())
            
            # Descargar datos satelitales
            if satelite == "SENTINEL-2":
                datos_satelitales = descargar_datos_sentinel2(gdf, fecha_inicio, fecha_fin, indice)
            elif satelite == "LANDSAT-8":
                datos_satelitales = descargar_datos_landsat8(gdf, fecha_inicio, fecha_fin, indice)
            else:
                datos_satelitales = {'valor_promedio': 0.65, 'fuente': 'Simulación'}
            
            # Calcular índices
            indices = calcular_indices_satelitales(gdf_dividido, cultivo, datos_satelitales)
            
            # Crear GeoDataFrame con resultados
            gdf_analizado = gdf_dividido.copy()
            for idx, indice_data in enumerate(indices):
                for key, value in indice_data.items():
                    gdf_analizado.loc[gdf_analizado.index[idx], key] = value
            
            # Calcular áreas
            areas_ha = []
            for idx, row in gdf_analizado.iterrows():
                area_gdf = gpd.GeoDataFrame({'geometry': [row.geometry]}, crs=gdf_analizado.crs)
                areas_ha.append(float(calcular_superficie(area_gdf)))
            gdf_analizado['area_ha'] = areas_ha
            
            resultados['gdf_analizado'] = gdf_analizado
            resultados['exitoso'] = True
            
        elif analisis_tipo == "RECOMENDACIONES NPK":
            # Análisis similar a fertilidad pero con recomendaciones
            nutriente = kwargs.get('nutriente', 'NITRÓGENO')
            satelite = kwargs.get('satelite', 'SENTINEL-2')
            indice = kwargs.get('indice', 'NDVI')
            
            # Obtener datos
            if satelite == "SENTINEL-2":
                datos_satelitales = descargar_datos_sentinel2(gdf, None, None, indice)
            else:
                datos_satelitales = {'valor_promedio': 0.65, 'fuente': 'Simulación'}
            
            # Calcular índices
            indices = calcular_indices_satelitales(gdf_dividido, cultivo, datos_satelitales)
            
            # Calcular recomendaciones
            recomendaciones = calcular_recomendaciones_npk(indices, nutriente, cultivo)
            
            # Crear GeoDataFrame
            gdf_analizado = gdf_dividido.copy()
            for idx, indice_data in enumerate(indices):
                for key, value in indice_data.items():
                    gdf_analizado.loc[gdf_analizado.index[idx], key] = value
            gdf_analizado['valor_recomendado'] = recomendaciones
            
            # Calcular áreas
            areas_ha = [float(calcular_superficie(gpd.GeoDataFrame({'geometry': [row.geometry]}, crs=gdf_analizado.crs))) 
                       for _, row in gdf_analizado.iterrows()]
            gdf_analizado['area_ha'] = areas_ha
            
            resultados['gdf_analizado'] = gdf_analizado
            resultados['exitoso'] = True
            
        elif analisis_tipo == "ANÁLISIS DE TEXTURA":
            # Análisis de textura del suelo
            gdf_analizado = analizar_textura_suelo(gdf_dividido, cultivo)
            resultados['gdf_analizado'] = gdf_analizado
            resultados['exitoso'] = True
            
        elif analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
            # Análisis topográfico
            intervalo_curvas = kwargs.get('intervalo_curvas', 5.0)
            resolucion_dem = kwargs.get('resolucion_dem', 10.0)
            generar_perfiles = kwargs.get('generar_perfiles', True)
            calcular_volumen = kwargs.get('calcular_volumen', False)
            
            # Generar DEM
            X, Y, Z, bounds, mask = generar_dem_sintetico(gdf, resolucion_dem)
            
            # Calcular pendientes
            pendiente_grid = calcular_pendiente(X, Y, Z, resolucion_dem)
            
            # Generar curvas de nivel
            curvas, elevaciones = generar_curvas_nivel(X, Y, Z, intervalo_curvas, gdf)
            
            # Calcular estadísticas de pendiente
            pendiente_flat = pendiente_grid.flatten()
            pendiente_flat = pendiente_flat[~np.isnan(pendiente_flat)]
            
            estadisticas_pendiente = {
                'promedio': float(np.mean(pendiente_flat)) if len(pendiente_flat) > 0 else 0,
                'min': float(np.min(pendiente_flat)) if len(pendiente_flat) > 0 else 0,
                'max': float(np.max(pendiente_flat)) if len(pendiente_flat) > 0 else 0,
                'std': float(np.std(pendiente_flat)) if len(pendiente_flat) > 0 else 0
            }
            
            # Calcular volumen si se solicita
            datos_volumen = None
            if calcular_volumen:
                elevacion_ref = kwargs.get('elevacion_referencia', np.nanmean(Z))
                vol_exc, vol_rell, area_total_m2 = calcular_volumen_tierra(X, Y, Z, elevacion_ref)
                datos_volumen = (vol_exc, vol_rell, area_total_m2)
            
            # Guardar resultados adicionales
            resultados['datos_adicionales'] = {
                'X': X,
                'Y': Y,
                'Z': Z,
                'pendiente_grid': pendiente_grid,
                'curvas': curvas,
                'elevaciones': elevaciones,
                'estadisticas_pendiente': estadisticas_pendiente,
                'datos_volumen': datos_volumen,
                'bounds': bounds,
                'mask': mask
            }
            
            resultados['gdf_analizado'] = gdf_dividido
            resultados['exitoso'] = True
            
        elif analisis_tipo == "BATCH PROCESSING":
            # Procesamiento por lotes
            st.info("🔄 Procesamiento por lotes en desarrollo...")
            resultados['gdf_analizado'] = gdf_dividido
            resultados['exitoso'] = True
            
        elif analisis_tipo == "COMPARATIVA HISTÓRICA":
            # Comparativa histórica
            st.info("📊 Comparativa histórica en desarrollo...")
            resultados['gdf_analizado'] = gdf_dividido
            resultados['exitoso'] = True
            
        else:
            st.error(f"❌ Tipo de análisis no soportado: {analisis_tipo}")
        
        return resultados
        
    except Exception as e:
        st.error(f"❌ Error en análisis: {str(e)}")
        import traceback
        st.error(f"Detalle: {traceback.format_exc()}")
        return resultados

# ===== INTERFAZ PRINCIPAL =====
def main():
    # Estado de la aplicación
    if 'resultados_guardados' not in st.session_state:
        st.session_state['resultados_guardados'] = None
    
    if 'analisis_ejecutado' not in st.session_state:
        st.session_state['analisis_ejecutado'] = False
    
    # Verificar si hay archivos subidos
    uploaded_file = None
    uploaded_files = []
    
    if 'uploaded_files' in locals() and uploaded_files:
        # Modo batch processing
        st.info(f"📦 Modo Batch: {len(uploaded_files)} archivos cargados")
        uploaded_file = uploaded_files[0]  # Procesar el primero por ahora
    elif 'uploaded_file' in locals() and uploaded_file:
        # Modo normal
        pass
    else:
        uploaded_file = None
    
    if uploaded_file:
        with st.spinner("🔄 Cargando parcela..."):
            try:
                gdf = cargar_archivo_parcela(uploaded_file)
                
                if gdf is not None:
                    st.success(f"✅ **Parcela cargada exitosamente**")
                    
                    # Mostrar información básica
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown('<div class="info-box">', unsafe_allow_html=True)
                        st.subheader("📊 INFORMACIÓN DE LA PARCELA")
                        area_total = calcular_superficie(gdf)
                        st.write(f"**Polígonos:** {len(gdf)}")
                        st.write(f"**Área total:** {area_total:.2f} ha")
                        st.write(f"**CRS:** {gdf.crs}")
                        st.write(f"**Formato:** {uploaded_file.name.split('.')[-1].upper()}")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Vista previa
                        fig, ax = plt.subplots(figsize=(8, 6))
                        gdf.plot(ax=ax, color='lightgreen', edgecolor='darkgreen', alpha=0.7)
                        ax.set_title("Vista Previa de la Parcela")
                        ax.set_xlabel("Longitud")
                        ax.set_ylabel("Latitud")
                        ax.grid(True, alpha=0.3)
                        st.pyplot(fig)
                    
                    with col2:
                        st.markdown('<div class="info-box">', unsafe_allow_html=True)
                        st.subheader("🎯 CONFIGURACIÓN DEL ANÁLISIS")
                        st.write(f"**Cultivo:** {ICONOS_CULTIVOS[cultivo]} {cultivo}")
                        st.write(f"**Análisis:** {analisis_tipo}")
                        st.write(f"**Zonas:** {n_divisiones}")
                        
                        if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"]:
                            st.write(f"**Satélite:** {SATELITES_DISPONIBLES[satelite_seleccionado]['nombre']}")
                            if analisis_tipo == "RECOMENDACIONES NPK":
                                st.write(f"**Nutriente:** {nutriente}")
                        
                        elif analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
                            st.write(f"**Intervalo curvas:** {intervalo_curvas} m")
                            st.write(f"**Resolución DEM:** {resolucion_dem} m")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Botón para ejecutar análisis
                    st.markdown("---")
                    if st.button("🚀 EJECUTAR ANÁLISIS COMPLETO", type="primary", use_container_width=True):
                        with st.spinner("🔄 Ejecutando análisis..."):
                            # Preparar parámetros según tipo de análisis
                            kwargs = {}
                            
                            if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"]:
                                kwargs['satelite'] = satelite_seleccionado
                                kwargs['indice'] = 'NDVI'  # Podría hacerse configurable
                                
                                if 'nutriente' in locals():
                                    kwargs['nutriente'] = nutriente
                            
                            elif analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
                                kwargs['intervalo_curvas'] = intervalo_curvas
                                kwargs['resolucion_dem'] = resolucion_dem
                                kwargs['generar_perfiles'] = True
                                kwargs['calcular_volumen'] = True
                            
                            # Ejecutar análisis
                            resultados = ejecutar_analisis_completo(
                                gdf, analisis_tipo, cultivo, n_divisiones, **kwargs
                            )
                            
                            if resultados['exitoso']:
                                st.session_state['resultados_guardados'] = resultados
                                st.session_state['analisis_ejecutado'] = True
                                st.session_state['cultivo_actual'] = cultivo
                                st.session_state['analisis_tipo_actual'] = analisis_tipo
                                st.session_state['area_total_actual'] = resultados['area_total']
                                st.session_state['gdf_original'] = gdf
                                
                                st.success("✅ **Análisis completado exitosamente!**")
                                
                                # Mostrar resultados según tipo de análisis
                                mostrar_resultados_por_tipo(resultados, cultivo, analisis_tipo, gdf)
                            else:
                                st.error("❌ Error en el análisis")
                
                else:
                    st.error("❌ No se pudo cargar el archivo")
                    
            except Exception as e:
                st.error(f"❌ Error procesando archivo: {str(e)}")
                import traceback
                st.error(f"Detalle: {traceback.format_exc()}")
    
    else:
        st.info("📁 **Sube un archivo de parcela para comenzar el análisis**")
        st.markdown("""
        **Formatos aceptados:**
        - 🗺️ Shapefile (.zip) - Debe incluir .shp, .shx, .dbf
        - 🌐 KML (.kml) - Formato Google Earth
        - 📦 KMZ (.kmz) - KML comprimido
        
        **Recomendaciones:**
        - Usa coordenadas en EPSG:4326 (WGS84)
        - El área recomendada es entre 1 y 1000 hectáreas
        - Los archivos deben contener polígonos
        """)
    
    # Mostrar resultados guardados si existen
    if st.session_state['resultados_guardados'] is not None:
        mostrar_panel_exportacion()
    
    # Información sobre metodología
    with st.expander("📚 INFORMACIÓN SOBRE LA METODOLOGÍA"):
        st.markdown("""
        **🌱 SISTEMA DE ANÁLISIS MULTI-CULTIVO PRO**
        
        **🛰️ TECNOLOGÍAS UTILIZADAS:**
        - **Sentinel-2:** Imágenes de 10m de resolución
        - **Landsat-8:** Datos históricos desde 2013
        - **Modelos Predictivos:** Algoritmos de machine learning
        - **Sistemas de Información Geográfica:** Análisis espacial avanzado
        
        **📊 PARÁMETROS ANALIZADOS:**
        1. **Fertilidad del Suelo:** NPK, materia orgánica, humedad
        2. **Textura del Suelo:** Composición arena-limo-arcilla
        3. **Topografía:** Pendientes, curvas de nivel, modelos 3D
        4. **Vegetación:** Índices NDVI, NDRE, EVI, etc.
        
        **🎯 APLICACIONES:**
        - Agricultura de precisión
        - Manejo variable de insumos
        - Diseño de sistemas de riego
        - Planificación de conservación de suelos
        - Análisis de riesgos de erosión
        
        **🔬 VALIDACIÓN:**
        - Los resultados satelitales deben validarse con análisis de laboratorio
        - Error estimado: ±15% para índices de vegetación
        - Resolución espacial: 10-30m según satélite
        
        **📞 SOPORTE:**
        Para consultas técnicas: soporte@agriculturadeprecision.com
        """)

def mostrar_resultados_por_tipo(resultados, cultivo, analisis_tipo, gdf_original):
    """Muestra resultados según el tipo de análisis"""
    
    if analisis_tipo == "FERTILIDAD ACTUAL":
        mostrar_resultados_fertilidad(resultados, cultivo)
    
    elif analisis_tipo == "RECOMENDACIONES NPK":
        mostrar_resultados_npk(resultados, cultivo, nutriente)
    
    elif analisis_tipo == "ANÁLISIS DE TEXTURA":
        mostrar_resultados_textura(resultados, cultivo)
    
    elif analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
        mostrar_resultados_curvas_nivel(resultados, cultivo, gdf_original)

def mostrar_resultados_fertilidad(resultados, cultivo):
    """Muestra resultados de fertilidad actual"""
    gdf_analizado = resultados['gdf_analizado']
    
    st.markdown("---")
    st.subheader(f"📊 RESULTADOS - FERTILIDAD ACTUAL ({cultivo})")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Zonas Analizadas", len(gdf_analizado))
    
    with col2:
        st.metric("Área Total", f"{resultados['area_total']:.2f} ha")
    
    with col3:
        if 'npk_actual' in gdf_analizado.columns:
            npk_prom = gdf_analizado['npk_actual'].mean()
            st.metric("Índice NPK Promedio", f"{npk_prom:.3f}")
    
    with col4:
        if 'npk_actual' in gdf_analizado.columns and gdf_analizado['npk_actual'].mean() > 0:
            coef_var = (gdf_analizado['npk_actual'].std() / gdf_analizado['npk_actual'].mean() * 100)
            st.metric("Coef. Variación", f"{coef_var:.1f}%")
    
    # Crear mapa
    st.subheader("🗺️ MAPA DE FERTILIDAD")
    try:
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        # Normalizar valores para colormap
        valores = gdf_analizado['npk_actual']
        vmin, vmax = valores.min(), valores.max()
        norm = plt.Normalize(vmin, vmax)
        cmap = LinearSegmentedColormap.from_list('fertilidad', PALETAS_GEE['FERTILIDAD'])
        
        for idx, row in gdf_analizado.iterrows():
            valor_norm = norm(row['npk_actual'])
            color = cmap(valor_norm)
            gdf_analizado.iloc[[idx]].plot(ax=ax, color=color, edgecolor='black', linewidth=1)
            
            # Etiqueta con valor
            centroid = row.geometry.centroid
            ax.annotate(f"{row['npk_actual']:.2f}", 
                       (centroid.x, centroid.y),
                       fontsize=8, ha='center', va='center',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        ax.set_title(f'Mapa de Fertilidad - {cultivo}', fontsize=14, fontweight='bold')
        ax.set_xlabel('Longitud')
        ax.set_ylabel('Latitud')
        
        # Barra de colores
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax)
        cbar.set_label('Índice NPK', fontsize=12)
        
        plt.tight_layout()
        
        # Guardar mapa en buffer
        mapa_buffer = io.BytesIO()
        plt.savefig(mapa_buffer, format='png', dpi=150, bbox_inches='tight')
        mapa_buffer.seek(0)
        st.image(mapa_buffer, use_container_width=True)
        
        # Guardar en session state para exportación
        st.session_state['mapa_buffer'] = mapa_buffer
        
        plt.close()
        
    except Exception as e:
        st.error(f"Error creando mapa: {str(e)}")
    
    # Tabla de datos
    st.subheader("📋 DATOS POR ZONA")
    columnas = ['id_zona', 'area_ha', 'npk_actual', 'ndvi', 'ndre', 'materia_organica', 'humedad_suelo']
    columnas = [col for col in columnas if col in gdf_analizado.columns]
    
    if columnas:
        df_display = gdf_analizado[columnas].copy()
        df_display.columns = ['Zona', 'Área (ha)', 'NPK', 'NDVI', 'NDRE', 'MO (%)', 'Humedad']
        st.dataframe(df_display, use_container_width=True)
    
    # Gráficos adicionales
    st.subheader("📈 ANÁLISIS ESTADÍSTICO")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Histograma
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.hist(gdf_analizado['npk_actual'], bins=20, edgecolor='black', alpha=0.7, color='skyblue')
        ax.axvline(gdf_analizado['npk_actual'].mean(), color='red', linestyle='--', label='Promedio')
        ax.set_xlabel('Índice NPK')
        ax.set_ylabel('Frecuencia')
        ax.set_title('Distribución de Fertilidad')
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
    
    with col2:
        # Correlación NDVI vs NPK
        if 'ndvi' in gdf_analizado.columns:
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.scatter(gdf_analizado['ndvi'], gdf_analizado['npk_actual'], alpha=0.6)
            ax.set_xlabel('NDVI')
            ax.set_ylabel('Índice NPK')
            ax.set_title('Correlación NDVI vs Fertilidad')
            ax.grid(True, alpha=0.3)
            
            # Línea de tendencia
            if len(gdf_analizado) > 1:
                z = np.polyfit(gdf_analizado['ndvi'], gdf_analizado['npk_actual'], 1)
                p = np.poly1d(z)
                ax.plot(gdf_analizado['ndvi'], p(gdf_analizado['ndvi']), "r--", alpha=0.8)
            
            st.pyplot(fig)

def mostrar_resultados_npk(resultados, cultivo, nutriente):
    """Muestra resultados de recomendaciones NPK"""
    gdf_analizado = resultados['gdf_analizado']
    
    st.markdown("---")
    st.subheader(f"📊 RECOMENDACIONES DE {nutriente} - {cultivo}")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Zonas Analizadas", len(gdf_analizado))
    
    with col2:
        st.metric("Área Total", f"{resultados['area_total']:.2f} ha")
    
    with col3:
        if 'valor_recomendado' in gdf_analizado.columns:
            rec_prom = gdf_analizado['valor_recomendado'].mean()
            st.metric(f"{nutriente} Promedio", f"{rec_prom:.1f} kg/ha")
    
    with col4:
        # Referencia de parámetros
        params = PARAMETROS_CULTIVOS[cultivo]
        if nutriente == "NITRÓGENO":
            rango = f"{params['NITROGENO']['min']}-{params['NITROGENO']['max']}"
        elif nutriente == "FÓSFORO":
            rango = f"{params['FOSFORO']['min']}-{params['FOSFORO']['max']}"
        else:
            rango = f"{params['POTASIO']['min']}-{params['POTASIO']['max']}"
        st.metric("Rango Óptimo", f"{rango} kg/ha")
    
    # Mapa de recomendaciones
    st.subheader(f"🗺️ MAPA DE APLICACIÓN DE {nutriente}")
    
    try:
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        # Obtener paleta según nutriente
        if nutriente == "NITRÓGENO":
            cmap_name = 'NITROGENO'
            titulo_nutriente = "Nitrógeno"
        elif nutriente == "FÓSFORO":
            cmap_name = 'FOSFORO'
            titulo_nutriente = "Fósforo"
        else:
            cmap_name = 'POTASIO'
            titulo_nutriente = "Potasio"
        
        cmap = LinearSegmentedColormap.from_list(cmap_name.lower(), PALETAS_GEE[cmap_name])
        
        # Normalizar valores
        valores = gdf_analizado['valor_recomendado']
        vmin, vmax = valores.min(), valores.max()
        norm = plt.Normalize(vmin, vmax)
        
        for idx, row in gdf_analizado.iterrows():
            valor_norm = norm(row['valor_recomendado'])
            color = cmap(valor_norm)
            gdf_analizado.iloc[[idx]].plot(ax=ax, color=color, edgecolor='black', linewidth=1)
            
            # Etiqueta con valor
            centroid = row.geometry.centroid
            ax.annotate(f"{row['valor_recomendado']:.0f}", 
                       (centroid.x, centroid.y),
                       fontsize=8, ha='center', va='center',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        ax.set_title(f'Recomendación de {titulo_nutriente} - {cultivo}', fontsize=14, fontweight='bold')
        ax.set_xlabel('Longitud')
        ax.set_ylabel('Latitud')
        
        # Barra de colores
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax)
        cbar.set_label(f'{titulo_nutriente} (kg/ha)', fontsize=12)
        
        plt.tight_layout()
        
        # Guardar mapa en buffer
        mapa_buffer = io.BytesIO()
        plt.savefig(mapa_buffer, format='png', dpi=150, bbox_inches='tight')
        mapa_buffer.seek(0)
        st.image(mapa_buffer, use_container_width=True)
        
        # Guardar en session state
        st.session_state['mapa_buffer'] = mapa_buffer
        
        plt.close()
        
    except Exception as e:
        st.error(f"Error creando mapa: {str(e)}")
    
    # Tabla de datos
    st.subheader("📋 RECOMENDACIONES POR ZONA")
    columnas = ['id_zona', 'area_ha', 'valor_recomendado', 'npk_actual', 'ndvi', 'ndre']
    columnas = [col for col in columnas if col in gdf_analizado.columns]
    
    if columnas:
        df_display = gdf_analizado[columnas].copy()
        df_display.columns = ['Zona', 'Área (ha)', f'{nutriente} (kg/ha)', 'NPK', 'NDVI', 'NDRE']
        st.dataframe(df_display, use_container_width=True)
    
    # Resumen de aplicación
    st.subheader("🎯 RESUMEN DE APLICACIÓN")
    
    if 'valor_recomendado' in gdf_analizado.columns:
        total_nutriente = (gdf_analizado['valor_recomendado'] * gdf_analizado['area_ha']).sum()
        promedio_ha = gdf_analizado['valor_recomendado'].mean()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Requerido", f"{total_nutriente:,.0f} kg")
        
        with col2:
            st.metric("Promedio por ha", f"{promedio_ha:.1f} kg/ha")
        
        with col3:
            # Clasificación de necesidades
            rec_max = gdf_analizado['valor_recomendado'].max()
            rec_min = gdf_analizado['valor_recomendado'].min()
            variacion = ((rec_max - rec_min) / promedio_ha * 100) if promedio_ha > 0 else 0
            st.metric("Variabilidad", f"{variacion:.1f}%")

def mostrar_resultados_textura(resultados, cultivo):
    """Muestra resultados de análisis de textura"""
    gdf_analizado = resultados['gdf_analizado']
    
    st.markdown("---")
    st.subheader(f"🏗️ ANÁLISIS DE TEXTURA - {cultivo}")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'textura_suelo' in gdf_analizado.columns:
            textura_pred = gdf_analizado['textura_suelo'].mode()[0] if len(gdf_analizado) > 0 else "N/D"
            st.metric("Textura Predominante", textura_pred)
    
    with col2:
        if 'arena' in gdf_analizado.columns:
            arena_prom = gdf_analizado['arena'].mean()
            st.metric("Arena Promedio", f"{arena_prom:.1f}%")
    
    with col3:
        if 'limo' in gdf_analizado.columns:
            limo_prom = gdf_analizado['limo'].mean()
            st.metric("Limo Promedio", f"{limo_prom:.1f}%")
    
    with col4:
        if 'arcilla' in gdf_analizado.columns:
            arcilla_prom = gdf_analizado['arcilla'].mean()
            st.metric("Arcilla Promedio", f"{arcilla_prom:.1f}%")
    
    # Gráficos
    st.subheader("📊 COMPOSICIÓN GRANULOMÉTRICA")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de torta
        fig, ax = plt.subplots(figsize=(6, 6))
        composicion = [gdf_analizado['arena'].mean(), 
                      gdf_analizado['limo'].mean(), 
                      gdf_analizado['arcilla'].mean()]
        labels = ['Arena', 'Limo', 'Arcilla']
        colors = ['#d8b365', '#f6e8c3', '#01665e']
        ax.pie(composicion, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.set_title('Composición Promedio')
        st.pyplot(fig)
    
    with col2:
        # Gráfico de barras por textura
        fig, ax = plt.subplots(figsize=(8, 6))
        if 'textura_suelo' in gdf_analizado.columns:
            textura_counts = gdf_analizado['textura_suelo'].value_counts()
            ax.bar(textura_counts.index, textura_counts.values, color='skyblue')
            ax.set_xlabel('Textura')
            ax.set_ylabel('Número de Zonas')
            ax.set_title('Distribución de Texturas')
            ax.tick_params(axis='x', rotation=45)
            st.pyplot(fig)
    
    # Mapa de texturas
    st.subheader("🗺️ MAPA DE TEXTURAS")
    
    try:
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        # Colores por textura
        colores_textura = {
            'Franco': '#c7eae5',
            'Franco Arcilloso': '#5ab4ac',
            'Franco Arenoso': '#f6e8c3',
            'Arenoso': '#d8b365',
            'Arcilloso': '#01665e',
            'NO_DETERMINADA': '#999999'
        }
        
        for idx, row in gdf_analizado.iterrows():
            textura = row['textura_suelo']
            color = colores_textura.get(textura, '#999999')
            gdf_analizado.iloc[[idx]].plot(ax=ax, color=color, edgecolor='black', linewidth=1.5)
            
            # Etiqueta
            centroid = row.geometry.centroid
            ax.annotate(f"Z{int(row['id_zona'])}\n{textura[:3]}", 
                       (centroid.x, centroid.y),
                       fontsize=8, ha='center', va='center',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.9))
        
        ax.set_title(f'Mapa de Texturas - {cultivo}', fontsize=14, fontweight='bold')
        ax.set_xlabel('Longitud')
        ax.set_ylabel('Latitud')
        ax.grid(True, alpha=0.3)
        
        # Leyenda
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor=color, edgecolor='black', label=textura)
                          for textura, color in colores_textura.items()]
        ax.legend(handles=legend_elements, title='Texturas', loc='upper left', bbox_to_anchor=(1.05, 1))
        
        plt.tight_layout()
        
        # Guardar mapa
        mapa_buffer = io.BytesIO()
        plt.savefig(mapa_buffer, format='png', dpi=150, bbox_inches='tight')
        mapa_buffer.seek(0)
        st.image(mapa_buffer, use_container_width=True)
        
        st.session_state['mapa_buffer'] = mapa_buffer
        
        plt.close()
        
    except Exception as e:
        st.error(f"Error creando mapa: {str(e)}")
    
    # Tabla de datos
    st.subheader("📋 DATOS POR ZONA")
    columnas = ['id_zona', 'area_ha', 'textura_suelo', 'arena', 'limo', 'arcilla']
    columnas = [col for col in columnas if col in gdf_analizado.columns]
    
    if columnas:
        df_display = gdf_analizado[columnas].copy()
        df_display.columns = ['Zona', 'Área (ha)', 'Textura', 'Arena (%)', 'Limo (%)', 'Arcilla (%)']
        st.dataframe(df_display, use_container_width=True)
    
    # Recomendaciones por textura
    st.subheader("💡 RECOMENDACIONES DE MANEJO")
    
    if 'textura_suelo' in gdf_analizado.columns:
        textura_pred = gdf_analizado['textura_suelo'].mode()[0] if len(gdf_analizado) > 0 else "NO_DETERMINADA"
        
        if textura_pred in RECOMENDACIONES_TEXTURA:
            info = RECOMENDACIONES_TEXTURA[textura_pred]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**✅ PROPIEDADES**")
                for prop in info['propiedades']:
                    st.markdown(f"• {prop}")
            
            with col2:
                st.markdown("**⚠️ LIMITANTES**")
                for lim in info['limitantes']:
                    st.markdown(f"• {lim}")
            
            with col3:
                st.markdown("**🛠️ MANEJO**")
                for man in info['manejo']:
                    st.markdown(f"• {man}")

def mostrar_resultados_curvas_nivel(resultados, cultivo, gdf_original):
    """Muestra resultados de análisis de curvas de nivel"""
    
    st.markdown("---")
    st.subheader(f"🏔️ ANÁLISIS TOPOGRÁFICO - {cultivo}")
    
    # Obtener datos adicionales
    datos_adicionales = resultados.get('datos_adicionales', {})
    X = datos_adicionales.get('X')
    Y = datos_adicionales.get('Y')
    Z = datos_adicionales.get('Z')
    pendiente_grid = datos_adicionales.get('pendiente_grid')
    curvas = datos_adicionales.get('curvas', [])
    elevaciones = datos_adicionales.get('elevaciones', [])
    estadisticas_pendiente = datos_adicionales.get('estadisticas_pendiente', {})
    datos_volumen = datos_adicionales.get('datos_volumen')
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if Z is not None:
            elev_prom = np.nanmean(Z)
            st.metric("Elevación Promedio", f"{elev_prom:.1f} m")
    
    with col2:
        if Z is not None:
            rango_elev = np.nanmax(Z) - np.nanmin(Z)
            st.metric("Rango Elevación", f"{rango_elev:.1f} m")
    
    with col3:
        if estadisticas_pendiente:
            pend_prom = estadisticas_pendiente.get('promedio', 0)
            st.metric("Pendiente Promedio", f"{pend_prom:.1f}%")
    
    with col4:
        st.metric("Curvas Generadas", len(curvas))
    
    # Mapa de pendientes interactivo
    st.subheader("🔥 MAPA DE PENDIENTES INTERACTIVO")
    
    if X is not None and Y is not None and pendiente_grid is not None:
        fig = crear_mapa_pendientes_interactivo(X, Y, pendiente_grid, gdf_original)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    # Visualización 3D
    st.subheader("🌄 VISUALIZACIÓN 3D DEL TERRENO")
    
    if X is not None and Y is not None and Z is not None:
        fig_3d = crear_visualizacion_3d(X, Y, Z, gdf_original)
        if fig_3d:
            st.plotly_chart(fig_3d, use_container_width=True)
    
    # Análisis de riesgo de erosión
    st.subheader("⚠️ ANÁLISIS DE RIESGO DE EROSION")
    
    if estadisticas_pendiente and 'distribucion' in estadisticas_pendiente:
        # Calcular riesgo
        riesgo_total = 0
        distribucion = estadisticas_pendiente.get('distribucion', {})
        
        for categoria, data in distribucion.items():
            if categoria in CLASIFICACION_PENDIENTES:
                riesgo_total += data.get('porcentaje', 0) * CLASIFICACION_PENDIENTES[categoria]['factor_erosivo']
        
        riesgo_promedio = riesgo_total / 100
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if riesgo_promedio < 0.3:
                st.success("✅ **RIESGO BAJO**")
                st.metric("Factor Riesgo", f"{riesgo_promedio:.2f}")
            elif riesgo_promedio < 0.6:
                st.warning("⚠️ **RIESGO MODERADO**")
                st.metric("Factor Riesgo", f"{riesgo_promedio:.2f}")
            else:
                st.error("🚨 **RIESGO ALTO**")
                st.metric("Factor Riesgo", f"{riesgo_promedio:.2f}")
        
        with col2:
            # Área crítica (>10% pendiente)
            porcentaje_critico = sum(data.get('porcentaje', 0) for cat, data in distribucion.items()
                                    if cat in ['FUERTE (10-15%)', 'MUY FUERTE (15-25%)', 'EXTREMA (>25%)'])
            area_critica = resultados['area_total'] * (porcentaje_critico / 100)
            st.metric("Área Crítica (>10%)", f"{area_critica:.2f} ha")
        
        with col3:
            # Área manejable
            porcentaje_manejable = sum(data.get('porcentaje', 0) for cat, data in distribucion.items()
                                      if cat in ['PLANA (0-2%)', 'SUAVE (2-5%)', 'MODERADA (5-10%)'])
            area_manejable = resultados['area_total'] * (porcentaje_manejable / 100)
            st.metric("Área Manejable", f"{area_manejable:.2f} ha")
    
    # Perfiles topográficos
    st.subheader("📐 PERFILES TOPOGRÁFICOS")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Configurar Perfil:**")
        if X is not None and Y is not None and gdf_original is not None:
            bounds = gdf_original.total_bounds
            punto_inicio_lon = st.number_input("Longitud inicio", 
                                              value=float(bounds[0]) + 0.0005,
                                              format="%.6f")
            punto_inicio_lat = st.number_input("Latitud inicio", 
                                              value=float(bounds[1]) + 0.0005,
                                              format="%.6f")
    
    with col2:
        st.write("**Punto Final:**")
        if X is not None and Y is not None and gdf_original is not None:
            bounds = gdf_original.total_bounds
            punto_fin_lon = st.number_input("Longitud fin", 
                                           value=float(bounds[2]) - 0.0005,
                                           format="%.6f")
            punto_fin_lat = st.number_input("Latitud fin", 
                                           value=float(bounds[3]) - 0.0005,
                                           format="%.6f")
    
    if st.button("Generar Perfil", key="generar_perfil"):
        if X is not None and Y is not None and Z is not None:
            distancias, z_vals, coordenadas = generar_perfil_topografico(
                X, Y, Z, 
                (punto_inicio_lon, punto_inicio_lat),
                (punto_fin_lon, punto_fin_lat)
            )
            
            if distancias is not None:
                # Gráfico del perfil
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.plot(distancias, z_vals, 'b-', linewidth=2, label='Perfil')
                ax.fill_between(distancias, z_vals, np.nanmin(z_vals), alpha=0.3)
                ax.set_xlabel("Distancia (m)")
                ax.set_ylabel("Elevación (m)")
                ax.set_title("Perfil Topográfico")
                ax.grid(True, alpha=0.3)
                ax.legend()
                
                st.pyplot(fig)
                
                # Datos del perfil para descarga
                df_perfil = pd.DataFrame({
                    'distancia_m': distancias,
                    'elevacion_m': z_vals,
                    'latitud': coordenadas[1] if coordenadas else [np.nan] * len(distancias),
                    'longitud': coordenadas[0] if coordenadas else [np.nan] * len(distancias)
                })
                
                csv_perfil = df_perfil.to_csv(index=False)
                st.download_button(
                    label="📥 Descargar Perfil (CSV)",
                    data=csv_perfil,
                    file_name=f"perfil_topografico_{cultivo}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
    
    # Cálculo de volumen de tierra
    st.subheader("📦 CÁLCULO DE VOLUMEN DE TIERRA")
    
    if X is not None and Y is not None and Z is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            elevacion_ref = st.number_input("Elevación de referencia (m)", 
                                           value=float(np.nanmean(Z)),
                                           format="%.1f")
        
        with col2:
            st.write("")
            st.write("")
            if st.button("Calcular Volumen", key="calcular_volumen"):
                vol_exc, vol_rell, area_m2 = calcular_volumen_tierra(X, Y, Z, elevacion_ref)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Volumen Excavación", f"{vol_exc:,.0f} m³")
                
                with col2:
                    st.metric("Volumen Relleno", f"{vol_rell:,.0f} m³")
                
                with col3:
                    st.metric("Área Total", f"{area_m2:,.0f} m²")
                
                # Balance de tierra
                balance = vol_exc - vol_rell
                if balance > 0:
                    st.info(f"📊 **Balance:** {balance:,.0f} m³ de excedente (excavación)")
                elif balance < 0:
                    st.info(f"📊 **Balance:** {abs(balance):,.0f} m³ de déficit (se necesita relleno)")
                else:
                    st.info("📊 **Balance:** Perfecto (excavación = relleno)")
                
                # Guardar datos de volumen
                st.session_state['datos_volumen'] = (vol_exc, vol_rell, area_m2)
    
    # Guardar datos adicionales para exportación
    st.session_state['datos_adicionales'] = datos_adicionales

def mostrar_panel_exportacion():
    """Muestra el panel de exportación de resultados"""
    
    st.markdown("---")
    st.subheader("📤 EXPORTACIÓN DE RESULTADOS")
    
    if st.session_state['resultados_guardados'] is None:
        st.warning("No hay resultados para exportar")
        return
    
    resultados = st.session_state['resultados_guardados']
    gdf_analizado = resultados.get('gdf_analizado')
    
    if gdf_analizado is None:
        st.error("No hay datos analizados para exportar")
        return
    
    # Botones de exportación
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("🗺️ GeoJSON", key="btn_geojson", use_container_width=True):
            geojson_data, nombre_archivo = exportar_a_geojson(
                gdf_analizado, 
                f"parcela_{st.session_state.get('cultivo_actual', 'analisis')}"
            )
            
            if geojson_data:
                st.download_button(
                    label="📥 Descargar GeoJSON",
                    data=geojson_data,
                    file_name=nombre_archivo,
                    mime="application/json",
                    key="dl_geojson"
                )
    
    with col2:
        if st.button("📊 CSV", key="btn_csv", use_container_width=True):
            # Exportar a CSV
            if 'geometry' in gdf_analizado.columns:
                df_export = gpd.GeoDataFrame(gdf_analizado).drop(columns=['geometry']).copy()
            else:
                df_export = gdf_analizado.copy()
            
            csv_data = df_export.to_csv(index=False)
            
            st.download_button(
                label="📥 Descargar CSV",
                data=csv_data,
                file_name=f"datos_{st.session_state.get('cultivo_actual', 'analisis')}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                key="dl_csv"
            )
    
    with col3:
        if st.button("📄 PDF Completo", key="btn_pdf", use_container_width=True):
            with st.spinner("Generando reporte PDF..."):
                # Preparar datos para el reporte
                cultivo = st.session_state.get('cultivo_actual', 'N/D')
                analisis_tipo = st.session_state.get('analisis_tipo_actual', 'N/D')
                area_total = st.session_state.get('area_total_actual', 0)
                
                # Generar estadísticas
                estadisticas = {}
                if analisis_tipo == "FERTILIDAD ACTUAL" and 'npk_actual' in gdf_analizado.columns:
                    estadisticas['Índice NPK Promedio'] = f"{gdf_analizado['npk_actual'].mean():.3f}"
                    estadisticas['Índice NPK Mínimo'] = f"{gdf_analizado['npk_actual'].min():.3f}"
                    estadisticas['Índice NPK Máximo'] = f"{gdf_analizado['npk_actual'].max():.3f}"
                
                # Generar recomendaciones
                recomendaciones = [
                    "Realizar análisis de suelo de laboratorio para validar resultados",
                    "Considerar agricultura de precisión para aplicación variable",
                    "Monitorear condiciones climáticas para ajustar recomendaciones"
                ]
                
                # Generar resumen ejecutivo
                resumen_ejecutivo = generar_resumen_ejecutivo(
                    gdf_analizado, analisis_tipo, cultivo, area_total
                )
                
                # Generar gráfico estadístico
                grafico_buffer = generar_grafico_estadisticas_embebido(
                    gdf_analizado, analisis_tipo, cultivo
                )
                
                # Obtener mapa buffer
                mapa_buffer = st.session_state.get('mapa_buffer')
                
                # Datos adicionales para curvas de nivel
                datos_curvas = None
                datos_volumen = None
                
                if analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
                    datos_adicionales = st.session_state.get('datos_adicionales', {})
                    datos_curvas = {
                        'estadisticas_pendiente': datos_adicionales.get('estadisticas_pendiente', {})
                    }
                    datos_volumen = st.session_state.get('datos_volumen')
                
                # Generar PDF
                pdf_buffer = generar_reporte_pdf_completo(
                    gdf_analizado, cultivo, analisis_tipo, area_total,
                    nutriente=st.session_state.get('nutriente_actual'),
                    satelite=st.session_state.get('satelite_actual'),
                    indice=st.session_state.get('indice_actual'),
                    mapa_buffer=mapa_buffer,
                    estadisticas=estadisticas,
                    recomendaciones=recomendaciones,
                    grafico_buffer=grafico_buffer,
                    resumen_ejecutivo=resumen_ejecutivo,
                    datos_curvas=datos_curvas,
                    datos_volumen=datos_volumen
                )
                
                if pdf_buffer:
                    st.download_button(
                        label="📥 Descargar PDF",
                        data=pdf_buffer,
                        file_name=f"reporte_{cultivo}_{analisis_tipo.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        key="dl_pdf"
                    )
    
    with col4:
        if st.button("📝 DOCX", key="btn_docx", use_container_width=True):
            with st.spinner("Generando reporte DOCX..."):
                # Similar al PDF pero más simple
                cultivo = st.session_state.get('cultivo_actual', 'N/D')
                analisis_tipo = st.session_state.get('analisis_tipo_actual', 'N/D')
                area_total = st.session_state.get('area_total_actual', 0)
                
                docx_buffer = generar_reporte_docx_completo(
                    gdf_analizado, cultivo, analisis_tipo, area_total,
                    nutriente=st.session_state.get('nutriente_actual'),
                    satelite=st.session_state.get('satelite_actual'),
                    indice=st.session_state.get('indice_actual'),
                    mapa_buffer=st.session_state.get('mapa_buffer'),
                    estadisticas={},
                    recomendaciones=[],
                    grafico_buffer=None,
                    resumen_ejecutivo="Resumen ejecutivo generado automáticamente."
                )
                
                if docx_buffer:
                    st.download_button(
                        label="📥 Descargar DOCX",
                        data=docx_buffer,
                        file_name=f"reporte_{cultivo}_{analisis_tipo.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key="dl_docx"
                    )
    
    with col5:
        # Exportar curvas de nivel (si aplica)
        if st.session_state.get('analisis_tipo_actual') == "ANÁLISIS DE CURVAS DE NIVEL":
            datos_adicionales = st.session_state.get('datos_adicionales', {})
            curvas = datos_adicionales.get('curvas', [])
            elevaciones = datos_adicionales.get('elevaciones', [])
            
            if curvas and len(curvas) > 0:
                if st.button("🔄 Curvas GeoJSON", key="btn_curvas", use_container_width=True):
                    geojson_curvas = exportar_curvas_geojson(curvas, elevaciones)
                    
                    if geojson_curvas:
                        st.download_button(
                            label="📥 Descargar Curvas",
                            data=geojson_curvas,
                            file_name=f"curvas_nivel_{st.session_state.get('cultivo_actual', 'analisis')}_{datetime.now().strftime('%Y%m%d_%H%M')}.geojson",
                            mime="application/json",
                            key="dl_curvas"
                        )
    
    # Información sobre exportación
    with st.expander("ℹ️ Información sobre formatos de exportación"):
        st.markdown("""
        **Formatos disponibles:**
        
        **🗺️ GeoJSON:**
        - Formato estándar para datos geográficos
        - Compatible con QGIS, ArcGIS, Google Earth
        - Incluye geometrías y atributos
        
        **📊 CSV:**
        - Formato tabular simple
        - Compatible con Excel, Google Sheets
        - Fácil de procesar y analizar
        
        **📄 PDF Completo:**
        - Reporte profesional con gráficos
        - Incluye resumen ejecutivo
        - Formato listo para imprimir
        
        **📝 DOCX:**
        - Documento Word editable
        - Fácil de personalizar
        - Ideal para presentaciones
        
        **🔄 Curvas GeoJSON:**
        - Solo para análisis topográfico
        - Incluye curvas de nivel como líneas
        - Elevación almacenada en propiedades
        """)

# ===== EJECUCIÓN PRINCIPAL =====
if __name__ == "__main__":
    main()
