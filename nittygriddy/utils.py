import json
import os


def get_dataset(name):
    """
    Get the dictionary for dataset `name`
    Parameters
    ----------
    name : string
        Name of the dataset
    Returns
    -------
    dict :
        dataset dictionary
    Raises
    ------
    KeyError :
        If no matching set is found
    """
    with open(os.path.dirname(os.path.abspath(__file__)) + "/datasets.json", "read") as f:
        datasets = json.load(f)
    return datasets[name]
