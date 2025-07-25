from typing import Optional, Dict, List

from . import parse_qdpx, parse_qdpx_dir, save_output_dfs, extract_files
from .dataframes import annotations_to_df
from .standardizer import Standardizer

def project_to_csv(input_path: str,
                   output_path: str,
                   project_name: str,
                   coder: str,
                   project_filename: Optional[str] = None,
                   code_groups: Optional[Dict[str, List[str]]] = None,
                   standardizer: Optional[Standardizer] = None
                   ) -> None:
    """From a QDPX file, extract all annotations in CSV format and save them to
    a specified output folder. If code_groups is not None, additional CSV files
    will be saved for each code group. The project_name parameter is used to
    name the output files.

    A ``standardizer`` instance can be passed to standardize the text data."""
    annotations = parse_qdpx(input_path, coder=coder,
                                 project_name=project_filename,
                                 standardizer=standardizer)
    clean_df = annotations_to_df(annotations)
    save_output_dfs(clean_df, output_path, project_name, code_groups)


def project_to_files(input_path: str,
                     output_path: str,
                     project_filename: str,
                     ) -> None:
    """From a QDPX file, extract all files in plain text format and save them
    to a specified output folder.

    A ``standardizer`` instance can be passed to standardize the text data."""
    files = extract_files(input_path, project_name=project_filename)
    print(f"Saving {len(files)} text files to: {output_path}")
    for file in files:
        with open(f"{output_path}/{file['name']}.txt", "w") as f:
            f.write(file["text"])


def folder_to_csv(input_path: str,
                  output_path: str,
                  project_name: str,
                  code_groups: Optional[Dict[str, List[str]]] = None,
                  standardizer=None
                  ) -> None:
    """Extract annotations from all QDPX files in a folder and save them as
    CSV files in the given output directory. If ``code_groups`` are provided,
    additional CSV files are created for each group.
    A ``standardizer`` instance can be supplied to adjust the annotation data.
    """
    annotations = parse_qdpx_dir(input_path, as_df=True,
                                     standardizer=standardizer)
    save_output_dfs(annotations, output_path, project_name, code_groups)
