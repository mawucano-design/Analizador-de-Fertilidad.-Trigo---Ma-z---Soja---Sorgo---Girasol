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

# ===== CONFIGURACIÓN DE PÁGINA CON CSS MEJORADO =====
st.set_page_config(
    page_title="🌱 Analizador Multi-Cultivo Satellital",
    layout="wide",
    page_icon="🛰️"
)

# ===== INICIALIZACIÓN DE VARIABLES GLOBALES =====
# IMPORTANTE: Definir todas las variables aquí para evitar errores
nutriente = None
satelite_seleccionado = "SENTINEL-2"
indice_seleccionado = "NDVI"  # Valor por defecto para evitar errores
fecha_inicio = datetime.now() - timedelta(days=30)
fecha_fin = datetime.now()
intervalo_curvas = 5.0
resolucion_dem = 10.0

# ===== CSS PERSONALIZADO PARA INTERFAZ PROFESIONAL =====
st.markdown("""
<style>
    /* FONDO GENERAL CON GRADIENTE SUTIL */
    .stApp {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* ENCABEZADO CON IMAGEN DE FONDO DE TRIGO */
    .main-header {
        background-image: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), 
                          url('https://images.unsplash.com/photo-1500382017468-9049fed747ef?ixlib=rb-1.2.1&auto=format&fit=crop&w=1600&q=80');
        background-size: cover;
        background-position: center 40%;
        padding: 50px 30px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }
    
    /* TARJETAS DE MÉTRICAS PROFESIONALES */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-left: 5px solid #28a745;
        margin: 10px 0;
        transition: all 0.3s ease;
        height: 100%;
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.12);
    }
    
    /* BOTONES MEJORADOS */
    .stButton > button {
        background: linear-gradient(45deg, #28a745, #20c997);
        color: white;
        border: none;
        padding: 12px 28px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px rgba(40, 167, 69, 0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(40, 167, 69, 0.3);
    }
    
    /* MEJORAR LOS SELECTBOX */
    .stSelectbox > div > div {
        border: 2px solid #28a745;
        border-radius: 8px;
        background: white;
    }
    
    /* MEJORAR LAS PESTAÑAS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #f8f9fa;
        padding: 10px;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 500;
        border: 1px solid #dee2e6;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(45deg, #28a745, #20c997);
        color: white !important;
        border: none;
    }
    
    /* MEJORAR LOS SLIDERS */
    .stSlider > div > div {
        background: #28a745;
    }
    
    /* TARJETAS DE EXPANSIÓN MEJORADAS */
    .streamlit-expanderHeader {
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        font-weight: 600;
        font-size: 1.1em;
        border-left: 4px solid #28a745;
    }
    
    /* FOOTER PROFESIONAL */
    .custom-footer {
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
        padding: 25px;
        border-radius: 15px;
        margin-top: 30px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(40, 167, 69, 0.2);
    }
    
    /* DASHBOARD CARD PARA ESTADO DEL CULTIVO */
    .dashboard-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        text-align: center;
        transition: all 0.3s ease;
        height: 100%;
    }
    
    .dashboard-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.12);
    }
    
    /* ANIMACIÓN SUTIL PARA LAS MÉTRICAS */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .metric-card, .dashboard-card {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* ESTILOS PARA LAS TABLAS */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    
    /* MEJORAR EL SIDEBAR */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
        color: white;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] .stSubheader,
    [data-testid="stSidebar"] .stMarkdown {
        color: white !important;
    }
    
    /* SCROLLBAR PERSONALIZADO */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #28a745;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #20c997;
    }
</style>
""", unsafe_allow_html=True)

# ===== ENCABEZADO PRINCIPAL MEJORADO =====
st.markdown("""
<div class="main-header">
    <h1 style="font-size: 3.2em; margin-bottom: 15px; font-weight: 700;">🌾 ANALIZADOR MULTI-CULTIVO</h1>
    <h3 style="font-weight: 400; color: #e9ecef; margin-bottom: 20px;">SENTINEL-2 & LANDSAT-8</h3>
    <p style="font-size: 1.2em; color: #f8f9fa; max-width: 800px; margin: 0 auto; line-height: 1.6;">
        Dashboard profesional para agricultura de precisión con análisis satelital avanzado
    </p>
    <div style="margin-top: 25px; display: flex; justify-content: center; gap: 15px;">
        <div style="background: rgba(255,255,255,0.1); padding: 8px 16px; border-radius: 20px; font-size: 0.9em;">
            🌱 5 Cultivos Soportados
        </div>
        <div style="background: rgba(255,255,255,0.1); padding: 8px 16px; border-radius: 20px; font-size: 0.9em;">
            🛰️ 3 Fuentes Satelitales
        </div>
        <div style="background: rgba(255,255,255,0.1); padding: 8px 16px; border-radius: 20px; font-size: 0.9em;">
            📊 4 Tipos de Análisis
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ===== CONFIGURACIÓN DE SATÉLITES DISPONIBLES =====
SATELITES_DISPONIBLES = {
    'SENTINEL-2': {
        'nombre': 'Sentinel-2',
        'resolucion': '10m',
        'revisita': '5 días',
        'bandas': ['B2', 'B3', 'B4', 'B5', 'B8', 'B11'],
        'indices': ['NDVI', 'NDRE', 'GNDVI', 'OSAVI', 'MCARI'],
        'icono': '🛰️'
    },
    'LANDSAT-8': {
        'nombre': 'Landsat 8',
        'resolucion': '30m',
        'revisita': '16 días',
        'bandas': ['B2', 'B3', 'B4', 'B5', 'B6', 'B7'],
        'indices': ['NDVI', 'NDWI', 'EVI', 'SAVI', 'MSAVI'],
        'icono': '🛰️'
    },
    'DATOS_SIMULADOS': {
        'nombre': 'Datos Simulados',
        'resolucion': '10m',
        'revisita': '5 días',
        'bandas': ['B2', 'B3', 'B4', 'B5', 'B8'],
        'indices': ['NDVI', 'NDRE', 'GNDVI'],
        'icono': '🔬'
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
        'MATERIA_ORGANica_OPTIMA': 3.2,
        'HUMEDAD_OPTIMA': 0.26,
        'NDVI_OPTIMO': 0.55,
        'NDRE_OPTIMO': 0.25
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

# ICONOS Y COLORES POR CULTIVO
ICONOS_CULTIVOS = {
    'TRIGO': '🌾',
    'MAÍZ': '🌽',
    'SOJA': '🫘',
    'SORGO': '🌾',
    'GIRASOL': '🌻'
}

COLORES_CULTIVOS = {
    'TRIGO': '#FFD700',
    'MAÍZ': '#FFA500',
    'SOJA': '#8B4513',
    'SORGO': '#D2691E',
    'GIRASOL': '#FFD700'
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

# ===== SIDEBAR MEJORADO CON IMÁGENES =====
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 10px;">
        <h2 style="color: white; margin-bottom: 5px;">⚙️ CONFIGURACIÓN</h2>
        <div style="height: 3px; background: linear-gradient(90deg, #28a745, #20c997); margin: 0 auto 20px; width: 80%;"></div>
    </div>
    """, unsafe_allow_html=True)
    
    cultivo = st.selectbox("**Cultivo:**", ["TRIGO", "MAÍZ", "SOJA", "SORGO", "GIRASOL"])
    analisis_tipo = st.selectbox("**Tipo de Análisis:**", ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK", "ANÁLISIS DE TEXTURA", "ANÁLISIS DE CURVAS DE NIVEL"])
    
    # Reinicializar nutriente según el tipo de análisis
    if analisis_tipo == "RECOMENDACIONES NPK":
        nutriente = st.selectbox("**Nutriente:**", ["NITRÓGENO", "FÓSFORO", "POTASIO"])
    else:
        nutriente = None

    st.markdown("---")
    st.markdown("### 🛰️ FUENTE DE DATOS")
    
    # Imagen del cultivo seleccionado en el sidebar
    cultivo_imagenes = {
        'TRIGO': 'https://images.unsplash.com/photo-1500382017468-9049fed747ef?ixlib=rb-1.2.1&auto=format&fit=crop&w=600&q=80',
        'MAÍZ': 'https://images.unsplash.com/photo-1625246333195-78d9c38ad449?ixlib=rb-1.2.1&auto=format&fit=crop&w=600&q=80',
        'SOJA': 'https://images.unsplash.com/photo-1596105314417-9c8b0f2b5c4a?ixlib=rb-1.2.1&auto=format&fit=crop&w=600&q=80',
        'SORGO': 'https://images.unsplash.com/photo-1592656094267-764a8c8c6b7b?ixlib=rb-1.2.1&auto=format&fit=crop&w=600&q=80',
        'GIRASOL': 'https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?ixlib=rb-1.2.1&auto=format&fit=crop&w=600&q=80'
    }
    
    st.image(cultivo_imagenes.get(cultivo, 'https://images.unsplash.com/photo-1500382017468-9049fed747ef'), 
             caption=f"{ICONOS_CULTIVOS.get(cultivo, '🌾')} {cultivo}",
             use_column_width=True)
    
    satelite_seleccionado = st.selectbox(
        "**Satélite:**",
        ["SENTINEL-2", "LANDSAT-8", "DATOS_SIMULADOS"],
        help="Selecciona la fuente de datos satelitales"
    )
    
    if satelite_seleccionado in SATELITES_DISPONIBLES:
        info_satelite = SATELITES_DISPONIBLES[satelite_seleccionado]
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin: 10px 0;">
            <div style="font-size: 1.2em; font-weight: bold; color: #20c997;">
                {info_satelite['icono']} {info_satelite['nombre']}
            </div>
            <div style="font-size: 0.9em; color: #f8f9fa;">
                📐 Resolución: {info_satelite['resolucion']}<br>
                🔄 Revisita: {info_satelite['revisita']}<br>
                📊 Índices: {', '.join(info_satelite['indices'][:3])}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Solo mostrar configuración de índices para análisis que lo requieren
    if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"]:
        st.markdown("### 📊 ÍNDICES DE VEGETACIÓN")
        if satelite_seleccionado == "SENTINEL-2":
            indice_seleccionado = st.selectbox("**Índice:**", SATELITES_DISPONIBLES['SENTINEL-2']['indices'])
        elif satelite_seleccionado == "LANDSAT-8":
            indice_seleccionado = st.selectbox("**Índice:**", SATELITES_DISPONIBLES['LANDSAT-8']['indices'])
        else:
            indice_seleccionado = st.selectbox("**Índice:**", SATELITES_DISPONIBLES['DATOS_SIMULADOS']['indices'])
    else:
        # Para otros tipos de análisis, usar valor por defecto
        indice_seleccionado = "NDVI"

    if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"]:
        st.markdown("### 📅 RANGO TEMPORAL")
        fecha_fin = st.date_input("**Fecha fin**", datetime.now())
        fecha_inicio = st.date_input("**Fecha inicio**", datetime.now() - timedelta(days=30))

    st.markdown("### 🎯 DIVISIÓN DE PARCELA")
    n_divisiones = st.slider("**Número de zonas de manejo:**", min_value=16, max_value=48, value=32, step=4)

    if analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
        st.markdown("### 🏔️ CONFIGURACIÓN CURVAS")
        intervalo_curvas = st.slider("**Intervalo entre curvas (metros):**", 1.0, 20.0, 5.0, 1.0)
        resolucion_dem = st.slider("**Resolución DEM (metros):**", 5.0, 50.0, 10.0, 5.0)

    st.markdown("### 📤 SUBIR PARCELA")
    uploaded_file = st.file_uploader("**Subir archivo de tu parcela**", type=['zip', 'kml', 'kmz'],
                                     help="Formatos aceptados: Shapefile (.zip), KML (.kml), KMZ (.kmz)")
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #f8f9fa; font-size: 0.8em;">
        <p>🌐 <strong>Analizador Multi-Cultivo v2.0</strong></p>
        <p>🛰️ Agricultura de Precisión</p>
    </div>
    """, unsafe_allow_html=True)

# ===== FUNCIONES AUXILIARES =====
def validar_y_corregir_crs(gdf):
    if gdf is None or len(gdf) == 0:
        return gdf
    try:
        if gdf.crs is None:
            gdf = gdf.set_crs('EPSG:4326', inplace=False)
            st.info("ℹ️ Se asignó EPSG:4326 al archivo (no tenía CRS)")
        elif str(gdf.crs).upper() != 'EPSG:4326':
            original_crs = str(gdf.crs)
            gdf = gdf.to_crs('EPSG:4326')
            st.info(f"ℹ️ Transformado de {original_crs} a EPSG:4326")
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
            st.warning("⚠️ Coordenadas fuera de rango para cálculo preciso de área")
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

# ===== FUNCIONES PARA CARGAR ARCHIVOS =====
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
        else:
            for placemark in root.findall('.//kml:Placemark', namespaces):
                for elem_name in ['Polygon', 'LineString', 'Point', 'LinearRing']:
                    elem = placemark.find(f'.//kml:{elem_name}', namespaces)
                    if elem is not None:
                        coords_elem = elem.find('.//kml:coordinates', namespaces)
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
                            break

        if polygons:
            gdf = gpd.GeoDataFrame({'geometry': polygons}, crs='EPSG:4326')
            return gdf
        return None
    except Exception as e:
        st.error(f"❌ Error parseando KML manualmente: {str(e)}")
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
                            st.error("❌ No se pudo cargar el archivo KML/KMZ")
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
                if str(gdf.crs).upper() != 'EPSG:4326':
                    st.warning(f"⚠️ El archivo no pudo ser convertido a EPSG:4326. CRS actual: {gdf.crs}")
                return gdf
            else:
                st.error("❌ No se encontraron polígonos en el archivo")
                return None
    except Exception as e:
        st.error(f"❌ Error cargando archivo: {str(e)}")
        import traceback
        st.error(f"Detalle: {traceback.format_exc()}")
        return None

# ===== FUNCIONES PARA DATOS SATELITALES =====
def descargar_datos_landsat8(gdf, fecha_inicio, fecha_fin, indice='NDVI'):
    try:
        st.info(f"🔍 Buscando escenas Landsat 8...")
        datos_simulados = {
            'indice': indice,
            'valor_promedio': 0.65 + np.random.normal(0, 0.1),
            'fuente': 'Landsat-8',
            'fecha': datetime.now().strftime('%Y-%m-%d'),
            'id_escena': f"LC08_{np.random.randint(1000000, 9999999)}",
            'cobertura_nubes': f"{np.random.randint(0, 15)}%",
            'resolucion': '30m'
        }
        st.success(f"✅ Escena Landsat 8 encontrada: {datos_simulados['id_escena']}")
        st.info(f"☁️ Cobertura de nubes: {datos_simulados['cobertura_nubes']}")
        return datos_simulados
    except Exception as e:
        st.error(f"❌ Error procesando Landsat 8: {str(e)}")
        return None

def descargar_datos_sentinel2(gdf, fecha_inicio, fecha_fin, indice='NDVI'):
    try:
        st.info(f"🔍 Buscando escenas Sentinel-2...")
        datos_simulados = {
            'indice': indice,
            'valor_promedio': 0.72 + np.random.normal(0, 0.08),
            'fuente': 'Sentinel-2',
            'fecha': datetime.now().strftime('%Y-%m-%d'),
            'id_escena': f"S2A_{np.random.randint(1000000, 9999999)}",
            'cobertura_nubes': f"{np.random.randint(0, 10)}%",
            'resolucion': '10m'
        }
        st.success(f"✅ Escena Sentinel-2 encontrada: {datos_simulados['id_escena']}")
        st.info(f"☁️ Cobertura de nubes: {datos_simulados['cobertura_nubes']}")
        return datos_simulados
    except Exception as e:
        st.error(f"❌ Error procesando Sentinel-2: {str(e)}")
        return None

def generar_datos_simulados(gdf, cultivo, indice='NDVI'):
    st.info("🔬 Generando datos simulados...")
    datos_simulados = {
        'indice': indice,
        'valor_promedio': PARAMETROS_CULTIVOS[cultivo]['NDVI_OPTIMO'] * 0.8 + np.random.normal(0, 0.1),
        'fuente': 'Simulación',
        'fecha': datetime.now().strftime('%Y-%m-%d'),
        'resolucion': '10m'
    }
    st.success("✅ Datos simulados generados")
    return datos_simulados

# ===== FUNCIONES DE ANÁLISIS GEE =====
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

# ===== FUNCIONES DE TEXTURA DEL SUELO =====
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

# ===== FUNCIONES DE CURVAS DE NIVEL =====
def clasificar_pendiente(pendiente_porcentaje):
    for categoria, params in CLASIFICACION_PENDIENTES.items():
        if params['min'] <= pendiente_porcentaje < params['max']:
            return categoria, params['color']
    return "EXTREMA (>25%)", CLASIFICACION_PENDIENTES['EXTREMA (>25%)']['color']

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

# ===== FUNCIONES DE EXPORTACIÓN Y REPORTES =====
def exportar_a_geojson(gdf, nombre_base="parcela"):
    try:
        gdf = validar_y_corregir_crs(gdf)
        geojson_data = gdf.to_json()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"{nombre_base}_{timestamp}.geojson"
        return geojson_data, nombre_archivo
    except Exception as e:
        st.error(f"❌ Error exportando a GeoJSON: {str(e)}")
        return None, None

def generar_resumen_estadisticas(gdf_analizado, analisis_tipo, cultivo):
    estadisticas = {}
    try:
        if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"]:
            if 'npk_actual' in gdf_analizado.columns:
                estadisticas['Índice NPK Promedio'] = f"{gdf_analizado['npk_actual'].mean():.3f}"
                estadisticas['Índice NPK Mínimo'] = f"{gdf_analizado['npk_actual'].min():.3f}"
                estadisticas['Índice NPK Máximo'] = f"{gdf_analizado['npk_actual'].max():.3f}"
            if 'ndvi' in gdf_analizado.columns:
                estadisticas['NDVI Promedio'] = f"{gdf_analizado['ndvi'].mean():.3f}"
            if 'materia_organica' in gdf_analizado.columns:
                estadisticas['Materia Orgánica Promedio'] = f"{gdf_analizado['materia_organica'].mean():.1f}%"
        elif analisis_tipo == "ANÁLISIS DE TEXTURA":
            if 'arena' in gdf_analizado.columns:
                estadisticas['Arena Promedio'] = f"{gdf_analizado['arena'].mean():.1f}%"
                estadisticas['Limo Promedio'] = f"{gdf_analizado['limo'].mean():.1f}%"
                estadisticas['Arcilla Promedio'] = f"{gdf_analizado['arcilla'].mean():.1f}%"
            if 'textura_suelo' in gdf_analizado.columns:
                textura_predominante = gdf_analizado['textura_suelo'].mode()[0] if len(gdf_analizado) > 0 else "N/D"
                estadisticas['Textura Predominante'] = textura_predominante
        if 'area_ha' in gdf_analizado.columns:
            estadisticas['Área Promedio por Zona'] = f"{gdf_analizado['area_ha'].mean():.2f} ha"
            if gdf_analizado['area_ha'].mean() > 0:
                estadisticas['Coeficiente de Variación'] = f"{(gdf_analizado['area_ha'].std() / gdf_analizado['area_ha'].mean() * 100):.1f}%"
    except Exception as e:
        st.warning(f"No se pudieron calcular algunas estadísticas: {str(e)}")
    return estadisticas

def generar_recomendaciones_generales(gdf_analizado, analisis_tipo, cultivo):
    recomendaciones = []
    try:
        if analisis_tipo == "FERTILIDAD ACTUAL":
            if 'npk_actual' in gdf_analizado.columns:
                npk_promedio = gdf_analizado['npk_actual'].mean()
                if npk_promedio < 0.3:
                    recomendaciones.append("Fertilidad MUY BAJA: Se recomienda aplicación urgente de fertilizantes balanceados")
                    recomendaciones.append("Considerar enmiendas orgánicas para mejorar la estructura del suelo")
                elif npk_promedio < 0.5:
                    recomendaciones.append("Fertilidad BAJA: Recomendada aplicación de fertilizantes según análisis de suelo")
                elif npk_promedio < 0.7:
                    recomendaciones.append("Fertilidad ADECUADA: Mantener prácticas de manejo actuales")
                else:
                    recomendaciones.append("Fertilidad ÓPTIMA: Excelente condición, continuar con manejo actual")
        elif analisis_tipo == "ANÁLISIS DE TEXTURA":
            if 'textura_suelo' in gdf_analizado.columns:
                textura_predominante = gdf_analizado['textura_suelo'].mode()[0] if len(gdf_analizado) > 0 else "N/D"
                if textura_predominante == "Arcilloso":
                    recomendaciones.append("Suelo arcilloso: Mejorar drenaje y evitar laboreo en condiciones húmedas")
                elif textura_predominante == "Arenoso":
                    recomendaciones.append("Suelo arenoso: Aumentar materia orgánica y considerar riego frecuente")
                elif textura_predominante == "Franco":
                    recomendaciones.append("Textura franca: Condiciones óptimas, mantener prácticas de conservación")
        if cultivo == "MAÍZ":
            recomendaciones.append("Para maíz: Considerar fertilización nitrogenada en etapas críticas de crecimiento")
        elif cultivo == "SOJA":
            recomendaciones.append("Para soja: Asegurar inoculación adecuada para fijación biológica de nitrógeno")
        elif cultivo == "TRIGO":
            recomendaciones.append("Para trigo: Monitorear niveles de nitrógeno en etapas de macollaje y encañado")
        recomendaciones.append("Realizar análisis de suelo de laboratorio para validar resultados satelitales")
        recomendaciones.append("Considerar agricultura de precisión para aplicación variable de insumos")
    except Exception as e:
        recomendaciones.append("Error generando recomendaciones específicas")
    return recomendaciones

def limpiar_texto_para_pdf(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    reemplazos = {
        '\u2022': '-',
        '\u2705': '[OK]',
        '\u26A0\uFE0F': '[!]',
        '\u274C': '[X]',
        '\u2013': '-',
        '\u2014': '--',
        '\u2018': "'",
        '\u2019': "'",
        '\u201C': '"',
        '\u201D': '"',
        '\u2192': '->',
        '\u2190': '<-',
        '\u2265': '>=',
        '\u2264': '<=',
        '\u00A0': ' ',
    }
    for original, reemplazo in reemplazos.items():
        texto = texto.replace(original, reemplazo)
    texto = texto.encode('latin-1', errors='replace').decode('latin-1')
    return texto

def generar_reporte_pdf(gdf_analizado, cultivo, analisis_tipo, area_total,
                        nutriente=None, satelite=None, indice=None,
                        mapa_buffer=None, estadisticas=None, recomendaciones=None):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font('Arial', '', 12)

        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, limpiar_texto_para_pdf(f'REPORTE DE ANÁLISIS AGRÍCOLA - {cultivo}'), 0, 1, 'C')
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, limpiar_texto_para_pdf(f'Tipo de Análisis: {analisis_tipo}'), 0, 1, 'C')
        pdf.cell(0, 10, limpiar_texto_para_pdf(f'Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M")}'), 0, 1, 'C')
        pdf.ln(10)

        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, '1. INFORMACIÓN GENERAL', 0, 1)
        pdf.set_font('Arial', '', 12)
        info_general = f"""Cultivo: {cultivo}
Área Total: {area_total:.2f} ha
Zonas Analizadas: {len(gdf_analizado)}
Tipo de Análisis: {analisis_tipo}"""
        if satelite:
            info_general += f"\nSatélite: {satelite}"
        if indice:
            info_general += f"\nÍndice: {indice}"
        if nutriente:
            info_general += f"\nNutriente Analizado: {nutriente}"
        for linea in info_general.strip().split('\n'):
            pdf.cell(0, 8, limpiar_texto_para_pdf(linea), 0, 1)
        pdf.ln(5)

        if estadisticas:
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, '2. ESTADÍSTICAS PRINCIPALES', 0, 1)
            pdf.set_font('Arial', '', 12)
            for key, value in estadisticas.items():
                linea = f"- {key}: {value}"
                pdf.cell(0, 8, limpiar_texto_para_pdf(linea), 0, 1)
            pdf.ln(5)

        if mapa_buffer:
            try:
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, '3. MAPA DE RESULTADOS', 0, 1)
                temp_img_path = "temp_map.png"
                with open(temp_img_path, "wb") as f:
                    f.write(mapa_buffer.getvalue())
                pdf.image(temp_img_path, x=10, w=190)
                pdf.ln(5)
                if os.path.exists(temp_img_path):
                    os.remove(temp_img_path)
            except Exception as e:
                pdf.cell(0, 8, limpiar_texto_para_pdf(f"Error al incluir mapa: {str(e)[:50]}..."), 0, 1)

        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, '4. RESUMEN DE ZONAS', 0, 1)
        pdf.set_font('Arial', '', 10)
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
                datos_tabla = [columnas_mostrar]
                for _, row in gdf_analizado.head(15).iterrows():
                    fila = []
                    for col in columnas_mostrar:
                        if col in gdf_analizado.columns:
                            valor = row[col]
                            if isinstance(valor, float):
                                if col in ['npk_actual']:
                                    fila.append(f"{valor:.3f}")
                                else:
                                    fila.append(f"{valor:.2f}")
                            else:
                                fila.append(str(valor))
                        else:
                            fila.append("N/A")
                    datos_tabla.append(fila)
                col_widths = [190 // len(columnas_mostrar)] * len(columnas_mostrar)
                for fila in datos_tabla:
                    for i, item in enumerate(fila):
                        if i < len(col_widths):
                            pdf.cell(col_widths[i], 8, limpiar_texto_para_pdf(str(item)), border=1)
                    pdf.ln()
                pdf.ln(5)

        if recomendaciones:
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, '5. RECOMENDACIONES', 0, 1)
            pdf.set_font('Arial', '', 12)
            for rec in recomendaciones:
                linea = f"- {limpiar_texto_para_pdf(rec)}"
                pdf.multi_cell(0, 8, linea)

        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, '6. METADATOS TÉCNICOS', 0, 1)
        pdf.set_font('Arial', '', 10)
        metadatos = f"""Generado por: Analizador Multi-Cultivo Satellital
Versión: 2.0
Fecha de generación: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Sistema de coordenadas: EPSG:4326 (WGS84)
Número de zonas: {len(gdf_analizado)}"""
        for linea in metadatos.strip().split('\n'):
            pdf.cell(0, 6, limpiar_texto_para_pdf(linea), 0, 1)

        pdf_output = BytesIO()
        pdf_output.write(pdf.output(dest='S').encode('latin-1'))
        pdf_output.seek(0)
        return pdf_output
    except Exception as e:
        st.error(f"❌ Error generando PDF: {str(e)}")
        import traceback
        st.error(f"Detalle: {traceback.format_exc()}")
        return None

def generar_reporte_docx(gdf_analizado, cultivo, analisis_tipo, area_total,
                        nutriente=None, satelite=None, indice=None,
                        mapa_buffer=None, estadisticas=None, recomendaciones=None):
    try:
        doc = Document()
        title = doc.add_heading(f'REPORTE DE ANÁLISIS AGRÍCOLA - {cultivo}', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subtitle = doc.add_paragraph(f'Tipo de Análisis: {analisis_tipo}')
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fecha = doc.add_paragraph(f'Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M")}')
        fecha.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph()

        doc.add_heading('1. INFORMACIÓN GENERAL', level=1)
        info_table = doc.add_table(rows=4, cols=2)
        info_table.style = 'Table Grid'
        info_table.cell(0, 0).text = 'Cultivo'
        info_table.cell(0, 1).text = cultivo
        info_table.cell(1, 0).text = 'Área Total'
        info_table.cell(1, 1).text = f'{area_total:.2f} ha'
        info_table.cell(2, 0).text = 'Zonas Analizadas'
        info_table.cell(2, 1).text = str(len(gdf_analizado))
        info_table.cell(3, 0).text = 'Tipo de Análisis'
        info_table.cell(3, 1).text = analisis_tipo
        row_count = 4

        if satelite:
            if row_count >= len(info_table.rows):
                info_table.add_row()
            info_table.cell(row_count, 0).text = 'Satélite'
            info_table.cell(row_count, 1).text = satelite
            row_count += 1
        if indice:
            if row_count >= len(info_table.rows):
                info_table.add_row()
            info_table.cell(row_count, 0).text = 'Índice'
            info_table.cell(row_count, 1).text = indice
            row_count += 1
        if nutriente:
            if row_count >= len(info_table.rows):
                info_table.add_row()
            info_table.cell(row_count, 0).text = 'Nutriente Analizado'
            info_table.cell(row_count, 1).text = nutriente
        doc.add_paragraph()

        if estadisticas:
            doc.add_heading('2. ESTADÍSTICAS PRINCIPALES', level=1)
            for key, value in estadisticas.items():
                p = doc.add_paragraph(style='List Bullet')
                run = p.add_run(f'{key}: ')
                run.bold = True
                p.add_run(str(value))
            doc.add_paragraph()

        if mapa_buffer:
            try:
                doc.add_heading('3. MAPA DE RESULTADOS', level=1)
                temp_img_path = "temp_map_docx.png"
                with open(temp_img_path, "wb") as f:
                    f.write(mapa_buffer.getvalue())
                doc.add_picture(temp_img_path, width=Inches(6.0))
                if os.path.exists(temp_img_path):
                    os.remove(temp_img_path)
                doc.add_paragraph()
            except Exception as e:
                doc.add_paragraph(f'Error al incluir mapa: {str(e)[:50]}...')

        doc.add_heading('4. RESUMEN DE ZONAS', level=1)
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
                for i, col in enumerate(columnas_mostrar):
                    tabla.cell(0, i).text = col.replace('_', ' ').upper()
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
                        else:
                            row_cells[i].text = "N/A"
                doc.add_paragraph()

        if recomendaciones:
            doc.add_heading('5. RECOMENDACIONES', level=1)
            for rec in recomendaciones:
                p = doc.add_paragraph(style='List Bullet')
                p.add_run(rec)

        doc.add_heading('6. METADATOS TÉCNICOS', level=1)
        metadatos = [
            ('Generado por', 'Analizador Multi-Cultivo Satellital'),
            ('Versión', '2.0'),
            ('Fecha de generación', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ('Sistema de coordenadas', 'EPSG:4326 (WGS84)'),
            ('Número de zonas', str(len(gdf_analizado)))
        ]
        for key, value in metadatos:
            p = doc.add_paragraph()
            run_key = p.add_run(f'{key}: ')
            run_key.bold = True
            p.add_run(value)

        docx_output = BytesIO()
        doc.save(docx_output)
        docx_output.seek(0)
        return docx_output
    except Exception as e:
        st.error(f"❌ Error generando DOCX: {str(e)}")
        import traceback
        st.error(f"Detalle: {traceback.format_exc()}")
        return None

# ===== FUNCIÓN PRINCIPAL DE ANÁLISIS =====
def ejecutar_analisis(gdf, nutriente, analisis_tipo, n_divisiones, cultivo,
                      satelite=None, indice=None, fecha_inicio=None,
                      fecha_fin=None, intervalo_curvas=5.0, resolucion_dem=10.0):
    resultados = {
        'exitoso': False,
        'gdf_analizado': None,
        'mapa_buffer': None,
        'tabla_datos': None,
        'estadisticas': {},
        'recomendaciones': [],
        'area_total': 0
    }
    try:
        gdf = validar_y_corregir_crs(gdf)
        area_total = calcular_superficie(gdf)
        resultados['area_total'] = area_total

        # === ANÁLISIS DE TEXTURA DEL SUELO ===
        if analisis_tipo == "ANÁLISIS DE TEXTURA":
            gdf_dividido = dividir_parcela_en_zonas(gdf, n_divisiones)
            gdf_analizado = analizar_textura_suelo(gdf_dividido, cultivo)
            resultados['gdf_analizado'] = gdf_analizado
            resultados['exitoso'] = True
            return resultados

        # === ANÁLISIS DE CURVAS DE NIVEL ===
        elif analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
            gdf_dividido = dividir_parcela_en_zonas(gdf, n_divisiones)
            resultados['gdf_analizado'] = gdf_dividido
            resultados['exitoso'] = True
            return resultados

        # === ANÁLISIS SATELITAL (FERTILIDAD O NPK) ===
        elif analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"]:
            datos_satelitales = None
            if satelite == "SENTINEL-2":
                datos_satelitales = descargar_datos_sentinel2(gdf, fecha_inicio, fecha_fin, indice)
            elif satelite == "LANDSAT-8":
                datos_satelitales = descargar_datos_landsat8(gdf, fecha_inicio, fecha_fin, indice)
            else:
                datos_satelitales = generar_datos_simulados(gdf, cultivo, indice)

            gdf_dividido = dividir_parcela_en_zonas(gdf, n_divisiones)
            indices_gee = calcular_indices_satelitales_gee(gdf_dividido, cultivo, datos_satelitales)

            gdf_analizado = gdf_dividido.copy()
            for idx, indice_data in enumerate(indices_gee):
                for key, value in indice_data.items():
                    gdf_analizado.loc[gdf_analizado.index[idx], key] = value

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

            resultados['gdf_analizado'] = gdf_analizado
            resultados['exitoso'] = True
            return resultados

        else:
            st.error(f"Tipo de análisis no soportado: {analisis_tipo}")
            return resultados

    except Exception as e:
        st.error(f"❌ Error en análisis: {str(e)}")
        import traceback
        st.error(f"Detalle: {traceback.format_exc()}")
        return resultados

# ===== FUNCIONES DE VISUALIZACIÓN MEJORADAS =====
def crear_mapa_estatico(gdf, titulo, columna_valor, analisis_tipo, nutriente, cultivo, satelite):
    try:
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        if analisis_tipo == "FERTILIDAD ACTUAL":
            cmap = LinearSegmentedColormap.from_list('fertilidad_gee', PALETAS_GEE['FERTILIDAD'])
            vmin, vmax = 0, 1
        else:
            if nutriente == "NITRÓGENO":
                cmap = LinearSegmentedColormap.from_list('nitrogeno_gee', PALETAS_GEE['NITROGENO'])
                vmin, vmax = (PARAMETROS_CULTIVOS[cultivo]['NITROGENO']['min'] * 0.8,
                              PARAMETROS_CULTIVOS[cultivo]['NITROGENO']['max'] * 1.2)
            elif nutriente == "FÓSFORO":
                cmap = LinearSegmentedColormap.from_list('fosforo_gee', PALETAS_GEE['FOSFORO'])
                vmin, vmax = (PARAMETROS_CULTIVOS[cultivo]['FOSFORO']['min'] * 0.8,
                              PARAMETROS_CULTIVOS[cultivo]['FOSFORO']['max'] * 1.2)
            else:
                cmap = LinearSegmentedColormap.from_list('potasio_gee', PALETAS_GEE['POTASIO'])
                vmin, vmax = (PARAMETROS_CULTIVOS[cultivo]['POTASIO']['min'] * 0.8,
                              PARAMETROS_CULTIVOS[cultivo]['POTASIO']['max'] * 1.2)

        for idx, row in gdf.iterrows():
            valor = row[columna_valor]
            valor_norm = (valor - vmin) / (vmax - vmin)
            valor_norm = max(0, min(1, valor_norm))
            color = cmap(valor_norm)
            gdf.iloc[[idx]].plot(ax=ax, color=color, edgecolor='black', linewidth=1.5)
            centroid = row.geometry.centroid
            ax.annotate(f"Z{row['id_zona']}\n{valor:.1f}", (centroid.x, centroid.y),
                        xytext=(5, 5), textcoords="offset points",
                        fontsize=8, color='black', weight='bold',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.9))
        info_satelite = SATELITES_DISPONIBLES.get(satelite, SATELITES_DISPONIBLES['DATOS_SIMULADOS'])
        ax.set_title(f'{ICONOS_CULTIVOS[cultivo]} ANÁLISIS GEE - {cultivo}\n'
                     f'{info_satelite["icono"]} {info_satelite["nombre"]} - {analisis_tipo}\n'
                     f'{columna_valor}',
                     fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Longitud')
        ax.set_ylabel('Latitud')
        ax.grid(True, alpha=0.3)
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, shrink=0.8)
        cbar.set_label(columna_valor, fontsize=12, fontweight='bold')
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        return buf
    except Exception as e:
        st.error(f"❌ Error creando mapa: {str(e)}")
        return None

# ===== INTERFAZ PRINCIPAL MEJORADA =====
if uploaded_file:
    with st.spinner("🔍 Cargando parcela..."):
        try:
            gdf = cargar_archivo_parcela(uploaded_file)
            if gdf is not None:
                st.success(f"✅ **Parcela cargada exitosamente:** {len(gdf)} polígono(s)")
                
                # ===== DASHBOARD DE INFORMACIÓN INICIAL =====
                area_total = calcular_superficie(gdf)
                
                # Métricas en tarjetas mejoradas
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="text-align: center;">
                            <div style="font-size: 2em; color: #28a745;">🗺️</div>
                            <h3 style="color: #333; margin: 10px 0;">{len(gdf)}</h3>
                            <p style="color: #666; margin: 0;">Polígonos</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="text-align: center;">
                            <div style="font-size: 2em; color: #2196F3;">📏</div>
                            <h3 style="color: #333; margin: 10px 0;">{area_total:.1f}</h3>
                            <p style="color: #666; margin: 0;">Hectáreas</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="text-align: center;">
                            <div style="font-size: 2em; color: #FF9800;">{ICONOS_CULTIVOS.get(cultivo, '🌾')}</div>
                            <h3 style="color: #333; margin: 10px 0;">{cultivo}</h3>
                            <p style="color: #666; margin: 0;">Cultivo</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="text-align: center;">
                            <div style="font-size: 2em; color: #9C27B0;">📊</div>
                            <h3 style="color: #333; margin: 10px 0;">{analisis_tipo}</h3>
                            <p style="color: #666; margin: 0;">Análisis</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # ===== DASHBOARD DE ESTADO DEL CULTIVO =====
                st.markdown("---")
                st.markdown("### 📊 ESTADO DEL CULTIVO - DASHBOARD")
                
                # Datos climáticos simulados
                col_temp, col_hum, col_vpci, col_ndvi = st.columns(4)
                
                with col_temp:
                    st.markdown("""
                    <div class="dashboard-card">
                        <div style="text-align: center;">
                            <div style="font-size: 2.5em; color: #FF5722;">🌡️</div>
                            <h3 style="color: #FF5722; margin: 10px 0;">25.3°C</h3>
                            <p style="color: #666; margin: 0;">Temperatura</p>
                            <small style="color: #999;">Óptima para """ + cultivo + """</small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_hum:
                    st.markdown("""
                    <div class="dashboard-card">
                        <div style="text-align: center;">
                            <div style="font-size: 2.5em; color: #2196F3;">💧</div>
                            <h3 style="color: #2196F3; margin: 10px 0;">68%</h3>
                            <p style="color: #666; margin: 0;">Humedad Relativa</p>
                            <small style="color: #999;">Condición ideal</small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_vpci:
                    st.markdown("""
                    <div class="dashboard-card">
                        <div style="text-align: center;">
                            <div style="font-size: 2.5em; color: #4CAF50;">📊</div>
                            <h3 style="color: #4CAF50; margin: 10px 0;">0.54 kPa</h3>
                            <p style="color: #666; margin: 0;">VPCI</p>
                            <small style="color: #999;">Presión de vapor</small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_ndvi:
                    ndvi_valor = PARAMETROS_CULTIVOS.get(cultivo, {}).get('NDVI_OPTIMO', 0.7)
                    st.markdown(f"""
                    <div class="dashboard-card">
                        <div style="text-align: center;">
                            <div style="font-size: 2.5em; color: #8BC34A;">🌱</div>
                            <h3 style="color: #8BC34A; margin: 10px 0;">{ndvi_valor:.2f}</h3>
                            <p style="color: #666; margin: 0;">NDVI Óptimo</p>
                            <small style="color: #999;">Para """ + cultivo + """</small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Gráfico de estado nutricional
                st.markdown("### 🌱 ESTADO NUTRICIONAL ESPERADO")
                fig, ax = plt.subplots(figsize=(10, 4))
                nutrientes = ['Nitrógeno (N)', 'Fósforo (P)', 'Potasio (K)', 'Materia Orgánica']
                valores = [75, 60, 80, 65]  # Valores de ejemplo
                colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
                bars = ax.bar(nutrientes, valores, color=colors)
                ax.set_ylim(0, 100)
                ax.set_ylabel('Disponibilidad (%)')
                ax.set_title('Disponibilidad de Nutrientes en Condiciones Óptimas')
                ax.grid(True, alpha=0.3, axis='y')
                
                # Añadir etiquetas
                for bar, valor in zip(bars, valores):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                            f'{valor}%', ha='center', va='bottom', fontweight='bold')
                
                st.pyplot(fig)
                
                # Vista previa de la parcela
                st.markdown("### 🗺️ VISTA PREVIA DE LA PARCELA")
                col_preview1, col_preview2 = st.columns([2, 1])
                
                with col_preview1:
                    fig, ax = plt.subplots(figsize=(10, 8))
                    gdf.plot(ax=ax, color=COLORES_CULTIVOS.get(cultivo, '#4CAF50'), 
                            edgecolor='darkgreen', alpha=0.7, linewidth=2)
                    ax.set_title(f"Parcela: {uploaded_file.name}", fontsize=14, fontweight='bold')
                    ax.set_xlabel("Longitud", fontweight='bold')
                    ax.set_ylabel("Latitud", fontweight='bold')
                    ax.grid(True, alpha=0.3)
                    ax.tick_params(axis='both', which='major', labelsize=10)
                    st.pyplot(fig)
                
                with col_preview2:
                    st.markdown("""
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px;">
                        <h4>📋 INFORMACIÓN TÉCNICA</h4>
                        <p><strong>Formato:</strong> """ + uploaded_file.name.split('.')[-1].upper() + """</p>
                        <p><strong>CRS:</strong> EPSG:4326</p>
                        <p><strong>Zonas a crear:</strong> """ + str(n_divisiones) + """</p>
                        <p><strong>Satélite:</strong> """ + SATELITES_DISPONIBLES[satelite_seleccionado]['nombre'] + """</p>
                        <hr>
                        <h4>⚡ CONFIGURACIÓN LISTA</h4>
                        <p>Presiona el botón para ejecutar el análisis completo con la configuración seleccionada.</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Botón de análisis mejorado
                st.markdown("---")
                col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                with col_btn2:
                    if st.button("🚀 EJECUTAR ANÁLISIS COMPLETO", type="primary", use_container_width=True):
                        resultados = None
                        
                        # Determinar qué parámetros pasar según el tipo de análisis
                        if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"]:
                            resultados = ejecutar_analisis(
                                gdf, nutriente, analisis_tipo, n_divisiones, 
                                cultivo, satelite_seleccionado, indice_seleccionado,
                                fecha_inicio, fecha_fin
                            )
                        elif analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
                            resultados = ejecutar_analisis(
                                gdf, None, analisis_tipo, n_divisiones, 
                                cultivo, None, None, None, None, 
                                intervalo_curvas, resolucion_dem
                            )
                        else:  # ANÁLISIS DE TEXTURA
                            resultados = ejecutar_analisis(
                                gdf, None, analisis_tipo, n_divisiones, 
                                cultivo, None, None, None, None
                            )

                        # GUARDAR RESULTADOS EN SESSION STATE
                        if resultados and resultados['exitoso']:
                            # Crear diccionario de resultados con todas las variables definidas
                            resultados_dict = {
                                'gdf_analizado': resultados['gdf_analizado'],
                                'analisis_tipo': analisis_tipo,
                                'cultivo': cultivo,
                                'area_total': resultados['area_total'],
                                'nutriente': nutriente,
                                'satelite_seleccionado': satelite_seleccionado,
                                'indice_seleccionado': indice_seleccionado,
                                'mapa_buffer': resultados.get('mapa_buffer'),
                                'X': None,
                                'Y': None,
                                'Z': None,
                                'pendiente_grid': None,
                                'gdf_original': gdf if analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL" else None
                            }
                            
                            # Para análisis de curvas de nivel, generar DEM adicional
                            if analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
                                X, Y, Z, _ = generar_dem_sintetico(gdf, resolucion_dem)
                                pendiente_grid = calcular_pendiente_simple(X, Y, Z, resolucion_dem)
                                resultados_dict.update({
                                    'X': X, 'Y': Y, 'Z': Z, 'pendiente_grid': pendiente_grid
                                })
                            
                            st.session_state['resultados_guardados'] = resultados_dict
                            
                            # Mostrar mensaje de éxito
                            st.success("✅ Análisis completado exitosamente!")
                            
                            # Mostrar resultados según tipo de análisis
                            if analisis_tipo == "ANÁLISIS DE TEXTURA":
                                st.subheader("📊 RESULTADOS DE ANÁLISIS DE TEXTURA")
                                
                                # Mostrar estadísticas básicas
                                col_text1, col_text2, col_text3, col_text4 = st.columns(4)
                                with col_text1:
                                    avg_arena = resultados['gdf_analizado']['arena'].mean()
                                    st.markdown(f"""
                                    <div class="metric-card">
                                        <div style="text-align: center;">
                                            <div style="font-size: 2em; color: #d8b365;">🏖️</div>
                                            <h3 style="color: #333; margin: 10px 0;">{avg_arena:.1f}%</h3>
                                            <p style="color: #666; margin: 0;">Arena</p>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                with col_text2:
                                    avg_limo = resultados['gdf_analizado']['limo'].mean()
                                    st.markdown(f"""
                                    <div class="metric-card">
                                        <div style="text-align: center;">
                                            <div style="font-size: 2em; color: #f6e8c3;">🌫️</div>
                                            <h3 style="color: #333; margin: 10px 0;">{avg_limo:.1f}%</h3>
                                            <p style="color: #666; margin: 0;">Limo</p>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                with col_text3:
                                    avg_arcilla = resultados['gdf_analizado']['arcilla'].mean()
                                    st.markdown(f"""
                                    <div class="metric-card">
                                        <div style="text-align: center;">
                                            <div style="font-size: 2em; color: #01665e;">🧱</div>
                                            <h3 style="color: #333; margin: 10px 0;">{avg_arcilla:.1f}%</h3>
                                            <p style="color: #666; margin: 0;">Arcilla</p>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                with col_text4:
                                    textura_predominante = resultados['gdf_analizado']['textura_suelo'].mode()[0] if len(resultados['gdf_analizado']) > 0 else "NO_DETERMINADA"
                                    st.markdown(f"""
                                    <div class="metric-card">
                                        <div style="text-align: center;">
                                            <div style="font-size: 2em; color: #5ab4ac;">🏗️</div>
                                            <h3 style="color: #333; margin: 10px 0;">{textura_predominante[:15]}</h3>
                                            <p style="color: #666; margin: 0;">Textura</p>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                # Mostrar tabla de resultados
                                st.markdown("### 📋 RESULTADOS POR ZONA")
                                columnas_textura = ['id_zona', 'area_ha', 'textura_suelo', 'arena', 'limo', 'arcilla']
                                columnas_textura = [col for col in columnas_textura if col in resultados['gdf_analizado'].columns]
                                if columnas_textura:
                                    tabla_textura = resultados['gdf_analizado'][columnas_textura].copy()
                                    tabla_textura.columns = ['Zona', 'Área (ha)', 'Textura', 'Arena (%)', 'Limo (%)', 'Arcilla (%)']
                                    st.dataframe(tabla_textura, use_container_width=True)
                                
                            elif analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
                                st.subheader("🏔️ RESULTADOS DE ANÁLISIS DE CURVAS DE NIVEL")
                                
                                # Mostrar estadísticas básicas
                                if 'Z' in resultados_dict and resultados_dict['Z'] is not None:
                                    Z_flat = resultados_dict['Z'].flatten()
                                    Z_flat = Z_flat[~np.isnan(Z_flat)]
                                    
                                    if len(Z_flat) > 0:
                                        col_curv1, col_curv2, col_curv3, col_curv4 = st.columns(4)
                                        
                                        with col_curv1:
                                            elevacion_promedio = np.mean(Z_flat)
                                            st.markdown(f"""
                                            <div class="metric-card">
                                                <div style="text-align: center;">
                                                    <div style="font-size: 2em; color: #2196F3;">🏔️</div>
                                                    <h3 style="color: #333; margin: 10px 0;">{elevacion_promedio:.1f} m</h3>
                                                    <p style="color: #666; margin: 0;">Elevación Prom.</p>
                                                </div>
                                            </div>
                                            """, unsafe_allow_html=True)
                                        
                                        with col_curv2:
                                            rango_elevacion = np.max(Z_flat) - np.min(Z_flat)
                                            st.markdown(f"""
                                            <div class="metric-card">
                                                <div style="text-align: center;">
                                                    <div style="font-size: 2em; color: #4CAF50;">📏</div>
                                                    <h3 style="color: #333; margin: 10px 0;">{rango_elevacion:.1f} m</h3>
                                                    <p style="color: #666; margin: 0;">Rango Elevación</p>
                                                </div>
                                            </div>
                                            """, unsafe_allow_html=True)
                                        
                                        with col_curv3:
                                            if resultados_dict['pendiente_grid'] is not None:
                                                pendiente_flat = resultados_dict['pendiente_grid'].flatten()
                                                pendiente_flat = pendiente_flat[~np.isnan(pendiente_flat)]
                                                if len(pendiente_flat) > 0:
                                                    pendiente_prom = np.mean(pendiente_flat)
                                                    st.markdown(f"""
                                                    <div class="metric-card">
                                                        <div style="text-align: center;">
                                                            <div style="font-size: 2em; color: #FF9800;">📐</div>
                                                            <h3 style="color: #333; margin: 10px 0;">{pendiente_prom:.1f}%</h3>
                                                            <p style="color: #666; margin: 0;">Pendiente Prom.</p>
                                                        </div>
                                                    </div>
                                                    """, unsafe_allow_html=True)
                                        
                                        with col_curv4:
                                            if 'pendiente_grid' in resultados_dict and resultados_dict['pendiente_grid'] is not None:
                                                mapa_pendientes, stats_pendiente = crear_mapa_pendientes_simple(
                                                    resultados_dict['X'], resultados_dict['Y'], 
                                                    resultados_dict['pendiente_grid'], gdf
                                                )
                                                st.markdown(f"""
                                                <div class="metric-card">
                                                    <div style="text-align: center;">
                                                        <div style="font-size: 2em; color: #9C27B0;">🔄</div>
                                                        <h3 style="color: #333; margin: 10px 0;">{stats_pendiente.get('promedio', 0):.1f}%</h3>
                                                        <p style="color: #666; margin: 0;">Pendiente Promedio</p>
                                                    </div>
                                                </div>
                                                """, unsafe_allow_html=True)
                                        
                                        # Mostrar mapa de pendientes
                                        st.markdown("### 🗺️ MAPA DE CALOR DE PENDIENTES")
                                        st.image(mapa_pendientes, use_container_width=True)
                                
                            else:
                                # Resultados para análisis satelital
                                gdf_analizado = resultados['gdf_analizado']
                                
                                # Mostrar métricas en tarjetas mejoradas
                                st.markdown("### 📊 RESULTADOS DEL ANÁLISIS")
                                col_res1, col_res2, col_res3, col_res4 = st.columns(4)
                                
                                with col_res1:
                                    st.markdown(f"""
                                    <div class="metric-card">
                                        <div style="text-align: center;">
                                            <div style="font-size: 2em; color: #28a745;">🗺️</div>
                                            <h3 style="color: #333; margin: 10px 0;">{len(gdf_analizado)}</h3>
                                            <p style="color: #666; margin: 0;">Zonas Analizadas</p>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                with col_res2:
                                    st.markdown(f"""
                                    <div class="metric-card">
                                        <div style="text-align: center;">
                                            <div style="font-size: 2em; color: #2196F3;">📏</div>
                                            <h3 style="color: #333; margin: 10px 0;">{resultados['area_total']:.1f}</h3>
                                            <p style="color: #666; margin: 0;">Hectáreas Totales</p>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                with col_res3:
                                    if analisis_tipo == "FERTILIDAD ACTUAL":
                                        valor_prom = gdf_analizado['npk_actual'].mean()
                                        st.markdown(f"""
                                        <div class="metric-card">
                                            <div style="text-align: center;">
                                                <div style="font-size: 2em; color: #FF9800;">🌱</div>
                                                <h3 style="color: #333; margin: 10px 0;">{valor_prom:.3f}</h3>
                                                <p style="color: #666; margin: 0;">Índice NPK Promedio</p>
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    else:
                                        valor_prom = gdf_analizado['valor_recomendado'].mean()
                                        st.markdown(f"""
                                        <div class="metric-card">
                                            <div style="text-align: center;">
                                                <div style="font-size: 2em; color: #FF9800;">💊</div>
                                                <h3 style="color: #333; margin: 10px 0;">{valor_prom:.1f}</h3>
                                                <p style="color: #666; margin: 0;">{nutriente} Promedio</p>
                                                <small style="color: #999;">kg/ha</small>
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                
                                with col_res4:
                                    if analisis_tipo == "FERTILIDAD ACTUAL" and gdf_analizado['npk_actual'].mean() > 0:
                                        coef_var = (gdf_analizado['npk_actual'].std() / gdf_analizado['npk_actual'].mean() * 100)
                                        color_coef = "#4CAF50" if coef_var < 20 else "#FF9800" if coef_var < 40 else "#F44336"
                                        st.markdown(f"""
                                        <div class="metric-card">
                                            <div style="text-align: center;">
                                                <div style="font-size: 2em; color: {color_coef};">📈</div>
                                                <h3 style="color: #333; margin: 10px 0;">{coef_var:.1f}%</h3>
                                                <p style="color: #666; margin: 0;">Coef. Variación</p>
                                                <small style="color: #999;">{"Baja" if coef_var < 20 else "Moderada" if coef_var < 40 else "Alta"}</small>
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    elif analisis_tipo == "RECOMENDACIONES NPK" and gdf_analizado['valor_recomendado'].mean() > 0:
                                        coef_var = (gdf_analizado['valor_recomendado'].std() / gdf_analizado['valor_recomendado'].mean() * 100)
                                        color_coef = "#4CAF50" if coef_var < 20 else "#FF9800" if coef_var < 40 else "#F44336"
                                        st.markdown(f"""
                                        <div class="metric-card">
                                            <div style="text-align: center;">
                                                <div style="font-size: 2em; color: {color_coef};">📈</div>
                                                <h3 style="color: #333; margin: 10px 0;">{coef_var:.1f}%</h3>
                                                <p style="color: #666; margin: 0;">Coef. Variación</p>
                                                <small style="color: #999;">{"Baja" if coef_var < 20 else "Moderada" if coef_var < 40 else "Alta"}</small>
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)

                                # Mapa de resultados
                                st.markdown("### 🗺️ MAPA DE RESULTADOS")
                                if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"]:
                                    columna_valor = 'valor_recomendado' if analisis_tipo == "RECOMENDACIONES NPK" else 'npk_actual'
                                    mapa_buffer = crear_mapa_estatico(gdf_analizado, f"ANÁLISIS {analisis_tipo}", 
                                                                     columna_valor, analisis_tipo, 
                                                                     nutriente, cultivo, satelite_seleccionado)
                                    if mapa_buffer:
                                        st.image(mapa_buffer, use_container_width=True)
                                        st.session_state['resultados_guardados']['mapa_buffer'] = mapa_buffer
                                        st.download_button(
                                            "📥 Descargar Mapa GEE",
                                            mapa_buffer,
                                            f"mapa_gee_{cultivo}_{satelite_seleccionado}_{analisis_tipo.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.png",
                                            "image/png",
                                            type="primary"
                                        )
                                
                                # Tabla de resultados
                                st.markdown("### 📋 RESULTADOS POR ZONA")
                                if analisis_tipo == "FERTILIDAD ACTUAL":
                                    columnas_indices = ['id_zona', 'area_ha', 'npk_actual', 'materia_organica', 'ndvi', 'ndre', 'humedad_suelo']
                                    rename_dict = {
                                        'id_zona': 'Zona',
                                        'area_ha': 'Área (ha)',
                                        'npk_actual': 'NPK Actual',
                                        'materia_organica': 'Materia Org (%)',
                                        'ndvi': 'NDVI',
                                        'ndre': 'NDRE',
                                        'humedad_suelo': 'Humedad'
                                    }
                                else:
                                    columnas_indices = ['id_zona', 'area_ha', 'valor_recomendado', 'npk_actual', 'materia_organica', 'ndvi', 'ndre']
                                    rename_dict = {
                                        'id_zona': 'Zona',
                                        'area_ha': 'Área (ha)',
                                        'valor_recomendado': f'Recomendación {nutriente}',
                                        'npk_actual': 'NPK Actual',
                                        'materia_organica': 'Materia Org (%)',
                                        'ndvi': 'NDVI',
                                        'ndre': 'NDRE'
                                    }
                                
                                columnas_indices = [col for col in columnas_indices if col in gdf_analizado.columns]
                                if columnas_indices:
                                    tabla_indices = gdf_analizado[columnas_indices].copy()
                                    tabla_indices = tabla_indices.rename(columns={k: v for k, v in rename_dict.items() if k in tabla_indices.columns})
                                    
                                    # Formatear números
                                    for col in tabla_indices.columns:
                                        if 'Área' in col:
                                            tabla_indices[col] = tabla_indices[col].map(lambda x: f"{x:.2f}")
                                        elif 'Materia' in col:
                                            tabla_indices[col] = tabla_indices[col].map(lambda x: f"{x:.1f}")
                                        elif 'NPK' in col or 'NDVI' in col or 'NDRE' in col or 'Humedad' in col:
                                            tabla_indices[col] = tabla_indices[col].map(lambda x: f"{x:.3f}" if isinstance(x, (int, float)) else x)
                                        elif 'Recomendación' in col:
                                            tabla_indices[col] = tabla_indices[col].map(lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else x)
                                    
                                    st.dataframe(tabla_indices, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Error procesando archivo: {str(e)}")
            import traceback
            st.error(f"Detalle: {traceback.format_exc()}")
else:
    # Pantalla inicial cuando no hay archivo cargado
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px; background: white; border-radius: 15px; margin: 20px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
        <div style="font-size: 5em; margin-bottom: 20px;">🌾</div>
        <h2 style="color: #333; margin-bottom: 15px;">¡Bienvenido al Analizador Multi-Cultivo!</h2>
        <p style="color: #666; font-size: 1.1em; max-width: 800px; margin: 0 auto 30px;">
            Una herramienta profesional para agricultura de precisión con análisis satelital avanzado.
        </p>
        <div style="display: flex; justify-content: center; gap: 20px; margin-top: 30px;">
            <div style="text-align: center;">
                <div style="font-size: 2.5em;">🛰️</div>
                <p style="font-weight: bold;">Datos Satelitales</p>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2.5em;">📊</div>
                <p style="font-weight: bold;">Análisis Avanzado</p>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2.5em;">💡</div>
                <p style="font-weight: bold;">Recomendaciones</p>
            </div>
        </div>
        <p style="color: #999; margin-top: 40px;">
            Sube un archivo de tu parcela en el panel izquierdo para comenzar
        </p>
    </div>
    """, unsafe_allow_html=True)

# ===== SECCIÓN DE EXPORTACIÓN MEJORADA =====
if 'resultados_guardados' in st.session_state:
    res = st.session_state['resultados_guardados']
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h2>📤 EXPORTAR RESULTADOS</h2>
        <p style="color: #666;">Descarga tus resultados en diferentes formatos</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_exp1, col_exp2, col_exp3, col_exp4 = st.columns(4)

    with col_exp1:
        if st.button("🗺️ **GeoJSON**", key="export_geojson", use_container_width=True):
            geojson_data, nombre_archivo = exportar_a_geojson(res['gdf_analizado'], f"parcela_{res['cultivo']}")
            if geojson_data:
                st.download_button(
                    label="📥 Descargar GeoJSON",
                    data=geojson_data,
                    file_name=nombre_archivo,
                    mime="application/json",
                    key="geojson_download",
                    use_container_width=True
                )

    with col_exp2:
        if st.button("📄 **Reporte PDF**", key="export_pdf", use_container_width=True):
            with st.spinner("Generando PDF..."):
                estadisticas = generar_resumen_estadisticas(res['gdf_analizado'], res['analisis_tipo'], res['cultivo'])
                recomendaciones = generar_recomendaciones_generales(res['gdf_analizado'], res['analisis_tipo'], res['cultivo'])
                mapa_buffer = res.get('mapa_buffer')
                pdf_buffer = generar_reporte_pdf(
                    res['gdf_analizado'], res['cultivo'], res['analisis_tipo'], res['area_total'],
                    res.get('nutriente'), res.get('satelite_seleccionado'), res.get('indice_seleccionado'),
                    mapa_buffer, estadisticas, recomendaciones
                )
                if pdf_buffer:
                    st.download_button(
                        label="📥 Descargar PDF",
                        data=pdf_buffer,
                        file_name=f"reporte_{res['cultivo']}_{res['analisis_tipo'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        key="pdf_download",
                        use_container_width=True
                    )
                else:
                    st.error("❌ No se pudo generar el reporte PDF")

    with col_exp3:
        if st.button("📝 **Reporte DOCX**", key="export_docx", use_container_width=True):
            with st.spinner("Generando DOCX..."):
                estadisticas = generar_resumen_estadisticas(res['gdf_analizado'], res['analisis_tipo'], res['cultivo'])
                recomendaciones = generar_recomendaciones_generales(res['gdf_analizado'], res['analisis_tipo'], res['cultivo'])
                mapa_buffer = res.get('mapa_buffer')
                docx_buffer = generar_reporte_docx(
                    res['gdf_analizado'], res['cultivo'], res['analisis_tipo'], res['area_total'],
                    res.get('nutriente'), res.get('satelite_seleccionado'), res.get('indice_seleccionado'),
                    mapa_buffer, estadisticas, recomendaciones
                )
                if docx_buffer:
                    st.download_button(
                        label="📥 Descargar DOCX",
                        data=docx_buffer,
                        file_name=f"reporte_{res['cultivo']}_{res['analisis_tipo'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key="docx_download",
                        use_container_width=True
                    )
                else:
                    st.error("❌ No se pudo generar el reporte DOCX")

    with col_exp4:
        if st.button("📊 **Datos CSV**", key="export_csv", use_container_width=True):
            if res['gdf_analizado'] is not None:
                if 'geometry' in res['gdf_analizado'].columns:
                    df_export = res['gdf_analizado'].drop(columns=['geometry']).copy()
                else:
                    df_export = res['gdf_analizado'].copy()
                csv = df_export.to_csv(index=False)
                st.download_button(
                    label="📥 Descargar CSV",
                    data=csv,
                    file_name=f"datos_{res['cultivo']}_{res['analisis_tipo'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="csv_download",
                    use_container_width=True
                )

# ===== FOOTER PROFESIONAL (CORREGIDO) =====
st.markdown("""
<div class="custom-footer">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="text-align: left;">
            <h3 style="margin: 0; color: white;">🌾 Analizador Multi-Cultivo</h3>
            <p style="margin: 5px 0 0 0; color: rgba(255,255,255,0.8); font-size: 0.9em;">
                Agricultura de Precisión v2.0
            </p>
        </div>
        <div style="text-align: right;">
            <p style="margin: 0; color: rgba(255,255,255,0.8); font-size: 0.9em;">
                📅 """ + datetime.now().strftime("%d/%m/%Y") + """<br>
                🛰️ Datos Satelitales<br>
                🌍 EPSG:4326
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ===== INFORMACIÓN ADICIONAL =====
with st.expander("📋 FORMATOS DE ARCHIVO ACEPTADOS"):
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; height: 100%;">
            <h4 style="color: #28a745;">🗺️ Shapefile (.zip)</h4>
            <ul style="color: #666;">
                <li>.shp (geometrías)</li>
                <li>.shx (índice)</li>
                <li>.dbf (atributos)</li>
                <li>.prj (opcional)</li>
            </ul>
            <p style="color: #999; font-size: 0.9em;">Se recomienda EPSG:4326</p>
        </div>
        """, unsafe_allow_html=True)
    with col_info2:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; height: 100%;">
            <h4 style="color: #2196F3;">🌐 KML (.kml)</h4>
            <ul style="color: #666;">
                <li>Formato Google Earth</li>
                <li>Geometrías y atributos</li>
                <li>Puede incluir estilos</li>
                <li>Siempre EPSG:4326</li>
            </ul>
            <p style="color: #999; font-size: 0.9em;">Ideal para Google Earth</p>
        </div>
        """, unsafe_allow_html=True)
    with col_info3:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 10px; height: 100%;">
            <h4 style="color: #FF9800;">📦 KMZ (.kmz)</h4>
            <ul style="color: #666;">
                <li>KML comprimido</li>
                <li>Incluye recursos</li>
                <li>Compatible con Google Earth</li>
                <li>Siempre EPSG:4326</li>
            </ul>
            <p style="color: #999; font-size: 0.9em;">Versión comprimida</p>
        </div>
        """, unsafe_allow_html=True)

# Nota final
st.markdown("""
<div style="text-align: center; color: #666; margin-top: 20px; font-size: 0.9em;">
    <p>🌱 <strong>Analizador Multi-Cultivo Satellital</strong> - Herramienta para agricultura de precisión</p>
    <p>Desarrollado por Raices Verdes. Consultora Agropecuaria, para agricultores y profesionales del agro</p>
</div>
""", unsafe_allow_html=True)
