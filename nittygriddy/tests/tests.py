import os

from unittest import TestCase, skip
import subprocess

from nittygriddy import utils, settings, parser
from nittygriddy.alienTokenError import AlienTokenError


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

    def test_par_file(self):
        self.assertRaises(ValueError, utils.prepare_par_files, "I_dont_exists.par", "test_folder")

    def test_find_user_grid_dir(self):
        grid_home = utils.find_user_grid_dir()
        self.assertRegexpMatches(grid_home, '/alice/cern.ch/user/\w/\w+/')

    def find_latest_merge_results(self):
        # a test dir set up under alien:///alice/cern.ch/user/c/cbourjau/
        workdir = "nitty_test"
        # try with not absolute workdir:
        self.assertRaises(ValueError, utils.find_latest_merge_results, workdir)
        # with absolut alien path
        alien_workdir = os.path.join(utils.find_user_grid_dir(), workdir)
        self.assertEqual(utils.find_latest_merge_results(alien_workdir),
                         ['/alice/cern.ch/user/c/cbourjau/nitty_test/AnalysisResults.root'])

    def test_find_merge_sources(self):
        workdir = "nitty_test"
        alien_workdir = os.path.join(utils.find_user_grid_dir(), workdir)
        merge_results = utils.find_latest_merge_results(alien_workdir)
        self.assertEqual(utils.find_sources_of_merged_files(merge_results),
                         ['/alice/cern.ch/user/c/cbourjau/nitty_test/001/AnalysisResults.root',
                          '/alice/cern.ch/user/c/cbourjau/nitty_test/002/AnalysisResults.root'])


class Test_environment(TestCase):
    """
    These tests require a valid alien token.
    """
    def test_alien_token_valid(self):
        self.assertTrue(utils.check_alien_token())

    @skip("Skip token invalid test")
    def test_alien_token_invalid(self):
        cmd = ['alien-token-destroy']
        subprocess.check_output(cmd)
        self.assertRaises(AlienTokenError, utils.check_alien_token)


class Test_create_GetSetting_c_file(TestCase):
    """
    Test the create of the GetSetting.C file
    """
    def test_create_getSetting_c(self):
        import tempfile
        tmp_dir = tempfile.gettempdir()
        _parser = parser.create_parser()
        args = _parser.parse_args(['run', 'lite', 'LHC12a11a'])
        utils.prepare_get_setting_c_file(tmp_dir, args)
