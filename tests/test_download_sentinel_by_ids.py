import unittest

from test_default_downloader import DefaultDownloaderParameters
from test_download_scenes_by_ids import DownloadByIds


class DownloadSentinelByIds(DownloadByIds):
    scenes = None
    default_downloader_params = None

    @classmethod
    def setUpClass(cls):
        default_downloader_params = DefaultDownloaderParameters()
        default_downloader_params.product_format = 'Full Resolution Browse in GeoTIFF format'
        default_downloader_params.product_name = 'Sentinel-2'
        default_downloader_params.identifiers = \
            ['S2A_OPER_MSI_L1C_TL_SGS__20160716T080034_20160716T113445_A005566_T39UWB_N02_04_01']

        DownloadSentinelByIds.scenes = DownloadByIds.call_default_download_scenes_by_ids(default_downloader_params)

    def test_should_download_sentinel_geotiff(self):
        self.assertEqual(1, len(DownloadSentinelByIds.scenes))


if __name__ == '__main__':
    unittest.main()
