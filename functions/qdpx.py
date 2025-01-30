# standard library
import pathlib
from collections import OrderedDict
from typing import Dict, List, Tuple, Union
import zipfile
import xml.etree.ElementTree as ET

# external libraries
import pandas as pd

# internal
from functions.constants import (CODEBOOK_QUERY, CODE_QUERY, DOCUMENT_QUERY,
                                 ANNOTATION_QUERY, CODEREF_QUERY)
from functions.dataframes import make_clean_df
from functions.paragraphs import make_paragraphs, assign_paragraphs
from functions.standardization import Standardizer
from functions.utils import list_files_by_type


def parse_qdpx(filepath: str,
               coder: str,
               standardizer: Standardizer = None
               ) -> List[Dict]:
    """From a string representing a path to a REFI-QDA export file from
    atlas.ti, extract all annotations in the project as a list of dictionaries.
    The dict contains one entry per code per citation (resulting in multiple
    entries for multiple-coded citations). Each entry contains information about
    the citation span, original text, its code and its place in the corpus
    (document id and file) as well as the coder (i.e. researcher).
    A standardizer class can be passed to the function to handle adjustments
    to individual annotations. The standardizer has to feature a `standardize`
    method that takes a list of annotations and a document as input and returns
    a list of standardized annotations, as well as a `preprocess` method that
    handles the necessary preprocessing on a document level and takes a list of
    documents as input. The standardizer can be used to e.g. adjust annotation
    spans.

    Args:
        filepath (str): Path to the REFI-QDA export file.
        coder (str): Name of the coder.
        standardizer (bool): custom Class of the standardization.Standardizer
            interface. If provided, the standardizer will be used to adjust
            returned annotation data. Default is None.

    Returns:
        List[Dict]: List of dictionaries with citation information.

    By default, anntoation dicts contain the following keys:
        doc_id:                 original id of the document in atlas.ti project
                                (starting at 1)
        citation:               original text of the citation
        code:                   code in the atlas.ti codebook
        start:                  start position as a string index of the
                                document's text
        end:                    end position as a string index of the
                                document's text
        start_atlas.ti:         original atlas.ti start position, referring to
                                the document's paragraphs (starting at 1)
        end_atlas.ti:           original atlas.ti end position, referring to the
                                document's paragraphs (starting at 1)
        file:                   name of the original plain text file in atlas.ti
                                project
        coder:                  name or abbreviation of coding researcher as
                                specified by the `coder` parameter

    If a standardizer is used, the annotation dicts may contain additional
    keys as specified by the standardizer's `custom_keys` attribute.
    """

    def add_paragraphs(documents):
        """Add paragraph information to each document. Paragraphs are modeled
        as implemented by Atlas.ti."""
        for document in documents:
            document["paragraphs"] = make_paragraphs(document["text"])

    def sort_and_standardize(documents):
        """Sort annotations by start position and standardize them if a
        standardizer is provided."""
        for document in documents:
            if len(document["annotations"]) > 0:
                document["annotations"] = sorted(document["annotations"],
                                                 key=lambda x: x[0])
                if standardizer is not None:
                    document["annotations"] = (
                        standardizer.standardize(document["annotations"],
                                                 document)
                        )

    def extract_annotations(documents,
                            custom_keys=None):
        """Extract annotations from documents and return them as a list of
        dictionaries."""
        all_annotations = []
        for idx, document in enumerate(documents):
            for a in document["annotations"]:
                start_p, end_p = assign_paragraphs(a, document["paragraphs"])
                for tag in a[2]:
                    annotation_items = [
                        ("doc_id", idx),
                        ("citation", document["text"][a[0]:a[1]]),
                        ("code", tag),
                        ("start", a[0]),
                        ("end", a[1]),
                        ("start_atlas.ti", start_p),
                        ("end_atlas.ti", end_p),
                        ("file", document["name"]),
                        ("coder", coder)
                    ]
                    if custom_keys:
                        for key, position in custom_keys.items():
                            annotation_items.insert(-3,
                                                    (key, a[position]))
                    annotation_dict = OrderedDict(annotation_items)
                    all_annotations.append(annotation_dict)

        return all_annotations

    documents, codes = read_qdpx(filepath)

    if standardizer is not None:
        print("Standardizer found. Preprocessing documents...")
        if not isinstance(standardizer, Standardizer):
            raise TypeError("The provided standardizer does not adhere to "
                            "the Standardizer protocol. Please provide a "
                            "standardizer object with a `standardize` and "
                            "`preprocess` method as well as a `custom_keys` "
                            "attribute.")
        documents = standardizer.preprocess(documents)
        custom_keys = standardizer.custom_keys
    else:
        custom_keys = None

    add_paragraphs(documents)
    sort_and_standardize(documents)
    all_annotations = extract_annotations(documents, custom_keys)

    return all_annotations


def read_qdpx(file: str) -> Tuple[List[Dict], Dict]:
    """From a string representing a path to a REFI-QDA export file, extract all
    documents with their annotations as well as all codes with their internal ID
    representations. The function has been adopted from
    https://gist.github.com/Whadup/a795fac02f4405ca1b5a278799ce6125.
    Changes were made to handle the specific structure of exports from Atlas.ti
    (including multiple tags per annotation and specific naming conventions for
    internal files in the QDPX archive. Additionally, some refactoring has been
    done.
    """

    def extract_tags(root):
        """Query for tags/codes and extract Dict to resolve tag IDs."""
        xpath_query = CODEBOOK_QUERY
        codebook = root.findall(xpath_query)[0]
        tags = {}
        entries = list(codebook.iter(tag=CODE_QUERY))
        parent_map = {c: p for p in entries for c in p}
        for entry in entries:
            parse_entry(entry, parent_map, tags)

        return tags

    def extract_docs(root):
        """Query for docs and extract doc data."""
        docs = []
        xpath_query = DOCUMENT_QUERY
        result_list = root.findall(xpath_query)
        for doc in result_list:
            dict_ = dict(parse_doc(doc))
            docs.append(dict_)

        return docs

    def parse_entry(entry, parent_map, tags):
        """Parse a single codebook entry and add it to the tags dict."""
        guid = entry.attrib["guid"]
        name = entry.attrib["name"]
        tags[guid] = name.replace(" ", "").replace("/", "-")
        parent = parent_map.get(entry, None)

        if parent and parent.attrib.get("guid", None) in tags:
            tags[guid] = f"{tags[parent.attrib.get('guid', None)]}/{tags[guid]}"

    def parse_doc(doc):
        """Parse a single document and return its text, filename and
        annotations.
        """
        xpath_query = ANNOTATION_QUERY
        annotations = []

        for annotation in doc.findall(xpath_query):
            result = parse_annotation(annotation)
            if result is not None:
                annotations.append(result)

        text = archive.open(make_source_path(doc), 'r').read().decode("utf-8")
        name = doc.attrib['name'].replace("/", "_")

        return {"text": text,
                "name": name,
                "annotations": annotations
                }

    def make_source_path(doc):
        return f"sources/{doc.attrib['plainTextPath'].replace('internal://', '')}"

    def parse_annotation(annotation):
        """Parse a single annotation and return its span and associated codes."""
        start = int(annotation.attrib["startPosition"])
        end = int(annotation.attrib["endPosition"])
        references = annotation.findall(CODEREF_QUERY)

        if not len(references):
            return None
        codes = [c.attrib["targetGUID"] for c in references]
        codes = [tags[c] for c in codes]

        return start, end, codes

    def get_qde_filename(file):
        """Get the internal atlas.ti project filename based upon the QDPX archive
        filename.
        """
        return pathlib.Path(file).with_suffix('.qde').name

    with zipfile.ZipFile(file) as archive:
        project_filename = get_qde_filename(file)
        tree = ET.parse(archive.open(project_filename))
        root = tree.getroot()
        tags = extract_tags(root)
        docs = extract_docs(root)

        return docs, tags


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
        return make_clean_df(results)
    else:
        return results
