import os
from typing import Dict, List, Optional, Any, Union
import uuid
from datetime import datetime

from app.models import Document, Tag, OCRStatus, SystemSettings


class InMemoryDB:
    """
    In-memory database implementation for development and testing.
    
    Note: This is a temporary solution for development. In production,
    this should be replaced with a proper database like PostgreSQL.
    """
    
    def __init__(self):
        self.documents: Dict[uuid.UUID, Document] = {}
        self.tags: Dict[uuid.UUID, Tag] = {}
        self.settings = SystemSettings()
        
    async def get_document(self, document_id: uuid.UUID) -> Optional[Document]:
        """Get a document by ID."""
        return self.documents.get(document_id)
    
    async def list_documents(
        self, 
        skip: int = 0, 
        limit: int = 100,
        folder_path: Optional[str] = None
    ) -> List[Document]:
        """List documents with pagination and optional folder filtering."""
        docs = list(self.documents.values())
        
        if folder_path:
            docs = [doc for doc in docs if doc.folder_path == folder_path]
            
        return docs[skip:skip+limit]
    
    async def create_document(self, document: Document) -> Document:
        """Create a new document."""
        self.documents[document.id] = document
        return document
    
    async def update_document(
        self, 
        document_id: uuid.UUID, 
        update_data: Dict[str, Any]
    ) -> Optional[Document]:
        """Update a document."""
        if document_id not in self.documents:
            return None
            
        doc = self.documents[document_id]
        
        for key, value in update_data.items():
            if hasattr(doc, key):
                setattr(doc, key, value)
                
        return doc
    
    async def delete_document(self, document_id: uuid.UUID) -> bool:
        """Delete a document."""
        if document_id in self.documents:
            del self.documents[document_id]
            return True
        return False
    
    async def search_documents(
        self,
        text: Optional[str] = None,
        tags: List[str] = [],
        folder_path: Optional[str] = None,
        mime_types: List[str] = [],
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "upload_date",
        sort_order: str = "desc"
    ) -> List[Document]:
        """
        Search documents based on various criteria.
        
        Note: This is a simple implementation for development.
        For production with large datasets, consider using a proper
        search engine like Elasticsearch.
        """
        results = list(self.documents.values())
        
        if text:
            text = text.lower()
            results = [
                doc for doc in results 
                if (doc.ocr_text and text in doc.ocr_text.lower()) or
                   text in doc.filename.lower()
            ]
        
        if tags:
            tag_names = set(tags)
            results = [
                doc for doc in results 
                if any(tag.name in tag_names for tag in doc.tags)
            ]
        
        if folder_path:
            results = [
                doc for doc in results 
                if doc.folder_path == folder_path
            ]
        
        if mime_types:
            mime_set = set(mime_types)
            results = [
                doc for doc in results 
                if doc.mime_type in mime_set
            ]
        
        if date_from:
            results = [
                doc for doc in results 
                if doc.upload_date >= date_from
            ]
        
        if date_to:
            results = [
                doc for doc in results 
                if doc.upload_date <= date_to
            ]
        
        reverse = sort_order.lower() == "desc"
        if sort_by == "upload_date":
            results.sort(key=lambda x: x.upload_date, reverse=reverse)
        elif sort_by == "filename":
            results.sort(key=lambda x: x.filename, reverse=reverse)
        elif sort_by == "size":
            results.sort(key=lambda x: x.size, reverse=reverse)
        
        return results[skip:skip+limit]
    
    async def get_tag(self, tag_id: uuid.UUID) -> Optional[Tag]:
        """Get a tag by ID."""
        return self.tags.get(tag_id)
    
    async def get_tag_by_name(self, name: str) -> Optional[Tag]:
        """Get a tag by name."""
        for tag in self.tags.values():
            if tag.name.lower() == name.lower():
                return tag
        return None
    
    async def list_tags(self) -> List[Tag]:
        """List all tags."""
        return list(self.tags.values())
    
    async def create_tag(self, tag: Tag) -> Tag:
        """Create a new tag."""
        self.tags[tag.id] = tag
        return tag
    
    async def update_tag(
        self, 
        tag_id: uuid.UUID, 
        name: Optional[str] = None,
        color: Optional[str] = None
    ) -> Optional[Tag]:
        """Update a tag."""
        if tag_id not in self.tags:
            return None
            
        tag = self.tags[tag_id]
        
        if name:
            tag.name = name
        if color:
            tag.color = color
                
        return tag
    
    async def delete_tag(self, tag_id: uuid.UUID) -> bool:
        """Delete a tag."""
        if tag_id in self.tags:
            del self.tags[tag_id]
            for doc in self.documents.values():
                doc.tags = [tag for tag in doc.tags if tag.id != tag_id]
            return True
        return False
    
    async def add_tag_to_document(
        self, 
        document_id: uuid.UUID, 
        tag_id: uuid.UUID
    ) -> Optional[Document]:
        """Add a tag to a document."""
        if document_id not in self.documents or tag_id not in self.tags:
            return None
            
        doc = self.documents[document_id]
        tag = self.tags[tag_id]
        
        if not any(t.id == tag.id for t in doc.tags):
            doc.tags.append(tag)
            
        return doc
    
    async def remove_tag_from_document(
        self, 
        document_id: uuid.UUID, 
        tag_id: uuid.UUID
    ) -> Optional[Document]:
        """Remove a tag from a document."""
        if document_id not in self.documents:
            return None
            
        doc = self.documents[document_id]
        doc.tags = [tag for tag in doc.tags if tag.id != tag_id]
            
        return doc
    
    async def get_settings(self) -> SystemSettings:
        """Get system settings."""
        return self.settings
    
    async def update_settings(self, settings: SystemSettings) -> SystemSettings:
        """Update system settings."""
        self.settings = settings
        return self.settings
    
    async def get_storage_info(self) -> Dict[str, Any]:
        """Get storage usage information."""
        total_size = sum(doc.size for doc in self.documents.values())
        
        return {
            "total_documents": len(self.documents),
            "total_size": total_size,
            "storage_type": self.settings.storage_type,
            "storage_location": "memory" if self.settings.storage_type == "local" else self.settings.s3_bucket
        }


db = InMemoryDB()
