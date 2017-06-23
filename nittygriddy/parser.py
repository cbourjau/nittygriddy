"""
Create the command line parser
"""

import argparse
from nittygriddy import run, merge, datasets, new, profile


def create_parser():
    """
    Creates the parser object

    By using a function, the parser is also easily available for unittests
    """
    class formatter_class(argparse.ArgumentDefaultsHelpFormatter,
                          argparse.RawTextHelpFormatter):
        pass

    parser = argparse.ArgumentParser(formatter_class=formatter_class)
    parser.add_argument(
        '-v', '--verbose', action='store_true', default=False)
    subparsers = parser.add_subparsers()
    run.create_subparsers(subparsers)
    merge.create_subparsers(subparsers)
    datasets.create_subparser(subparsers)
    new.create_subparsers(subparsers)
    profile.create_subparsers(subparsers)
    return parser
