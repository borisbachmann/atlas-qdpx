# standard library
import pathlib
from typing import Dict, List, Tuple
import zipfile
import xml.etree.ElementTree as ET

# external packages
import spacy
from tqdm.auto import tqdm

from functions.constants import (CODEBOOK_QUERY, CODE_QUERY, DOCUMENT_QUERY,
                                 ANNOTATION_QUERY, CODEREF_QUERY)


def parse_qdpx(filepath: str,
               coder: str,
               standardize: bool = False,
               spacy_nlp: spacy.language.Language = None,
               cutoff: bool = False) -> List[Dict]:
    """From a string representing a path to a REFI-QDA export file from
    atlas.ti, extract all annotations in the project as a list of dictionaries.
    The dict contains one entry per code per citation (resulting in multiple
    entries for multiple-coded citations). Each entry contains information about
    the citation span, original text, its code and its place in the corpus
    (document id and file) as well as the coder (i.e. researcher). If
    `standardize` is set to true, the above standardization function is used to
    generate a prototype standardized citation based upon spaCy. In this case,
    a spaCy nlp object must be provided under the `spacy_nlp` parameter. The
    `cutoff` parameter can be passed to the internal standardization function
    to try to cope with leading headers sometimes merged into sentences by
    spaCy (prototype).

    Args:
        filepath (str): Path to the REFI-QDA export file.
        coder (str): Name of the coder.
        standardize (bool): Whether to standardize the citation spans.
        spacy_nlp (spacy.language.Language): A spaCy nlp object. Must be
            provided if standardize is set to True.
        cutoff (bool): Whether to cut off leading headers in standardized
            citations (prototype).

    Returns:
        List[Dict]: List of dictionaries with citation information.
    """

    def add_spacy_docs(documents):
        for document in tqdm(documents):
            text = document["text"]
            if len(document["annotations"]) > 0:
                document["doc"] = spacy_nlp(text)
            else:
                document["doc"] = None
            # paragraphs = text.split("\n")

    def sort_and_standardize(documents):
        for document in documents:
            if len(document["annotations"]) > 0:
                document["annotations"] = sorted(document["annotations"],
                                                 key=lambda x: x[0])
                if standardize:
                    document["annotations"] = [
                        standardize_citation(a, document["doc"], cutoff=cutoff)
                        for a in document["annotations"]]
                else:
                    document["annotations"] = [
                        (a[0], a[1], a[2], None, None, None)
                        for a in document["annotations"]]

    def extract_annotations(documents):
        all_annotations = []
        for idx, document in enumerate(documents):
            for a in document["annotations"]:
                for tag in a[2]:
                    _dict = {
                        "doc_id": idx,
                        "file": document["name"],
                        "start": a[0],
                        "end": a[1],
                        "citation_original": document["text"][a[0]:a[1]],
                        "citation_standardized": a[5],
                        "code": tag,
                        "coder": coder
                    }
                    all_annotations.append(_dict)

        return all_annotations

    documents, codes = read_qdpx(filepath)

    # prepare spacy docs for each annotated atlas.ti document
    # implemented as separate loop to show progress bar only in case of
    # standardization
    if standardize:
        if spacy_nlp == None:
            raise TypeError("A spacy nlp object must be provided for text "
                            "standardization.")
        add_spacy_docs(documents)

    sort_and_standardize(documents)
    all_annotations = extract_annotations(documents)

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


def standardize_citation(annotation: Tuple,
                         doc: spacy.tokens.Doc,
                         cutoff: bool = False) -> Tuple:
    """For an annotation based upon a string span, add a standardized span based
    upon full spaCy sentences. Adds sentence ids for first and last sentence as
    well as plain text.
    """

    def find_first_sentence(start, sents):
        """Find the first sentence containing the start position."""
        for idx, sent in enumerate(sents):
            # correcte sentence end for some cases where trainling punctuation
            # leads to sentence overlaps in spaCy
            sent_end_char = sent.end_char
            if sent.text.endswith("\n"):
                sent_end_char -= 1
            if start >= sent.start_char and sent_end_char >= start:
                return idx + 1, sent.start_char
        return None, None

    def find_last_sentence(end, sents):
        """Find the last sentence containing the end position."""
        for idx, sent in enumerate(sents):
            sent_end_char = sent.end_char
            if sent.text.endswith("\n"):
                sent_end_char -= 1
            if end >= sent.start_char and sent_end_char >= end:
                return idx, sents[idx].end_char
        return None, None

    start, end, tag = annotation[0], annotation[1], annotation[2]
    sents = list(doc.sents)

    start_sent, start_char = find_first_sentence(start, sents)
    end_sent, end_char = find_last_sentence(end, sents)

    text = strip_extracted_text(doc.text[start_char:end_char], cutoff=cutoff)

    return start, end, tag, start_sent, end_sent, text

def strip_extracted_text(text: str, cutoff: bool = False) -> str:
    """Strip extracted text from surplus line breaks and possible leading headers.
    """
    text = text.strip()
    if cutoff:
        parts = text.split("\n")
        if len(parts) > 1:
            return parts[1]
        else:
            return parts[0]
    else:
        return text
