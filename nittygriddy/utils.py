from glob import glob
import json
import os
import re
import shutil
import subprocess
import sys
import urllib2
import zipfile

import ROOT
from rootpy.io import root_open

from nittygriddy import settings
from nittygriddy.alienTokenError import AlienTokenError

GRID_CONNECTION = None


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


def download_file(alien_src, local_dest):
    """
    Download file `alien_src` to `local_path`.

    Parameters
    ----------
    alien_path, local_path : string
        Full path to files

    Returns
    -------
    int : File size in bytes
    """
    check_alien_token()
    try:
        os.makedirs(os.path.dirname(local_dest))
    except OSError:
        pass
    # fix the dest to include the file name
    if not os.path.basename(local_dest):
        local_dest = os.path.join(local_dest, os.path.basename(alien_src))

    with root_open("alien://" + alien_src) as f:
        if not f.Cp(local_dest):
            try:
                os.remove(local_dest)
            except OSError:
                pass  # file probably didn't exist at all
            raise OSError("An error occued while downloading {}; "
                          "The broken file was deleted.".format(local_dest))
        return f.GetSize()


def find_associated_archive_files(datadir, run_number_prefix, runs, data_pattern):
    check_alien_token()
    urls = []
    for run in runs:
        # Create a search string for this run; make sure its a string not u""
        search_string = str(os.path.join(datadir,
                                         run_number_prefix + str(run),
                                         os.path.dirname(data_pattern)))
        # search for the respective archives depending on the required file name
        if "AliESDs.root" in data_pattern:
            archive_name = "root_archive.zip"
        if "AliAOD.root" in data_pattern:
            archive_name = "root_archive.zip"  # "aod_archive.zip"
        finds = ROOT.TAliEnFind(search_string, archive_name)
        # Get file turns the URL into a string. Talk about indirection...
        urls += [el.GetFirstUrl().GetFile() for el in finds.GetCollection().GetList()]
    return urls


def download_from_grid_archive(alien_src, local_dest):
    """
    Download the files from a grid-zip-file at `alien_src` to `local_path`.
    If all files from the archive already exist locally, do not re-download them.

    Parameters
    ----------
    alien_path, local_path : string
        Full path to files

    Returns
    -------
    int : File size in bytes
    """
    check_alien_token()
    try:
        os.makedirs(os.path.dirname(local_dest))
    except OSError:
        pass

    # fix the dest to include the file name
    if not os.path.basename(local_dest):
        local_dest = os.path.join(local_dest, os.path.basename(alien_src))

    with root_open("alien://" + alien_src) as f:
        if not f.IsArchive():
            raise ValueError("{} does not point to an archive file.".format(alien_src))
        fsize = f.GetSize()
        fnames = [m.GetName() for m in f.GetArchive().GetMembers()]
        local_dir = os.path.dirname(local_dest)
        if all([os.path.isfile(os.path.join(local_dir, fname)) for fname in fnames]):
            raise OSError("Files exist; not redownloading")

        if not f.Cp(local_dest):
            raise RuntimeError("Could not download {}!".format(alien_src))

    with zipfile.ZipFile(local_dest) as zf:
        try:
            zf.extractall(os.path.dirname(local_dest))
        except IOError:
            print "Error unzipping {}. File was deleted".format(local_dest)
    # Delete the zip archive file
    try:
        os.remove(local_dest)
    except OSError:
        pass  # file probably didn't exist at all?!
    return fsize


def download_dataset(dataset, volume, runs=None):
    """
    Download files from the given dataset until the target volume is met
    Parameters
    ----------
    dataset : string
        Name of the dataset
    volume : int, float
        Download files until the total volume is this number in GB
    runs : str
        Optional; Comma separeated list of runs which should be downloaded.
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
    try:
        if runs:
            runs = [int(r.strip()) for r in runs.split(",")]
        else:
            runs = [int(r.strip()) for r in ds["run_list"].split(",")]
    except ValueError:
        raise ValueError("Malformated run number. Check run list!")

    urls = find_associated_archive_files(ds["datadir"],
                                         ds["run_number_prefix"],
                                         runs,
                                         ds["data_pattern"])
    cum_size = 0
    for url in urls:
        local_path = os.path.join(local_data_dir, url.lstrip('/'))
        try:
            cum_size += download_from_grid_archive(url, local_path)
        except OSError:
            if not warned_about_skipped:
                warned_about_skipped = True
                print "Some files were present and were not redownloaded"
        except RuntimeError as e:
            # Error in download; probably with MD5 sum
            print e.message
            pass

        sys.stdout.write("\rDownloaded {:2f}% of {}GB so far"
                         .format(100 * cum_size / 1e9 / volume, volume))
        sys.stdout.flush()
        if (cum_size / 1e9) > volume:
            return


def get_latest_aliphysics():
    """
    Find the latest version of aliphysics deployed on the grid.

    Returns
    -------
    string :
        tag as its usable in run.C; eg., 'vAN-20160606-1'
    """
    html = urllib2.urlopen('http://alimonitor.cern.ch/packages/').read()
    tag_pattern = r'vAN-\d{8}-\d+'
    return sorted(re.findall(tag_pattern, html)).pop()


def find_latest_merge_results(alien_workdir):
    """
    Find the files resulting from the latest online merge. It relies on
    the resulting files being called `AnalysisResults.root`

    Parameters
    ----------
    workdir : str
        Absolute alien path to grid workdir

    Returns
    -------
    list :
        List of full alien paths to the latest merge files

    Raises
    ------
    ValueError :
        workdir does not exist in user directory

    """
    try:
        subprocess.check_output(['alien_ls', alien_workdir])
    except subprocess.CalledProcessError:
        raise ValueError("{} does not exist".format(alien_workdir))

    cmd = ['alien_find', alien_workdir, 'AnalysisResults.root']
    finds = subprocess.check_output(cmd).strip().split()
    # alien_find puts some jibberish; stop at first line without path
    finds = [path for path in finds if path.startswith("/")]

    # do we have a result file in output/{run}/AnalysisResults.root?
    pattern = r".*/output/\d+/AnalysisResults.root"
    if [f for f in finds if re.match(pattern, f)]:
        return [f for f in finds if re.match(pattern, f)]

    # Do we have merge stages?
    pattern = r".*/output/\d+/Stage_(\d+)/\d+/AnalysisResults.root"
    stages = [int(re.match(pattern, f).group(1)) for f in finds if re.match(pattern, f)]
    if stages:
        max_stage = max(stages)
        pattern = r".*/output/\d+/Stage_{}/\d+/AnalysisResults.root".format(max_stage)
        return [f for f in finds if re.match(pattern, f)]
    # find shortest path; last resort
    min_nfolders = min([len(path.split("/")) for path in finds])
    top_level_files = [path for path in finds if len(path.split("/")) == min_nfolders]
    return top_level_files


def check_alien_token():
    """
    Check if a valid alien toke exists

    Raises
    ------
    AlienTokenError :
        If there was an error checking the token or if the existing token is invalid
    """
    # Tell python that GRID_CONNECTION is a global variable which we might write to
    global GRID_CONNECTION
    if GRID_CONNECTION is None:
        GRID_CONNECTION = ROOT.TGrid.Connect("alien")
    if not GRID_CONNECTION.IsConnected():
        raise AlienTokenError("No grid connection. Call `alien-token-init` before running nittygriddy.")
    cmd = ['alien-token-info']
    try:
        output = subprocess.check_output(cmd)
    except subprocess.CalledProcessError:
        raise AlienTokenError("Could not call `alien-token-info` to check token.")
    for l in output.splitlines():
        if "Token is still valid!" in l:
            return True
    raise AlienTokenError("Alien token is invalid. Call `alien-token-init` before running nittygriddy.")


def prepare_par_files(par_files, output_dir):
    """
    Copy par files to output_dir

    Parameters
    ----------
    par_files : str
        Comma separated string of par file names
    output_dir : str
        Folder to where the par files should be copied

    Raises
    ------
    ValueError :
        If par file could not be found
    """
    par_dir = os.path.expandvars("$ALICE_PHYSICS/PARfiles/")
    for par_file in par_files.split():
        if par_file.startswith("lib") and par_file.endswith(".so"):
            continue
        # only copy par files, libs are loaded from grid installation
        try:
            shutil.copy(os.path.join(par_dir, par_file), output_dir)
        except IOError:
            raise ValueError("Par file {} could not be copied!".format(par_file))


def find_user_grid_dir():
    """
    Figure out the user's grid home directory.

    Return
    ------
    string :
        Absolute path to user's home directory
    """
    check_alien_token()
    user_name = ROOT.TGrid.Connect("alien").GetUser()
    # user_name = subprocess.check_output(['alien_whoami']).strip()
    alien_home = "/alice/cern.ch/user/{}/{}/".format(user_name[0], user_name)
    return alien_home


def find_sources_of_merged_files(merge_results):
    """
    Find the files used for an online merge. It relies on
    the involved files being called `AnalysisResults.root`

    Parameters
    ----------
    merge_results : list
        alien path to the succesful merge results

    Returns
    -------
    list :
        List of full alien paths to the pre merges' source files
    """
    sources = []
    for merge_result in merge_results:
        # make a search string for the source files
        # this assumes that the source files are in folders below
        # the given AnalysisResults.root file
        # Thus: /alienpath/AnalysisResults.root -> /alienpath/*/
        search_str_sources = merge_result.replace("AnalysisResults.root", "*/")
        cmd = ['alien_find', search_str_sources, 'AnalysisResults.root']
        finds = subprocess.check_output(cmd).strip().split()
        # alien_find puts some jibberish; stop at first line without path
        finds = [path for path in finds if path.startswith("/")]

        # Safety: make sure that the paths of the sources are longer
        # than their merge result
        for find in finds:
            if len(merge_result) >= len(find):
                raise ValueError("Algorithm for finding merge source files produced unexpected results")
        sources += finds
    return sources


def yn_choice(message, default='y'):
    """
    Querry the user if he or she wants to proceed.

    Parameters
    ----------
    message :
        Yes/No message presented to the user.
    default :
        Default action if no input is given

    Returns
    -------
    bool :
        `True` for yes, else `False`
    """
    choices = 'Y/n' if default.lower() in ('y', 'yes') else 'y/N'
    choice = raw_input("%s (%s) " % (message, choices))
    values = ('y', 'yes', '') if default == 'y' else ('y', 'yes')
    return choice.strip().lower() in values


def prepare_get_setting_c_file(output_dir, args):
    ds = get_datasets()[args.dataset]
    with open(os.path.join(output_dir, "GetSetting.C"), "w") as get_setting_c:
        if args.run_list:
            # the grid plugin expects the runs to be separeated by ", "; not the space!
            runs = [run.strip() for run in args.run_list.split(",")]
            runs_str = ", ".join(runs)
        else:
            runs_str = ds['run_list']
        as_string = get_template_GetSetting().\
            format(workdir=os.path.split(output_dir)[1],
                   datadir=ds['datadir'],
                   data_pattern=ds['data_pattern'],
                   run_number_prefix=ds['run_number_prefix'],
                   run_list=runs_str,
                   is_mc=ds["is_mc"],
                   datatype=ds["datatype"],
                   runmode=args.runmode,
                   nworkers=args.nworkers,
                   wait_for_gdb="true" if args.wait_for_gdb else "false",
                   aliphysics_version=get_latest_aliphysics() if args.runmode == "grid" else "",
                   par_files=args.par_files if args.par_files else "",
                   ttl=args.ttl,
                   max_files_subjob=args.max_files_subjob,
                   use_train_conf="true" if project_uses_train_cfg() else "false",
                   runs_per_master=args.runs_per_master)
        get_setting_c.write(as_string)


def is_valid_project_dir():
    """
    Check if the current directory is a valid "project" directory.

    Raises
    ------
    ValueError:
        If the current directory does not meet the standards
    """
    cur_dir = os.path.abspath(os.path.curdir)
    wagon_conf_file = os.path.isfile(os.path.join(cur_dir, "ConfigureWagon.C"))
    train_conf = os.path.isfile(os.path.join(cur_dir, "MLTrainDefinition.cfg"))

    # Project dir has either an ConfigureWagon.C or a
    # MLTrainDefinition.cfg file, but not both
    if not (wagon_conf_file or train_conf) and (wagon_conf_file ^ train_conf):
        raise ValueError("Can only run from a nittygriddy project folder! "
                         "A project folder has either an `ConfigureWagon.C` or a "
                         "`MLTrainDefinition.cfg` file, but not both.")


def project_uses_ConfigureWagon():
    cur_dir = os.path.abspath(os.path.curdir)
    return os.path.isfile(os.path.join(cur_dir, "ConfigureWagon.C"))


def project_uses_train_cfg():
    cur_dir = os.path.abspath(os.path.curdir)
    return os.path.isfile(os.path.join(cur_dir, "MLTrainDefinition.cfg"))
