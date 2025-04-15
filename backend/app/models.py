from datetime import datetime
import enum
import uuid
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class OCRStatus(str, enum.Enum):
    """Status of OCR processing for a document."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Tag(BaseModel):
    """Tag model for document categorization."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    color: str = "#808080"  # Default gray color


class DocumentBase(BaseModel):
    """Base model for document metadata."""
    filename: str
    mime_type: str
    size: int
    folder_path: str = "/"  # Default to root folder


class DocumentCreate(DocumentBase):
    """Model for document creation."""
    tags: List[str] = []  # List of tag names to apply


class Document(DocumentBase):
    """Full document model with OCR and storage information."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    file_path: str
    thumbnail_path: Optional[str] = None
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    ocr_status: OCRStatus = OCRStatus.PENDING
    ocr_text: Optional[str] = None
    ocr_engine: Optional[str] = None
    ocr_engine_version: Optional[str] = None
    tags: List[Tag] = []
    metadata: Dict[str, Any] = {}

    class Config:
        orm_mode = True


class DocumentUpdate(BaseModel):
    """Model for document updates."""
    folder_path: Optional[str] = None
    ocr_status: Optional[OCRStatus] = None
    ocr_text: Optional[str] = None
    ocr_engine: Optional[str] = None
    ocr_engine_version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchQuery(BaseModel):
    """Model for search queries."""
    text: Optional[str] = None
    tags: List[str] = []
    folder_path: Optional[str] = None
    mime_types: List[str] = []
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = 1
    page_size: int = 20
    sort_by: str = "upload_date"
    sort_order: str = "desc"


class SystemSettings(BaseModel):
    """Model for system settings."""
    storage_type: str = "local"  # "local" or "s3"
    s3_endpoint: Optional[str] = None
    s3_bucket: Optional[str] = None
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    max_zip_size: int = 50 * 1024 * 1024  # 50MB
    default_ocr_engine: str = "tesseract"


class StorageInfo(BaseModel):
    """Model for storage usage information."""
    total_documents: int
    total_size: int  # in bytes
    storage_type: str
    storage_location: str
