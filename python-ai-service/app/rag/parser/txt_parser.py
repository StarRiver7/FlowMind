"""TXT Parser — 纯文本文件解析.

特性:
  - 编码自动检测 (UTF-8 / GBK / Latin-1)，chardet 可选
  - 空行过滤
  - 段落按双换行分割
"""

try:
    import chardet
    _HAS_CHARDET = True
except ImportError:
    _HAS_CHARDET = False

from app.rag.parser.parser_factory import BaseParser, ParsedDocument, ParagraphInfo
from app.core.logger import get_logger

logger = get_logger(__name__)


class TxtParser(BaseParser):
    """纯文本解析器 — 支持多编码自动检测."""

    @property
    def supported_types(self) -> list[str]:
        return [".txt"]

    def parse(self, file_path: str, file_name: str, content: bytes) -> ParsedDocument:
        # 编码检测
        encoding = "utf-8"
        if _HAS_CHARDET:
            try:
                detected = chardet.detect(content)
                if detected and detected.get("encoding"):
                    enc = detected["encoding"]
                    if enc.lower() in ("gb2312", "gb18030"):
                        enc = "gbk"
                    encoding = enc
            except Exception:
                pass

        try:
            text = content.decode(encoding, errors="replace")
        except Exception:
            text = content.decode("utf-8", errors="replace")

        paragraphs: list[ParagraphInfo] = []
        errors: list[str] = []
        char_offset = 0

        # 按双换行分段落
        for para_text in text.split("\n\n"):
            cleaned = para_text.strip()
            if not cleaned:
                char_offset += len(para_text) + 2
                continue

            paragraphs.append(ParagraphInfo(
                text=cleaned,
                page_number=0,
                char_offset=char_offset,
                char_count=len(cleaned),
                is_heading=False,
            ))
            char_offset += len(cleaned) + 2

        if not paragraphs:
            # 回退: 按单换行
            for line in text.split("\n"):
                stripped = line.strip()
                if stripped:
                    paragraphs.append(ParagraphInfo(
                        text=stripped,
                        page_number=0,
                        char_offset=char_offset,
                        char_count=len(stripped),
                    ))
                    char_offset += len(stripped) + 1

        full_text = "\n\n".join(p.text for p in paragraphs)

        logger.info(
            f"[TxtParser] 解析完成: '{file_name}' "
            f"chars={len(full_text)} encoding={encoding} paras={len(paragraphs)}"
        )

        return ParsedDocument(
            file_name=file_name,
            file_type="txt",
            total_chars=len(full_text),
            total_pages=0,
            full_text=full_text,
            paragraphs=paragraphs,
            metadata={
                "parser": "TxtParser",
                "encoding": encoding,
            },
            parse_errors=errors,
        )
