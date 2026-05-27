"""Markdown Parser — 结构化 Markdown 文档解析.

特性:
  - 标题层级识别 (H1-H6)
  - code block 保留（不破坏缩进）
  - list 结构识别
  - front matter 跳过
"""

import re
from app.rag.parser.parser_factory import BaseParser, ParsedDocument, ParagraphInfo, HeadingInfo
from app.core.logger import get_logger

logger = get_logger(__name__)


class MdParser(BaseParser):
    """Markdown 文档解析器."""

    # 匹配 Markdown 标题: # 到 ######
    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    # Front matter 分隔符
    FRONT_MATTER_PATTERN = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)

    @property
    def supported_types(self) -> list[str]:
        return [".md"]

    def parse(self, file_path: str, file_name: str, content: bytes) -> ParsedDocument:
        text = content.decode("utf-8", errors="replace")

        # 移除 front matter
        text = self.FRONT_MATTER_PATTERN.sub("", text)

        paragraphs: list[ParagraphInfo] = []
        headings: list[HeadingInfo] = []
        errors: list[str] = []
        char_offset = 0
        in_code_block = False

        for line in text.split("\n"):
            stripped = line.strip()

            # 追踪 code block
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                char_offset += len(line) + 1
                continue

            if in_code_block:
                # code block 内的内容原样保留
                paragraphs.append(ParagraphInfo(
                    text=line,
                    page_number=0,
                    char_offset=char_offset,
                    char_count=len(line),
                    is_heading=False,
                ))
                char_offset += len(line) + 1
                continue

            if not stripped:
                char_offset += 1
                continue

            # 标题检测
            heading_match = self.HEADING_PATTERN.match(stripped)
            if heading_match:
                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()

                paragraphs.append(ParagraphInfo(
                    text=heading_text,
                    page_number=0,
                    char_offset=char_offset,
                    char_count=len(heading_text),
                    is_heading=True,
                    heading_level=level,
                ))
                headings.append(HeadingInfo(
                    level=level,
                    text=heading_text,
                    page_number=0,
                    char_offset=char_offset,
                ))
                char_offset += len(line) + 1
                continue

            # 跳过纯链接/图片行
            if re.match(r"^!\[.*\]\(.*\)$", stripped) or re.match(r"^\[.*\]\(.*\)$", stripped):
                char_offset += len(line) + 1
                continue

            # 普通段落
            paragraphs.append(ParagraphInfo(
                text=stripped,
                page_number=0,
                char_offset=char_offset,
                char_count=len(stripped),
                is_heading=False,
            ))
            char_offset += len(line) + 1

        full_text = "\n\n".join(p.text for p in paragraphs)
        title_path = [h.text for h in headings if h.level <= 2]

        logger.info(
            f"[MdParser] 解析完成: '{file_name}' "
            f"chars={len(full_text)} paras={len(paragraphs)} "
            f"headings={len(headings)}"
        )

        return ParsedDocument(
            file_name=file_name,
            file_type="md",
            total_chars=len(full_text),
            total_pages=0,
            full_text=full_text,
            paragraphs=paragraphs,
            headings=headings,
            title_path=title_path,
            metadata={
                "parser": "MarkdownParser",
                "heading_count": len(headings),
            },
            parse_errors=errors,
        )
