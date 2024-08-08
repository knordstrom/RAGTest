import pypdf 
import docx
import textract

class DocumentParser:

    def parse(self, filename: str) -> str:
        pass

    @staticmethod
    def retrieve(filename: str) -> str:
        if filename.endswith('.docx') or filename.endswith('.doc'):
            return DocxParser().parse(filename)
        elif filename.endswith('.pdf'):
            return PdfParser().parse(filename)
        else:
            raise ValueError('Unknown file type')

class DocxParser(DocumentParser):

    def parse(self, filename: str) -> str:
        f: bytes = textract.process(filename)
        return f.decode('utf-8').lstrip()

class PdfParser(DocumentParser):

    def parse(self, filename: str) -> str:
        reader = pypdf.PdfReader(filename)
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text())
        return '\n'.join(pages)


