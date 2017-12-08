from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from builtins import str

import json

from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter

from nittygriddy import utils


def _pprint_json(dics):
    json_str = json.dumps(dics, sort_keys=True, indent=4)
    print(highlight(str(json_str, 'UTF-8'),
                    JsonLexer(), TerminalFormatter()))


def datasets(args):
    if args.list:
        _pprint_json(utils.get_datasets())
    elif args.show:
        ds = utils.get_datasets().get(args.show, None)
        if not ds:
            raise ValueError("Dataset not found.")
        _pprint_json(ds)
    elif args.search:
        search_datasets_for_string(args.search)
    elif args.download:
        ds_name, volume = args.download
        try:
            volume = float(volume)
        except ValueError:
            raise ValueError("Volume has to be a valid number, not `{}`".format(volume))
        if not utils.get_datasets().get(ds_name, False):
            raise ValueError("Dataset `{}` not found.".format(ds_name))
        elif args.run_list:
            # is the given run list a subset of the full run list?
            user_run_list = [int(r.strip()) for r in args.run_list.split(",")]
            full_run_list = [int(r.strip()) for r in
                             utils.get_datasets().get(ds_name)['run_list'].split(",")]
            if not set(user_run_list).issubset(full_run_list):
                raise ValueError("Run {} list is not a subset of this periods run list ({})!"
                                 .format(user_run_list, full_run_list))
        utils.download_dataset(ds_name, volume, args.run_list)


def search_datasets_for_string(s):
    def flatten(dictionary):
        for key, value in dictionary.items():
            if isinstance(value, dict):
                # recurse
                for res in flatten(value):
                    yield res
            else:
                yield key, value
    datasets = utils.get_datasets()
    matches = []
    for dset_name, dset in datasets.items():
        for key, value in flatten(dset):
            if s in value:
                matches.append({dset_name: dset})
    _pprint_json(matches)


def create_subparser(subparsers):
    # Create dataset sub-parser
    parser_datasets = subparsers.add_parser('datasets')
    parser_datasets.add_argument(
        '-l', '--list',
        help="list all predifined datasets", default=False, action='store_true')
    parser_datasets.add_argument(
        '-s', '--search',
        help="Search for string in datasets and show matches", type=str)
    parser_datasets.add_argument(
        '--show',
        help="show only given dataset", type=str)
    parser_datasets.add_argument(
        '--download',
        nargs=2,
        metavar=('dataset', 'volume [GB]'),
        help="Download `volume [GB]` of specified dataset")
    parser_datasets.add_argument(
        '--run_list',
        help="Optional; use with --download; comma separeated string", type=str)

    parser_datasets.set_defaults(op=datasets)
