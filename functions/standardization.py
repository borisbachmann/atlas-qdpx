"""
Standardization of annotation data is implemented by passing a standardizer
object to the parsing functions. Standardizers take annotation and document
data and adjust annotations to a standardized format, which may change existing
and add new attributes. The Standardizer class defines the interface for
standardizers, which require a `preprocess` and `standardize` method, as well
as a `custom_keys` attribute to handle custom annotation keys created by the
standardizer. Standardizers can be used to e.g. enforce coding standards such
as specified coding units (Mayring) or change the name of codes.
"""

# File contains example (prototype) standardizer aiming to adjust annotation
# spans to full sentences (i.e.: enforce coding unit (Mayring) to be a group
# of full sentences) as well as a protocoll to define the interface for such
# standardizer objects.

from typing import Tuple, Dict, List, Optional, Protocol, runtime_checkable

import spacy
from tqdm.auto import tqdm

@runtime_checkable
class Standardizer(Protocol):
    """Protocoll to define the interface for standardizers. Standardizers
    should feature a `preprocess` and `standardize` method, the first applying
    necessary preprocessing on a doc level, the second handling annotations of
    individual documents.
    Standardizers should also feature an optional `custom_keys` parameter to
    handle custom annotation keys created by the standardizer. Custom keys
    are passed as a dict of keys and corresponding indices referring to
    annotation tuples."""
    custom_keys: Optional[Dict[str, int]]

    def preprocess(self, documents: List[Dict]) -> List[Dict]:
        """Method to apply required preprocessing on a document level by
        changing values or adding new key-value pairs to the individual
        document dicts. Should return a list of processed documents."""
        ...

    def standardize(self, annotations: List[Tuple], document: Dict
                    ) -> List[Tuple]:
        """Method to turn annotations into a standardized format by changing
        values or adding new values to individual annotation tuples. Should
        return a list of standardized annotation tuples."""
        ...

class SpacyStandardizer:
    """Prototype example Standardizer for spaCy documents. Adjusts annotation
    spans to full spaCy sentences. Initiated with a spaCy nlp object. The
    `cutoff` parameter can be passed to the internal standardization function
    to try to cope with leading headers sometimes merged into sentences by
    spaCy, which may at the moment lead to undesirable side results.
    """
    def __init__(self,
                 nlp: spacy.language.Language,
                 custom_keys: Optional[Dict[str, int]] = None,
                 cutoff: bool = False):
        self.nlp = nlp
        self.custom_keys = custom_keys
        self.cutoff = cutoff

    def preprocess(self, documents: List[Dict]) -> List[Dict]:
        """Create spaCy docs for all documents and save them under the `doc`
        key."""
        print("Creating spaCy docs...")
        for document in tqdm(documents):
            text = document["text"]
            if len(document["annotations"]) > 0:
                document["doc"] = self.nlp(text)
            else:
                document["doc"] = None

        return documents

    def standardize(self,
                    annotations: List[Tuple],
                    document: Dict
                    ) -> List[Tuple]:
        """Create standardized annotation spans and texts based upon full spaCy
        sentences for each annotation in the document.
        """
        return [self._standardize_citation(a, document["doc"])
                for a in annotations]

    def _standardize_citation(self,
                              annotation: Tuple,
                              doc: spacy.tokens.Doc
                              ) -> Tuple:
        """For an annotation based upon a string span, add a standardized span
        based upon full spaCy sentences. Adds sentence ids for first and last
        sentence as well as plain text.
        """
        def find_first_sentence(start, sents):
            """Find the first sentence containing the start position."""
            for idx, sent in enumerate(sents):
                # correct sentence end for some cases where trailing
                # punctuation leads to sentence overlaps in spaCy
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

        text = self._strip_extracted_text(doc.text[start_char:end_char],
                                    cutoff=self.cutoff)

        return start, end, tag, start_sent, end_sent, text

    def _strip_extracted_text(self,
                              text: str,
                              cutoff: bool = False
                              ) -> str:
        """Strip extracted text from surplus line breaks and possible leading
        headers.
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
