import unittest


class DefaultDownloaderParameters:
    def __init__(self):
        self.login = 'User'
        self.password = 'Sekret'
        self.identifiers = ['S2A_OPER_MSI_L1C_TL_SGS__20160716T080034_20160716T113445_A005566_T39UWB_N02_04_01']
        self.temp_dir = '/tmp'
        self.product_name = ''
        self.product_format = ''
        self.result_dir = None


class DefaultDownloader(unittest.TestCase):
    def setUp(self):
        self.downloader_parameters = DefaultDownloaderParameters()
