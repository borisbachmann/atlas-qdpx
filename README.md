# atlas-qdpx

atlas-qdpx is a small tool to handle QDA-REFI exports from the atlas.ti QDA (Qualitative Data Analysis) software 
written in Python. The QDA-REFI format is an XML-based format that is used to exchange QDA data between different 
software tools. Atlas-qdpx helps to extract citations and respective codes for all documents in one or multiple 
QDA-REFI files quickly to enable further analysis of the data.

## Installation

To install the library, you can use pip:

```bash
pip install git+https://github.com/sereios/atlas_qdpx
```

After pulling the repository, and creating a virtual environment, you can install dependencies with:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

The library provides functions designed to be used in a Jupyter notebook or Python script. Functions operate either on 
a single QDA-REFI file or a directory containing multiple files. The basic functions are `parse_qdpx` and 
`parse_qdpx_dir`, each returning a list of dictionaries with the extracted data containing the following keys:

| Key | Description |
| --- | --- |
| `doc_id` | original id of the document in atlas.ti project (starting at 1) |
| `citation` | original text of the citation |
| `code` | code in the atlas.ti codebook |
| `start` | start position as a string index of the document's text |
| `end` | end position as a string index of the document's text |
| `start_atlas.ti` | original atlas.ti start position, referring to the document's paragraphs (starting at 1) |
| `end_atlas.ti` | original atlas.ti end position, referring to the document's paragraphs (starting at 1) |
| `file` | name of the original plain text file in atlas.ti project |
| `coder` | name or abbreviation of coding researcher as specified by the `coder` parameter |

When calling on a single file, the Coder has to be specified as a parameter. When calling on a directory, the Coder 
is derived from the file name, assuming the files carry a suffix with the coder's name (e.g. `file_coder.qdpx`).

The library also includes three basic DataFrame functions, based upon the `pandas` library:
1. `annotations_to_df` creates a sorted pandas DataFrame from the list of dictionaries.
2. `extract_code_group_dfs` creates a dictionary of DataFrames, each containing the annotations for a group of codes.
   Code groups have to be passed as a dictionary with the group name as key and a list of codes as values. Codes 
   not included in any group are added to a group named `"misc"`.
3. `save_output_dfs` saves DataFrames to an output directory in CSV format. If a dictionary of code groups is passed, 
   the function saves a CSV file for each code group in addition to the main DataFrame. A project name has to be 
   provided to create file names.

Finally, the library includes two functions wrapping the functionality by directly reading a QDA-REFI file or a 
directory and saving the output to a directory (`project_to_csv`, `folder_to_csv`).

#### Examples

For a single file:

```python
from atlas_qdpx import parse_qdpx, annotations_to_df, make_code_group_dfs, save_output_dfs, project_to_csv

input_file = "path/to/file.qdpx"
coder = "coder_name"

# extract annotations
annotations = parse_qdpx(input_file, coder="coder_name")

# convert to DataFrame
annotations_df = annotations_to_df(annotations)

# extract code group dataframes
code_groups = {"group_name_1": ["code1", "code2"],
               "group_name_2": ["code3", "code4"]}
code_group_dfs = make_code_group_dfs(annotations_df, code_groups=code_groups)

# save output to csv
output_dir = "path/to/output"
project_name = "project_name"
save_output_dfs(annotations_df,
                output_path=output_dir,
                project_name=project_name,
                code_groups=code_groups)

# parse directly from file to csv
project_to_csv(input_file,
               output_path=output_dir,
               project_name=project_name,
               coder=coder,
               code_groups=code_groups)
```

For a directory of files:

```python
from atlas_qdpx import parse_qdpx_dir, folder_to_csv

input_dir = "path/to/directory"

# extract annotations
annotations = parse_qdpx_dir(input_dir)

# parse directly from directory to csv
code_groups = {"group_name_1": ["code1", "code2"],
               "group_name_2": ["code3", "code4"]}
output_dir = "path/to/output"
project_name = "project_name"

folder_to_csv(input_dir, 
              output_path=output_dir, 
              project_name=project_name,
              code_groups=code_groups)
```

Code group extraction and manual saving to CSV work the same way as for single files, as all annotations are colected 
in a single DataFrame.

### Advanced Usage: 

#### Transformations

Atlas-qpdx also includes a `transformations` module with functions to transform the extracted data. Three 
functions are included:

1. `merge_citations`: Merges citations with matching spans and codes into a single annotation, creating a list of 
   coders for each merged annotation.
2. `group_overlaps`: Groups overlapping annotations, creating either a list of annotations or assigning a group 
   identifier to each annotation.
3. `extract_code_groups`: Extracts annotations for groups of codes, based upon a dictionary of code groups.

```python
from atlas_qdpx import parse_qdpx, merge_citations, group_overlaps, extract_code_groups

input_file = "path/to/file.qdpx"
coder = "coder_name"

# extract annotations
annotations = parse_qdpx(input_file, coder="coder_name")

# parse directly from directory to csv
code_groups = {"group_name_1": ["code1", "code2"],
               "group_name_2": ["code3", "code4"]}

# create dfs for all code groups, based upon merged and grouped annotations
merged_annotations = merge_citations(annotations)
code_group_annotations = extract_code_groups(merged_annotations, code_groups)
for value in code_group_annotations.values():
    value = group_overlaps(value, output="numbered")
```

#### Review

A basic functionality to create standardized review dataframes is also provided. The resulting dataframe format proved 
useful for manual review of extracted data, e.g. in a collaborative Google sheet. It may not be suitable for all use 
cases, but the function can be used as a starting point for custom review dataframes. If the data has been grouped 
before (per the `group_overlaps` function above), data will be aggregated on a group level, allowing to review all codes 
assigned to clusters of overlapping annotations.

```python
from atlas_qdpx import make_review_df

output_path = "path/to/review_output"

# re-use data from the previous example
dfs = {}
for group, value in code_group_annotations.items():
    codes = code_groups[group]
    df = annotations_to_df(value)
    df = make_review_df(df, codes, output="plain")
    dfs[group] = (df)

# Save dataframes to disk
output_path = "data/output/NSP_Narrative"
for group, df in dfs.items():
    df.to_csv(f"{output_path}/NSP_Narrative_codes_{group}.csv")
```
    
#### Standardization

Additionally, the library allows all basic functions (working upon QDPX files) to accept with an additional 
`standardizer` parameter. This can be used to impose certain modifications on or extract derived attributes from the 
annotations – such as e.g. imposing common boundaries upon citations (i.e. "coding units" following Mayring) or 
mapping code names to a common standard.

Functions accepts any class sharing a common interface defined by the `Standardizer` class in the `standardizer` 
module. These classes have to implement the following methods:

- `preprocess`: Method to preprocess documents to derive necessary information for standardization. As documents are 
  internally handled as a list of dicts, the method has to take this as input and return the same output format.
- `standardize`: Method to implement the desired standardization of annotations. As annotations are internally 
  handled as tuples, the method also has to accept and return a list tuples. Basic tuples are structured as follows
- `(start_index, end_index, code)` and return tuples have to include additional features starting at index 3.

Additionally, standardizers have to carry a `custom_keys` attribute which has to be a dictionary mapping custom keys 
to be included in the returned annotation dicts to the respective index in the tuple.

As an example, the repository includes the `SpacyStandardizer` class, which uses the `spacy` library reconstruct 
full sentences around citations and returns standardized citations and spans based upon groups of consecutive 
complete sentences (as if the coding unit would have been defined as at least one complete sentence). The class is 
for demonstration purposes only and can be used to guide the implementation of custom standardizers.

```python
import spacy

from atlas_qdpx import parse_qdpx
from atlas_qdpx.spacy_standardizer.spacy_standardizer import SpacyStandardizer

input_file = "path/to/file.qdpx"
coder = "coder_name"

# load spacy model
nlp = spacy.load("de_core_news_sm")

# define standardizer (the cutoff parameter is optional and tries to cut off trailing headers sometimes included in 
# spaCy sentences)
standardizer = SpacyStandardizer(nlp, cutoff=True)

# extract annotations
annotations = parse_qdpx(input_file,
                        coder="coder_name",
                        standardizer=standardizer)
```

## Dependencies
This project uses the following third-party dependencies: 
- [pandas](https://pandas.pydata.org/) library, licensed under the BSD 3-Clause License.
- [tqdm](https://github.com/tqdm/tqdm), licensed under the MIT License.

Additionally, the example standardizer uses the following third-party dependencies (not needed for the Atlas-qdpx 
library):
- [spaCy](https://spacy.io/), licensed under the MIT License.

## Credits
The basic function to extract annotations from QDA-REFI XML is based upon the gist 
https://gist.github.com/Whadup/a795fac02f4405ca1b5a278799ce6125 by Lukas Pfahler.

## Acknowledgements
This is a personal project, but the core functionality was developed as a tool for the research project 
"Narrative Futures" at the University of Wuppertal, Germany (funded from 2023 to 2026 by the VolkswagenStiftung). The 
project aims to combine qualitative and quantitative methods of text analysis to investigate narrative futures in the 
context of sustainability transformations.