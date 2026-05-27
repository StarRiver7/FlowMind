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
        parser_factory.register(PdfParser())
        parser_factory.register(DocxParser())
        parser_factory.register(MdParser())
        parser_factory.register(TxtParser())
        assert "pdf" in parser_factory.registered_types
        assert "docx" in parser_factory.registered_types
        assert "md" in parser_factory.registered_types
        assert "txt" in parser_factory.registered_types

    def test_get_parser(self):
        from app.rag.parser.parser_factory import parser_factory
        from app.rag.parser.pdf_parser import PdfParser
        from app.rag.parser.txt_parser import TxtParser
        parser_factory._parsers.clear()
        parser_factory.register(PdfParser())
        parser_factory.register(TxtParser())
        assert isinstance(parser_factory.get_parser("pdf"), PdfParser)
        assert isinstance(parser_factory.get_parser("txt"), TxtParser)
        assert parser_factory.get_parser("xyz") is None

    def test_unsupported_type_raises(self):
        from app.rag.parser.parser_factory import parser_factory
        parser_factory._parsers.clear()
        with pytest.raises(ValueError):
            parser_factory.parse("path", "file.exe", b"data", "exe")

class TestTxtParser:
    def test_basic_parse(self):
        from app.rag.parser.txt_parser import TxtParser
        parser = TxtParser()
        content = "Para one\n\nPara two\n\nPara three".encode("utf-8")
        doc = parser.parse("test.txt", "test.txt", content)
        assert doc.file_type == "txt"
        assert doc.total_chars > 0
        assert len(doc.paragraphs) == 3

    def test_single_paragraph(self):
        from app.rag.parser.txt_parser import TxtParser
        parser = TxtParser()
        doc = parser.parse("single.txt", "single.txt", "Just one".encode("utf-8"))
        assert len(doc.paragraphs) == 1

    def test_empty_file(self):
        from app.rag.parser.txt_parser import TxtParser
        parser = TxtParser()
        doc = parser.parse("empty.txt", "empty.txt", b"")
        assert doc.total_chars == 0
        assert len(doc.paragraphs) == 0

    def test_multiline_paragraph(self):
        from app.rag.parser.txt_parser import TxtParser
        parser = TxtParser()
        content = "Line A\nLine B\nLine C\n\nNew para".encode("utf-8")
        doc = parser.parse("multi.txt", "multi.txt", content)
        assert len(doc.paragraphs) >= 2

class TestMdParser:
    def test_headings(self):
        from app.rag.parser.md_parser import MdParser
        content = b"# Introduction\ncontent\n## 1.1 Overview\nmore\n### 1.1.1 Detail\ndetail"
        parser = MdParser()
        doc = parser.parse("doc.md", "doc.md", content)
        headings = doc.headings
        assert len(headings) >= 2
        assert headings[0].text == "Introduction"
        assert headings[0].level == 1
        assert "Introduction" in doc.title_path

    def test_code_block_preserved(self):
        from app.rag.parser.md_parser import MdParser
        content = b"# Doc\n\n```python\nprint(42)\n```\n\nEnd"
        parser = MdParser()
        doc = parser.parse("code.md", "code.md", content)
        assert "print" in doc.full_text

    def test_front_matter_skipped(self):
        from app.rag.parser.md_parser import MdParser
        content = b"---\ntitle: test\n---\n\n# Body start\ncontent"
        parser = MdParser()
        doc = parser.parse("fm.md", "fm.md", content)
        assert "title:" not in doc.full_text
        assert "Body start" in doc.full_text

class TestTextCleaner:
    def test_whitespace_compress(self):
        from app.rag.parser.text_cleaner import TextCleaner
        cleaner = TextCleaner()
        text = "hello     world\n\n\n\nfoo"
        cleaned, report = cleaner.clean(text)
        assert "    " not in cleaned
        assert cleaned.count("\n") <= 2
        assert report.removed_chars > 0

    def test_html_removal(self):
        from app.rag.parser.text_cleaner import TextCleaner
        cleaner = TextCleaner()
        text = "<p>Hello</p> <b>World</b>"
        cleaned, report = cleaner.clean(text)
        assert "<p>" not in cleaned
        assert "Hello World" in cleaned
        assert report.html_tags_removed > 0

    def test_html_entities(self):
        from app.rag.parser.text_cleaner import TextCleaner
        cleaner = TextCleaner()
        text = "Price: &lt;100 &amp; &gt;50"
        cleaned, _ = cleaner.clean(text)
        assert "&lt;" not in cleaned

    def test_control_chars(self):
        from app.rag.parser.text_cleaner import TextCleaner
        cleaner = TextCleaner()
        text = "hello\x00\x01world"
        cleaned, report = cleaner.clean(text)
        assert "\x00" not in cleaned
        assert report.control_chars_removed > 0

    def test_unicode_normalize(self):
        from app.rag.parser.text_cleaner import TextCleaner
        cleaner = TextCleaner()
        text = "caf\u00e9"
        cleaned, _ = cleaner.clean(text)
        assert len(cleaned) > 0

    def test_zero_width_removal(self):
        from app.rag.parser.text_cleaner import TextCleaner
        cleaner = TextCleaner()
        text = "hello\u200bworld"
        cleaned, _ = cleaner.clean(text)
        assert "\u200b" not in cleaned

    def test_empty_input(self):
        from app.rag.parser.text_cleaner import TextCleaner
        cleaner = TextCleaner()
        cleaned, report = cleaner.clean("")
        assert cleaned == ""
        assert report.original_chars == 0

class TestChunkStrategy:
    def test_basic_split(self):
        from app.rag.chunk.chunk_strategy import ChunkStrategy, ChunkConfig
        config = ChunkConfig(chunk_size=100, chunk_overlap=20, min_chunk_size=10)
        strategy = ChunkStrategy(config)
        text = "Test content text. " * 50
        chunks = strategy.split(text)
        assert len(chunks) > 1
        for c in chunks:
            assert c.char_count >= config.min_chunk_size

    def test_overlap(self):
        from app.rag.chunk.chunk_strategy import ChunkStrategy, ChunkConfig
        config = ChunkConfig(chunk_size=60, chunk_overlap=20, min_chunk_size=10)
        strategy = ChunkStrategy(config)
        text = "ABCDEFGHIJ" * 20
        chunks = strategy.split(text)
        assert len(chunks) > 0

    def test_empty_text(self):
        from app.rag.chunk.chunk_strategy import ChunkStrategy
        strategy = ChunkStrategy()
        assert len(strategy.split("")) == 0
        assert len(strategy.split("   ")) == 0

    def test_short_text(self):
        from app.rag.chunk.chunk_strategy import ChunkStrategy, ChunkConfig
        config = ChunkConfig(chunk_size=500, min_chunk_size=2)
        strategy = ChunkStrategy(config)
        text = "Short"
        chunks = strategy.split(text)
        assert len(chunks) == 1

    def test_heading_detection(self):
        from app.rag.chunk.chunk_strategy import ChunkStrategy
        assert ChunkStrategy._starts_with_heading("# Title")
        assert ChunkStrategy._starts_with_heading("## Subtitle")
        assert not ChunkStrategy._starts_with_heading("Normal text.")

    def test_page_location(self):
        from app.rag.chunk.chunk_strategy import ChunkStrategy
        strategy = ChunkStrategy()
        pages = [
            {"page_number": 1, "char_start": 0, "char_end": 100},
            {"page_number": 2, "char_start": 101, "char_end": 200},
        ]
        assert strategy._locate_page(50, 60, pages) == 1
        assert strategy._locate_page(150, 160, pages) == 2

    def test_quality_filter_removes_empty(self):
        from app.rag.chunk.chunk_strategy import ChunkStrategy, ChunkConfig, ChunkResult
        config = ChunkConfig(min_chunk_size=10)
        strategy = ChunkStrategy(config)
        chunks = [
            ChunkResult(index=0, content="ok content here", char_count=15),
            ChunkResult(index=1, content="   ", char_count=3),
            ChunkResult(index=2, content="also ok content", char_count=14),
        ]
        filtered = strategy._quality_filter(chunks)
        assert len(filtered) == 2

class TestTokenCounter:
    def test_count_text(self):
        from app.rag.chunk.token_counter import token_counter
        result = token_counter.count("Test sentence for token counting.")
        assert result.char_count > 0
        assert result.deepseek_tokens > 0
        assert result.bge_tokens == result.char_count

    def test_batch_count(self):
        from app.rag.chunk.token_counter import token_counter
        results = token_counter.count_batch(["A", "B", "C"])
        assert len(results) == 3

    def test_total_stats(self):
        from app.rag.chunk.token_counter import token_counter
        results = token_counter.count_batch(["A", "BB", "CCC"])
        total = token_counter.total_stats(results)
        assert total.deepseek_tokens > 0
        assert total.char_count == 6

class TestChunkMetadata:
    def test_build_metadata(self):
        from app.rag.chunk.chunk_metadata import build_chunk_metadata
        meta = build_chunk_metadata(
            document_id=1, chunk_index=0, content="test content",
            token_count=4, page_number=5,
            title_path=["Chapter 1", "1.1 Overview"],
        )
        assert meta.document_id == 1
        assert meta.chunk_index == 0
        assert meta.char_count == len("test content")
        assert meta.page_number == 5

    def test_to_source_citation(self):
        from app.rag.chunk.chunk_metadata import build_chunk_metadata
        meta = build_chunk_metadata(
            document_id=1, chunk_index=0,
            content="Employee handbook content...",
            page_number=3,
        )
        citation = meta.to_source_citation("handbook.pdf")
        assert "handbook.pdf" in citation["display"]

    def test_to_db_dict(self):
        from app.rag.chunk.chunk_metadata import build_chunk_metadata
        meta = build_chunk_metadata(document_id=1, chunk_index=0, content="test")
        db_dict = meta.to_db_dict()
        assert db_dict["document_id"] == 1
        assert db_dict["chunk_index"] == 0
        assert db_dict["content"] == "test"
        assert db_dict["is_embedded"] == 0
        assert db_dict["milvus_id"] is None

class TestDocumentStatusExtended:
    def test_chunking_to_chunked(self):
        from app.kb.document_status import can_transition, next_status, DocumentStatus
        assert can_transition("chunking", "chunked") is True
        assert next_status("chunking") == DocumentStatus.CHUNKED

    def test_chunked_to_embedding(self):
        from app.kb.document_status import can_transition, next_status, DocumentStatus
        assert can_transition("chunked", "embedding") is True
        assert next_status("chunked") == DocumentStatus.EMBEDDING

    def test_chunked_cannot_skip(self):
        from app.kb.document_status import can_transition
        assert can_transition("chunked", "indexed") is False
        assert can_transition("chunked", "ready") is False

    def test_chunked_display_name(self):
        from app.kb.document_status import status_display_name
        assert len(status_display_name("chunked")) > 0

    def test_chunked_is_retryable(self):
        from app.kb.document_status import is_retryable
        assert is_retryable("chunked") is True

    def test_pipeline_flow(self):
        from app.kb.document_status import can_transition
        flow = [
            ("uploaded", "parsing"), ("parsing", "parsed"),
            ("parsed", "chunking"), ("chunking", "chunked"),
        ]
        for cur, nxt in flow:
            assert can_transition(cur, nxt), f"Fail: {cur} to {nxt}"
