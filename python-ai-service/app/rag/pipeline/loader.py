import os
from app.common.exceptions.exceptions import RAGException


class DocumentLoader:
    """文档加载器 — 支持PDF/Word/Markdown/TXT"""

    SUPPORTED_TYPES = {"pdf", "docx", "md", "txt"}

    async def load(self, file_path: str, file_type: str) -> str:
        """加载文档内容"""
        if file_type not in self.SUPPORTED_TYPES:
            raise RAGException(f"Unsupported file type: {file_type}")

        if not os.path.exists(file_path):
            raise RAGException(f"File not found: {file_path}")

        if file_type == "txt" or file_type == "md":
            return await self._load_text(file_path)

        # PDF/Word — 占位，实际接入PyPDF2/python-docx
        raise RAGException(f"Document type {file_type} not yet implemented (need PyPDF2/python-docx)")

    async def _load_text(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()


document_loader = DocumentLoader()
