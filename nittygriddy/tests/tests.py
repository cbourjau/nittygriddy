import os

from unittest import TestCase
from nittygriddy import download, settings


class Test_downloader(TestCase):
    def test_invalid_dataset(self):
        self.assertRaises(KeyError, download, "invalid_dataset", 5)

    def test_downloaded_something(self):
        download("LHC10h", 5)
        self.assertTrue(os.path.isdir(os.path.expanduser(settings["local_data_dir"])))
