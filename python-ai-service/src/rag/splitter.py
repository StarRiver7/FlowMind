from src.config import settings


class TextSplitter:
    """文本分块器 — 使用RecursiveCharacterTextSplitter策略"""

    def __init__(self):
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap

    def split(self, text: str) -> list[str]:
        """将文本按chunk_size切分，保留chunk_overlap重叠"""
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunks.append(text[start:end])
            start += self.chunk_size - self.chunk_overlap

        return chunks


text_splitter = TextSplitter()
