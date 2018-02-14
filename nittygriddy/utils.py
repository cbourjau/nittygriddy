from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from builtins import input

from glob import glob
import yaml
import logging
import os
import re
import shutil
import subprocess
import sys
try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

import zipfile

import ROOT
from rootpy.io import root_open

from nittygriddy import settings
from nittygriddy.alienTokenError import AlienTokenError

GRID_CONNECTION = None


def validate_dataset(ds):
    """
    Check if all entries in this dataset have all the required fields
    Parameters
    ----------
    ds : dict
        Dictionary of datasets
    Raises
    ------
    ValueError: If a field is missing
    """
    req_fields = [
        'data_pattern', 'datadir', 'datatype', 'is_mc', 'notes',
        'run_list', 'run_number_prefix', 'system']
    # ds are all datasets; entry is _one_ dataset!
    for name, entry in list(ds.items()):
        for field in req_fields:
            if field not in list(entry.keys()):
                raise ValueError("Field `{}` missing in `{}` dataset definition".format(field, name))
        # Make sure that the run list is a string; if its only one run it might be interpreted as int
        if isinstance(entry['run_list'], int):
            entry['run_list'] = str(entry['run_list'])


def get_datasets():
    """
    Get the dictionary describing the datasets
    Returns
    -------
    dict :
        dataset dictionary
    """
    default_ds_name = os.path.join(_internal_files_dir(), "datasets.yml")
    user_ds_name = os.path.expanduser("~/nitty_datasets.yml")
    with open(default_ds_name, "read") as f:
        default_ds = yaml.safe_load(f)
        validate_dataset(default_ds)
    # open the user's definitions; create the file if it does not exist
    try:
        with open(user_ds_name, "read") as f:
            user_ds = yaml.safe_load(f)
            if user_ds:
                validate_dataset(user_ds)
            else:
                user_ds = {}
    except IOError:
        # raise ValueError("No user datasets found!")
        # File did not exist
        user_ds = {}
    # check if there is an intersection between the user defined and the default dataset
    intersect = set(default_ds.keys()).intersection(list(user_ds.keys()))
    if intersect:
        raise ValueError("The following user datasets are also in the default definitions. "
                         "Please rename your ones in `~/nitty_datasets.yml`:\n {}"
                         .format('/n'.join(intersect)))
    full_ds = dict(default_ds)
    full_ds.update(user_ds)
    return full_ds


def copy_template_files_to(dest):
    template_dir = _internal_files_dir()
    shutil.copy(os.path.join(template_dir, "run.C"), dest)


def get_template_GetSetting():
    template_dir = _internal_files_dir()
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
    archive_names = ["root_archive.zip"]
    if "AliAOD.root" in data_pattern:
        # Sometimes, just sometimes, it seemed like a good idea to
        # call the archives differently...
        # we put the aod_archive.zip in the front of the list. This way its tried first
        archive_names.insert(0, "aod_archive.zip")

    for archive_name in archive_names:
        for run in runs:
            # Create a search string for this run; make sure its a string not u""
            search_string = str(os.path.join(datadir,
                                             run_number_prefix + str(run),
                                             os.path.dirname(data_pattern)))
            # Most archives are called `root_archive.zip` but some are called aod_archive.root
            # Maybe there are more species out there waiting to be found by a keen explorer!
            finds = ROOT.TAliEnFind(search_string, archive_name)
            # Ok, so. ROOT thinks linked lists are fucking
            # awesome. Unfortunately, their access is is n^2, so we
            # choke on a call to finds.GetCollection() if we have a
            # few thousand urls, because deep inside the shit code of
            # AliEn, we iterate through the shit that is a TList. I
            # just want to get a few fucking files! Its 2017! Bottom
            # line, we avoid some of this crap by fishing out the urls
            # manually from the TGridResult...
            gr = finds.GetGridResult()
            urls.extend([str(el.GetValue('turl')).replace("alien://", "") for el in gr])
        # Did we find any files? If not, lets try it with the next archive name
        if len(urls) != 0:
            break
    logging.debug("Number of files found matching search string {}".format(len(urls)))
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
            print("Error unzipping {}. File was deleted".format(local_dest))
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
                print("Some files were present and were not redownloaded")
        except RuntimeError as e:
            # Error in download; probably with MD5 sum
            print(e.message)
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
    html = urlopen('http://alimonitor.cern.ch/packages/').read()
    tag_pattern = r'vAN-\d{8}-\d+'
    return sorted(re.findall(tag_pattern, html)).pop()

def check_aliphysics_version(version):
    """
    Check wether a version od aliphysics has been deployed.
    If it is, the version name is returned. Otherwhise an error is raised

    Returns
    -------
    string: version

    Raises
    ------
    if the version is not deployed
    """
    html = urlopen('http://alimonitor.cern.ch/packages/').read()
    if html.find(version) < 0:
        raise ValueError("AliPhysics version {} is not deployed!".format(version))
    return version

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
    choice = input("%s (%s) " % (message, choices))
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
                   aliphysics_version= get_latest_aliphysics() if args.runmode == "grid" and args.aliphysics_version==""
                     else check_aliphysics_version(args.aliphysics_version) if args.runmode == "grid" and args.aliphysics_version!=""
                     else "",
                   par_files=args.par_files if args.par_files else "",
                   ttl=args.ttl,
                   max_files_subjob=args.max_files_subjob,
                   use_train_conf="true" if project_uses_train_cfg() else "false",
                   runs_per_master=args.runs_per_master,
                   max_n_events=args.max_n_events)
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
    train_conf_file = os.path.isfile(os.path.join(cur_dir, "ConfigureTrain.C"))
    train_conf = os.path.isfile(os.path.join(cur_dir, "MLTrainDefinition.cfg"))

    # Project dir has either an ConfigureTrain.C or a
    # MLTrainDefinition.cfg file, but not both
    if not (train_conf_file or train_conf) and (train_conf_file ^ train_conf):
        raise ValueError("Can only run from a nittygriddy project folder! "
                         "A project folder has either an `ConfigureTrain.C` or a "
                         "`MLTrainDefinition.cfg` file, but not both.")


def project_uses_ConfigureTrain():
    cur_dir = os.path.abspath(os.path.curdir)
    # is the current project using the old ConfigureWagon.C file?
    if os.path.isfile(os.path.join(cur_dir, "ConfigureWagon.C")):
        raise RuntimeError("Please migrate to using `ConfigureTrain.C`")
    return os.path.isfile(os.path.join(cur_dir, "ConfigureTrain.C"))


def project_uses_train_cfg():
    cur_dir = os.path.abspath(os.path.curdir)
    return os.path.isfile(os.path.join(cur_dir, "MLTrainDefinition.cfg"))


def load_alice_libs():
    """
    Load some default ALICE libraries. Basically, this makes aliroot available through pyroot
    """
    libs = ["$ALIROOT/lib/libSTAT.so", "$ALIROOT/lib/libSTEERBase.so"]
    includes = ["$ALICE_ROOT/include", "$ALICE_PHYSICS/include"]
    for lib in libs:
        if ROOT.gSystem.Load(lib) < 0:
            raise ValueError("Error loading {}".format(lib))
    for inc in includes:
        # This function is void, so we have to check it ourselfs
        if not os.path.exists(os.path.expandvars(inc)):
            raise ValueError("Unable to add {} to include path".format(inc))
        ROOT.gSystem.AddIncludePath("-I" + inc)


def _internal_files_dir():
    """
    Return the absolute path to directory with nitty's internal files
    """
    # The dir with the python files
    src_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(src_dir, 'non-python-files')
