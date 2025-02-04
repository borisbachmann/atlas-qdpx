import copy
from typing import List, Dict, Optional, Tuple, Union

def merge_citations(citations: List[Dict],
                    merge_key: Tuple[str] = ("start", "end", "code")
                    ) -> List[Dict]:
    """Merges matching citations. By default, the start, end, and code values
    are used to identify matching citations, but other keys can be specified
    to facilitate reusability. In the process of merging, the 'coder' values
    of the merged citations are combined into a list of unique values.

    Args:
        citations (list): List of citation dictionaries with 'start', 'end',
        'code', and 'coder' keys.
        merge_key (tuple): Tuple of keys that should be used to identify matching
        citations. (default: ("start", "end", "code"))

    Returns:
        list: List of merged citation dictionaries.
    """
    citations = copy.deepcopy(citations)
    citation_map = {}

    for citation in citations:
        # Make tuples as keys for dict
        key = tuple(citation[k] for k in merge_key)
        coder = citation['coder']
        if not isinstance(coder, list):
            coder = [coder]
        if key in citation_map:
            # Merge coders
            existing_citation = citation_map[key]
            existing_citation['coder'] += coder
        else:
            citation['coder'] = coder
            citation_map[key] = citation

        citation['coder'] = list(set(citation['coder']))

    merged_citations = list(citation_map.values())

    return merged_citations


def extract_code_groups(annotations: List[Dict],
                        code_groups: Dict[str, List[str]],
                        misc_group: Optional[str] = "misc"
                        ) -> Dict[str, List[Dict]]:
    """Extracts annotations based on code groups. Returns a dictionary with code
    group names as keys and lists of annotations in dictionary form as values.
    All annotations not in any code group are saved to a separate group with the
    name provided in the misc parameter.

    Args:
        annotations (list): List of annotation dictionaries.
        code_groups (dict): Dictionary with code group names as keys and lists of
        codes as values.
        misc (str): Name of the group for annotations not in any code group.
        (default: "misc")

    Returns:
        dict: Dictionary with code group names as keys and lists of annotation
        dictionaries as values.
    """
    results = {}
    for group, codes in code_groups.items():
        matches = [a for a in annotations if a["code"] in codes]
        results[group] = matches
    all_codes = [c for g in code_groups.values() for c in g]
    misc_codes = [a for a in annotations if a["code"] not in all_codes]
    if misc_codes:
        results[misc_group] = misc_codes
    return results


def group_overlaps(annotations: List[Dict],
                   output: str = "grouped"
                   ) -> Union[List[List[Dict]], List[Dict]]:
    """Groups overlapping citations.

    Args:
        annotations (list): List of citation dictionaries.
        output (str): Output format. Options are "grouped" and "numbered".
        (default: "grouped")

    Returns:
        list: Depending on output type, either a List of lists containing
        citation dictionaries per group ("grouped") or a flat list of citation
        dictionaries with additional "group" key ("numbered").
    """
    if output not in ["grouped", "numbered"]:
        raise ValueError(
            f"Unsupported output: {output}. Must be 'grouped' or 'numbered'.")

    annotations = sorted(annotations, key=lambda a: (a["doc_id"], a["start"]))

    groups = []
    current_group = []
    # current counters mark ends for iteration
    current_end = None
    current_doc_id = None

    for a in annotations:
        start, end, doc_id = a["start"], a["end"], a["doc_id"]

        # conditions to start new group: Begin of loop or new text id
        if not current_group or doc_id != current_doc_id:
            # if there's an existing group, save it first.
            if current_group:
                groups.append(current_group)
            # start a new group with the current span.
            current_group = [a]
            current_end = end
            current_doc_id = doc_id
        else:
            # if still in the same text, check for overlap.
            if start <= current_end:
                current_group.append(a)
                current_end = max(current_end, end)
            else:
                groups.append(current_group)
                current_group = [a]
                current_end = end

    # Append the final group if it exists.
    if current_group:
        groups.append(current_group)

    # manage output type
    if output == "numbered":
        for group_id, group in enumerate(groups):
            for a in group:
                a["group"] = group_id
        groups = [a for g in groups for a in g]

    return groups
