"""Text Cleaner — 企业级文本清洗管道.

清洗步骤 (按顺序):
  1. Unicode 标准化 (NFKC)
  2. 控制字符移除
  3. HTML 残留清理
  4. 连续空白合并
  5. 重复换行压缩
  6. 全角/半角规范化
  7. 零宽字符移除
  8. 首尾空白裁剪

不要暴力 replace；每一步都是可配置、可审计的清理规则。
"""

import re
import unicodedata
from typing import Optional
from dataclasses import dataclass
from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CleaningReport:
    """清洗报告."""
    original_chars: int
    cleaned_chars: int
    removed_chars: int
    blank_lines_removed: int
    html_tags_removed: int
    control_chars_removed: int
    steps_applied: list[str]


class TextCleaner:
    """文本清洗器.

    链式调用每一清洗步骤，生成清洗报告。
    """

    # HTML 标签模式
    HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
    # HTML 实体
    HTML_ENTITY_PATTERN = re.compile(r"&[a-zA-Z]+;|&#\d+;")
    # 控制字符 (除 \n \r \t)
    CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
    # 连续 3+ 换行
    MULTI_NEWLINE_PATTERN = re.compile(r"\n{3,}")
    # 连续 2+ 空格/制表符
    MULTI_SPACE_PATTERN = re.compile(r"[ \t]{2,}")
    # 零宽字符
    ZERO_WIDTH_PATTERN = re.compile(r"[\u200b\u200c\u200d\u200e\u200f\u2028\u2029\u202a-\u202e\ufeff]")
    # 行首尾空白
    LINE_WS_PATTERN = re.compile(r"^[ \t]+|[ \t]+$", re.MULTILINE)

    # HTML 实体映射
    HTML_ENTITIES = {
        "&nbsp;": " ", "&lt;": "<", "&gt;": ">", "&amp;": "&", "&quot;": '"',
        "&apos;": "'", "&#39;": "'", "&mdash;": "—", "&ndash;": "–",
        "&ldquo;": "\u201c", "&rdquo;": "\u201d",
    }

    def __init__(
        self,
        normalize_unicode: bool = True,
        remove_control_chars: bool = True,
        clean_html: bool = True,
        compress_whitespace: bool = True,
        compress_newlines: bool = True,
        remove_zero_width: bool = True,
        trim_lines: bool = True,
    ):
        self.normalize_unicode = normalize_unicode
        self.remove_control_chars = remove_control_chars
        self.clean_html = clean_html
        self.compress_whitespace = compress_whitespace
        self.compress_newlines = compress_newlines
        self.remove_zero_width = remove_zero_width
        self.trim_lines = trim_lines

    def clean(self, text: str) -> tuple[str, CleaningReport]:
        """执行完整的文本清洗管线.

        Returns:
            (cleaned_text, CleaningReport)
        """
        if not text:
            return text, CleaningReport(
                original_chars=0, cleaned_chars=0, removed_chars=0,
                blank_lines_removed=0, html_tags_removed=0,
                control_chars_removed=0, steps_applied=[],
            )

        original_len = len(text)
        report = CleaningReport(
            original_chars=original_len,
            cleaned_chars=0,
            removed_chars=0,
            blank_lines_removed=0,
            html_tags_removed=0,
            control_chars_removed=0,
            steps_applied=[],
        )

        # Step 1: Unicode 标准化
        if self.normalize_unicode:
            text = unicodedata.normalize("NFKC", text)
            report.steps_applied.append("unicode_normalize(NFKC)")

        # Step 2: 零宽字符
        if self.remove_zero_width:
            before = len(text)
            text = self.ZERO_WIDTH_PATTERN.sub("", text)
            removed = before - len(text)
            if removed:
                report.steps_applied.append(f"zero_width_removed({removed})")

        # Step 3: HTML 残留
        if self.clean_html:
            before = len(text)
            text = self.HTML_TAG_PATTERN.sub("", text)
            after_tags = len(text)
            report.html_tags_removed = before - after_tags

            # HTML 实体替换
            for entity, replacement in self.HTML_ENTITIES.items():
                text = text.replace(entity, replacement)
            text = self.HTML_ENTITY_PATTERN.sub("", text)

            if report.html_tags_removed:
                report.steps_applied.append(f"html_cleaned({report.html_tags_removed})")

        # Step 4: 控制字符
        if self.remove_control_chars:
            before = len(text)
            text = self.CONTROL_CHAR_PATTERN.sub("", text)
            report.control_chars_removed = before - len(text)
            if report.control_chars_removed:
                report.steps_applied.append(f"control_chars_removed({report.control_chars_removed})")

        # Step 5: 全角转半角（仅标点和数字）
        text = self._normalize_fullwidth(text)

        # Step 6: 连续换行压缩（最多保留 2 个连续换行）
        if self.compress_newlines:
            before = len(text)
            text = self.MULTI_NEWLINE_PATTERN.sub("\n\n", text)
            report.blank_lines_removed = (before - len(text)) // 2
            if report.blank_lines_removed:
                report.steps_applied.append(f"blank_lines_removed({report.blank_lines_removed})")

        # Step 7: 连续空格压缩
        if self.compress_whitespace:
            text = self.MULTI_SPACE_PATTERN.sub(" ", text)
            report.steps_applied.append("whitespace_compressed")

        # Step 8: 行首尾空白
        if self.trim_lines:
            text = self.LINE_WS_PATTERN.sub("", text)
            report.steps_applied.append("lines_trimmed")

        # Step 9: 首尾空白
        text = text.strip()

        report.cleaned_chars = len(text)
        report.removed_chars = original_len - report.cleaned_chars

        if report.removed_chars > 0:
            logger.debug(
                f"[TextCleaner] {original_len} → {report.cleaned_chars} chars "
                f"(-{report.removed_chars}, {report.removed_chars/original_len*100:.1f}%) "
                f"steps: {report.steps_applied}"
            )

        return text, report

    @staticmethod
    def _normalize_fullwidth(text: str) -> str:
        """全角标点和数字 → 半角."""
        result = []
        for ch in text:
            code = ord(ch)
            if 0xFF01 <= code <= 0xFF5E:  # 全角 ! 到 ~
                result.append(chr(code - 0xFEE0))
            elif code == 0x3000:  # 全角空格
                result.append(" ")
            else:
                result.append(ch)
        return "".join(result)


# 默认实例
text_cleaner = TextCleaner()
