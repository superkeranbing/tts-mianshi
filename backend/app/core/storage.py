import os
import aiofiles
from app.config import get_settings

settings = get_settings()

class LocalStorage:
    """本地文件存储，替代 MinIO"""
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

    def get_absolute_path(self, relative_path: str) -> str:
        return os.path.abspath(relative_path)

storage = LocalStorage()
