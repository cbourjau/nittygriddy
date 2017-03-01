import json

from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter

from nittygriddy import utils


def _pprint_json(dics):
    json_str = json.dumps(dics, sort_keys=True, indent=4)
    print highlight(unicode(json_str, 'UTF-8'),
                    JsonLexer(), TerminalFormatter())


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
        if not args.volume:
            raise ValueError("No download volume specified")
        elif not utils.get_datasets().get(args.download, False):
            raise ValueError("Dataset not found.")
        utils.download_dataset(args.download, args.volume)


def search_datasets_for_string(s):
    def flatten(dictionary):
        for key, value in dictionary.iteritems():
            if isinstance(value, dict):
                # recurse
                for res in flatten(value):
                    yield res
            else:
                yield key, value
    datasets = utils.get_datasets()
    matches = []
    for dset_name, dset in datasets.iteritems():
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
        '-d', '--download',
        help="Download subset of specified dataset (see --volume)", type=str)
    parser_datasets.add_argument(
        '--volume',
        help="Use with --download; Download this many GB", type=float)
    parser_datasets.set_defaults(op=datasets)
