# strings for xpath queries

# Namespace for QDA-XML
NAMESPACE = "urn:QDA-XML:project:1.0"

# Query to find codebook
CODEBOOK_QUERY = fr"./{{{NAMESPACE}}}CodeBook/{{{NAMESPACE}}}Codes"

# Query to find individual codes
CODE_QUERY = f"{{{NAMESPACE}}}Code"

# Query to find documents
DOCUMENT_QUERY = fr"./{{{NAMESPACE}}}Sources/{{{NAMESPACE}}}TextSource"

# Query to find PDF documents
DOCUMENT_QUERY_PDF = fr"./{{{NAMESPACE}}}Sources/{{{NAMESPACE}}}PDFSource"

# Query to find annotations
ANNOTATION_QUERY = fr"./{{{NAMESPACE}}}PlainTextSelection"

# Query to find code references
CODEREF_QUERY = fr"./{{{NAMESPACE}}}Coding/{{{NAMESPACE}}}CodeRef"
