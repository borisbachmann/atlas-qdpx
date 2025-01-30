import pathlib
from typing import Union, List, Dict

import pandas as pd
import spacy

from functions.qdpx import parse_qdpx
from functions.utils import list_files_by_type


def parse_qdpx_directory(input_path: str,
                         as_df: bool,
                         standardizer=None
                         ) -> Union[List[Dict], pd.DataFrame]:
    """From a path to a folder containing QDPX files, generate a single list of
    annotations for all documents in each project. Project file names have to
    include a `_somename` suffix for individual coders (e.g.
    `atlas-ti-project_JRoe.qdpx`). The `coder` value is automatically generated
    by extracting this suffix.

    If as_df is set to `True` a single sorted pandas DataFrame will be returned
    instead of a list of dicts.

    Standardization parameters (`standardize`, `spacy_nlp` and `cutoff`) can
    be passed as for single projects.
    """
    print("Reading Datatables from QDPX files...")
    projects = list_files_by_type(input_path, "qdpx")
    paths = [f"{input_path}/{project}" for project in projects]
    for path in paths:
        print("  ", path)
    coders = [pathlib.Path(file).with_suffix("").name.split("_")[-1] for file
              in projects]

    project_annotations = []

    for path, coder in zip(paths, coders):
        print(f"Parsing annotations by {coder}")
        project_annotations.append(parse_qdpx(path, coder, standardizer))

    results = [dict_ for list_ in project_annotations for dict_ in list_]

    if as_df:
        return (pd.DataFrame(results).sort_values(["doc_id", "start"]).
                reset_index(drop=True))
    else:
        return results
