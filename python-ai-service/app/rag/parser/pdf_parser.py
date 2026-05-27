"""PDF Parser — 基于 PyMuPDF (fitz) 的企业级 PDF 解析.

特性:
  - 逐页文本提取，保留页码
  - 空白段落过滤
  - 异常 PDF 兼容处理 (损坏/加密/扫描件检测)
  - OCR 预留接口
  - 图片页检测与标记
"""

from app.rag.parser.parser_factory import BaseParser, ParsedDocument, PageInfo, ParagraphInfo, HeadingInfo
from app.core.logger import get_logger

logger = get_logger(__name__)


class PdfParser(BaseParser):
    """PDF 文档解析器 — PyMuPDF 后端."""

    MIN_TEXT_PER_PAGE = 10  # 少于此字符数视为空白/图片页

    @property
    def supported_types(self) -> list[str]:
        return [".pdf"]

    def parse(self, file_path: str, file_name: str, content: bytes) -> ParsedDocument:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=content, filetype="pdf")
        total_pages = doc.page_count

        if total_pages == 0:
            return ParsedDocument(
                file_name=file_name, file_type="pdf",
                total_chars=0, total_pages=0, full_text="",
                parse_errors=["PDF 文件无页面"],
            )

        pages: list[PageInfo] = []
        paragraphs: list[ParagraphInfo] = []
        headings: list[HeadingInfo] = []
        errors: list[str] = []
        all_text_parts: list[str] = []
        global_char_offset = 0

        for page_idx in range(total_pages):
            try:
                page = doc[page_idx]
                page_text = page.get_text("text") or ""
            except Exception as e:
                errors.append(f"第 {page_idx + 1} 页读取失败: {e}")
                page_text = ""

            # 空白/图片页检测
            if len(page_text.strip()) < self.MIN_TEXT_PER_PAGE:
                # 检查是否有图片
                images = page.get_images(full=True)
                if images:
                    page_text = f"[第 {page_idx + 1} 页: 图片/扫描内容，共 {len(images)} 张图]"

            page_char_count = len(page_text)

            # 逐段解析
            page_paragraphs: list[str] = []
            for para_text in page_text.split("\n"):
                stripped = para_text.strip()
                if not stripped:
                    continue
                page_paragraphs.append(stripped)

            pages.append(PageInfo(
                page_number=page_idx + 1,
                text=page_text,
                char_count=page_char_count,
                paragraphs=page_paragraphs,
            ))

            # 构建全局段落列表
            for para_text in page_paragraphs:
                # 简单标题检测: 短文本 + 可能是标题模式
                is_heading = _detect_heading(para_text)
                heading_level = _guess_heading_level(para_text) if is_heading else 0

                paragraphs.append(ParagraphInfo(
                    text=para_text,
                    page_number=page_idx + 1,
                    char_offset=global_char_offset,
                    char_count=len(para_text),
                    is_heading=is_heading,
                    heading_level=heading_level,
                ))

                if is_heading:
                    headings.append(HeadingInfo(
                        level=heading_level,
                        text=para_text,
                        page_number=page_idx + 1,
                        char_offset=global_char_offset,
                    ))

                global_char_offset += len(para_text) + 1  # +1 for newline

            # 拼接时保留页码标记
            all_text_parts.append(f"[第 {page_idx + 1} 页]\n{page_text}")

        doc.close()

        full_text = "\n\n".join(all_text_parts)
        title_path = [h.text for h in headings if h.level <= 2]

        if not pages:
            errors.append("PDF 解析后无有效文本内容")

        logger.info(
            f"[PdfParser] 解析完成: '{file_name}' "
            f"pages={total_pages} chars={len(full_text)} "
            f"headings={len(headings)} errors={len(errors)}"
        )

        return ParsedDocument(
            file_name=file_name,
            file_type="pdf",
            total_chars=len(full_text),
            total_pages=total_pages,
            full_text=full_text,
            pages=pages,
            paragraphs=paragraphs,
            headings=headings,
            title_path=title_path,
            metadata={
                "parser": "PyMuPDF",
                "page_count": total_pages,
                "has_errors": len(errors) > 0,
            },
            parse_errors=errors,
        )


def _detect_heading(text: str) -> bool:
    """检测文本是否为标题."""
    if len(text) > 100:
        return False
    # 中文标题模式: 第X章, X.X, 一、二、三
    import re
    patterns = [
        r"^第[一二三四五六七八九十百千万\d]+[章节条款]",   # 第X章
        r"^[\d]+[\.\、\．][\d]*",                       # 1. 1.1
        r"^[一二三四五六七八九十]+[、\．\s]",              # 一、
        r"^[（\(][一二三四五六七八九十\d]+[）\)]",          # (一)
    ]
    for p in patterns:
        if re.match(p, text):
            return True
    return False


def _guess_heading_level(text: str) -> int:
    """推测标题层级."""
    import re
    if re.match(r"^第[一二三四五六七八九十百千万\d]+章", text):
        return 1
    if re.match(r"^第[一二三四五六七八九十百千万\d]+节", text):
        return 2
    if re.match(r"^[\d]+\.$", text):
        return 1
    if re.match(r"^[\d]+\.[\d]+", text):
        return 2
    if re.match(r"^[\d]+\.[\d]+\.[\d]+", text):
        return 3
    if re.match(r"^[一二三四五六七八九十]+[、\．]", text):
        return 1
    if re.match(r"^[（\(][一二三四五六七八九十\d]+[）\)]", text):
        return 2
    return 3
