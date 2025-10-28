import os
from datetime import datetime, timedelta

# Configuración Sentinel Hub
SENTINELHUB_CONFIG = {
    'instance_id': os.getenv('SENTINELHUB_INSTANCE_ID', ''),
    'client_id': os.getenv('SENTINELHUB_CLIENT_ID', ''),
    'client_secret': os.getenv('SENTINELHUB_CLIENT_SECRET', '')
}

# Configuración USGS EarthExplorer (Landsat)
USGS_CONFIG = {
    'username': os.getenv('USGS_USERNAME', ''),
    'password': os.getenv('USGS_PASSWORD', '')
}

# Parámetros de imágenes por cultivo
IMAGE_PARAMETERS = {
    'TRIGO': {
        'optimal_months': [5, 6, 7],  # Mayo-Julio (hemisferio norte)
        'cloud_cover_max': 10,
        'resolution': 10  # metros
    },
    'MAÍZ': {
        'optimal_months': [6, 7, 8],
        'cloud_cover_max': 10,
        'resolution': 10
    },
    'SOJA': {
        'optimal_months': [1, 2, 3],  # Enero-Marzo (hemisferio sur)
        'cloud_cover_max': 15,
        'resolution': 10
    },
    'SORGO': {
        'optimal_months': [3, 4, 5],
        'cloud_cover_max': 10,
        'resolution': 10
    },
    'GIRASOL': {
        'optimal_months': [7, 8, 9],
        'cloud_cover_max': 10,
        'resolution': 10
    }
}
