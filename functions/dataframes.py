from typing import Dict, List, Optional

import pandas as pd

from functions.qdpx import parse_qdpx_directory


def extract_code_group_dfs(input_df: pd.DataFrame,
                           code_groups: Dict[str, List[str]],
                           misc_group: Optional[str] = "misc"
                           ) -> Dict[str, pd.DataFrame]:
    """From an input dataframe, and a dictionary of code groups, return a
    dictionary of dataframes where each dataframe contains only the rows that
    contain the codes in the respective code group list. Codes not in any code
    group will be saved to a separate dataframe with "misc" as default group
    name. Optionally, a different name can be provided under the misc_group
    parameter.
    """
    all_dfs = {}
    for group, codes in code_groups.items():
        df = create_code_group_df(input_df, codes)
        all_dfs[group] = df

    misc_df = input_df[~input_df["code"].isin([code for codes
                                               in code_groups.values()
                                               for code in codes])]
    if len(misc_df) > 0:
        all_dfs[misc_group] = misc_df

    return all_dfs


def create_code_group_df(input_df: pd.DataFrame,
                         code_group: List[str]
                         ) -> pd.DataFrame:
    """From an input dataframe, return a new dataframe with only the rows that
    contain the codes in the code_group list.
    """
    return input_df[input_df["code"].isin(code_group)]


def save_output_dfs(input_df: pd.DataFrame,
                    output_path: str,
                    project_name: str,
                    code_groups: Optional[Dict[str, List[str]]] = None
                    ) -> None:
    """Save input dataframe to csv files. If code_groups is not None, an
    additional df will be saved for each code group. The file name will be
    code group will be saved to a separate file.
    """
    print("Saving Dataframes to...")
    input_df_path = f"{output_path}/{project_name}_all.csv"
    input_df.to_csv(input_df_path)
    print("  ", input_df_path)
    if code_groups:
        dfs = extract_code_group_dfs(input_df, code_groups)
        for group, df in dfs.items():
            group_df_path = f"{output_path}/{project_name}_{group}.csv"
            df.to_csv(group_df_path)
            print("  ", group_df_path)


def project_folder_to_dfs(input_path: str,
                          output_path: str,
                          project_name: str,
                          code_groups: Optional[Dict[str, List[str]]] = None,
                          standardizer=None
                          ) -> None:
    """From a folder containing QDPX files, extract all annotations in CSV
    format and save them to a specified output folder. If code_groups is not
    None, additional CSV files will be saved for each code group. The
    project_name parameter is used to name the output files.

    Standardization parameters (`standardize`, `spacy_nlp` and `cutoff`) can
    be passed as for single projects.
    """
    all_annotations = parse_qdpx_directory(input_path, as_df=True,
                                           standardizer=standardizer)
    save_output_dfs(all_annotations, output_path, project_name, code_groups)


def make_clean_df(annotations: List[Dict]) -> pd.DataFrame:
    """Create a clean dataframe from a list of annotation dictionaries."""
    return (pd.DataFrame(annotations).sort_values(["doc_id", "start"]).
            reset_index(drop=True))
