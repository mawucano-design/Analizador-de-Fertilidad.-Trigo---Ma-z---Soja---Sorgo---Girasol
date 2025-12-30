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

# ===== CONFIGURACIÓN INICIAL - DEBE SER LO PRIMERO =====
st.set_page_config(
    page_title="🌱 Analizador Multi-Cultivo Satellital",
    layout="wide",
    page_icon="🛰️",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo',
        'Report a bug': 'https://github.com/your-repo/issues',
        'About': '### 🌱 Analizador Multi-Cultivo Satellital v2.0\nSistema de análisis agrícola con datos satelitales.'
    }
)

# ===== INYECTAR ESTILOS CSS PERSONALIZADOS =====
def inject_custom_css():
    st.markdown("""
    <style>
    /* ESTILOS GENERALES */
    .main {
        background-color: #f8f9fa;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* HEADER PERSONALIZADO */
    .main-header {
        background: linear-gradient(90deg, #1a6b3c, #2e8b57, #4caf50);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        color: white;
        text-align: center;
    }
    
    .main-header h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .main-header h2 {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.2rem;
        font-weight: 300;
    }
    
    /* SIDEBAR MEJORADA */
    .css-1d391kg {
        background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
        padding: 1rem;
    }
    
    section[data-testid="stSidebar"] > div {
        background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
        padding-top: 1rem;
    }
    
    .sidebar .sidebar-content {
        background-color: #2c3e50;
    }
    
    .sidebar-header {
        color: white;
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1.5rem;
        text-align: center;
        border-bottom: 2px solid #4CAF50;
        padding-bottom: 0.5rem;
    }
    
    /* BOTONES MEJORADOS */
    .stButton > button {
        background: linear-gradient(90deg, #4CAF50, #2E7D32);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        background: linear-gradient(90deg, #2E7D32, #1B5E20);
    }
    
    /* TARJETAS DE INFORMACIÓN */
    .info-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        margin-bottom: 1.5rem;
        border-left: 5px solid #4CAF50;
        transition: transform 0.3s ease;
    }
    
    .info-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.12);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border: 1px solid #e0e0e0;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #2E7D32;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        color: #666;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* SECCIONES */
    .section-header {
        background: linear-gradient(90deg, #4CAF50, #2E7D32);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin: 2rem 0 1rem 0;
        font-size: 1.3rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .section-header i {
        font-size: 1.5rem;
    }
    
    /* PESTAÑAS MEJORADAS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #e8f5e9;
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        font-weight: 600;
        border: 1px solid #c8e6c9;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #c8e6c9;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4CAF50 !important;
        color: white !important;
        border-color: #4CAF50 !important;
    }
    
    /* PROGRESS BAR MEJORADO */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #4CAF50, #2E7D32);
    }
    
    /* FOOTER */
    .footer {
        text-align: center;
        padding: 1.5rem;
        margin-top: 3rem;
        color: #666;
        font-size: 0.9rem;
        border-top: 1px solid #e0e0e0;
        background: rgba(255, 255, 255, 0.9);
        border-radius: 10px;
    }
    
    /* TOOLTIPS */
    .tooltip {
        position: relative;
        display: inline-block;
        border-bottom: 1px dotted #666;
    }
    
    /* TABLAS MEJORADAS */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    
    .dataframe th {
        background: linear-gradient(90deg, #4CAF50, #2E7D32) !important;
        color: white !important;
        font-weight: 600;
        padding: 12px !important;
    }
    
    .dataframe td {
        padding: 10px !important;
        border-bottom: 1px solid #e0e0e0;
    }
    
    .dataframe tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    /* ALERTAS PERSONALIZADAS */
    .stAlert {
        border-radius: 8px;
        border-left: 5px solid;
    }
    
    .stAlert[data-baseweb="notification"] {
        padding: 1rem;
        border-radius: 8px;
    }
    
    /* INPUTS MEJORADOS */
    .stSelectbox, .stDateInput, .stNumberInput, .stTextInput {
        background-color: white;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    
    /* EXPANDER MEJORADO */
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, #4CAF50, #2E7D32);
        color: white;
        border-radius: 8px;
        font-weight: 600;
    }
    
    .streamlit-expanderContent {
        background-color: white;
        border-radius: 0 0 8px 8px;
        padding: 1.5rem;
    }
    
    /* GRID DE COLUMNAS */
    .col-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        height: 100%;
        border: 1px solid #e0e0e0;
    }
    
    /* ANIMACIONES */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* RESPONSIVE */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 1.8rem;
        }
        .metric-value {
            font-size: 1.5rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Inyectar CSS al inicio
inject_custom_css()

# ===== CABECERA MEJORADA =====
st.markdown("""
<div class="main-header fade-in">
    <h1>🛰️ ANALIZADOR MULTI-CULTIVO - SENTINEL-2 & LANDSAT-8</h1>
    <h2>Sistema Inteligente de Análisis Agrícola con Datos Satelitales</h2>
</div>
""", unsafe_allow_html=True)

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

# ===== INICIALIZACIÓN SEGURA DE VARIABLES =====
if 'resultados_guardados' not in st.session_state:
    st.session_state.resultados_guardados = None
if 'gdf_cargado' not in st.session_state:
    st.session_state.gdf_cargado = None
if 'analisis_completado' not in st.session_state:
    st.session_state.analisis_completado = False

# ===== SIDEBAR MEJORADA =====
with st.sidebar:
    st.markdown('<div class="sidebar-header">⚙️ CONFIGURACIÓN</div>', unsafe_allow_html=True)
    
    # Tarjeta de cultivo
    with st.container():
        st.markdown('<div class="info-card fade-in">', unsafe_allow_html=True)
        cultivo = st.selectbox("🌱 **Cultivo:**", ["TRIGO", "MAÍZ", "SOJA", "SORGO", "GIRASOL"])
        st.markdown(f'<p style="color: #666; font-size: 0.9rem; margin-top: 10px;">{ICONOS_CULTIVOS[cultivo]} {cultivo}</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Tarjeta de tipo de análisis
    with st.container():
        st.markdown('<div class="info-card fade-in">', unsafe_allow_html=True)
        analisis_tipo = st.selectbox("📊 **Tipo de Análisis:**", ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK", "ANÁLISIS DE TEXTURA", "ANÁLISIS DE CURVAS DE NIVEL"])
        
        if analisis_tipo == "RECOMENDACIONES NPK":
            nutriente = st.selectbox("🧪 **Nutriente:**", ["NITRÓGENO", "FÓSFORO", "POTASIO"])
        else:
            nutriente = None
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Tarjeta de satélite
    with st.container():
        st.markdown('<div class="info-card fade-in">', unsafe_allow_html=True)
        st.subheader("🛰️ **Fuente de Datos Satelitales**")
        satelite_seleccionado = st.selectbox(
            "**Satélite:**",
            ["SENTINEL-2", "LANDSAT-8", "DATOS_SIMULADOS"],
            help="Selecciona la fuente de datos satelitales"
        )
        
        if satelite_seleccionado in SATELITES_DISPONIBLES:
            info_satelite = SATELITES_DISPONIBLES[satelite_seleccionado]
            st.markdown(f"""
            <div style="background: rgba(76, 175, 80, 0.1); padding: 10px; border-radius: 8px; margin-top: 10px;">
                <strong>{info_satelite['icono']} {info_satelite['nombre']}</strong><br>
                📏 Resolución: {info_satelite['resolucion']}<br>
                🔄 Revisita: {info_satelite['revisita']}<br>
                📈 Índices: {', '.join(info_satelite['indices'][:3])}
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Configuración específica por tipo de análisis
    if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"]:
        with st.container():
            st.markdown('<div class="info-card fade-in">', unsafe_allow_html=True)
            st.subheader("📊 **Índices de Vegetación**")
            if satelite_seleccionado == "SENTINEL-2":
                indice_seleccionado = st.selectbox("📈 **Índice:**", SATELITES_DISPONIBLES['SENTINEL-2']['indices'])
            elif satelite_seleccionado == "LANDSAT-8":
                indice_seleccionado = st.selectbox("📈 **Índice:**", SATELITES_DISPONIBLES['LANDSAT-8']['indices'])
            else:
                indice_seleccionado = st.selectbox("📈 **Índice:**", SATELITES_DISPONIBLES['DATOS_SIMULADOS']['indices'])
            st.markdown('</div>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="info-card fade-in">', unsafe_allow_html=True)
            st.subheader("📅 **Rango Temporal**")
            col1, col2 = st.columns(2)
            with col1:
                fecha_inicio = st.date_input("**Desde**", datetime.now() - timedelta(days=30))
            with col2:
                fecha_fin = st.date_input("**Hasta**", datetime.now())
            st.markdown('</div>', unsafe_allow_html=True)
    
    # División de parcela
    with st.container():
        st.markdown('<div class="info-card fade-in">', unsafe_allow_html=True)
        st.subheader("🎯 **División de Parcela**")
        n_divisiones = st.slider("**Número de zonas de manejo:**", min_value=16, max_value=48, value=32, help="Divide la parcela en zonas para análisis detallado")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Configuración para curvas de nivel
    if analisis_tipo == "ANÁLISIS DE CURVAS DE NIVEL":
        with st.container():
            st.markdown('<div class="info-card fade-in">', unsafe_allow_html=True)
            st.subheader("🏔️ **Configuración Curvas de Nivel**")
            intervalo_curvas = st.slider("**Intervalo entre curvas (metros):**", 1.0, 20.0, 5.0, 1.0)
            resolucion_dem = st.slider("**Resolución DEM (metros):**", 5.0, 50.0, 10.0, 5.0)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Subida de archivo
    with st.container():
        st.markdown('<div class="info-card fade-in">', unsafe_allow_html=True)
        st.subheader("📤 **Subir Parcela**")
        uploaded_file = st.file_uploader(
            "**Selecciona archivo de tu parcela**", 
            type=['zip', 'kml', 'kmz'],
            help="Formatos aceptados: Shapefile (.zip), KML (.kml), KMZ (.kmz)"
        )
        
        if uploaded_file:
            st.success(f"✅ Archivo listo: {uploaded_file.name}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Botón de información
    st.markdown("---")
    if st.button("ℹ️ **Mostrar Información de Ayuda**", use_container_width=True):
        st.info("""
        ### 📋 Guía Rápida:
        1. Selecciona el cultivo y tipo de análisis
        2. Elige la fuente de datos satelitales
        3. Sube tu archivo de parcela
        4. Configura los parámetros específicos
        5. Ejecuta el análisis
        """)

# ===== FUNCIONES AUXILIARES (MANTENIDAS IGUAL) =====
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

# ===== FUNCIONES PARA CARGAR ARCHIVOS (MANTENIDAS IGUAL) =====
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

# ===== FUNCIONES PARA DATOS SATELITALES (MANTENIDAS IGUAL) =====
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

# ===== FUNCIONES DE ANÁLISIS GEE (MANTENIDAS IGUAL) =====
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

# ===== FUNCIONES DE TEXTURA DEL SUELO (MANTENIDAS IGUAL) =====
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

# ===== FUNCIONES DE CURVAS DE NIVEL (MANTENIDAS IGUAL) =====
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

# ===== FUNCIONES DE EXPORTACIÓN Y REPORTES (MANTENIDAS IGUAL) =====
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
        '\u2022': '-',          # • → -
        '\u2705': '[OK]',       # ✅
        '\u26A0\uFE0F': '[!]',  # ⚠️
        '\u274C': '[X]',        # ❌
        '\u2013': '-',          # – → -
        '\u2014': '--',         # — → --
        '\u2018': "'",          # ‘
        '\u2019': "'",          # ’
        '\u201C': '"',          # "
        '\u201D': '"',          # ”
        '\u2192': '->',         # →
        '\u2190': '<-',         # ←
        '\u2265': '>=',         # ≥
        '\u2264': '<=',         # ≤
        '\u00A0': ' ',          # non-breaking space → espacio normal
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

# ===== FUNCIÓN PRINCIPAL DE ANÁLISIS (MANTENIDA IGUAL) =====
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
def mostrar_resultados_textura(gdf_analizado, cultivo, area_total):
    st.markdown('<div class="section-header fade-in">📊 ESTADÍSTICAS DE TEXTURA</div>', unsafe_allow_html=True)
    
    # Métricas en tarjetas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        textura_predominante = gdf_analizado['textura_suelo'].mode()[0] if len(gdf_analizado) > 0 else "NO_DETERMINADA"
        st.markdown(f"""
        <div class="metric-card fade-in">
            <div class="metric-label">🏗️ TEXTURA PREDOMINANTE</div>
            <div class="metric-value">{textura_predominante}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        avg_arena = gdf_analizado['arena'].mean()
        st.markdown(f"""
        <div class="metric-card fade-in">
            <div class="metric-label">🏖️ ARENA PROMEDIO</div>
            <div class="metric-value">{avg_arena:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        avg_limo = gdf_analizado['limo'].mean()
        st.markdown(f"""
        <div class="metric-card fade-in">
            <div class="metric-label">🌫️ LIMO PROMEDIO</div>
            <div class="metric-value">{avg_limo:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        avg_arcilla = gdf_analizado['arcilla'].mean()
        st.markdown(f"""
        <div class="metric-card fade-in">
            <div class="metric-label">🧱 ARCILLA PROMEDIO</div>
            <div class="metric-value">{avg_arcilla:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-header fade-in">📈 COMPOSICIÓN GRANULOMÉTRICA</div>', unsafe_allow_html=True)
    
    # Gráficos en tarjeta
    with st.container():
        st.markdown('<div class="col-card fade-in">', unsafe_allow_html=True)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        composicion = [gdf_analizado['arena'].mean(), gdf_analizado['limo'].mean(), gdf_analizado['arcilla'].mean()]
        labels = ['Arena', 'Limo', 'Arcilla']
        colors_pie = ['#d8b365', '#f6e8c3', '#01665e']
        ax1.pie(composicion, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90)
        ax1.set_title('Composición Promedio del Suelo')
        
        textura_dist = gdf_analizado['textura_suelo'].value_counts()
        ax2.bar(textura_dist.index, textura_dist.values, color=[PALETAS_GEE['TEXTURA'][i % len(PALETAS_GEE['TEXTURA'])] for i in range(len(textura_dist))])
        ax2.set_title('Distribución de Texturas')
        ax2.set_xlabel('Textura')
        ax2.set_ylabel('Número de Zonas')
        ax2.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-header fade-in">🗺️ MAPA DE TEXTURAS</div>', unsafe_allow_html=True)
    
    # Mapa en tarjeta
    with st.container():
        st.markdown('<div class="col-card fade-in">', unsafe_allow_html=True)
        try:
            fig, ax = plt.subplots(1, 1, figsize=(12, 8))
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
                centroid = row.geometry.centroid
                ax.annotate(f"Z{row['id_zona']}\n{textura[:3]}", (centroid.x, centroid.y),
                            xytext=(5, 5), textcoords="offset points",
                            fontsize=8, color='black', weight='bold',
                            bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.9))
            ax.set_title(f'{ICONOS_CULTIVOS[cultivo]} MAPA DE TEXTURAS - {cultivo}',
                         fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('Longitud')
            ax.set_ylabel('Latitud')
            ax.grid(True, alpha=0.3)
            from matplotlib.patches import Patch
            legend_elements = [Patch(facecolor=color, edgecolor='black', label=textura)
                               for textura, color in colores_textura.items()]
            ax.legend(handles=legend_elements, title='Texturas', loc='upper left', bbox_to_anchor=(1.05, 1))
            plt.tight_layout()
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            st.image(buf, use_container_width=True)
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                st.download_button(
                    "📥 Descargar Mapa de Texturas",
                    buf,
                    f"mapa_texturas_{cultivo}_{datetime.now().strftime('%Y%m%d_%H%M')}.png",
                    "image/png",
                    use_container_width=True
                )
            with col_btn2:
                if st.button("🔄 Regenerar Mapa", use_container_width=True):
                    st.rerun()
        except Exception as e:
            st.error(f"Error creando mapa: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-header fade-in">📋 TABLA DE RESULTADOS POR ZONA</div>', unsafe_allow_html=True)
    
    # Tabla en tarjeta
    with st.container():
        st.markdown('<div class="col-card fade-in">', unsafe_allow_html=True)
        columnas_textura = ['id_zona', 'area_ha', 'textura_suelo', 'arena', 'limo', 'arcilla']
        columnas_textura = [col for col in columnas_textura if col in gdf_analizado.columns]
        if columnas_textura:
            tabla_textura = gdf_analizado[columnas_textura].copy()
            tabla_textura.columns = ['Zona', 'Área (ha)', 'Textura', 'Arena (%)', 'Limo (%)', 'Arcilla (%)']
            st.dataframe(tabla_textura, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-header fade-in">💡 RECOMENDACIONES DE MANEJO POR TEXTURA</div>', unsafe_allow_html=True)
    
    # Recomendaciones en tarjetas
    if 'textura_suelo' in gdf_analizado.columns:
        textura_predominante = gdf_analizado['textura_suelo'].mode()[0] if len(gdf_analizado) > 0 else "NO_DETERMINADA"
        if textura_predominante in RECOMENDACIONES_TEXTURA:
            with st.container():
                st.markdown(f'<div class="info-card fade-in"><h3>🏗️ {textura_predominante.upper()}</h3></div>', unsafe_allow_html=True)
                info_textura = RECOMENDACIONES_TEXTURA[textura_predominante]
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown('<div class="col-card fade-in">', unsafe_allow_html=True)
                    st.markdown("**✅ PROPIEDADES FÍSICAS**")
                    for prop in info_textura['propiedades']:
                        st.markdown(f"• {prop}")
                    st.markdown('</div>', unsafe_allow_html=True)
                with col2:
                    st.markdown('<div class="col-card fade-in">', unsafe_allow_html=True)
                    st.markdown("**⚠️ LIMITANTES**")
                    for lim in info_textura['limitantes']:
                        st.markdown(f"• {lim}")
                    st.markdown('</div>', unsafe_allow_html=True)
                with col3:
                    st.markdown('<div class="col-card fade-in">', unsafe_allow_html=True)
                    st.markdown("**🛠️ MANEJO RECOMENDADO**")
                    for man in info_textura['manejo']:
                        st.markdown(f"• {man}")
                    st.markdown('</div>', unsafe_allow_html=True)

# ===== CONTENIDO PRINCIPAL CON PESTAÑAS =====
# Crear pestañas para mejor organización
tab1, tab2, tab3, tab4 = st.tabs(["📁 CARGA DE DATOS", "📊 ANÁLISIS", "📈 RESULTADOS", "ℹ️ INFORMACIÓN"])

with tab1:
    st.markdown('<div class="section-header fade-in">📁 CARGA DE ARCHIVO DE PARCELA</div>', unsafe_allow_html=True)
    
    if uploaded_file:
        with st.spinner("🔄 Cargando parcela..."):
            try:
                gdf = cargar_archivo_parcela(uploaded_file)
                if gdf is not None:
                    st.session_state.gdf_cargado = gdf
                    st.session_state.analisis_completado = False
                    
                    st.markdown('<div class="info-card fade-in">', unsafe_allow_html=True)
                    st.success(f"✅ **Parcela cargada exitosamente:** {len(gdf)} polígono(s)")
                    area_total = calcular_superficie(gdf)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("""
                        <div class="col-card">
                            <h3>📊 INFORMACIÓN DE LA PARCELA</h3>
                            <p><strong>Polígonos:</strong> {}</p>
                            <p><strong>Área total:</strong> {:.1f} ha</p>
                            <p><strong>CRS:</strong> {}</p>
                            <p><strong>Formato:</strong> {}</p>
                        </div>
                        """.format(len(gdf), area_total, gdf.crs, uploaded_file.name.split('.')[-1].upper()), unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("""
                        <div class="col-card">
                            <h3>🎯 CONFIGURACIÓN ACTUAL</h3>
                            <p><strong>Cultivo:</strong> {} {}</p>
                            <p><strong>Análisis:</strong> {}</p>
                            <p><strong>Zonas:</strong> {}</p>
                            {}
                        </div>
                        """.format(ICONOS_CULTIVOS[cultivo], cultivo, analisis_tipo, n_divisiones,
                                 f"<p><strong>Satélite:</strong> {SATELITES_DISPONIBLES[satelite_seleccionado]['nombre']}</p>" if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"] else ""), unsafe_allow_html=True)
                    
                    st.markdown('<h3>📍 VISTA PREVIA DE LA PARCELA</h3>', unsafe_allow_html=True)
                    fig, ax = plt.subplots(figsize=(10, 8))
                    gdf.plot(ax=ax, color='lightgreen', edgecolor='darkgreen', alpha=0.7)
                    ax.set_title(f"Parcela: {uploaded_file.name}", fontsize=14, fontweight='bold')
                    ax.set_xlabel("Longitud")
                    ax.set_ylabel("Latitud")
                    ax.grid(True, alpha=0.3)
                    st.pyplot(fig)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Botón para ejecutar análisis
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("🚀 EJECUTAR ANÁLISIS COMPLETO", type="primary", use_container_width=True):
                            with st.spinner("🔄 Ejecutando análisis..."):
                                # Ejecutar análisis según el tipo
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
                                
                                if resultados and resultados['exitoso']:
                                    st.session_state.resultados_guardados = {
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
                                    st.session_state.analisis_completado = True
                                    st.success("✅ Análisis completado exitosamente!")
                                    st.rerun()
                    
                    with col_btn2:
                        if st.button("🔄 LIMPIAR DATOS", type="secondary", use_container_width=True):
                            st.session_state.gdf_cargado = None
                            st.session_state.resultados_guardados = None
                            st.session_state.analisis_completado = False
                            st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Error procesando archivo: {str(e)}")
                import traceback
                st.error(f"Detalle: {traceback.format_exc()}")
    else:
        st.markdown("""
        <div class="info-card fade-in">
            <h3>📤 SUBE TU ARCHIVO PARA COMENZAR</h3>
            <p>Selecciona un archivo de parcela en formato:</p>
            <ul>
                <li><strong>🗺️ Shapefile</strong> (.zip que contenga .shp, .shx, .dbf)</li>
                <li><strong>🌐 KML</strong> (Google Earth, Google Maps)</li>
                <li><strong>📦 KMZ</strong> (KML comprimido)</li>
            </ul>
            <p>Recomendación: Usa coordenadas en EPSG:4326 (WGS84) para mejores resultados.</p>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="section-header fade-in">📊 CONFIGURACIÓN DE ANÁLISIS</div>', unsafe_allow_html=True)
    
    if st.session_state.gdf_cargado:
        gdf = st.session_state.gdf_cargado
        area_total = calcular_superficie(gdf)
        
        # Mostrar configuración actual
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="col-card">
                <h3>🌱 CONFIGURACIÓN ACTUAL</h3>
                <p><strong>Cultivo:</strong> {} {}</p>
                <p><strong>Tipo de Análisis:</strong> {}</p>
                {}
                <p><strong>Zonas de manejo:</strong> {}</p>
            </div>
            """.format(
                ICONOS_CULTIVOS[cultivo], cultivo, 
                analisis_tipo,
                f"<p><strong>Nutriente:</strong> {nutriente}</p>" if nutriente else "",
                n_divisiones
            ), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="col-card">
                <h3>🛰️ DATOS SATELITALES</h3>
                {}
                {}
                {}
            </div>
            """.format(
                f"<p><strong>Satélite:</strong> {SATELITES_DISPONIBLES[satelite_seleccionado]['icono']} {SATELITES_DISPONIBLES[satelite_seleccionado]['nombre']}</p>" if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"] else "<p><em>No aplica para este tipo de análisis</em></p>",
                f"<p><strong>Índice:</strong> {indice_seleccionado}</p>" if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"] else "",
                f"<p><strong>Período:</strong> {fecha_inicio} a {fecha_fin}</p>" if analisis_tipo in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"] else ""
            ), unsafe_allow_html=True)
        
        # Mostrar información específica del cultivo
        st.markdown('<div class="section-header fade-in">🌱 PARÁMETROS DEL CULTIVO</div>', unsafe_allow_html=True)
        
        if cultivo in PARAMETROS_CULTIVOS:
            params = PARAMETROS_CULTIVOS[cultivo]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="col-card">
                    <h4>🧪 NUTRIENTES (kg/ha)</h4>
                    <p><strong>Nitrógeno:</strong> {params['NITROGENO']['min']} - {params['NITROGENO']['max']}</p>
                    <p><strong>Fósforo:</strong> {params['FOSFORO']['min']} - {params['FOSFORO']['max']}</p>
                    <p><strong>Potasio:</strong> {params['POTASIO']['min']} - {params['POTASIO']['max']}</p>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="col-card">
                    <h4>📊 ÍNDICES ÓPTIMOS</h4>
                    <p><strong>NDVI:</strong> {params['NDVI_OPTIMO']:.2f}</p>
                    <p><strong>NDRE:</strong> {params['NDRE_OPTIMO']:.2f}</p>
                    <p><strong>Materia orgánica:</strong> {params['MATERIA_ORGANICA_OPTIMA']}%</p>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class="col-card">
                    <h4>💧 CONDICIONES DEL SUELO</h4>
                    <p><strong>Humedad óptima:</strong> {params['HUMEDAD_OPTIMA']:.2f}</p>
                    {}
                </div>
                """.format(
                    f"<p><strong>Textura óptima:</strong> {TEXTURA_SUELO_OPTIMA[cultivo]['textura_optima']}</p>" if cultivo in TEXTURA_SUELO_OPTIMA else ""
                ), unsafe_allow_html=True)
    else:
        st.info("📁 Primero carga un archivo de parcela en la pestaña 'Carga de Datos'")

with tab3:
    st.markdown('<div class="section-header fade-in">📈 RESULTADOS DEL ANÁLISIS</div>', unsafe_allow_html=True)
    
    if st.session_state.analisis_completado and st.session_state.resultados_guardados:
        res = st.session_state.resultados_guardados
        gdf_analizado = res['gdf_analizado']
        
        # Mostrar resultados según el tipo de análisis
        if res['analisis_tipo'] == "ANÁLISIS DE TEXTURA":
            mostrar_resultados_textura(gdf_analizado, res['cultivo'], res['area_total'])
        
        elif res['analisis_tipo'] == "ANÁLISIS DE CURVAS DE NIVEL":
            st.markdown('<div class="section-header fade-in">🏔️ ANÁLISIS DE CURVAS DE NIVEL</div>', unsafe_allow_html=True)
            
            # Generar DEM sintético
            X, Y, Z, bounds = generar_dem_sintetico(res['gdf_original'], resolucion_dem)
            pendiente_grid = calcular_pendiente_simple(X, Y, Z, resolucion_dem)
            curvas, elevaciones = generar_curvas_nivel_simple(X, Y, Z, intervalo_curvas, res['gdf_original'])
            
            # Métricas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                elevacion_promedio = np.nanmean(Z)
                st.markdown(f"""
                <div class="metric-card fade-in">
                    <div class="metric-label">🏔️ ELEVACIÓN PROMEDIO</div>
                    <div class="metric-value">{elevacion_promedio:.1f} m</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                rango_elevacion = np.nanmax(Z) - np.nanmin(Z)
                st.markdown(f"""
                <div class="metric-card fade-in">
                    <div class="metric-label">📏 RANGO DE ELEVACIÓN</div>
                    <div class="metric-value">{rango_elevacion:.1f} m</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                mapa_pendientes, stats_pendiente = crear_mapa_pendientes_simple(X, Y, pendiente_grid, res['gdf_original'])
                st.markdown(f"""
                <div class="metric-card fade-in">
                    <div class="metric-label">📐 PENDIENTE PROMEDIO</div>
                    <div class="metric-value">{stats_pendiente['promedio']:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            with col4:
                num_curvas = len(curvas) if curvas else 0
                st.markdown(f"""
                <div class="metric-card fade-in">
                    <div class="metric-label">🔄 NÚMERO DE CURVAS</div>
                    <div class="metric-value">{num_curvas}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Mapa de pendientes
            st.markdown('<div class="section-header fade-in">🔥 MAPA DE CALOR DE PENDIENTES</div>', unsafe_allow_html=True)
            with st.container():
                st.markdown('<div class="col-card fade-in">', unsafe_allow_html=True)
                st.image(mapa_pendientes, use_container_width=True)
                st.download_button(
                    "📥 Descargar Mapa de Pendientes",
                    mapa_pendientes,
                    f"mapa_pendientes_{res['cultivo']}_{datetime.now().strftime('%Y%m%d_%H%M')}.png",
                    "image/png",
                    use_container_width=True
                )
                st.markdown('</div>', unsafe_allow_html=True)
        
        else:  # FERTILIDAD ACTUAL o RECOMENDACIONES NPK
            st.markdown(f'<div class="section-header fade-in">📊 RESULTADOS {res["analisis_tipo"]}</div>', unsafe_allow_html=True)
            
            # Métricas principales
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                <div class="metric-card fade-in">
                    <div class="metric-label">📋 ZONAS ANALIZADAS</div>
                    <div class="metric-value">{len(gdf_analizado)}</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="metric-card fade-in">
                    <div class="metric-label">📏 ÁREA TOTAL</div>
                    <div class="metric-value">{res['area_total']:.1f} ha</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                if res['analisis_tipo'] == "FERTILIDAD ACTUAL":
                    valor_prom = gdf_analizado['npk_actual'].mean()
                    st.markdown(f"""
                    <div class="metric-card fade-in">
                        <div class="metric-label">📈 ÍNDICE NPK PROMEDIO</div>
                        <div class="metric-value">{valor_prom:.3f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    valor_prom = gdf_analizado['valor_recomendado'].mean()
                    st.markdown(f"""
                    <div class="metric-card fade-in">
                        <div class="metric-label">🧪 {res['nutriente']} PROMEDIO</div>
                        <div class="metric-value">{valor_prom:.1f} kg/ha</div>
                    </div>
                    """, unsafe_allow_html=True)
            with col4:
                if res['analisis_tipo'] == "FERTILIDAD ACTUAL" and gdf_analizado['npk_actual'].mean() > 0:
                    coef_var = (gdf_analizado['npk_actual'].std() / gdf_analizado['npk_actual'].mean() * 100)
                    st.markdown(f"""
                    <div class="metric-card fade-in">
                        <div class="metric-label">📊 COEF. VARIACIÓN</div>
                        <div class="metric-value">{coef_var:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                elif res['analisis_tipo'] == "RECOMENDACIONES NPK" and gdf_analizado['valor_recomendado'].mean() > 0:
                    coef_var = (gdf_analizado['valor_recomendado'].std() / gdf_analizado['valor_recomendado'].mean() * 100)
                    st.markdown(f"""
                    <div class="metric-card fade-in">
                        <div class="metric-label">📊 COEF. VARIACIÓN</div>
                        <div class="metric-value">{coef_var:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="metric-card fade-in">
                        <div class="metric-label">📊 ESTADO</div>
                        <div class="metric-value">COMPLETADO</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Función para crear mapa estático (mantenida igual)
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
            
            # Crear y mostrar mapa
            if res['analisis_tipo'] in ["FERTILIDAD ACTUAL", "RECOMENDACIONES NPK"]:
                columna_valor = 'valor_recomendado' if res['analisis_tipo'] == "RECOMENDACIONES NPK" else 'npk_actual'
                mapa_buffer = crear_mapa_estatico(gdf_analizado, f"ANÁLISIS {res['analisis_tipo']}", columna_valor, res['analisis_tipo'], res.get('nutriente'), res['cultivo'], res.get('satelite_seleccionado'))
                
                if mapa_buffer:
                    st.markdown('<div class="section-header fade-in">🗺️ MAPA DE RESULTADOS</div>', unsafe_allow_html=True)
                    with st.container():
                        st.markdown('<div class="col-card fade-in">', unsafe_allow_html=True)
                        st.image(mapa_buffer, use_container_width=True)
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            st.download_button(
                                "📥 Descargar Mapa GEE",
                                mapa_buffer,
                                f"mapa_gee_{res['cultivo']}_{res.get('satelite_seleccionado', '')}_{res['analisis_tipo'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.png",
                                "image/png",
                                use_container_width=True
                            )
                        with col_btn2:
                            if st.button("🔄 Regenerar Mapa", use_container_width=True):
                                st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                
                # Tabla de resultados
                st.markdown('<div class="section-header fade-in">🔬 ÍNDICES SATELITALES GEE POR ZONA</div>', unsafe_allow_html=True)
                with st.container():
                    st.markdown('<div class="col-card fade-in">', unsafe_allow_html=True)
                    columnas_indices = ['id_zona', 'npk_actual', 'materia_organica', 'ndvi', 'ndre', 'humedad_suelo']
                    if res['analisis_tipo'] == "RECOMENDACIONES NPK":
                        columnas_indices = ['id_zona', 'valor_recomendado', 'npk_actual', 'materia_organica', 'ndvi', 'ndre', 'humedad_suelo']
                    columnas_indices = [col for col in columnas_indices if col in gdf_analizado.columns]
                    tabla_indices = gdf_analizado[columnas_indices].copy()
                    rename_dict = {
                        'id_zona': 'Zona',
                        'npk_actual': 'NPK Actual',
                        'valor_recomendado': 'Recomendación',
                        'materia_organica': 'Materia Org (%)',
                        'ndvi': 'NDVI',
                        'ndre': 'NDRE',
                        'humedad_suelo': 'Humedad'
                    }
                    tabla_indices = tabla_indices.rename(columns={k: v for k, v in rename_dict.items() if k in tabla_indices.columns})
                    st.dataframe(tabla_indices, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
        
        # Sección de exportación (mantenida igual)
        st.markdown('<div class="section-header fade-in">💾 EXPORTAR RESULTADOS</div>', unsafe_allow_html=True)
        
        col_exp1, col_exp2, col_exp3, col_exp4 = st.columns(4)
        
        with col_exp1:
            if st.button("🗺️ Exportar GeoJSON", key="export_geojson", use_container_width=True):
                geojson_data, nombre_archivo = exportar_a_geojson(gdf_analizado, f"parcela_{res['cultivo']}")
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
            if st.button("📄 Generar Reporte PDF", key="export_pdf", use_container_width=True):
                with st.spinner("Generando PDF..."):
                    estadisticas = generar_resumen_estadisticas(gdf_analizado, res['analisis_tipo'], res['cultivo'])
                    recomendaciones = generar_recomendaciones_generales(gdf_analizado, res['analisis_tipo'], res['cultivo'])
                    mapa_buffer = res.get('mapa_buffer')
                    pdf_buffer = generar_reporte_pdf(
                        gdf_analizado, res['cultivo'], res['analisis_tipo'], res['area_total'],
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
            if st.button("📝 Generar Reporte DOCX", key="export_docx", use_container_width=True):
                with st.spinner("Generando DOCX..."):
                    estadisticas = generar_resumen_estadisticas(gdf_analizado, res['analisis_tipo'], res['cultivo'])
                    recomendaciones = generar_recomendaciones_generales(gdf_analizado, res['analisis_tipo'], res['cultivo'])
                    mapa_buffer = res.get('mapa_buffer')
                    docx_buffer = generar_reporte_docx(
                        gdf_analizado, res['cultivo'], res['analisis_tipo'], res['area_total'],
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
            if st.button("📊 Exportar CSV", key="export_csv", use_container_width=True):
                if gdf_analizado is not None:
                    if 'geometry' in gdf_analizado.columns:
                        df_export = gdf_analizado.drop(columns=['geometry']).copy()
                    else:
                        df_export = gdf_analizado.copy()
                    csv = df_export.to_csv(index=False)
                    st.download_button(
                        label="📥 Descargar CSV",
                        data=csv,
                        file_name=f"datos_{res['cultivo']}_{res['analisis_tipo'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        key="csv_download",
                        use_container_width=True
                    )
    
    elif st.session_state.gdf_cargado and not st.session_state.analisis_completado:
        st.info("📊 Los datos están cargados pero el análisis aún no se ha ejecutado. Ve a la pestaña 'Análisis' o haz clic en 'Ejecutar Análisis' en la pestaña de carga.")
    else:
        st.info("📁 Primero carga un archivo de parcela y ejecuta el análisis para ver los resultados.")

with tab4:
    st.markdown('<div class="section-header fade-in">ℹ️ INFORMACIÓN Y AYUDA</div>', unsafe_allow_html=True)
    
    # Acordeón de información
    with st.expander("📋 FORMATOS DE ARCHIVO ACEPTADOS", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div class="col-card">
                <h4>🗺️ Shapefile (.zip)</h4>
                <p>Archivo ZIP que contiene:</p>
                <ul>
                    <li>.shp (geometrías)</li>
                    <li>.shx (índice)</li>
                    <li>.dbf (atributos)</li>
                    <li>.prj (proyección, opcional)</li>
                </ul>
                <p>Se recomienda usar EPSG:4326 (WGS84)</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class="col-card">
                <h4>🌐 KML (.kml)</h4>
                <p>Formato Keyhole Markup Language</p>
                <ul>
                    <li>Usado por Google Earth</li>
                    <li>Contiene geometrías y atributos</li>
                    <li>Puede incluir estilos y colores</li>
                    <li>Siempre en EPSG:4326</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div class="col-card">
                <h4>📦 KMZ (.kmz)</h4>
                <p>Versión comprimida de KML</p>
                <ul>
                    <li>Archivo ZIP con extensión .kmz</li>
                    <li>Puede incluir recursos (imágenes, etc.)</li>
                    <li>Compatible con Google Earth</li>
                    <li>Siempre en EPSG:4326</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    with st.expander("🌱 CULTIVOS SOPORTADOS"):
        cols = st.columns(5)
        cultivos_info = [
            ("🌾 TRIGO", "Cereal de clima templado", "#FFD700"),
            ("🌽 MAÍZ", "Cereal de alta demanda nutricional", "#FFA500"),
            ("🫘 SOJA", "Leguminosa fijadora de nitrógeno", "#8B4513"),
            ("🌾 SORGO", "Cereal resistente a sequía", "#D2691E"),
            ("🌻 GIRASOL", "Oleaginosa de profundas raíces", "#FFD700")
        ]
        
        for idx, (cultivo_nombre, descripcion, color) in enumerate(cultivos_info):
            with cols[idx]:
                st.markdown(f"""
                <div class="col-card" style="border-left: 5px solid {color};">
                    <h4 style="color: {color};">{cultivo_nombre}</h4>
                    <p>{descripcion}</p>
                </div>
                """, unsafe_allow_html=True)
    
    with st.expander("🛰️ SATÉLITES DISPONIBLES"):
        for sat_key, sat_info in SATELITES_DISPONIBLES.items():
            st.markdown(f"""
            <div class="info-card">
                <h4>{sat_info['icono']} {sat_info['nombre']}</h4>
                <p><strong>Resolución:</strong> {sat_info['resolucion']}</p>
                <p><strong>Revisita:</strong> {sat_info['revisita']}</p>
                <p><strong>Índices disponibles:</strong> {', '.join(sat_info['indices'])}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with st.expander("🔬 METODOLOGÍA CIENTÍFICA"):
        st.markdown("""
        <div class="col-card">
            <h4>📊 SISTEMA DE ANÁLISIS MULTI-CULTIVO CON DATOS SATELITALES</h4>
            
            <h5>🚀 FUNCIONALIDADES:</h5>
            <ul>
                <li><strong>🌱 Fertilidad Actual:</strong> Estado NPK del suelo usando índices satelitales</li>
                <li><strong>💊 Recomendaciones NPK:</strong> Dosis específicas por cultivo</li>
                <li><strong>🏗️ Análisis de Textura:</strong> Composición del suelo (arena, limo, arcilla)</li>
                <li><strong>🏔️ Curvas de Nivel:</strong> Análisis topográfico con mapa de calor de pendientes</li>
            </ul>
            
            <h5>🔬 METODOLOGÍA CIENTÍFICA:</h5>
            <ul>
                <li>Análisis basado en imágenes satelitales</li>
                <li>Parámetros específicos para cada cultivo</li>
                <li>Cálculo de índices de vegetación y suelo</li>
                <li>Modelos digitales de elevación (DEM) sintéticos</li>
                <li>Recomendaciones validadas científicamente</li>
            </ul>
            
            <h5>💡 CONSEJOS:</h5>
            <ul>
                <li>Para mejores resultados, usa archivos en coordenadas EPSG:4326 (WGS84)</li>
                <li>Los archivos KML deben contener polígonos (no puntos o líneas)</li>
                <li>El área recomendada es entre 1 y 1000 hectáreas</li>
                <li>Todos los cálculos se realizan en EPSG:4326</li>
                <li>Realizar análisis de suelo de laboratorio para validar resultados satelitales</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# ===== FOOTER =====
st.markdown("""
<div class="footer fade-in">
    <p>🌱 <strong>Analizador Multi-Cultivo Satellital v2.0</strong> | Sistema Inteligente de Análisis Agrícola</p>
    <p style="font-size: 0.8rem; color: #888;">Desarrollado con Streamlit, GeoPandas y datos satelitales | {} | © 2024</p>
</div>
""".format(datetime.now().strftime('%d/%m/%Y %H:%M:%S')), unsafe_allow_html=True)
