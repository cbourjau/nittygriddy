import os

from nittygriddy import settings
from utils import get_datasets


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
    local_data_dir = os.path.expanduser(settings.settings["local_data_dir"])
    period_dir = os.path.join(local_data_dir, ds["datadir"].lstrip('/'))
    try:
        os.makedirs(period_dir)
    except OSError:
        pass
    for run in ds["run_list"]:
        run_files = os.popen("alien_find {}".format(os.path.join(ds["datadir"],
                                                                 ds["run_number_prefix"] + str(run),
                                                                 ds["data_pattern"])))
        # this should be sorted in order to download sequentially
        for f in run_files:
            # check present size
            # command to check cummulated size of downloaded files
            du_sc_dir = os.path.join(period_dir, "*", ds["data_pattern"])
            cum_size = int(os.popen("du -sc " + du_sc_dir + "| tail -n1 | awk '{print $1}'").read())
            print cum_size
            if (cum_size / 1e6) > volume:
                break

            # paths to file
            local_path = os.path.join(local_data_dir, f.lstrip('/'))
            alien_path = "alien:/" + f
            try:
                os.makedirs(os.path.dirname(local_path))
            except OSError:
                pass
            alien_cmd = "alien_cp -m -s {} {}".format(alien_path, local_path)
            print "Executing " + alien_cmd
            print os.popen(alien_cmd).read()

