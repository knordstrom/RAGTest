import unittest
import unittest
import os
import library.document_parser as dp

class DocumentParserTest(unittest.TestCase):

    folder = os.path.dirname(__file__), '../resources'

    def test_parse_pdf(self):
        parser = dp.PdfParser()
        file_path = os.path.join(self.folder, 'MS Office HTTPS Connectors.pdf')
        parsed_text = parser.parse(file_path)
        assert parsed_text[0:26] == "MS Office HTTPS Connectors"

    def test_parse_docx(self):
        parser = dp.DocxParser()
        file_path = os.path.join(self.folder, 'MS Office HTTPS Connectors.docx')
        parsed_text = parser.parse(file_path)
        assert parsed_text[0:26] == "MS Office HTTPS Connectors"

    def test_retrieve(self):
        file_path = os.path.join(self.folder, 'MS Office HTTPS Connectors.pdf')
        parsed_text = dp.DocumentParser.retrieve(file_path)
        assert parsed_text[0:26] == "MS Office HTTPS Connectors"

        file_path = os.path.join(self.folder, 'MS Office HTTPS Connectors.docx')
        parsed_text = dp.DocumentParser.retrieve(file_path)
        assert parsed_text[0:26] == "MS Office HTTPS Connectors"

        file_path = os.path.join(self.folder, 'MS Office HTTPS Connectors.doc')
        parsed_text = dp.DocumentParser.retrieve(file_path)
        assert parsed_text[0:26] == "MS Office HTTPS Connectors"
