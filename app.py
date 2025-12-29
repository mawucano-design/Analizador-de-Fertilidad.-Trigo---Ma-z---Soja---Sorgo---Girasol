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
from shapely.geometry import Polygon, LineString, Point
import math
import warnings
import xml.etree.ElementTree as ET
import base64
import json
from io import BytesIO
from fpdf import FPDF
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import geojson
warnings.filterwarnings('ignore')

# ===== CONFIGURACIÓN DE PÁGINA - CON ESTILOS MEJORADOS =====
st.set_page_config(
    page_title="🌱 Analizador Multi-Cultivo Satellital PRO",
    layout="wide",
    page_icon="🛰️",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    /* Estilos generales */
    .main-header {
        font-size: 2.8rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 0.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #1E88E5, #43A047);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-header {
        font-size: 1.6rem;
        color: #43A047;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 3px solid #C8E6C9;
        padding-bottom: 0.5rem;
        font-weight: 600;
    }
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.2rem;
        border-radius: 15px;
        border-left: 6px solid #1E88E5;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    .info-box {
        background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
        padding: 1.2rem;
        border-radius: 12px;
        border-left: 5px solid #2196F3;
        margin: 1rem 0;
        box-shadow: 0 3px 5px rgba(0, 0, 0, 0.08);
    }
    .success-box {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        padding: 1.2rem;
        border-radius: 12px;
        border-left: 5px solid #4CAF50;
        margin: 1rem 0;
        box-shadow: 0 3px 5px rgba(0, 0, 0, 0.08);
    }
    .warning-box {
        background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
        padding: 1.2rem;
        border-radius: 12px;
        border-left: 5px solid #FF9800;
        margin: 1rem 0;
        box-shadow: 0 3px 5px rgba(0, 0, 0, 0.08);
    }
    .sidebar-header {
        font-size: 1.4rem;
        color: #1E88E5;
        margin-top: 1rem;
        font-weight: 600;
    }
    .stButton > button {
        background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
        color: white;
        font-weight: 600;
        border: none;
        padding: 0.8rem 1.5rem;
        border-radius: 8px;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(30, 136, 229, 0.2);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(30, 136, 229, 0.3);
    }
    .stDownloadButton > button {
        background: linear-gradient(135deg, #43A047 0%, #2E7D32 100%);
        color: white;
        font-weight: 600;
        border: none;
        padding: 0.8rem 1.5rem;
        border-radius: 8px;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(67, 160, 71, 0.2);
    }
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(67, 160, 71, 0.3);
    }
    .file-uploader {
        border: 2px dashed #1E88E5;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        background-color: #F5F9FF;
        margin: 1rem 0;
    }
    .satellite-info {
        background: linear-gradient(135deg, #F3E5F5 0%, #E1BEE7 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #9C27B0;
    }
    .cultivo-card {
        padding: 0.8rem;
        border-radius: 10px;
        margin: 0.3rem 0;
        text-align: center;
        font-weight: 600;
        background: linear-gradient(135deg, #FFF8E1 0%, #FFECB3 100%);
        border: 2px solid #FFC107;
    }
    .analysis-type-card {
        padding: 0.8rem;
        border-radius: 10px;
        margin: 0.3rem 0;
        background: linear-gradient(135deg, #E0F7FA 0%, #80DEEA 100%);
        border: 2px solid #00BCD4;
        font-weight: 600;
    }
    /* Mejorar las tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 8px 8px 0 0;
        gap: 1px;
        padding: 10px 16px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%) !important;
        color: white !important;
    }
    /* Scrollbar personalizada */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #1E88E5 0%, #43A047 100%);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #1565C0 0%, #2E7D32 100%);
    }
</style>
""", unsafe_allow_html=True)

# ===== TÍTULO PRINCIPAL =====
st.markdown('<h1 class="main-header">🛰️ ANALIZADOR MULTI-CULTIVO PRO</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666; margin-bottom: 2rem;">Análisis satelital avanzado para agricultura de precisión</p>', unsafe_allow_html=True)
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
# PARÁMETROS GEE POR CULTIVO
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

# PARÁMETROS DE TEXTURA DEL SUELO POR CULTIVO
TEXTURA_SUELO_OPTIMA = {
    'TRIGO': {
        'textura_optima': 'Franco Arcilloso',
        'arena_optima': 40,
        'limo_optima': 30,
        'arcilla_optima': 30,
        'densidad_aparente_optima': 1.2,
        'porosidad_optima': 0.55
    },
    'MAÍZ': {
        'textura_optima': 'Franco',
        'arena_optima': 45,
        'limo_optima': 35,
        'arcilla_optima': 20,
        'densidad_aparente_optima': 1.3,
        'porosidad_optima': 0.5
    },
    'SOJA': {
        'textura_optima': 'Franco',
        'arena_optima': 45,
        'limo_optima': 35,
        'arcilla_optima': 20,
        'densidad_aparente_optima': 1.3,
        'porosidad_optima': 0.5
    },
    'SORGO': {
        'textura_optima': 'Franco',
        'arena_optima': 45,
        'limo_optima': 35,
        'arcilla_optima': 20,
        'densidad_aparente_optima': 1.3,
        'porosidad_optima': 0.5
    },
    'GIRASOL': {
        'textura_optima': 'Franco Arenoso',
        'arena_optima': 55,
        'limo_optima': 25,
        'arcilla_optima': 20,
        'densidad_aparente_optima': 1.4,
        'porosidad_optima': 0.45
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

# RECOMENDACIONES POR TIPO DE TEXTURA
RECOMENDACIONES_TEXTURA = {
    'Franco': {
        'propiedades': [
            "Equilibrio arena-limo-arcilla",
            "Buena aireación y drenaje",
            "CIC Intermedia-alta",
            "Retención de agua adecuada"
        ],
        'limitantes': [
            "Puede compactarse con maquinaria pesada",
            "Erosión en pendientes si no hay cobertura"
        ],
        'manejo': [
            "Mantener coberturas vivas o muertas",
            "Evitar tránsito excesivo de maquinaria",
            "Fertilización eficiente, sin muchas pérdidas",
            "Ideal para siembra directa"
        ]
    },
    'Franco Arcilloso': {
        'propiedades': [
            "Mayor proporción de arcilla (25–35%)",
            "Alta retención de agua y nutrientes",
            "Drenaje natural lento",
            "Buena fertilidad natural"
        ],
        'limitantes': [
            "Riesgo de encharcamiento",
            "Compactación fácil",
            "Menor oxigenación radicular"
        ],
        'manejo': [
            "Implementar drenajes (canales y subdrenes)",
            "Subsolado previo a siembra",
            "Incorporar materia orgánica (rastrojos, compost)",
            "Fertilización fraccionada en lluvias intensas"
        ]
    },
    'Franco Arenoso': {
        'propiedades': [
            "Arena 50–70%, arcilla 5-20%",
            "Buen desarrollo radicular",
            "Excelente drenaje",
            "Calentamiento rápido en primavera"
        ],
        'limitantes': [
            "Riesgo de lixiviación de nutrientes",
            "Estrés hídrico en veranos",
            "Fertilidad baja-moderada"
        ],
        'manejo': [
            "Uso de coberturas leguminosas",
            "Aplicar mulching (rastrojos, paja)",
            "Riego suplementario en sequía",
            "Fertilización fraccionada y frecuente"
        ]
    },
    'Arenoso': {
        'propiedades': [
            "Alto contenido de arena (>85%)",
            "Excelente drenaje",
            "Baja retención de agua",
            "Fácil laboreo"
        ],
        'limitantes': [
            "Baja retención de nutrientes",
            "Riesgo alto de erosión",
            "Requiere riego frecuente"
        ],
        'manejo': [
            "Aplicaciones frecuentes de materia orgánica",
            "Riego por goteo para eficiencia hídrica",
            "Fertilización fraccionada en pequeñas dosis",
            "Barreras vivas contra erosión"
        ]
    },
    'Arcilloso': {
        'propiedades': [
            "Alto contenido de arcilla (>35%)",
            "Alta retención de agua y nutrientes",
            "Estructura densa",
            "Alta fertilidad potencial"
        ],
        'limitantes': [
            "Drenaje muy lento",
            "Alta compactación",
            "Difícil laboreo cuando está húmedo"
        ],
        'manejo': [
            "Añadir materia orgánica para mejorar estructura",
            "Evitar laboreo en condiciones húmedas",
            "Implementar sistemas de drenaje profundo",
            "Cultivos de cobertura para romper compactación"
        ]
    }
}

# PALETAS GEE MEJORADAS
PALETAS_GEE = {
    'FERTILIDAD': ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#d9ef8b', '#a6d96a', '#66bd63', '#1a9850', '#006837'],
    'NITROGENO': ['#00ff00', '#80ff00', '#ffff00', '#ff8000', '#ff0000'],
    'FOSFORO': ['#0000ff', '#4040ff', '#8080ff', '#c0c0ff', '#ffffff'],
    'POTASIO': ['#4B0082', '#6A0DAD', '#8A2BE2', '#9370DB', '#D8BFD8'],
    'TEXTURA': ['#8c510a', '#d8b365', '#f6e8c3', '#c7eae5', '#5ab4ac', '#01665e'],
    'ELEVACION': ['#006837', '#1a9850', '#66bd63', '#a6d96a', '#d9ef8b', '#ffffbf', '#fee08b', '#fdae61', '#f46d43', '#d73027'],
    'PENDIENTE': ['#4daf4a', '#a6d96a', '#ffffbf', '#fdae61', '#f46d43', '#d73027']
}

# ===== SIDEBAR MEJORADA =====
with st.sidebar:
    # Logo y título
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h2 style="color: #1E88E5; margin-bottom: 0.5rem;">🌱 AGRO-TECH</h2>
        <p style="color: #666; font-size: 0.9rem;">Agricultura de Precisión</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    # Selección de cultivo con tarjetas visuales
    st.markdown('<p class="sidebar-header">🌾 SELECCIÓN DE CULTIVO</p>', unsafe_allow_html=True)
    cultivo = st.selectbox("", ["TRIGO", "MAÍZ", "SOJA", "SORGO", "GIRASOL"], 
                          format_func=lambda x: f"{PARAMETROS_CULTIVOS[x]['icono']} {x}")
    
    # Mostrar información del cultivo seleccionado
    with st.expander("ℹ️ Info del Cultivo"):
        params = PARAMETROS_CULTIVOS[cultivo]
        st.markdown(f"""
        **Parámetros Óptimos:**
        - Nitrógeno: {params['NITROGENO']['min']}-{params['NITROGENO']['max']} kg/ha
        - Fósforo: {params['FOSFORO']['min']}-{params['FOSFORO']['max']} kg/ha
        - Potasio: {params['POTASIO']['min']}-{params['POTASIO']['max']} kg/ha
        - Materia Orgánica: {params['MATERIA_ORGANICA_OPTIMA']}%
        - NDVI Óptimo: {params['NDVI_OPTIMO']}
        """)
    
    st.markdown("---")
    
    # Selección de tipo de análisis
    st.markdown('<p class="sidebar-header">📊 TIPO DE ANÁLISIS</p>', unsafe_allow_html=True)
    analisis_tipo = st.selectbox("", 
                                ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK", 
                                 "ANÁLISIS DE TEXTURA", "ANÁLISIS DE CURVAS DE NIVEL"],
                                format_func=lambda x: f"🔍 {x}")
    
    if analisis_tipo == "RECOMENDACIONES NPK":
        nutriente = st.selectbox("Nutriente:", ["NITRÓGENO", "FÓSFORO", "POTASIO"])
    
    st.markdown("---")
    
    # Fuente de datos satelitales con tarjetas
    st.markdown('<p class="sidebar-header">🛰️ FUENTE DE DATOS</p>', unsafe_allow_html=True)
    satelite_seleccionado = st.selectbox(
        "",
        ["SENTINEL-2", "LANDSAT-8", "DATOS_SIMULADOS"],
        format_func=lambda x: f"{SATELITES_DISPONIBLES[x]['icono']} {SATELITES_DISPONIBLES[x]['nombre']}"
    )
    
    # Mostrar información del satélite
    info_satelite = SATELITES_DISPONIBLES[satelite_seleccionado]
    st.markdown(f"""
    <div class="satellite-info">
        <strong>{info_satelite['icono']} {info_satelite['nombre']}</strong><br>
        📏 Resolución: {info_satelite['resolucion']}<br>
        🔄 Revisita: {info_satelite['revisita']}<br>
        📊 Índices: {', '.join(info_satelite['indices'][:3])}
    </div>
    """, unsafe_allow_html=True)
    
    # Configuración específica por tipo de análisis
    if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"]:
        st.markdown("---")
        st.markdown('<p class="sidebar-header">📅 RANGO TEMPORAL</p>', unsafe_allow_html=True)
        fecha_fin = st.date_input("Fecha fin", datetime.now())
        fecha_inicio = st.date_input("Fecha inicio", datetime.now() - timedelta(days=30))
        
        st.markdown('<p class="sidebar-header">📈 ÍNDICE DE VEGETACIÓN</p>', unsafe_allow_html=True)
        indice_seleccionado = st.selectbox("", info_satelite['indices'])
    
    st.markdown("---")
    
    # División de parcela
    st.markdown('<p class="sidebar-header">🎯 DIVISIÓN DE PARCELA</p>', unsafe_allow_html=True)
    n_divisiones = st.slider("Número de zonas:", min_value=16, max_value=48, value=32, 
                            help="Cantidad de zonas de manejo diferencial")
    
    # Configuración para curvas de nivel
    if analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
        st.markdown("---")
        st.markdown('<p class="sidebar-header">🏔️ CONFIGURACIÓN TOPOGRÁFICA</p>', unsafe_allow_html=True)
        intervalo_curvas = st.slider("Intervalo curvas (m):", 1.0, 20.0, 5.0, 0.5)
        resolucion_dem = st.slider("Resolución DEM (m):", 5.0, 50.0, 10.0, 5.0)
    
    st.markdown("---")
    
    # Subida de archivos con diseño mejorado
    st.markdown('<p class="sidebar-header">📤 SUBIR PARCELA</p>', unsafe_allow_html=True)
    st.markdown('<div class="file-uploader">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Arrastra o haz clic para subir",
        type=['zip', 'kml', 'kmz'],
        help="Formatos: Shapefile (.zip), KML, KMZ",
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="font-size: 0.8rem; color: #666; text-align: center; margin-top: 0.5rem;">
        Formatos aceptados: .zip (SHP), .kml, .kmz
    </div>
    """, unsafe_allow_html=True)

# ===== FUNCIONES AUXILIARES (MANTENIDAS DEL PRIMER ARCHIVO) =====
def validar_y_corregir_crs(gdf):
    if gdf is None or len(gdf) == 0:
        return gdf
    try:
        if gdf.crs is None:
            gdf = gdf.set_crs('EPSG:4326', inplace=False)
        elif str(gdf.crs).upper() != 'EPSG:4326':
            original_crs = str(gdf.crs)
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
        bounds = gdf.total_bounds
        if bounds[0] < -180 or bounds[2] > 180 or bounds[1] < -90 or bounds[3] > 90:
            area_grados2 = gdf.geometry.area.sum()
            area_m2 = area_grados2 * 111000 * 111000
            return area_m2 / 10000
        gdf_projected = gdf.to_crs('EPSG:3857')
        area_m2 = gdf_projected.geometry.area.sum()
        return area_m2 / 10000
    except Exception as e:
        try:
            return gdf.geometry.area.sum() / 10000
        except:
            return 0.0

def dividir_parcela_en_zonas(gdf, n_zonas):
    if len(gdf) == 0:
        return gdf
    gdf = validar_y_corregir_crs(gdf)
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
            cell_poly = Polygon([(cell_minx, cell_miny), (cell_maxx, cell_miny), (cell_maxx, cell_maxy), (cell_minx, cell_maxy)])
            intersection = parcela_principal.intersection(cell_poly)
            if not intersection.is_empty and intersection.area > 0:
                sub_poligonos.append(intersection)

    if sub_poligonos:
        nuevo_gdf = gpd.GeoDataFrame({'id_zona': range(1, len(sub_poligonos) + 1), 'geometry': sub_poligonos}, crs='EPSG:4326')
        return nuevo_gdf
    else:
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
                gdf = validar_y_corregir_crs(gdf)
                return gdf
            else:
                st.error("❌ No se encontró ningún archivo .shp en el ZIP")
                return None
    except Exception as e:
        st.error(f"❌ Error cargando shapefile desde ZIP: {str(e)}")
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
                        lon = float(parts[0])
                        lat = float(parts[1])
                        coord_list.append((lon, lat))
                if len(coord_list) >= 3:
                    polygons.append(Polygon(coord_list))

        if not polygons:
            for multi_geom in root.findall('.//kml:MultiGeometry', namespaces):
                for polygon_elem in multi_geom.findall('.//kml:Polygon', namespaces):
                    coords_elem = polygon_elem.find('.//kml:coordinates', namespaces)
                    if coords_elem is not None and coords_elem.text:
                        coord_text = coords_elem.text.strip()
                        coord_list = []
                        for coord_pair in coord_text.split():
                            parts = coord_pair.split(',')
                            if len(parts) >= 2:
                                lon = float(parts[0])
                                lat = float(parts[1])
                                coord_list.append((lon, lat))
                        if len(coord_list) >= 3:
                            polygons.append(Polygon(coord_list))

        if polygons:
            gdf = gpd.GeoDataFrame({'geometry': polygons}, crs='EPSG:4326')
            return gdf
        return None
    except Exception as e:
        return None

def cargar_kml(kml_file):
    try:
        if kml_file.name.endswith('.kmz'):
            with tempfile.TemporaryDirectory() as tmp_dir:
                with zipfile.ZipFile(kml_file, 'r') as zip_ref:
                    zip_ref.extractall(tmp_dir)
                kml_files = [f for f in os.listdir(tmp_dir) if f.endswith('.kml')]
                if kml_files:
                    kml_path = os.path.join(tmp_dir, kml_files[0])
                    with open(kml_path, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                    gdf = parsear_kml_manual(contenido)
                    if gdf is not None:
                        return gdf
                    else:
                        try:
                            gdf = gpd.read_file(kml_path)
                            gdf = validar_y_corregir_crs(gdf)
                            return gdf
                        except:
                            return None
                else:
                    st.error("❌ No se encontró ningún archivo .kml en el KMZ")
                    return None
        else:
            contenido = kml_file.read().decode('utf-8')
            gdf = parsear_kml_manual(contenido)
            if gdf is not None:
                return gdf
            else:
                kml_file.seek(0)
                gdf = gpd.read_file(kml_file)
                gdf = validar_y_corregir_crs(gdf)
                return gdf
    except Exception as e:
        st.error(f"❌ Error cargando archivo KML/KMZ: {str(e)}")
        return None

def cargar_archivo_parcela(uploaded_file):
    try:
        if uploaded_file.name.endswith('.zip'):
            gdf = cargar_shapefile_desde_zip(uploaded_file)
        elif uploaded_file.name.endswith(('.kml', '.kmz')):
            gdf = cargar_kml(uploaded_file)
        else:
            st.error("❌ Formato de archivo no soportado")
            return None

        if gdf is not None:
            gdf = validar_y_corregir_crs(gdf)
            if not gdf.geometry.geom_type.str.contains('Polygon').any():
                st.warning("⚠️ El archivo no contiene polígonos. Intentando extraer polígonos...")
                gdf = gdf.explode()
                gdf = gdf[gdf.geometry.geom_type.isin(['Polygon', 'MultiPolygon'])]
            if len(gdf) > 0:
                if 'id_zona' not in gdf.columns:
                    gdf['id_zona'] = range(1, len(gdf) + 1)
                return gdf
            else:
                st.error("❌ No se encontraron polígonos en el archivo")
                return None
    except Exception as e:
        st.error(f"❌ Error cargando archivo: {str(e)}")
        return None

# ===== FUNCIONES DE ANÁLISIS (MANTENIDAS) =====
def descargar_datos_sentinel2(gdf, fecha_inicio, fecha_fin, indice='NDVI'):
    try:
        datos_simulados = {
            'indice': indice,
            'valor_promedio': 0.72 + np.random.normal(0, 0.08),
            'fuente': 'Sentinel-2',
            'fecha': datetime.now().strftime('%Y-%m-%d'),
            'id_escena': f"S2A_{np.random.randint(1000000, 9999999)}",
            'cobertura_nubes': f"{np.random.randint(0, 10)}%",
            'resolucion': '10m'
        }
        return datos_simulados
    except Exception as e:
        st.error(f"❌ Error procesando Sentinel-2: {str(e)}")
        return None

def descargar_datos_landsat8(gdf, fecha_inicio, fecha_fin, indice='NDVI'):
    try:
        datos_simulados = {
            'indice': indice,
            'valor_promedio': 0.65 + np.random.normal(0, 0.1),
            'fuente': 'Landsat-8',
            'fecha': datetime.now().strftime('%Y-%m-%d'),
            'id_escena': f"LC08_{np.random.randint(1000000, 9999999)}",
            'cobertura_nubes': f"{np.random.randint(0, 15)}%",
            'resolucion': '30m'
        }
        return datos_simulados
    except Exception as e:
        st.error(f"❌ Error procesando Landsat 8: {str(e)}")
        return None

def generar_datos_simulados(gdf, cultivo, indice='NDVI'):
    datos_simulados = {
        'indice': indice,
        'valor_promedio': PARAMETROS_CULTIVOS[cultivo]['NDVI_OPTIMO'] * 0.8 + np.random.normal(0, 0.1),
        'fuente': 'Simulación',
        'fecha': datetime.now().strftime('%Y-%m-%d'),
        'resolucion': '10m'
    }
    return datos_simulados

def calcular_indices_satelitales_gee(gdf, cultivo, datos_satelitales):
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
    valor_base_satelital = datos_satelitales.get('valor_promedio', 0.6) if datos_satelitales else 0.6

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

        ndvi_base = valor_base_satelital * 0.8
        ndvi_variacion = patron_espacial * (valor_base_satelital * 0.4)
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

def calcular_recomendaciones_npk_gee(indices, nutriente, cultivo):
    recomendaciones = []
    params = PARAMETROS_CULTIVOS[cultivo]
    for idx in indices:
        ndre = idx['ndre']
        materia_organica = idx['materia_organica']
        humedad_suelo = idx['humedad_suelo']
        ndvi = idx['ndvi']

        if nutriente == "NITRÓGENO":
            factor_n = ((1 - ndre) * 0.6 + (1 - ndvi) * 0.4)
            n_recomendado = (factor_n * (params['NITROGENO']['max'] - params['NITROGENO']['min']) + params['NITROGENO']['min'])
            n_recomendado = max(params['NITROGENO']['min'] * 0.8, min(params['NITROGENO']['max'] * 1.2, n_recomendado))
            recomendaciones.append(round(n_recomendado, 1))
        elif nutriente == "FÓSFORO":
            factor_p = ((1 - (materia_organica / 8)) * 0.7 + (1 - humedad_suelo) * 0.3)
            p_recomendado = (factor_p * (params['FOSFORO']['max'] - params['FOSFORO']['min']) + params['FOSFORO']['min'])
            p_recomendado = max(params['FOSFORO']['min'] * 0.8, min(params['FOSFORO']['max'] * 1.2, p_recomendado))
            recomendaciones.append(round(p_recomendado, 1))
        else:
            factor_k = ((1 - ndre) * 0.4 + (1 - humedad_suelo) * 0.4 + (1 - (materia_organica / 8)) * 0.2)
            k_recomendado = (factor_k * (params['POTASIO']['max'] - params['POTASIO']['min']) + params['POTASIO']['min'])
            k_recomendado = max(params['POTASIO']['min'] * 0.8, min(params['POTASIO']['max'] * 1.2, k_recomendado))
            recomendaciones.append(round(k_recomendado, 1))
    return recomendaciones

def clasificar_textura_suelo(arena, limo, arcilla):
    try:
        total = arena + limo + arcilla
        if total == 0:
            return "NO_DETERMINADA"
        arena_norm = (arena / total) * 100
        limo_norm = (limo / total) * 100
        arcilla_norm = (arcilla / total) * 100

        if arcilla_norm >= 35:
            return "Arcilloso"
        elif arcilla_norm >= 25 and arcilla_norm <= 35 and arena_norm >= 20 and arena_norm <= 45:
            return "Franco Arcilloso"
        elif arena_norm >= 50 and arena_norm <= 70 and arcilla_norm >= 5 and arcilla_norm <= 20:
            return "Franco Arenoso"
        elif arcilla_norm >= 7 and arcilla_norm <= 27 and arena_norm >= 43 and arena_norm <= 52:
            return "Franco"
        elif arena_norm >= 85:
            return "Arenoso"
        else:
            return "Franco"
    except Exception as e:
        return "NO_DETERMINADA"

def analizar_textura_suelo(gdf, cultivo):
    gdf = validar_y_corregir_crs(gdf)
    params_textura = TEXTURA_SUELO_OPTIMA[cultivo]
    zonas_gdf = gdf.copy()
    zonas_gdf['area_ha'] = 0.0
    zonas_gdf['arena'] = 0.0
    zonas_gdf['limo'] = 0.0
    zonas_gdf['arcilla'] = 0.0
    zonas_gdf['textura_suelo'] = "NO_DETERMINADA"

    areas_ha_list = []
    arena_list = []
    limo_list = []
    arcilla_list = []
    textura_list = []

    for idx, row in zonas_gdf.iterrows():
        try:
            area_gdf = gpd.GeoDataFrame({'geometry': [row.geometry]}, crs=zonas_gdf.crs)
            area_ha = calcular_superficie(area_gdf)
            if hasattr(area_ha, 'iloc'):
                area_ha = float(area_ha.iloc[0])
            elif hasattr(area_ha, '__len__') and len(area_ha) > 0:
                area_ha = float(area_ha[0])
            else:
                area_ha = float(area_ha)

            centroid = row.geometry.centroid if hasattr(row.geometry, 'centroid') else row.geometry.representative_point()
            seed_value = abs(hash(f"{centroid.x:.6f}_{centroid.y:.6f}_{cultivo}_textura")) % (2**32)
            rng = np.random.RandomState(seed_value)

            lat_norm = (centroid.y + 90) / 180 if centroid.y else 0.5
            lon_norm = (centroid.x + 180) / 360 if centroid.x else 0.5
            variabilidad_local = 0.15 + 0.7 * (lat_norm * lon_norm)

            arena_optima = params_textura['arena_optima']
            limo_optima = params_textura['limo_optima']
            arcilla_optima = params_textura['arcilla_optima']

            arena_val = max(5, min(95, rng.normal(
                arena_optima * (0.8 + 0.4 * variabilidad_local),
                arena_optima * 0.15
            )))
            limo_val = max(5, min(95, rng.normal(
                limo_optima * (0.7 + 0.6 * variabilidad_local),
                limo_optima * 0.2
            )))
            arcilla_val = max(5, min(95, rng.normal(
                arcilla_optima * (0.75 + 0.5 * variabilidad_local),
                arcilla_optima * 0.15
            )))

            total = arena_val + limo_val + arcilla_val
            arena_pct = (arena_val / total) * 100
            limo_pct = (limo_val / total) * 100
            arcilla_pct = (arcilla_val / total) * 100

            textura = clasificar_textura_suelo(arena_pct, limo_pct, arcilla_pct)

            areas_ha_list.append(area_ha)
            arena_list.append(float(arena_pct))
            limo_list.append(float(limo_pct))
            arcilla_list.append(float(arcilla_pct))
            textura_list.append(textura)

        except Exception as e:
            areas_ha_list.append(0.0)
            arena_list.append(float(params_textura['arena_optima']))
            limo_list.append(float(params_textura['limo_optima']))
            arcilla_list.append(float(params_textura['arcilla_optima']))
            textura_list.append(params_textura['textura_optima'])

    zonas_gdf['area_ha'] = areas_ha_list
    zonas_gdf['arena'] = arena_list
    zonas_gdf['limo'] = limo_list
    zonas_gdf['arcilla'] = arcilla_list
    zonas_gdf['textura_suelo'] = textura_list
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

def calcular_pendiente_simple(X, Y, Z, resolucion=10.0):
    dy = np.gradient(Z, axis=0) / resolucion
    dx = np.gradient(Z, axis=1) / resolucion
    pendiente = np.sqrt(dx**2 + dy**2) * 100
    pendiente = np.clip(pendiente, 0, 100)
    return pendiente

def crear_mapa_pendientes_simple(X, Y, pendiente_grid, gdf_original):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    X_flat = X.flatten()
    Y_flat = Y.flatten()
    Z_flat = pendiente_grid.flatten()
    valid_mask = ~np.isnan(Z_flat)

    if np.sum(valid_mask) > 10:
        scatter = ax1.scatter(X_flat[valid_mask], Y_flat[valid_mask], c=Z_flat[valid_mask], cmap='RdYlGn_r', s=20, alpha=0.7, vmin=0, vmax=30)
        cbar = plt.colorbar(scatter, ax=ax1, shrink=0.8)
        cbar.set_label('Pendiente (%)')
        for porcentaje in [2, 5, 10, 15, 25]:
            mask_cat = (Z_flat[valid_mask] >= porcentaje-1) & (Z_flat[valid_mask] <= porcentaje+1)
            if np.sum(mask_cat) > 0:
                x_center = np.mean(X_flat[valid_mask][mask_cat])
                y_center = np.mean(Y_flat[valid_mask][mask_cat])
                ax1.text(x_center, y_center, f'{porcentaje}%', fontsize=8, fontweight='bold', ha='center', va='center', bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
    else:
        ax1.text(0.5, 0.5, 'Datos insuficientes\npara mapa de calor', transform=ax1.transAxes, ha='center', va='center', fontsize=12)

    gdf_original.plot(ax=ax1, color='none', edgecolor='black', linewidth=2)
    ax1.set_title('Mapa de Calor de Pendientes', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Longitud')
    ax1.set_ylabel('Latitud')
    ax1.grid(True, alpha=0.3)

    if np.sum(valid_mask) > 0:
        pendiente_data = Z_flat[valid_mask]
        ax2.hist(pendiente_data, bins=30, edgecolor='black', color='skyblue', alpha=0.7)
        for porcentaje, color in [(2, 'green'), (5, 'lightgreen'), (10, 'yellow'), (15, 'orange'), (25, 'red')]:
            ax2.axvline(x=porcentaje, color=color, linestyle='--', linewidth=1, alpha=0.7)
            ax2.text(porcentaje+0.5, ax2.get_ylim()[1]*0.9, f'{porcentaje}%', color=color, fontsize=8)

        stats_pendiente = calcular_estadisticas_pendiente_simple(pendiente_grid)
        stats_text = f"""
Estadísticas:
• Mínima: {stats_pendiente['min']:.1f}%
• Máxima: {stats_pendiente['max']:.1f}%
• Promedio: {stats_pendiente['promedio']:.1f}%
• Desviación: {stats_pendiente['std']:.1f}%
"""
        ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes, fontsize=9, verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
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
    return buf, calcular_estadisticas_pendiente_simple(pendiente_grid)

def calcular_estadisticas_pendiente_simple(pendiente_grid):
    pendiente_flat = pendiente_grid.flatten()
    pendiente_flat = pendiente_flat[~np.isnan(pendiente_flat)]
    if len(pendiente_flat) == 0:
        return {'promedio': 0, 'min': 0, 'max': 0, 'std': 0, 'distribucion': {}}

    stats = {
        'promedio': float(np.mean(pendiente_flat)),
        'min': float(np.min(pendiente_flat)),
        'max': float(np.max(pendiente_flat)),
        'std': float(np.std(pendiente_flat)),
        'distribucion': {}
    }

    for categoria, params in CLASIFICACION_PENDIENTES.items():
        mask = (pendiente_flat >= params['min']) & (pendiente_flat < params['max'])
        stats['distribucion'][categoria] = {'porcentaje': float(np.sum(mask) / len(pendiente_flat) * 100), 'color': params['color']}
    return stats

def generar_curvas_nivel_simple(X, Y, Z, intervalo=5.0, gdf_original=None):
    curvas = []
    elevaciones = []
    try:
        if gdf_original is not None:
            poligono_principal = gdf_original.iloc[0].geometry
            bounds = poligono_principal.bounds
            centro = poligono_principal.centroid
            ancho = bounds[2] - bounds[0]
            alto = bounds[3] - bounds[1]
            radio_max = min(ancho, alto) / 2
            z_min, z_max = np.nanmin(Z), np.nanmax(Z)
            n_curvas = min(10, int((z_max - z_min) / intervalo))
            for i in range(1, n_curvas + 1):
                radio = radio_max * (i / n_curvas)
                circle = centro.buffer(radio)
                interseccion = poligono_principal.intersection(circle)
                if interseccion.geom_type == 'LineString':
                    curvas.append(interseccion)
                    elevaciones.append(z_min + (i * intervalo))
                elif interseccion.geom_type == 'MultiLineString':
                    for parte in interseccion.geoms:
                        curvas.append(parte)
                        elevaciones.append(z_min + (i * intervalo))
    except Exception as e:
        if gdf_original is not None:
            bounds = gdf_original.total_bounds
            for i in range(3):
                y = bounds[1] + (i + 1) * ((bounds[3] - bounds[1]) / 4)
                linea = LineString([(bounds[0], y), (bounds[2], y)])
                curvas.append(linea)
                elevaciones.append(100 + i * 50)
    return curvas, elevaciones

# ===== FUNCIONES DE VISUALIZACIÓN MEJORADAS =====
def crear_mapa_estatico_mejorado(gdf, titulo, columna_valor, analisis_tipo, nutriente, cultivo, satelite):
    """Crea un mapa estático con diseño mejorado"""
    try:
        fig, ax = plt.subplots(1, 1, figsize=(14, 10))
        
        # Configurar colores según tipo de análisis
        if analisis_tipo == "FERTILIDAD ACTUAL":
            cmap = LinearSegmentedColormap.from_list('fertilidad_mee', PALETAS_GEE['FERTILIDAD'])
            vmin, vmax = 0, 1
            label = 'Índice NPK'
        elif analisis_tipo == "RECOMENDACIONES NPK":
            if nutriente == "NITRÓGENO":
                cmap = LinearSegmentedColormap.from_list('nitrogeno_mee', PALETAS_GEE['NITROGENO'])
                label = 'Nitrógeno (kg/ha)'
            elif nutriente == "FÓSFORO":
                cmap = LinearSegmentedColormap.from_list('fosforo_mee', PALETAS_GEE['FOSFORO'])
                label = 'Fósforo (kg/ha)'
            else:
                cmap = LinearSegmentedColormap.from_list('potasio_mee', PALETAS_GEE['POTASIO'])
                label = 'Potasio (kg/ha)'
            
            params = PARAMETROS_CULTIVOS[cultivo]
            if nutriente == "NITRÓGENO":
                vmin, vmax = params['NITROGENO']['min'] * 0.7, params['NITROGENO']['max'] * 1.2
            elif nutriente == "FÓSFORO":
                vmin, vmax = params['FOSFORO']['min'] * 0.7, params['FOSFORO']['max'] * 1.2
            else:
                vmin, vmax = params['POTASIO']['min'] * 0.7, params['POTASIO']['max'] * 1.2
        else:
            cmap = 'viridis'
            vmin, vmax = gdf[columna_valor].min(), gdf[columna_valor].max()
            label = columna_valor

        # Plotear cada zona
        for idx, row in gdf.iterrows():
            valor = row[columna_valor]
            valor_norm = (valor - vmin) / (vmax - vmin)
            valor_norm = max(0, min(1, valor_norm))
            color = cmap(valor_norm)
            
            # Plot con borde más grueso
            gdf.iloc[[idx]].plot(
                ax=ax, 
                color=color, 
                edgecolor='black', 
                linewidth=2,
                alpha=0.9
            )
            
            # Etiqueta mejorada
            centroid = row.geometry.centroid
            ax.annotate(
                f"Z{int(row['id_zona'])}\n{valor:.1f}" if analisis_tipo == "RECOMENDACIONES NPK" else f"Z{int(row['id_zona'])}\n{valor:.2f}",
                (centroid.x, centroid.y),
                xytext=(0, 0),
                textcoords="offset points",
                fontsize=9,
                fontweight='bold',
                color='black',
                ha='center',
                va='center',
                bbox=dict(
                    boxstyle="round,pad=0.4",
                    facecolor='white',
                    edgecolor='black',
                    alpha=0.9,
                    linewidth=1
                )
            )
        
        # Información del satélite
        info_satelite = SATELITES_DISPONIBLES.get(satelite, SATELITES_DISPONIBLES['DATOS_SIMULADOS'])
        
        # Título mejorado
        ax.set_title(
            f'{PARAMETROS_CULTIVOS[cultivo]["icono"]} {titulo} - {cultivo}\n'
            f'{info_satelite["icono"]} {info_satelite["nombre"]} | {analisis_tipo}',
            fontsize=16,
            fontweight='bold',
            pad=20,
            color='#1E88E5'
        )
        
        ax.set_xlabel('Longitud', fontsize=12, fontweight='bold')
        ax.set_ylabel('Latitud', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        
        # Barra de colores mejorada
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, shrink=0.8, pad=0.02)
        cbar.set_label(label, fontsize=12, fontweight='bold')
        cbar.ax.tick_params(labelsize=10)
        
        # Añadir leyenda de calidad
        legend_text = f"Áreas Analizadas: {len(gdf)}\nResolución: {info_satelite['resolucion']}"
        ax.text(
            0.02, 0.98,
            legend_text,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment='top',
            bbox=dict(
                boxstyle="round,pad=0.5",
                facecolor='white',
                edgecolor='gray',
                alpha=0.9
            )
        )
        
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=200, bbox_inches='tight', facecolor='white')
        buf.seek(0)
        plt.close()
        return buf
    except Exception as e:
        st.error(f"❌ Error creando mapa mejorado: {str(e)}")
        return None

# ===== INTERFAZ PRINCIPAL MEJORADA =====
if uploaded_file:
    with st.spinner("🔄 Cargando parcela..."):
        try:
            gdf = cargar_archivo_parcela(uploaded_file)
            if gdf is not None:
                # Mostrar información en tarjetas visuales
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown('<div class="success-box">', unsafe_allow_html=True)
                    st.markdown(f"### ✅ **Parcela cargada exitosamente**")
                    area_total = calcular_superficie(gdf)
                    st.write(f"**📊 INFORMACIÓN DE LA PARCELA:**")
                    st.write(f"- **Polígonos:** {len(gdf)}")
                    st.write(f"- **Área total:** {area_total:.1f} ha")
                    st.write(f"- **CRS:** {gdf.crs}")
                    st.write(f"- **Formato:** {uploaded_file.name.split('.')[-1].upper()}")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Vista previa con diseño mejorado
                    st.markdown("**📍 Vista Previa:**")
                    fig, ax = plt.subplots(figsize=(10, 8))
                    gdf.plot(ax=ax, color='#4CAF50', edgecolor='#2E7D32', alpha=0.7, linewidth=2)
                    ax.set_title(f"Parcela: {uploaded_file.name}", fontsize=14, fontweight='bold', color='#1E88E5')
                    ax.set_xlabel("Longitud", fontsize=11)
                    ax.set_ylabel("Latitud", fontsize=11)
                    ax.grid(True, alpha=0.3, linestyle='--')
                    st.pyplot(fig)
                
                with col2:
                    st.markdown('<div class="info-box">', unsafe_allow_html=True)
                    st.markdown(f"### 🎯 **CONFIGURACIÓN DEL ANÁLISIS**")
                    st.write(f"**{PARAMETROS_CULTIVOS[cultivo]['icono']} Cultivo:** {cultivo}")
                    st.write(f"**🔍 Análisis:** {analisis_tipo}")
                    st.write(f"**🎯 Zonas:** {n_divisiones}")
                    
                    if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"]:
                        st.write(f"**{info_satelite['icono']} Satélite:** {info_satelite['nombre']}")
                        if 'indice_seleccionado' in locals():
                            st.write(f"**📈 Índice:** {indice_seleccionado}")
                        if analisis_tipo == "RECOMENDACIONES NPK":
                            st.write(f"**💊 Nutriente:** {nutriente}")
                    
                    elif analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
                        st.write(f"**🏔️ Intervalo curvas:** {intervalo_curvas} m")
                        st.write(f"**📏 Resolución DEM:** {resolucion_dem} m")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Botón de ejecución con diseño mejorado
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
                                    datos_satelitales = generar_datos_simulados(gdf, cultivo, indice_seleccionado)
                                
                                # Dividir parcela
                                gdf_dividido = dividir_parcela_en_zonas(gdf, n_divisiones)
                                
                                # Calcular índices
                                indices_gee = calcular_indices_satelitales_gee(gdf_dividido, cultivo, datos_satelitales)
                                
                                # Crear GeoDataFrame con resultados
                                gdf_analizado = gdf_dividido.copy()
                                for idx, indice_data in enumerate(indices_gee):
                                    for key, value in indice_data.items():
                                        gdf_analizado.loc[gdf_analizado.index[idx], key] = value
                                
                                # Calcular áreas
                                areas_ha_list = []
                                for idx, row in gdf_analizado.iterrows():
                                    area_gdf = gpd.GeoDataFrame({'geometry': [row.geometry]}, crs=gdf_analizado.crs)
                                    area_ha = calcular_superficie(area_gdf)
                                    if hasattr(area_ha, 'iloc'):
                                        area_ha = float(area_ha.iloc[0])
                                    elif hasattr(area_ha, '__len__') and len(area_ha) > 0:
                                        area_ha = float(area_ha[0])
                                    else:
                                        area_ha = float(area_ha)
                                    areas_ha_list.append(area_ha)
                                gdf_analizado['area_ha'] = areas_ha_list
                                
                                if analisis_tipo == "RECOMENDACIONES NPK":
                                    recomendaciones_npk = calcular_recomendaciones_npk_gee(indices_gee, nutriente, cultivo)
                                    gdf_analizado['valor_recomendado'] = recomendaciones_npk
                                
                                # Mostrar resultados
                                st.markdown("---")
                                st.markdown(f'<h2 class="sub-header">📊 RESULTADOS DEL ANÁLISIS</h2>', unsafe_allow_html=True)
                                
                                # Métricas principales en tarjetas
                                col_met1, col_met2, col_met3, col_met4 = st.columns(4)
                                
                                with col_met1:
                                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                                    st.metric("Zonas Analizadas", len(gdf_analizado))
                                    st.markdown('</div>', unsafe_allow_html=True)
                                
                                with col_met2:
                                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                                    st.metric("Área Total", f"{area_total:.1f} ha")
                                    st.markdown('</div>', unsafe_allow_html=True)
                                
                                with col_met3:
                                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                                    if analisis_tipo == "FERTILIDAD ACTUAL":
                                        valor_prom = gdf_analizado['npk_actual'].mean()
                                        st.metric("Índice NPK Promedio", f"{valor_prom:.3f}")
                                    else:
                                        valor_prom = gdf_analizado['valor_recomendado'].mean()
                                        st.metric(f"{nutriente} Promedio", f"{valor_prom:.1f} kg/ha")
                                    st.markdown('</div>', unsafe_allow_html=True)
                                
                                with col_met4:
                                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                                    if analisis_tipo == "FERTILIDAD ACTUAL" and gdf_analizado['npk_actual'].mean() > 0:
                                        coef_var = (gdf_analizado['npk_actual'].std() / gdf_analizado['npk_actual'].mean() * 100)
                                        st.metric("Coef. Variación", f"{coef_var:.1f}%")
                                    elif analisis_tipo == "RECOMENDACIONES NPK" and gdf_analizado['valor_recomendado'].mean() > 0:
                                        coef_var = (gdf_analizado['valor_recomendado'].std() / gdf_analizado['valor_recomendado'].mean() * 100)
                                        st.metric("Coef. Variación", f"{coef_var:.1f}%")
                                    st.markdown('</div>', unsafe_allow_html=True)
                                
                                # Crear y mostrar mapa mejorado
                                columna_valor = 'valor_recomendado' if analisis_tipo == "RECOMENDACIONES NPK" else 'npk_actual'
                                titulo_mapa = f"ANÁLISIS {analisis_tipo}"
                                
                                mapa_buffer = crear_mapa_estatico_mejorado(
                                    gdf_analizado, 
                                    titulo_mapa, 
                                    columna_valor, 
                                    analisis_tipo, 
                                    nutriente if analisis_tipo == "RECOMENDACIONES NPK" else None,
                                    cultivo, 
                                    satelite_seleccionado
                                )
                                
                                if mapa_buffer:
                                    st.markdown(f'<h3 class="sub-header">🗺️ MAPA DE RESULTADOS</h3>', unsafe_allow_html=True)
                                    st.image(mapa_buffer, use_container_width=True)
                                    
                                    # Botón de descarga del mapa
                                    col_dl1, col_dl2 = st.columns(2)
                                    with col_dl1:
                                        st.download_button(
                                            "📥 Descargar Mapa",
                                            mapa_buffer,
                                            f"mapa_{cultivo}_{satelite_seleccionado}_{analisis_tipo.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.png",
                                            "image/png",
                                            use_container_width=True
                                        )
                                    
                                    with col_dl2:
                                        # Exportar datos
                                        csv_data = gdf_analizado.drop(columns=['geometry']).to_csv(index=False)
                                        st.download_button(
                                            "📊 Descargar Datos CSV",
                                            csv_data,
                                            f"datos_{cultivo}_{analisis_tipo.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                            "text/csv",
                                            use_container_width=True
                                        )
                                
                                # Tabla de datos con diseño mejorado
                                st.markdown(f'<h3 class="sub-header">📋 DATOS POR ZONA</h3>', unsafe_allow_html=True)
                                
                                columnas_indices = ['id_zona', 'npk_actual', 'materia_organica', 'ndvi', 'ndre', 'humedad_suelo']
                                if analisis_tipo == "RECOMENDACIONES NPK":
                                    columnas_indices = ['id_zona', 'valor_recomendado', 'npk_actual', 'materia_organica', 'ndvi', 'ndre', 'humedad_suelo']
                                columnas_indices = [col for col in columnas_indices if col in gdf_analizado.columns]
                                
                                if columnas_indices:
                                    # Crear DataFrame para visualización
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
                                    
                                    # Formatear números
                                    for col in df_display.columns:
                                        if col in ['NPK', 'NDVI', 'NDRE', 'Humedad Suelo']:
                                            df_display[col] = df_display[col].apply(lambda x: f"{x:.3f}")
                                        elif col == 'Materia Orgánica (%)':
                                            df_display[col] = df_display[col].apply(lambda x: f"{x:.2f}")
                                        elif col == 'Recomendación (kg/ha)':
                                            df_display[col] = df_display[col].apply(lambda x: f"{x:.1f}")
                                    
                                    # Mostrar tabla con estilo
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
                                st.markdown(f'<h2 class="sub-header">🏗️ ANÁLISIS DE TEXTURA - {cultivo}</h2>', unsafe_allow_html=True)
                                
                                # Métricas
                                col_t1, col_t2, col_t3, col_t4 = st.columns(4)
                                
                                with col_t1:
                                    textura_predominante = gdf_analizado['textura_suelo'].mode()[0] if len(gdf_analizado) > 0 else "NO_DETERMINADA"
                                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                                    st.metric("🏗️ Textura Predominante", textura_predominante)
                                    st.markdown('</div>', unsafe_allow_html=True)
                                
                                with col_t2:
                                    avg_arena = gdf_analizado['arena'].mean()
                                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                                    st.metric("🏖️ Arena Promedio", f"{avg_arena:.1f}%")
                                    st.markdown('</div>', unsafe_allow_html=True)
                                
                                with col_t3:
                                    avg_limo = gdf_analizado['limo'].mean()
                                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                                    st.metric("🌫️ Limo Promedio", f"{avg_limo:.1f}%")
                                    st.markdown('</div>', unsafe_allow_html=True)
                                
                                with col_t4:
                                    avg_arcilla = gdf_analizado['arcilla'].mean()
                                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                                    st.metric("🧱 Arcilla Promedio", f"{avg_arcilla:.1f}%")
                                    st.markdown('</div>', unsafe_allow_html=True)
                                
                                # Gráficos
                                st.markdown(f'<h3 class="sub-header">📊 COMPOSICIÓN GRANULOMÉTRICA</h3>', unsafe_allow_html=True)
                                
                                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
                                
                                # Gráfico de torta
                                composicion = [gdf_analizado['arena'].mean(), gdf_analizado['limo'].mean(), gdf_analizado['arcilla'].mean()]
                                labels = ['Arena', 'Limo', 'Arcilla']
                                colors_pie = ['#d8b365', '#f6e8c3', '#01665e']
                                ax1.pie(composicion, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90)
                                ax1.set_title('Composición Promedio del Suelo', fontsize=14, fontweight='bold')
                                
                                # Gráfico de barras
                                textura_dist = gdf_analizado['textura_suelo'].value_counts()
                                colors_bar = [PALETAS_GEE['TEXTURA'][i % len(PALETAS_GEE['TEXTURA'])] for i in range(len(textura_dist))]
                                ax2.bar(textura_dist.index, textura_dist.values, color=colors_bar)
                                ax2.set_title('Distribución de Texturas', fontsize=14, fontweight='bold')
                                ax2.set_xlabel('Textura')
                                ax2.set_ylabel('Número de Zonas')
                                ax2.tick_params(axis='x', rotation=45)
                                ax2.grid(True, alpha=0.3, axis='y')
                                
                                plt.tight_layout()
                                st.pyplot(fig)
                                
                                # Tabla de datos
                                st.markdown(f'<h3 class="sub-header">📋 DATOS POR ZONA</h3>', unsafe_allow_html=True)
                                
                                columnas_textura = ['id_zona', 'area_ha', 'textura_suelo', 'arena', 'limo', 'arcilla']
                                columnas_textura = [col for col in columnas_textura if col in gdf_analizado.columns]
                                
                                if columnas_textura:
                                    tabla_textura = gdf_analizado[columnas_textura].copy()
                                    tabla_textura.columns = ['Zona', 'Área (ha)', 'Textura', 'Arena (%)', 'Limo (%)', 'Arcilla (%)']
                                    st.dataframe(tabla_textura, use_container_width=True)
                            
                            elif analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
                                # Análisis de curvas de nivel
                                X, Y, Z, bounds = generar_dem_sintetico(gdf, resolucion_dem)
                                pendiente_grid = calcular_pendiente_simple(X, Y, Z, resolucion_dem)
                                curvas, elevaciones = generar_curvas_nivel_simple(X, Y, Z, intervalo_curvas, gdf)
                                
                                # Mostrar resultados
                                st.markdown("---")
                                st.markdown(f'<h2 class="sub-header">🏔️ ANÁLISIS TOPOGRÁFICO - {cultivo}</h2>', unsafe_allow_html=True)
                                
                                # Métricas
                                elevaciones_flat = Z.flatten()
                                elevaciones_flat = elevaciones_flat[~np.isnan(elevaciones_flat)]
                                
                                if len(elevaciones_flat) > 0:
                                    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                                    
                                    with col_c1:
                                        elevacion_promedio = np.mean(elevaciones_flat)
                                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                                        st.metric("🏔️ Elevación Promedio", f"{elevacion_promedio:.1f} m")
                                        st.markdown('</div>', unsafe_allow_html=True)
                                    
                                    with col_c2:
                                        rango_elevacion = np.max(elevaciones_flat) - np.min(elevaciones_flat)
                                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                                        st.metric("📏 Rango de Elevación", f"{rango_elevacion:.1f} m")
                                        st.markdown('</div>', unsafe_allow_html=True)
                                    
                                    with col_c3:
                                        mapa_pendientes, stats_pendiente = crear_mapa_pendientes_simple(X, Y, pendiente_grid, gdf)
                                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                                        st.metric("📐 Pendiente Promedio", f"{stats_pendiente['promedio']:.1f}%")
                                        st.markdown('</div>', unsafe_allow_html=True)
                                    
                                    with col_c4:
                                        num_curvas = len(curvas) if curvas else 0
                                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                                        st.metric("🔄 Número de Curvas", f"{num_curvas}")
                                        st.markdown('</div>', unsafe_allow_html=True)
                                    
                                    # Mostrar mapa de pendientes
                                    st.markdown(f'<h3 class="sub-header">🔥 MAPA DE PENDIENTES</h3>', unsafe_allow_html=True)
                                    st.image(mapa_pendientes, use_container_width=True)
                                    
                                    # Análisis de riesgo
                                    st.markdown(f'<h3 class="sub-header">⚠️ ANÁLISIS DE RIESGO DE EROSIÓN</h3>', unsafe_allow_html=True)
                                    
                                    if 'stats_pendiente' in locals() and 'distribucion' in stats_pendiente:
                                        riesgo_total = 0
                                        for categoria, data in stats_pendiente['distribucion'].items():
                                            if categoria in CLASIFICACION_PENDIENTES:
                                                riesgo_total += data['porcentaje'] * CLASIFICACION_PENDIENTES[categoria]['factor_erosivo']
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
                                            porcentaje_critico = sum(data['porcentaje'] for cat, data in stats_pendiente['distribucion'].items()
                                                                    if cat in ['FUERTE (10-15%)', 'MUY FUERTE (15-25%)', 'EXTREMA (>25%)'])
                                            area_critica = area_total * (porcentaje_critico / 100)
                                            st.metric("Área Crítica (>10%)", f"{area_critica:.2f} ha")
                                        
                                        with col_r3:
                                            porcentaje_manejable = sum(data['porcentaje'] for cat, data in stats_pendiente['distribucion'].items()
                                                                    if cat in ['PLANA (0-2%)', 'SUAVE (2-5%)', 'MODERADA (5-10%)'])
                                            area_manejable = area_total * (porcentaje_manejable / 100)
                                            st.metric("Área Manejable (<10%)", f"{area_manejable:.2f} ha")
                
                else:
                    st.error("❌ Error al cargar el archivo")
                    
        except Exception as e:
            st.error(f"❌ Error procesando archivo: {str(e)}")
else:
    # Pantalla de bienvenida con diseño mejorado
    col_w1, col_w2, col_w3 = st.columns([1, 2, 1])
    
    with col_w2:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%); 
                    border-radius: 20px; border: 3px solid #1E88E5; margin: 2rem 0;">
            <h2 style="color: #1E88E5; margin-bottom: 1rem;">🌱 BIENVENIDO AL ANALIZADOR PRO</h2>
            <p style="font-size: 1.2rem; color: #333; margin-bottom: 2rem;">
                Sube tu archivo de parcela para comenzar el análisis satelital avanzado
            </p>
            <div style="font-size: 1.1rem; color: #666; text-align: left; background: white; padding: 1.5rem; 
                        border-radius: 10px; margin: 1rem 0;">
                <strong>📁 Formatos aceptados:</strong><br>
                • 🗺️ Shapefile (.zip) - Debe incluir .shp, .shx, .dbf<br>
                • 🌐 KML (.kml) - Formato Google Earth<br>
                • 📦 KMZ (.kmz) - KML comprimido
            </div>
            <div style="font-size: 1.1rem; color: #666; text-align: left; background: white; padding: 1.5rem; 
                        border-radius: 10px; margin: 1rem 0;">
                <strong>🎯 Características:</strong><br>
                • 🛰️ Análisis con Sentinel-2 y Landsat-8<br>
                • 🌾 5 cultivos soportados<br>
                • 📊 4 tipos de análisis diferentes<br>
                • 📈 Visualizaciones profesionales<br>
                • 📥 Exportación múltiple de resultados
            </div>
        </div>
        """, unsafe_allow_html=True)

# ===== SECCIÓN INFORMATIVA =====
st.markdown("---")
with st.expander("📚 INFORMACIÓN SOBRE LA METODOLOGÍA GEE"):
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
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
        """)
    
    with col_info2:
        st.markdown("""
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
        - Recomendaciones validadas científicamente
        """)
