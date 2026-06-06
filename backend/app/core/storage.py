"""统一文件存储层 — 支持本地文件系统与 MinIO S3 兼容对象存储

通过环境变量 STORAGE_BACKEND=local|minio 切换后端。
"""

import io
import os
import tempfile
import logging
from abc import ABC, abstractmethod
from typing import Optional

import aiofiles
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


# ── 抽象基类 ──────────────────────────────────────────────

class BaseStorage(ABC):
    """统一存储接口"""

    @abstractmethod
    async def save_audio(self, file_data: bytes, filename: str) -> str:
        """保存音频文件，返回存储路径标识"""
        ...

    @abstractmethod
    async def save_resume(self, file_data: bytes, filename: str) -> str:
        """保存简历文件，返回存储路径标识"""
        ...

    @abstractmethod
    async def save_export(self, file_data: bytes, filename: str) -> str:
        """保存导出文件，返回存储路径标识"""
        ...

    @abstractmethod
    async def get_file(self, path: str) -> bytes:
        """读取文件内容"""
        ...

    @abstractmethod
    async def delete_file(self, path: str) -> None:
        """删除文件"""
        ...

    @abstractmethod
    def exists(self, path: str) -> bool:
        """检查文件是否存在"""
        ...

    @abstractmethod
    async def get_local_path(self, path: str) -> str:
        """
        获取可用于本地读取的文件路径。
        - 本地存储：直接返回原路径
        - MinIO：下载到临时文件，返回临时路径（调用方负责清理）
        """
        ...


# ── 本地存储 ──────────────────────────────────────────────

class LocalStorage(BaseStorage):
    """本地文件系统存储（开发默认）"""

    def __init__(self):
        os.makedirs(settings.AUDIO_DIR, exist_ok=True)
        os.makedirs(settings.RESUME_DIR, exist_ok=True)
        os.makedirs(settings.EXPORT_DIR, exist_ok=True)

    async def save_audio(self, file_data: bytes, filename: str) -> str:
        path = os.path.join(settings.AUDIO_DIR, filename)
        async with aiofiles.open(path, "wb") as f:
            await f.write(file_data)
        return path

    async def save_resume(self, file_data: bytes, filename: str) -> str:
        path = os.path.join(settings.RESUME_DIR, filename)
        async with aiofiles.open(path, "wb") as f:
            await f.write(file_data)
        return path

    async def save_export(self, file_data: bytes, filename: str) -> str:
        path = os.path.join(settings.EXPORT_DIR, filename)
        async with aiofiles.open(path, "wb") as f:
            await f.write(file_data)
        return path

    async def get_file(self, path: str) -> bytes:
        async with aiofiles.open(path, "rb") as f:
            return await f.read()

    async def delete_file(self, path: str) -> None:
        if os.path.exists(path):
            os.remove(path)

    def exists(self, path: str) -> bool:
        return os.path.exists(path)

    async def get_local_path(self, path: str) -> str:
        return path


# ── MinIO 存储 ────────────────────────────────────────────

class MinioStorage(BaseStorage):
    """MinIO S3 兼容对象存储（生产环境）"""

    BUCKET = settings.MINIO_BUCKET
    AUDIO_PREFIX = "audio/"
    RESUME_PREFIX = "resumes/"
    EXPORT_PREFIX = "exports/"

    def __init__(self):
        from minio import Minio
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False,
        )
        # Ensure bucket exists
        if not self.client.bucket_exists(self.BUCKET):
            self.client.make_bucket(self.BUCKET)
            logger.info(f"Created MinIO bucket: {self.BUCKET}")

    def _make_path(self, prefix: str, filename: str) -> str:
        """返回统一路径格式: minio://bucket/key"""
        return f"minio://{self.BUCKET}/{prefix}{filename}"

    def _parse_path(self, path: str) -> tuple[str, str]:
        """解析 minio://bucket/key 为 (bucket, key)"""
        if path.startswith("minio://"):
            path = path[8:]  # strip prefix
        parts = path.split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""
        return bucket, key

    async def save_audio(self, file_data: bytes, filename: str) -> str:
        key = self.AUDIO_PREFIX + filename
        self.client.put_object(self.BUCKET, key, io.BytesIO(file_data), len(file_data))
        return self._make_path(self.AUDIO_PREFIX, filename)

    async def save_resume(self, file_data: bytes, filename: str) -> str:
        key = self.RESUME_PREFIX + filename
        self.client.put_object(self.BUCKET, key, io.BytesIO(file_data), len(file_data))
        return self._make_path(self.RESUME_PREFIX, filename)

    async def save_export(self, file_data: bytes, filename: str) -> str:
        key = self.EXPORT_PREFIX + filename
        self.client.put_object(self.BUCKET, key, io.BytesIO(file_data), len(file_data))
        return self._make_path(self.EXPORT_PREFIX, filename)

    async def get_file(self, path: str) -> bytes:
        bucket, key = self._parse_path(path)
        resp = self.client.get_object(bucket, key)
        try:
            return resp.read()
        finally:
            resp.close()
            resp.release_conn()

    async def delete_file(self, path: str) -> None:
        bucket, key = self._parse_path(path)
        try:
            self.client.remove_object(bucket, key)
        except Exception as e:
            logger.warning(f"MinIO delete failed for {path}: {e}")

    def exists(self, path: str) -> bool:
        bucket, key = self._parse_path(path)
        try:
            self.client.stat_object(bucket, key)
            return True
        except Exception:
            return False

    async def get_local_path(self, path: str) -> str:
        """下载到临时文件并返回临时路径；调用方负责清理"""
        bucket, key = self._parse_path(path)
        ext = os.path.splitext(key)[1]
        fd, tmp_path = tempfile.mkstemp(suffix=ext)
        os.close(fd)  # 关闭句柄，否则 Windows 下 fget_object 无法覆盖
        try:
            self.client.fget_object(bucket, key, tmp_path)
            return tmp_path
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise


# ── 自动选择后端 ──────────────────────────────────────────

if settings.STORAGE_BACKEND == "minio":
    storage: BaseStorage = MinioStorage()
    logger.info(f"Using MinIO storage: endpoint={settings.MINIO_ENDPOINT}, bucket={settings.MINIO_BUCKET}")
else:
    storage = LocalStorage()
    logger.info("Using local filesystem storage")
