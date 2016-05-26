from glob import glob
import json
import os
import shutil
import subprocess
import sys

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


def download_file(alien_path, local_path):
    """
    Download the file `alien` to `local`

    Parameters
    ----------
    alien_path, local_path : string
        Full path to files
    """
    if os.path.isfile(local_path):
        raise ValueError("Local file exists")
    try:
        os.makedirs(os.path.dirname(local_path))
    except OSError:
        pass
    alien_path = "alien:/" + alien_path
    cp_cmd = ['alien_cp', '-m', '-s', alien_path, local_path]
    p = subprocess.Popen(cp_cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    p.wait()
    if p.returncode != 0:
        print "\n", p.stdout.read()
        print("An error occued while downloading {}; "
              "The broken file was deleted.".format(local_path))
        try:
            os.remove(local_path)
        except OSError:
            pass


def download_dataset(dataset, volume):
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
    warned_about_skipped = False
    for run in ds["run_list"].split(","):
        run = run.strip()  # get rid of spaces around the number
        search_string = os.path.join(ds["datadir"],
                                     ds["run_number_prefix"] + str(run),
                                     ds["data_pattern"])
        find_cmd = ['alien_find',
                    os.path.dirname(search_string),
                    os.path.basename(search_string)]
        run_files = subprocess.check_output(find_cmd).split()
        run_files.sort()

        for alien_path in run_files:
            # alien_find puts some jibberish; stop at first line without path
            if not alien_path.startswith("/"):
                break
            # paths to file
            local_path = os.path.join(local_data_dir, alien_path.lstrip('/'))
            try:
                download_file(alien_path, local_path)
            except ValueError:
                if not warned_about_skipped:
                    warned_about_skipped = True
                    print "Some files were present and were not redownloaded"
            cum_size = get_size(os.path.join(period_dir, "*", ds["data_pattern"]))
            sys.stdout.write("\rDownloaded {:2f}% of {}GB so far"
                             .format(100 * cum_size / 1e9 / volume, volume))
            sys.stdout.flush()
            if (cum_size / 1e9) > volume:
                return


def get_latest_aliphysics():
    """
    Return the latest aliphysics version string as expected by the grid plugin.
    """
    from datetime import datetime, timedelta
    from pytz import timezone
    tz = timezone('Europe/Zurich')
    tagtime = datetime.now(tz=tz)
    if tagtime.hour < 18:
        tagtime -= timedelta(days=1)
    return "vAN-{}-1".format(tagtime.strftime("%Y%m%d"))


def find_latest_merge_results(workdir):
    """
    Find the files resulting from the latest online merge. It relies on
   the resulting files being called `AnalysisResults.root`

    Parameters
    ----------
    workdir : str
        name of the grid workdir

    Returns
    -------
    list :
        List of full alien paths to the latest merge files

    Raises
    ------
    ValueError :
        workdir does not exist in user directory

    """
    user_name = subprocess.check_output(['alien_whoami']).strip()
    alien_workdir = os.path.join("/alice/cern.ch/user/{}/{}/".format(user_name[0], user_name), workdir)
    try:
        subprocess.check_output(['alien_ls', alien_workdir])
    except subprocess.CalledProcessError:
        raise ValueError("{} does not exist".format(alien_workdir))

    cmd = ['alien_find', alien_workdir, 'AnalysisResults.root']
    finds = subprocess.check_output(cmd).strip().split()
    # alien_find puts some jibberish; stop at first line without path
    finds = [path for path in finds if path.startswith("/")]
    # find shortest path
    min_nfolders = min([len(path.split("/")) for path in finds])
    top_level_files = [path for path in finds if len(path.split("/")) == min_nfolders]
    return top_level_files
