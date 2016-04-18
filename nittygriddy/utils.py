from glob import glob
import json
import os
import shutil
import subprocess

from nittygriddy import settings


def get_datasets():
    """
    Get the dictionary describing the datasets
    Returns
    -------
    dict :
        dataset dictionary
    """
    with open(os.path.dirname(os.path.abspath(__file__)) + "/datasets.json", "read") as f:
        datasets = json.load(f)
    return datasets


def copy_template_files_to(dest):
    template_dir = os.path.dirname(os.path.abspath(__file__))
    shutil.copy(os.path.join(template_dir, "run.C"), dest)


def get_template_GetSetting():
    template_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(template_dir, "GetSetting.C")) as get_setting_c:
        return get_setting_c.read()


def get_size(search_string):
    """
    Return
    ------
    int : Accumulated size of all files matching the search string
    """
    total_size = 0
    for path2file in glob(search_string):
        total_size += os.path.getsize(path2file)
    return total_size


def download(dataset, volume):
    """
    Download files from the given dataset until the target volume is met
    Parameters
    ----------
    dataset : string
        Name of the dataset
    volume : int, float
        Download files until the total volume is this number in GB
    """
    ds = get_datasets()[dataset]
    # check if the root datadir exists
    local_data_dir = os.path.expanduser(settings["local_data_dir"])
    period_dir = os.path.join(local_data_dir, ds["datadir"].lstrip('/'))
    try:
        os.makedirs(period_dir)
    except OSError:
        pass
    for run in ds["run_list"].split(" "):
        search_string = os.path.join(ds["datadir"],
                                     ds["run_number_prefix"] + str(run),
                                     ds["data_pattern"])
        find_cmd = ['alien_find',
                    os.path.split(search_string)[0],
                    os.path.split(search_string)[1]]
        run_files = subprocess.check_output(find_cmd).split()
        # this should be sorted in order to download sequentially
        for path2file in run_files:
            # alien_find puts some jibberish; stop at first line without path
            if not path2file.startswith("/"):
                break
            # paths to file
            local_path = os.path.join(local_data_dir, path2file.lstrip('/'))
            alien_path = "alien:/" + path2file
            try:
                os.makedirs(os.path.dirname(local_path))
            except OSError:
                pass
            cp_cmd = ['alien_cp', '-m', '-s', alien_path, local_path]
            subprocess.check_output(cp_cmd)

            cum_size = get_size(os.path.join(period_dir, "*", ds["data_pattern"]))
            print "Downloaded {}GB of {} so far".format(cum_size / 1e9, volume)
            if (cum_size / 1e9) > volume:
                return
