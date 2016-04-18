import os

from unittest import TestCase
from nittygriddy import utils, settings


class Test_downloader(TestCase):
    def setUp(self):
        test_local_dir = "~/lhc_data_test/"
        settings["local_data_dir"] = test_local_dir
        try:
            os.rmdir(test_local_dir)
        except OSError:
            pass

    def test_invalid_dataset(self):
        self.assertRaises(KeyError, utils.download, "invalid_dataset", 5)

    def test_downloaded_something(self):
        utils.download("LHC10h_AOD160", 0.001)
