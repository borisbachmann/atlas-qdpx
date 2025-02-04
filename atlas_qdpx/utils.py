# Reusable utility functions not bound to the main functionality of the toolkit.

import os
from typing import List

def list_files_by_type(path: str, file_type: str) -> List[str]:
    """List files in a directory. Output can be printed, returned as list of
    filenames or as list of tuples with index and filename.

    Args:
        path (str): Path to directory.
        file_type (str): file extension to be selected from path

    Returns:
        List[str]: List filenames in directory
        """
    file_list = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if type is not None:
                if file.endswith(f".{file_type.lower()}"):
                    file_list.append(file)
            else:
                file_list.append(file)
        break

    return file_list
