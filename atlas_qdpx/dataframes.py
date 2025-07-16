from collections import OrderedDict
from typing import Dict, List, Optional, Union

import pandas as pd

from .transformations import extract_code_groups, merge_citations


def make_code_group_dfs(annotations: Union[List[Dict], pd.DataFrame],
                        code_groups: Dict[str, List[str]],
                        misc_group: Optional[str] = "misc"
                        ) -> Dict[str, pd.DataFrame]:
    """From annotations passed in list or dataframe for, return a dictionary
    of dataframes where each dataframe contains only the rows that contain the
    coded annotations in the respective code group list. Codes not in any code
    group will be saved to a separate dataframe with "misc" as default group
    name. Optionally, a different name can be provided under the misc_group
    parameter.
    """
    if not isinstance(annotations, pd.DataFrame):
        groups = extract_code_groups(annotations, code_groups, misc_group)
        return {group: annotations_to_df(matches)
                for group, matches in groups.items()}

    else:
        return extract_code_group_dfs(annotations, code_groups, misc_group)


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
        dfs = make_code_group_dfs(input_df, code_groups)
        for group, df in dfs.items():
            group_df_path = f"{output_path}/{project_name}_{group}.csv"
            df.to_csv(group_df_path)
            print("  ", group_df_path)


def annotations_to_df(annotations: List[Dict]) -> pd.DataFrame:
    """Create a clean dataframe from a list of annotation dictionaries."""
    return (pd.DataFrame(annotations).sort_values(["doc_id", "start"]).
            reset_index(drop=True))


def make_review_df(df, all_codes, output="data"):
    """Create a review dataframe from a dataframe of coded annotations. Review
    dataframes are used to compare annotations between coders.
    If the dataframe is grouped (i.e. carries a "group_id" column signifying
    overlapping citations, all citations belonging to each group will be
    gathered in a single row. Text citations are stored as tuples with the
    citation text and the coder who made the citation, and for each code applied
    to the group, a list of coders is stored. These aggregate columns can be
    turned into plain text for easier manual review.

    Args:
        df (pd.DataFrame): Dataframe of coded annotations.
        all_codes (list): List of all codes used in the coding process.
        output (str): Output format. If data, the dataframe will be returned
        as is. If plain, the text citations and coder lists will be formatted
        as plain text.

    Returns:
        pd.DataFrame: Review dataframe
        """
    def ensure_list(cell):
        if not isinstance(cell, list):
            return [cell]
        return cell

    def order_codes(row):
        for code in all_codes:
            if row["code"] == code:
                row[code] = row["coder"]
            else:
                row[code] = []
        return row

    def sign_citation(row):
        row["citation"] = (row["citation"], row["coder"])
        return row

    def make_citation_dicts(tuple):
        return {"key": tuple[0],
                "coder": tuple[1]
                }

    def unpack_citations(list_):
        return [tuple(v.values()) for v in list_]

    def plain_citations(list_):
        list_ = [
            f'"{element[0]}" ## {" | ".join(element[1])}' for element in list_]
        list_ = "\n\n".join(list_)

        return list_

    # Prepare and transform Dataframe
    df["coder"] = df["coder"].apply(lambda x: ensure_list(x))
    df = df.apply(order_codes, axis=1)

    if "group" in df.columns:
        if output not in ["data", "plain"]:
            raise ValueError(
                f"Unsupported output: {output}. Must be 'data' or 'plain'.")

        df = df.apply(sign_citation, axis=1)
        df["citation"] = df["citation"].apply(lambda x: make_citation_dicts(x))

        # Make ordered aggregation dict
        agg_items = [
            ("citation", lambda x: merge_citations(x, merge_key=("key",))),
            ("start", min),
            ("end", max),
            ("start_atlas.ti", min),
            ("end_atlas.ti", max),
            ("file", lambda x: list(x)[0])
        ]
        for code in reversed(all_codes):
            agg_items.insert(
                1,
                (code, lambda x: sorted(list({e for l in x for e in l})))
            )
        agg_dict = OrderedDict(agg_items)

        # group and aggregate dataframe
        df = df.groupby(["doc_id", "group"]).agg(agg_dict)

        # post-process dataframe
        df["citation"] = df["citation"].apply(lambda x: unpack_citations(x))
        if output == "plain":
            df["citation"] = df["citation"].apply(plain_citations)
            for code in all_codes:
                df[code] = df[code].apply(lambda x: ", ".join(x))

    return df
