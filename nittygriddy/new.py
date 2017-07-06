import os
import shutil


def new(args):
    new_dir = os.path.join(os.path.abspath(os.path.curdir), args.name)
    try:
        os.mkdir(new_dir)
    except OSError:
        print "Cannot create output folder {}".format(new_dir)
        return
    # Copy default `configureWagon.C` to new folder
    template_dir = os.path.dirname(os.path.abspath(__file__))
    shutil.copy(os.path.join(template_dir, "ConfigureWagon.C"), new_dir)
    print "Created new project directory {}".format(args.name)


def create_subparsers(subparsers):
    description = """Create a new project folder with a default `ConfigureWagon.C` file."""
    parser_new = subparsers.add_parser('new', description=description)
    parser_new.add_argument('name', help='The name of the new project; used for folder name')
    parser_new.set_defaults(op=new)
