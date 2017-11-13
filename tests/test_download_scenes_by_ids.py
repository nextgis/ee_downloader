import unittest

from ee_downloader.downloader import download_scenes_by_ids
from test_default_downloader import DefaultDownloader


class DownloadByIds(DefaultDownloader):
    @classmethod
    def call_default_download_scenes_by_ids(cls, downloader_parameters):
        return download_scenes_by_ids(
            login=downloader_parameters.login,
            password=downloader_parameters.password,
            identifiers=downloader_parameters.identifiers,
            temp_dir=downloader_parameters.temp_dir,
            product_name=downloader_parameters.product_name,
            product_format=downloader_parameters.product_format
        )

    def test_should_raise_exception_if_product_name_is_wrong(self):
        self.downloader_parameters.product_name = 'Wrong product name'
        with self.assertRaises(ValueError):
            DownloadByIds.call_default_download_scenes_by_ids(self.downloader_parameters)

    def test_should_raise_exception_if_product_format_is_wrong(self):
        self.downloader_parameters.product_format = 'Wrong product format'
        with self.assertRaises(ValueError):
            DownloadByIds.call_default_download_scenes_by_ids(self.downloader_parameters)

    def test_should_raise_exception_if_identifiers_is_not_array(self):
        self.downloader_parameters.identifiers = None
        with self.assertRaises(ValueError):
            DownloadByIds.call_default_download_scenes_by_ids(self.downloader_parameters)

    def test_should_raise_exception_if_identifiers_is_empty_array(self):
        self.downloader_parameters.identifiers = []
        with self.assertRaises(ValueError):
            DownloadByIds.call_default_download_scenes_by_ids(self.downloader_parameters)


if __name__ == '__main__':
    unittest.main()
