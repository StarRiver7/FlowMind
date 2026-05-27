"""Token Counter — 多模型 Token 估算.

支持:
  - DeepSeek Token 估算 (基于 cl100k_base / o200k_base)
  - BGE Token 估算 (字符级)
  - 总 Token 统计
"""

from typing import Optional
from dataclasses import dataclass
from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TokenCount:
    """Token 统计结果."""
    deepseek_tokens: int = 0    # DeepSeek 模型估算
    bge_tokens: int = 0         # BGE 模型估算 (≈字符数)
    char_count: int = 0


class TokenCounter:
    """多模型 Token 计数器.

    DeepSeek: 使用 tiktoken cl100k_base 编码器估算
    BGE:     字符数近似 (BGE tokenizer 约等于字符数)
    """

    def __init__(self):
        self._encoder = None
        self._encoder_name = "cl100k_base"

    def _ensure_encoder(self):
        if self._encoder is not None:
            return
        try:
            import tiktoken
            self._encoder = tiktoken.get_encoding(self._encoder_name)
            logger.debug(f"[TokenCounter] 加载编码器: {self._encoder_name}")
        except ImportError:
            logger.warning("[TokenCounter] tiktoken 未安装，使用字符数估算")
        except Exception as e:
            logger.warning(f"[TokenCounter] 编码器加载失败: {e}，使用字符数估算")

    def count(self, text: str) -> TokenCount:
        """计算单个文本的 Token 数."""
        self._ensure_encoder()

        char_count = len(text)

        if self._encoder:
            deepseek_tokens = len(self._encoder.encode(text))
        else:
            # 粗略估算: 中文 1.5 字符/token, 英文 4 字符/token
            deepseek_tokens = int(char_count / 2.5)

        # BGE: 字符级 tokenization
        bge_tokens = char_count

        return TokenCount(
            deepseek_tokens=deepseek_tokens,
            bge_tokens=bge_tokens,
            char_count=char_count,
        )

    def count_batch(self, texts: list[str]) -> list[TokenCount]:
        """批量计算 Token 数."""
        return [self.count(t) for t in texts]

    def total_stats(self, counts: list[TokenCount]) -> TokenCount:
        """汇总统计."""
        return TokenCount(
            deepseek_tokens=sum(c.deepseek_tokens for c in counts),
            bge_tokens=sum(c.bge_tokens for c in counts),
            char_count=sum(c.char_count for c in counts),
        )


# 全局单例
token_counter = TokenCounter()
