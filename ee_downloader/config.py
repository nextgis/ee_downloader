EE_URL = 'https://earthexplorer.usgs.gov'
AUTH_URL = 'https://ers.cr.usgs.gov/login/'
MAX_SCENE_COUNT = 25000

PRODUCT = 'Sentinel-2'
PRODUCTS = {
    'Landsat 8 OLI/TIRS C1 Level-1': {
        'id': 12864,
        'field_identifier_ids': ['text_20520_1', 'text_20520_2', 'text_20520_3', 'text_20520_4'],
        'select_ids': ['select_20522_5', 'select_20515_5', 'select_20510_4', 'select_20517_4',
                       'select_20518_4', 'select_20513_3', 'select_20519_3'],
        'scene_identifier_key': 'Landsat Product Identifier'
    },
    'Sentinel-2': {
        'id': 10880,
        'field_identifier_ids': ['text_18698_1', 'text_18698_2', 'text_18698_3', 'text_18698_4'],
        'select_ids': ['select_18696_5', 'select_18697_3'],
        'scene_identifier_key': 'Entity ID'
    }
}

FORMAT = 'Full Resolution Browse in GeoTIFF format'
FORMATS = {
    # For Landsat 8
    'LandsatLook Quality Image': {
        'extension': '.jpg'
    },
    'Level-1 GeoTIFF Data Product': {
        'extension': '.tar.gz'
    },

    # For Sentinel-2
    'Full Resolution Browse in GeoTIFF format': {
        'extension': '.tif'
    },
    'L1C Tile in JPEG2000 format': {
        'extension': '.zip'
    }
}
