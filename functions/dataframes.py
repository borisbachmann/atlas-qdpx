from typing import Dict, List, Optional
import pandas as pd

from bulk import parse_qdpx_directory

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
    input_df.to_csv(f"{output_path}/{project_name}_all.csv")
    if code_groups:
        dfs = extract_code_group_dfs(input_df, code_groups)
        for group, df in dfs.items():
            df.to_csv(f"{output_path}/{project_name}_{group}.csv")


def project_folder_to_dfs(input_path: str,
                          output_path: str,
                          project_name: str,
                          code_groups: Optional[Dict[str, List[str]]] = None
                          ) -> None:
    """From a folder containing QDPX files, extract all annotations in CSV
    format and save them to a specified output folder. If code_groups is not
    None, additional CSV files will be saved for each code group. The
    project_name parameter is used to name the output files.
    """
    all_annotations = parse_qdpx_directory(input_path, as_df=True)
    save_output_dfs(all_annotations, output_path, project_name, code_groups)
