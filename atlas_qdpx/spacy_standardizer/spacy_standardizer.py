"""
Example (prototype) standardizer to adjust annotation spans to full sentences.
It demonstrates how to implement the required protocol for custom
standardizers.
"""

from typing import List, Dict, Tuple

import spacy
from tqdm.auto import tqdm


class SpacyStandardizer:
    """Prototype example Standardizer for spaCy documents. Adjusts annotation
    spans to full spaCy sentences. Initiated with a spaCy nlp object. The
    `cutoff` parameter can be passed to the internal standardization function
    to try to cope with leading headers sometimes merged into sentences by
    spaCy, which may at the moment lead to undesirable side results.
    """
    def __init__(self,
                 nlp: spacy.language.Language,
                 cutoff: bool = False):
        self.nlp = nlp
        self.custom_keys = {"citation_standardized": 5,
                            "start_standardized": 6,
                            "end_standardized": 7}
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

        text, new_start, new_end = (
            self._strip_extracted_text(doc.text, start_char, end_char,
                                       cutoff=self.cutoff))

        return start, end, tag, start_sent, end_sent, text, new_start, new_end

    def _strip_extracted_text(self,
                              doc_text: str,
                              start: int,
                              end: int,
                              cutoff: bool = False
                              ) -> Tuple[str, int, int]:
        """Strip extracted text from surplus line breaks and possible leading
        headers. Returns stripped text, new start and end positions. If cutoff
        the heuristic will try to cut off leading headers by splitting the text
        at the first line break.
        """
        text = doc_text[start:end].strip()
        new_start = start + (len(doc_text[start:end]) - len(text))
        new_end = end - (len(doc_text[start:end]) - len(text.rstrip()))

        if cutoff:
            parts = text.split("\n", 1)
            if len(parts) > 1:
                cut_text =  parts[1].lstrip()
                new_start += len(text) - len(cut_text)
                text = cut_text

        return text, new_start, new_end
