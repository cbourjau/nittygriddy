from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import shutil
from . import utils


def new(args):
    new_dir = os.path.join(os.path.abspath(os.path.curdir), args.name)
    try:
        os.mkdir(new_dir)
    except OSError:
        print("Cannot create output folder {}".format(new_dir))
        return
    # Copy default `configureTrain.C` to new folder
    template_dir = utils._internal_files_dir()
    shutil.copy(os.path.join(template_dir, "ConfigureTrain.C"), new_dir)
    print("Created new project directory {}".format(args.name))


def create_subparsers(subparsers):
    description = """Create a new project folder with a default `ConfigureTrain.C` file."""
    parser_new = subparsers.add_parser('new', description=description)
    parser_new.add_argument('name', help='The name of the new project; used for folder name')
    parser_new.set_defaults(op=new)
