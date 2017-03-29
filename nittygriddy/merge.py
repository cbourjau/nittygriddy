import os
from pprint import pprint
import ctypes

import subprocess

import ROOT

from nittygriddy import utils


def merge(args):
    # check if we are in a output dirname
    if not ((os.path.isfile("./ConfigureWagon.C") or
             os.path.isfile("./MLTrainDefinition.cfg")) and
            os.path.isfile("./GetSetting.C") and
            os.path.isfile("./run.C")):
        raise ValueError("This command needs to be run from an output directory")

    if not utils.check_alien_token():
        print "No valid alien token present. Run `alien-token-init` before nittygriddy"
        quit()

    ROOT.gROOT.LoadMacro(r'GetSetting.C')
    if ctypes.c_char_p(ROOT.gROOT.ProcessLine(r'GetSetting("runmode").c_str()')).value != "grid":
        raise ValueError("The data in this folder was not run on the grid!")

    # root does not like it if the stdout is piped and it uses some shell functionality
    # thus, using call on the whole string and shell True
    if args.mergemode == 'online':
        cmd = r'root -b -l -q -x "run.C(\"merge_online\")"'
        subprocess.check_call(cmd, shell=True)
    elif args.mergemode == 'offline':
        cmd = r'root -b -l -q -x "run.C(\"merge_offline\")"'
        subprocess.check_call(cmd, shell=True)

    if args.mergemode == 'download':
        workdir = os.path.dirname(os.path.abspath("./run.C")).split("/")[-1]
        alien_workdir = os.path.join(utils.find_user_grid_dir(), workdir)
        files = utils.find_latest_merge_results(alien_workdir)
        print "The following files will be downloaded:"
        pprint(files)
        for alien_path in files:
            local_path = alien_path.split(workdir)[-1].lstrip("/")
            try:
                utils.download_file(alien_path, local_path)
            except ValueError:
                print "{} exists and is not redownloaded.".format(local_path)
            except OSError, e:
                # If there was an error in the download, just print, but keep going
                print e.message

    if args.mergemode == 'clean':
        workdir = os.path.dirname(os.path.abspath("./run.C")).split("/")[-1]
        alien_workdir = os.path.join(utils.find_user_grid_dir(), workdir)
        files = utils.find_sources_of_merged_files(utils.find_latest_merge_results(alien_workdir))
        folders = [os.path.split(f)[0] for f in files]
        if not folders:
            print "No files to be cleaned up"
            return
        print "The following folders will be __DELETED__:"
        pprint(folders)
        shall_delete = utils.yn_choice("Do you really want to delete these Folders? This may take a while")
        if shall_delete:
            # its not possible to pass all arguments at once (too many)
            # Hence, pass 10 at a time
            for slice_start in range(len(folders))[::10]:
                cmd = ['alien_rmdir'] + folders[slice_start:(slice_start + 10)]
                # alien_rmdir always seems to return a non-zero exit code... Yeah!
                subprocess.call(cmd)
        # see if the deletion was successful:
        left_files = utils.find_sources_of_merged_files(utils.find_latest_merge_results(alien_workdir))
        if left_files:
            print "The following files could not be deleted:"
            pprint(left_files)

    if args.mergemode == 'unmerge':
        workdir = os.path.dirname(os.path.abspath("./run.C")).split("/")[-1]
        alien_workdir = os.path.join(utils.find_user_grid_dir(), workdir)
        subprocess.call(['alien_rm', os.path.join(alien_workdir, 'output/*/Stage_*.xml')])
        subprocess.call(['alien_rm', os.path.join(alien_workdir, 'output/*/AnalysisResults.root')])
        subprocess.call(['alien_rm', os.path.join(alien_workdir, 'output/*/root_archive.zip')])
        subprocess.call(['alien_rmdir', os.path.join(alien_workdir, 'output/*/Stage_*')])


def create_subparsers(subparsers):
    # Create merge sub-parser
    description_merge = """Merge related tasks connected to a previously run grid analysis. Must be
    executed from output folder of that analysis."""
    parser_merge = subparsers.add_parser('merge', description=description_merge)
    parser_merge.add_argument('mergemode',
                              choices=('online', 'offline', 'download', 'clean', 'unmerge'),
                              help=("Merge files online, offline or download the latest merge results. "
                                    "Use `clean` to delete previous merge stages. Use this with care! "
                                    "`unmerge` deletes all merge stages. Don't use this in combination with `clean`."))
    parser_merge.set_defaults(op=merge)
