import json
import os
import shutil


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
