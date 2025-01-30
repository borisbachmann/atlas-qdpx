from typing import List, Dict, Tuple


def make_paragraphs(text: str) -> List[Dict]:
    """Function to create paragraphs with information about length and offset to
    match original paragraphs in atlas.ti documents.
    """
    paragraphs = text.split("\n")
    paragraphs = [
        {"id": idx + 1,
         "text": p,
         "length": len(p)
         } for idx, p in enumerate(paragraphs)]

    for idx, p in enumerate(paragraphs):
        if idx == 0:
            p["start"] = 0
        if idx > 0:
            last_p = paragraphs[idx - 1]
            p["start"] = last_p["start"] + last_p["length"] + 1
        p["end"] = p["start"] + p["length"]

    return paragraphs


def assign_paragraphs(annotation: Tuple, paragraphs: List[Dict]) -> Tuple:
    """Match an annotation in a document with the document paragraphs and return
    its start and end paragraph."""
    start_p, end_p = None, None
    for p in paragraphs:
        span_range = range(p["start"], p["end"] + 1)
        if annotation[0] in span_range:
            start_p = p["id"]
            break
    for p in paragraphs:
        span_range = range(p["start"], p["end"] + 1)
        if annotation[1] in span_range:
            end_p = p["id"]
            break
    return start_p, end_p
