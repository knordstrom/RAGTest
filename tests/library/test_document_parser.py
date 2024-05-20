import unittest
import unittest
import os
from library.document_parser import DocxParser, PdfParser
import library.document_parser as document_parser

class DocumentParserTest(unittest.TestCase):

    def test_parse_pdf(self):
        parser = PdfParser()
        file_path = os.path.join(os.path.dirname(__file__), '../resources', 'MS Office HTTPS Connectors.pdf')
        parsed_text = parser.parse(file_path)
        assert parsed_text[0:26] == "MS Office HTTPS Connectors"

    def test_parse_docx(self):
        parser = DocxParser()
        file_path = os.path.join(os.path.dirname(__file__), '../resources', 'MS Office HTTPS Connectors.docx')
        parsed_text = parser.parse(file_path)
        assert parsed_text[0:26] == "MS Office HTTPS Connectors"

    def test_retrieve_pdf(self):
        file_path = os.path.join(os.path.dirname(__file__), '../resources', 'MS Office HTTPS Connectors.pdf')
        parsed_text = document_parser.DocumentParser.retrieve(file_path)
        assert parsed_text[0:26] == "MS Office HTTPS Connectors"

        file_path = os.path.join(os.path.dirname(__file__), '../resources', 'MS Office HTTPS Connectors.docx')
        parsed_text = document_parser.DocumentParser.retrieve(file_path)
        assert parsed_text[0:26] == "MS Office HTTPS Connectors"

        file_path = os.path.join(os.path.dirname(__file__), '../resources', 'MS Office HTTPS Connectors.doc')
        parsed_text = document_parser.DocumentParser.retrieve(file_path)
        assert parsed_text[0:26] == "MS Office HTTPS Connectors"
