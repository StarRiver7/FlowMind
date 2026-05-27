import io, sys, pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

class TestParserFactory:
    def test_registration(self):
        from app.rag.parser.parser_factory import parser_factory
        from app.rag.parser.pdf_parser import PdfParser
        from app.rag.parser.docx_parser import DocxParser
        from app.rag.parser.md_parser import MdParser
        from app.rag.parser.txt_parser import TxtParser
        parser_factory._parsers.clear()
        parser_factory.register(PdfParser()); parser_factory.register(DocxParser())
        parser_factory.register(MdParser()); parser_factory.register(TxtParser())
        assert 'pdf' in parser_factory.registered_types
        assert 'docx' in parser_factory.registered_types
