from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tempfile
import os
from os import path
import subprocess
from . import utils


def profile(args):
    """
    Run the poor-mans-profiler and open a browser to see the produced svg
    """
    pid = str(args.pid)
    tmpdir = tempfile.gettempdir()
    # make sure we don't have old files floating around
    gdb_file = path.join(tmpdir, pid + ".gdb")
    svg_file = path.join(tmpdir, pid + ".svg")
    for f in [gdb_file, svg_file]:
        try:
            os.remove(f)
        except:
            pass
    nitty_root = utils._internal_files_dir()
    poor_mans = path.join(nitty_root, "poormans.sh")
    print("See the profiling result at {}".format(svg_file))
    p = subprocess.Popen(['bash', poor_mans, str(args.nsamples), pid, gdb_file, svg_file, nitty_root])
    try:
        p.wait()
    except KeyboardInterrupt:
        p.kill()


def create_subparsers(subparsers):
    description = """Profile a running nitty-process. The profiler produces a svg file which can be view in the browsers. It updates every few seconds, so be patient. This feature depends on gdb. If you get "ERROR: No stack counts found" messages, you might not have set the proper permissions for gdb. Google for the file /etc/sysctl.d/10-ptrace.conf"""
    parser_new = subparsers.add_parser('profile', description=description)
    parser_new.add_argument('pid', help='PID of the process you want to profile')
    parser_new.add_argument('--nsamples', help='Number of samples to be taken', default=50)
    parser_new.set_defaults(op=profile)
