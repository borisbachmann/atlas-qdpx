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

from typing import Tuple, Dict, List, Optional, Protocol, runtime_checkable


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
