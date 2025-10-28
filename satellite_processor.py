import numpy as np
import rasterio
from sentinelhub import (
    SHConfig, 
    BBox, 
    CRS, 
    DataCollection, 
    MimeType, 
    MosaickingOrder,
    SentinelHubRequest, 
    bbox_to_dimensions
)
from datetime import datetime, timedelta
import logging

class SatelliteProcessor:
    def __init__(self, config):
        self.config = config
        self.sh_config = SHConfig()
        self._setup_sentinelhub_config()
    
    def _setup_sentinelhub_config(self):
        """Configurar credenciales de Sentinel Hub"""
        if self.config['SENTINELHUB_CONFIG']['instance_id']:
            self.sh_config.instance_id = self.config['SENTINELHUB_CONFIG']['instance_id']
        if self.config['SENTINELHUB_CONFIG']['client_id']:
            self.sh_config.sh_client_id = self.config['SENTINELHUB_CONFIG']['client_id']
        if self.config['SENTINELHUB_CONFIG']['client_secret']:
            self.sh_config.sh_client_secret = self.config['SENTINELHUB_CONFIG']['client_secret']
    
    def get_field_bbox(self, gdf):
        """Obtener bounding box de la parcela"""
        bounds = gdf.total_bounds
        return BBox(bbox=bounds, crs=CRS.WGS84)
    
    def calculate_evalscript(self, indices):
        """Generar evalscript para los índices requeridos"""
        evalscript = """
        //VERSION=3
        function setup() {
            return {
                input: [{
                    bands: ["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12"],
                    units: "REFLECTANCE"
                }],
                output: [
                    {id: "indices", bands: %d, sampleType: "FLOAT32"}
                ]
            };
        }
        
        function evaluatePixel(sample) {
            // Cálculo de índices básicos
            let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
            let ndre = (sample.B08 - sample.B05) / (sample.B08 + sample.B05);
            let gndvi = (sample.B08 - sample.B03) / (sample.B08 + sample.B03);
            let osavi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04 + 0.16);
            let mcari = ((sample.B05 - sample.B04) - 0.2 * (sample.B05 - sample.B03)) * (sample.B05 / sample.B04);
            
            return {
                indices: [%s]
            };
        }
        """ % (len(indices), ", ".join(indices))
        
        return evalscript
    
    def download_sentinel2_data(self, gdf, start_date, end_date, indices=['ndvi', 'ndre']):
        """Descargar datos de Sentinel-2 para la parcela"""
        try:
            bbox = self.get_field_bbox(gdf)
            resolution = 10
            size = bbox_to_dimensions(bbox, resolution=resolution)
            
            # Mapear índices a cálculos
            index_calculations = {
                'ndvi': '(sample.B08 - sample.B04) / (sample.B08 + sample.B04)',
                'ndre': '(sample.B08 - sample.B05) / (sample.B08 + sample.B05)',
                'gndvi': '(sample.B08 - sample.B03) / (sample.B08 + sample.B03)',
                'osavi': '(sample.B08 - sample.B04) / (sample.B08 + sample.B04 + 0.16)',
                'mcari': '((sample.B05 - sample.B04) - 0.2 * (sample.B05 - sample.B03)) * (sample.B05 / sample.B04)'
            }
            
            selected_indices = [index_calculations[idx] for idx in indices if idx in index_calculations]
            evalscript = self.calculate_evalscript(selected_indices)
            
            request = SentinelHubRequest(
                evalscript=evalscript,
                input_data=[
                    SentinelHubRequest.input_data(
                        data_collection=DataCollection.SENTINEL2_L2A,
                        time_interval=(start_date, end_date),
                        mosaicking_order=MosaickingOrder.LEAST_CC
                    )
                ],
                responses=[SentinelHubRequest.output_response('indices', MimeType.TIFF)],
                bbox=bbox,
                size=size,
                config=self.sh_config
            )
            
            data = request.get_data()
            return data[0] if data else None
            
        except Exception as e:
            logging.error(f"Error descargando datos Sentinel-2: {str(e)}")
            return None
    
    def calculate_zonal_statistics(self, gdf, satellite_data):
        """Calcular estadísticas zonales para cada polígono"""
        results = []
        
        for idx, row in gdf.iterrows():
            geometry = row.geometry
            
            # Extraer valores de píxeles dentro del polígono
            mask = self._create_mask(satellite_data, geometry)
            masked_data = satellite_data * mask
            
            # Calcular estadísticas
            valid_pixels = masked_data[masked_data != 0]
            
            if len(valid_pixels) > 0:
                stats = {
                    'mean': float(np.nanmean(valid_pixels)),
                    'std': float(np.nanstd(valid_pixels)),
                    'min': float(np.nanmin(valid_pixels)),
                    'max': float(np.nanmax(valid_pixels)),
                    'median': float(np.nanmedian(valid_pixels)),
                    'pixels_count': len(valid_pixels)
                }
            else:
                stats = {
                    'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'median': 0, 'pixels_count': 0
                }
            
            results.append(stats)
        
        return results
    
    def _create_mask(self, data, geometry):
        """Crear máscara para el polígono (simplificado)"""
        # Implementar lógica de máscara espacial
        # Esto es una simplificación - necesitarás rasterio/geopandas para implementación completa
        return np.ones_like(data)
