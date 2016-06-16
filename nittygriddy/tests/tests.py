import os

from unittest import TestCase, skip
import subprocess

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

    @skip("Skip download test")
    def test_downloaded_something(self):
        utils.download_dataset("LHC10h_AOD160", 0.001)


class Test_grid_features(TestCase):
    def test_latest_aliphysics(self):
        self.assertNotEqual(utils.get_latest_aliphysics(), "")


class Test_find_latest_merge_files(TestCase):
    def test_workdir_does_not_exist(self):
        self.assertRaises(ValueError, utils.find_latest_merge_results, "asdfasdfasdf")

    def test_find_something(self):
        self.assertNotEqual(0, len(utils.find_latest_merge_results("20160504_0035_15j_CINT7_multFluc")))


class Test_environment(TestCase):
    def tes_alien_token_invalid(self):
        cmd = ['alien-token-destroy']
        subprocess.check_output(cmd)
        self.assertFalse(utils.check_alien_token())
