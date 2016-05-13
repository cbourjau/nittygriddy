import os

from unittest import TestCase
from nittygriddy import utils, settings


class Test_downloader(TestCase):
    def setUp(self):
        test_local_dir = "~/lhc_data_test/"
        settings["local_data_dir"] = test_local_dir
        try:
            # make sure that we really only delete a __test__ dir
            if 'test' in test_local_dir:
                os.rmdir(test_local_dir)
        except OSError:
            pass

    def test_invalid_dataset(self):
        self.assertRaises(KeyError, utils.download_dataset, "invalid_dataset", 5)

    def test_downloaded_something(self):
        utils.download_dataset("LHC10h_AOD160", 0.001)


class Test_grid_features(TestCase):
    def test_latest_aliphysics(self):
        self.assertNotEqual(utils.get_latest_aliphysics(), "")
