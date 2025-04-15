import os
import shutil
from pathlib import Path
import uuid
from typing import Optional, BinaryIO, Tuple, List
import mimetypes
from PIL import Image
import io

from app.database import db
from app.models import SystemSettings


class StorageError(Exception):
    """Exception raised for storage-related errors."""
    pass


class StorageBase:
    """Base class for storage implementations."""
    
    async def save_file(self, file_content: BinaryIO, filename: str) -> str:
        """
        Save a file to storage.
        
        Args:
            file_content: File-like object containing the file data
            filename: Original filename
            
        Returns:
            str: Path or identifier for the stored file
        """
        raise NotImplementedError
    
    async def get_file(self, file_path: str) -> Tuple[BinaryIO, str]:
        """
        Retrieve a file from storage.
        
        Args:
            file_path: Path or identifier of the file
            
        Returns:
            Tuple[BinaryIO, str]: File content and mime type
        """
        raise NotImplementedError
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            file_path: Path or identifier of the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        raise NotImplementedError
    
    async def create_thumbnail(self, file_path: str, max_size: Tuple[int, int] = (200, 200)) -> Optional[str]:
        """
        Create a thumbnail for an image file.
        
        Args:
            file_path: Path or identifier of the image file
            max_size: Maximum dimensions (width, height) for the thumbnail
            
        Returns:
            Optional[str]: Path or identifier for the thumbnail, or None if not an image
        """
        try:
            file_content, mime_type = await self.get_file(file_path)
            
            if not mime_type.startswith('image/'):
                return None
                
            img = Image.open(file_content)
            img.thumbnail(max_size)
            
            thumb_buffer = io.BytesIO()
            img.save(thumb_buffer, format=img.format)
            thumb_buffer.seek(0)
            
            thumb_path = f"{file_path}_thumbnail"
            
            return await self.save_file(thumb_buffer, f"thumb_{os.path.basename(file_path)}")
        except Exception as e:
            print(f"Error creating thumbnail: {e}")
            return None


class LocalStorage(StorageBase):
    """Local filesystem storage implementation."""
    
    def __init__(self, base_dir: str = "storage"):
        """
        Initialize local storage.
        
        Args:
            base_dir: Base directory for file storage
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        (self.base_dir / "documents").mkdir(exist_ok=True)
        (self.base_dir / "thumbnails").mkdir(exist_ok=True)
    
    async def save_file(self, file_content: BinaryIO, filename: str) -> str:
        """Save a file to local storage."""
        ext = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = self.base_dir / "documents" / unique_filename
        
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file_content, f)
            
        return str(file_path)
    
    async def get_file(self, file_path: str) -> Tuple[BinaryIO, str]:
        """Retrieve a file from local storage."""
        path = Path(file_path)
        
        if not path.exists():
            raise StorageError(f"File not found: {file_path}")
            
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"
            
        return open(path, "rb"), mime_type
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete a file from local storage."""
        path = Path(file_path)
        
        if not path.exists():
            return False
            
        try:
            path.unlink()
            return True
        except Exception:
            return False


class S3Storage(StorageBase):
    """
    S3-compatible storage implementation.
    
    Note: This is a placeholder implementation. In a real application,
    you would use boto3 or another S3 client library.
    """
    
    def __init__(self, settings: SystemSettings):
        """
        Initialize S3 storage.
        
        Args:
            settings: System settings containing S3 configuration
        """
        self.settings = settings
        
    async def save_file(self, file_content: BinaryIO, filename: str) -> str:
        """
        Save a file to S3 storage.
        
        Note: This is a placeholder implementation.
        """
        ext = os.path.splitext(filename)[1]
        unique_key = f"documents/{uuid.uuid4()}{ext}"
        
        
        return unique_key
    
    async def get_file(self, file_path: str) -> Tuple[BinaryIO, str]:
        """
        Retrieve a file from S3 storage.
        
        Note: This is a placeholder implementation.
        """
        
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"
            
        raise StorageError("S3 storage is not fully implemented")
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from S3 storage.
        
        Note: This is a placeholder implementation.
        """
        
        return False


async def get_storage():
    """
    Factory function to get the appropriate storage implementation.
    
    Returns:
        StorageBase: Storage implementation based on system settings
    """
    settings = await db.get_settings()
    
    if settings.storage_type == "s3":
        return S3Storage(settings)
    else:
        return LocalStorage()
