"""Local file storage — 按知识空间分目录的三层存储结构.

Layout:
    storage/
    ├── uploads/    — 原始上传文件
    │   └── {space_id}/
    ├── parsed/     — 解析后的纯文本
    │   └── {space_id}/
    └── temp/       — 临时处理文件
"""

import os
import shutil
import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime


# 默认存储根目录: python-ai-service/storage/
DEFAULT_STORAGE_ROOT = Path(__file__).resolve().parent.parent.parent / "storage"


class FileStorage:
    """本地文件存储管理器.

    负责文件的物理存储、读取、删除，按知识空间分目录组织。
    """

    def __init__(self, root: Optional[Path] = None):
        self.root = Path(root) if root else DEFAULT_STORAGE_ROOT
        self._ensure_dirs()

    @property
    def uploads_dir(self) -> Path:
        return self.root / "uploads"

    @property
    def parsed_dir(self) -> Path:
        return self.root / "parsed"

    @property
    def temp_dir(self) -> Path:
        return self.root / "temp"

    # ---- 目录管理 ----

    def _ensure_dirs(self) -> None:
        for d in (self.uploads_dir, self.parsed_dir, self.temp_dir):
            d.mkdir(parents=True, exist_ok=True)

    def ensure_space_dir(self, space_id: int) -> tuple[Path, Path]:
        """为指定知识空间创建目录并返回 (uploads_subdir, parsed_subdir)."""
        up = self.uploads_dir / str(space_id)
        pa = self.parsed_dir / str(space_id)
        up.mkdir(parents=True, exist_ok=True)
        pa.mkdir(parents=True, exist_ok=True)
        return up, pa

    # ---- 上传文件保存 ----

    def save_upload(
        self,
        content: bytes,
        space_id: int,
        original_filename: str,
    ) -> tuple[str, str, int]:
        """保存上传文件到 storage/uploads/{space_id}/.

        Returns:
            (file_path, file_hash, file_size)
        """
        file_hash = hashlib.sha256(content).hexdigest()
        file_size = len(content)

        up_dir, _ = self.ensure_space_dir(space_id)

        # 处理重名: 原名 + 时间戳
        stem, ext = os.path.splitext(original_filename)
        safe_name = f"{stem}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}{ext}"
        dest = up_dir / safe_name

        dest.write_bytes(content)

        # 返回相对于 storage 根目录的路径
        rel_path = str(dest.relative_to(self.root))
        return rel_path, file_hash, file_size

    # ---- 文件读取 ----

    def read_file(self, rel_path: str) -> bytes:
        """根据相对路径读取文件."""
        abs_path = self.root / rel_path
        if not abs_path.exists():
            raise FileNotFoundError(f"File not found: {rel_path}")
        return abs_path.read_bytes()

    def get_absolute_path(self, rel_path: str) -> Path:
        """获取绝对路径."""
        return self.root / rel_path

    # ---- 文件删除 ----

    def delete_file(self, rel_path: str) -> bool:
        """删除文件."""
        abs_path = self.root / rel_path
        if abs_path.exists():
            abs_path.unlink()
            return True
        return False

    def delete_space_files(self, space_id: int) -> int:
        """删除知识空间下的所有文件，返回删除的文件数."""
        count = 0
        for sub in (self.uploads_dir, self.parsed_dir):
            d = sub / str(space_id)
            if d.exists():
                for f in d.iterdir():
                    if f.is_file():
                        f.unlink()
                        count += 1
        return count

    # ---- 磁盘占用 ----

    def space_disk_usage(self, space_id: int) -> int:
        """获取知识空间的磁盘占用（字节）."""
        total = 0
        for sub in (self.uploads_dir, self.parsed_dir):
            d = sub / str(space_id)
            if d.exists():
                for f in d.rglob("*"):
                    if f.is_file():
                        total += f.stat().st_size
        return total

    # ---- 清理临时文件 ----

    def clean_temp(self, max_age_minutes: int = 60) -> int:
        """清理超过一定时间的临时文件."""
        count = 0
        now = datetime.now().timestamp()
        for f in self.temp_dir.rglob("*"):
            if f.is_file():
                age = (now - f.stat().st_mtime) / 60
                if age > max_age_minutes:
                    f.unlink()
                    count += 1
        return count


# 全局单例
file_storage = FileStorage()

