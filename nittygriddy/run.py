"""
Logic associated with the nitty run
"""
from datetime import datetime
from glob import glob
import os
import shutil
import subprocess

from nittygriddy import utils, settings

def _prepare_output_dir(args):
    """
    Prepare the output dir for the current job

    Returns
    str : Absolut path to the output directory
    """
    output_dir = os.path.join(os.path.abspath(os.path.curdir), datetime.now().strftime("%Y%m%d_%H%M"))
    if args.suffix:
        if "-" in args.suffix:
            raise ValueError('Hyphens ("-") are not allowed in the suffix')
        output_dir += args.suffix
    try:
        os.mkdir(output_dir)
    except OSError:
        print "Cannot create output folder {}".format(output_dir)
        return
    try:
        os.symlink(output_dir, "latest")
    except OSError as e:
        if os.path.islink("latest"):
            os.remove("latest")
            os.symlink(output_dir, "latest")
        else:
            raise e
    utils.copy_template_files_to(output_dir)

    if utils.project_uses_ConfigureWagon():
        shutil.copy(os.path.join(os.path.dirname(output_dir), "ConfigureWagon.C"), output_dir)
    if utils.project_uses_train_cfg():
        shutil.copy(os.path.join(os.path.dirname(output_dir), "MLTrainDefinition.cfg"), output_dir)
    if args.par_files:
        utils.prepare_par_files(args.par_files, output_dir)

    # create GetSetting.C in output dir (from template)
    utils.prepare_get_setting_c_file(output_dir, args)

    return output_dir


def run(args):
    utils.is_valid_project_dir()
    output_dir = _prepare_output_dir(args)

    # start the analysis
    os.chdir(output_dir)
    if args.runmode != "grid":
        # generate input file
        ds = utils.get_datasets()[args.dataset]
        # create list of local files
        with open(os.path.join(output_dir, "input_files.dat"), 'a') as input_files:
            search_string = os.path.join(settings["local_data_dir"],
                                         ds["datadir"].lstrip("/"),
                                         "*",
                                         ds["data_pattern"])
            search_string = os.path.expanduser(search_string)
            search_results = glob(search_string)
            # Filter the found files to match the given run list
            if args.run_list:
                run_list = [r.strip() for r in args.run_list.split(",")]
            else:
                run_list = [r.strip() for r in ds["run_list"].split(",")]
            filtered_results = []
            for path in search_results:
                if any([r for r in run_list if r in path]):
                    filtered_results.append(path)
            if len(filtered_results) == 0:
                raise ValueError("No local files found at {} matching run list".format(search_string))
            input_files.write('\n'.join(filtered_results) + '\n')
        # command to start the analysis
        cmd = ['root', '-l', '-q', 'run.C']
    else:
        cmd = ['root', '-l', '-q', '-b', '-x', 'run.C(\"full\")']
    procs = []
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        procs.append(p)
        for line in iter(p.stdout.readline, b''):
            print(line.rstrip())  # rstrip to remove \n; doesn't like carriage returns
    except KeyboardInterrupt, e:
        for proc in procs:
            print "Killing: ", proc
            proc.terminate()
        raise e


def create_subparsers(subparsers):
    """
    Create the "run" subparser
    """
    description_run = """Start analysis on target platform. Must be executed from a
    nittygriddy project folder (ie. next to the ConfigureWagon.C or a MLTrainDefinition.cfg files)"""
    parser_run = subparsers.add_parser('run', description=description_run)
    parser_run.add_argument('runmode', choices=('local', 'lite', 'grid'))
    parser_run.add_argument('dataset', type=str, help="Use this dataset")
    parser_run.add_argument('--suffix', type=str, help="Attach to the end of the folder name and files uploaded to the grid")
    parser_run.add_argument('--nworkers', type=str, help="Number of workers for proof lite", default="-1")
    parser_run.add_argument('--par_files', type=str, default="",
                            help="Patch aliphysics on the grid with these space separeated par or libXXX.so files. Build par_files before with cd $ALICE_PHYSICS/../build; make MODULE.par; make -j$MJ install")
    parser_run.add_argument('--run_list', type=str,
                            help="Overwrite default (comma seperated) run list for the given dataset")
    parser_run.add_argument('--ttl', type=str, help="Number of seconds this job should live", default="30000")
    parser_run.add_argument('--max_files_subjob', type=str, help="Maximum number of files per subjob", default="50")
    parser_run.add_argument('--wait_for_gdb', action='store_true', default=False,
                            help="Pause the execution to allow for connecting gdb to the process")
    parser_run.add_argument('--runs_per_master', type=str, default="1",
                            help="Number of runs to be processed by each master job. Set it to 0 to process\
                            the entire runlist with one masterjob.")
    parser_run.set_defaults(op=run)
