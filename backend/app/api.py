from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
import uuid
import io
import zipfile
import mimetypes
import os
from datetime import datetime

from app.models import (
    Document, DocumentCreate, DocumentUpdate, Tag, 
    SearchQuery, SystemSettings, StorageInfo, OCRStatus
)
from app.database import db
from app.storage import get_storage, StorageError
from app.ocr import get_ocr_processor, get_available_ocr_engines, OCRError


router = APIRouter()


@router.post("/documents", response_model=Document)
async def create_document(
    file: UploadFile = File(...),
    tags: Optional[str] = Form(None),
    folder_path: str = Form("/"),
    ocr_engine: Optional[str] = Form(None)
):
    """
    Upload a new document and process it with OCR.
    
    Args:
        file: The file to upload
        tags: Comma-separated list of tag names
        folder_path: Virtual folder path for organization
        ocr_engine: OCR engine to use (defaults to system setting)
        
    Returns:
        Document: The created document
    """
    settings = await db.get_settings()
    
    content = await file.read()
    file_size = len(content)
    
    if file_size > settings.max_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_file_size} bytes"
        )
    
    file_content = io.BytesIO(content)
    
    storage = await get_storage()
    
    filename = file.filename
    mime_type = file.content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    
    if mime_type == "application/zip":
        if file_size > settings.max_zip_size:
            raise HTTPException(
                status_code=413,
                detail=f"ZIP file too large. Maximum size is {settings.max_zip_size} bytes"
            )
            
        documents = []
        with zipfile.ZipFile(file_content) as zip_file:
            for zip_info in zip_file.infolist():
                if zip_info.is_dir():
                    continue
                    
                if zip_info.file_size > settings.max_file_size:
                    continue
                    
                file_mime_type = mimetypes.guess_type(zip_info.filename)[0]
                if not file_mime_type or not (
                    file_mime_type.startswith("image/") or 
                    file_mime_type == "application/pdf"
                ):
                    continue
                    
                with zip_file.open(zip_info) as f:
                    file_data = io.BytesIO(f.read())
                    
                try:
                    file_path = await storage.save_file(file_data, zip_info.filename)
                except StorageError as e:
                    raise HTTPException(status_code=500, detail=str(e))
                    
                doc = Document(
                    filename=os.path.basename(zip_info.filename),
                    file_path=file_path,
                    mime_type=file_mime_type or "application/octet-stream",
                    size=zip_info.file_size,
                    folder_path=folder_path,
                    ocr_status=OCRStatus.PENDING
                )
                
                if tags:
                    tag_names = [t.strip() for t in tags.split(",")]
                    for tag_name in tag_names:
                        if not tag_name:
                            continue
                            
                        tag = await db.get_tag_by_name(tag_name)
                        if not tag:
                            tag = Tag(name=tag_name)
                            tag = await db.create_tag(tag)
                            
                        doc.tags.append(tag)
                
                doc = await db.create_document(doc)
                documents.append(doc)
                
                await process_document_ocr(doc.id, ocr_engine or settings.default_ocr_engine)
                
        if documents:
            return documents[0]
        else:
            raise HTTPException(
                status_code=400,
                detail="No valid files found in ZIP archive"
            )
    
    try:
        file_path = await storage.save_file(file_content, filename)
        
        thumbnail_path = None
        if mime_type.startswith("image/"):
            file_content.seek(0)
            thumbnail_path = await storage.create_thumbnail(file_path)
        
        doc = Document(
            filename=filename,
            file_path=file_path,
            thumbnail_path=thumbnail_path,
            mime_type=mime_type,
            size=file_size,
            folder_path=folder_path,
            ocr_status=OCRStatus.PENDING
        )
        
        if tags:
            tag_names = [t.strip() for t in tags.split(",")]
            for tag_name in tag_names:
                if not tag_name:
                    continue
                    
                tag = await db.get_tag_by_name(tag_name)
                if not tag:
                    tag = Tag(name=tag_name)
                    tag = await db.create_tag(tag)
                    
                doc.tags.append(tag)
        
        doc = await db.create_document(doc)
        
        await process_document_ocr(doc.id, ocr_engine or settings.default_ocr_engine)
        
        return doc
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))


async def process_document_ocr(document_id: uuid.UUID, ocr_engine: str):
    """
    Process a document with OCR.
    
    Args:
        document_id: ID of the document to process
        ocr_engine: OCR engine to use
    """
    doc = await db.get_document(document_id)
    if not doc:
        return
    
    await db.update_document(
        document_id,
        {"ocr_status": OCRStatus.PROCESSING}
    )
    
    try:
        storage = await get_storage()
        
        file_content, mime_type = await storage.get_file(doc.file_path)
        
        processor = await get_ocr_processor(ocr_engine)
        
        if mime_type == "application/pdf":
            pages = await processor.process_pdf(file_content)
            text = "\n\n".join(pages)
        else:
            text = await processor.process_image(file_content)
        
        await db.update_document(
            document_id,
            {
                "ocr_status": OCRStatus.COMPLETED,
                "ocr_text": text,
                "ocr_engine": processor.name,
                "ocr_engine_version": processor.version
            }
        )
    except (StorageError, OCRError) as e:
        await db.update_document(
            document_id,
            {
                "ocr_status": OCRStatus.FAILED,
                "metadata": {"error": str(e)}
            }
        )


@router.get("/documents", response_model=List[Document])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    folder_path: Optional[str] = None
):
    """
    List documents with pagination and optional folder filtering.
    
    Args:
        skip: Number of documents to skip
        limit: Maximum number of documents to return
        folder_path: Filter by folder path
        
    Returns:
        List[Document]: List of documents
    """
    return await db.list_documents(skip, limit, folder_path)


@router.get("/documents/{document_id}", response_model=Document)
async def get_document(document_id: uuid.UUID):
    """
    Get a document by ID.
    
    Args:
        document_id: ID of the document to get
        
    Returns:
        Document: The document
    """
    doc = await db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/documents/{document_id}")
async def delete_document(document_id: uuid.UUID):
    """
    Delete a document.
    
    Args:
        document_id: ID of the document to delete
        
    Returns:
        Dict[str, bool]: Success status
    """
    doc = await db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    storage = await get_storage()
    
    try:
        await storage.delete_file(doc.file_path)
        
        if doc.thumbnail_path:
            await storage.delete_file(doc.thumbnail_path)
    except StorageError:
        pass
    
    success = await db.delete_document(document_id)
    
    return {"success": success}


@router.get("/documents/{document_id}/original")
async def get_document_original(document_id: uuid.UUID):
    """
    Get the original file for a document.
    
    Args:
        document_id: ID of the document
        
    Returns:
        StreamingResponse: The file content
    """
    doc = await db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    storage = await get_storage()
    
    try:
        file_content, mime_type = await storage.get_file(doc.file_path)
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return StreamingResponse(
        file_content,
        media_type=mime_type,
        headers={"Content-Disposition": f'attachment; filename="{doc.filename}"'}
    )


@router.get("/documents/{document_id}/thumbnail")
async def get_document_thumbnail(document_id: uuid.UUID):
    """
    Get the thumbnail for a document.
    
    Args:
        document_id: ID of the document
        
    Returns:
        StreamingResponse: The thumbnail content
    """
    doc = await db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not doc.thumbnail_path:
        raise HTTPException(status_code=404, detail="Thumbnail not available")
    
    storage = await get_storage()
    
    try:
        file_content, mime_type = await storage.get_file(doc.thumbnail_path)
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return StreamingResponse(
        file_content,
        media_type=mime_type
    )


@router.post("/documents/{document_id}/reocr")
async def reocr_document(
    document_id: uuid.UUID,
    ocr_engine: Optional[str] = None
):
    """
    Re-process a document with OCR.
    
    Args:
        document_id: ID of the document to process
        ocr_engine: OCR engine to use
        
    Returns:
        Dict[str, str]: Status message
    """
    doc = await db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    settings = await db.get_settings()
    
    await process_document_ocr(document_id, ocr_engine or settings.default_ocr_engine)
    
    return {"status": "OCR processing started"}


@router.get("/search", response_model=List[Document])
async def search_documents(
    q: Optional[str] = None,
    tags: Optional[str] = None,
    folder_path: Optional[str] = None,
    mime_types: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "upload_date",
    sort_order: str = "desc"
):
    """
    Search documents based on various criteria.
    
    Args:
        q: Text to search for
        tags: Comma-separated list of tag names
        folder_path: Filter by folder path
        mime_types: Comma-separated list of MIME types
        date_from: Filter by upload date (from)
        date_to: Filter by upload date (to)
        page: Page number
        page_size: Number of documents per page
        sort_by: Field to sort by
        sort_order: Sort order (asc or desc)
        
    Returns:
        List[Document]: List of matching documents
    """
    tag_list = []
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    
    mime_type_list = []
    if mime_types:
        mime_type_list = [t.strip() for t in mime_types.split(",") if t.strip()]
    
    skip = (page - 1) * page_size
    
    return await db.search_documents(
        text=q,
        tags=tag_list,
        folder_path=folder_path,
        mime_types=mime_type_list,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.post("/search/advanced", response_model=List[Document])
async def advanced_search(query: SearchQuery):
    """
    Advanced search with complex query.
    
    Args:
        query: Search query
        
    Returns:
        List[Document]: List of matching documents
    """
    skip = (query.page - 1) * query.page_size
    
    return await db.search_documents(
        text=query.text,
        tags=query.tags,
        folder_path=query.folder_path,
        mime_types=query.mime_types,
        date_from=query.date_from,
        date_to=query.date_to,
        skip=skip,
        limit=query.page_size,
        sort_by=query.sort_by,
        sort_order=query.sort_order
    )


@router.get("/folders")
async def list_folders():
    """
    List all folders.
    
    Returns:
        List[Dict[str, Any]]: List of folders
    """
    docs = await db.list_documents(0, 1000000)  # Get all documents
    
    folders = set()
    for doc in docs:
        parts = doc.folder_path.strip("/").split("/")
        current_path = "/"
        folders.add(current_path)
        
        for part in parts:
            if not part:
                continue
            current_path = f"{current_path}{part}/"
            folders.add(current_path)
    
    folder_list = []
    for folder in sorted(folders):
        count = sum(1 for doc in docs if doc.folder_path == folder)
        
        folder_list.append({
            "path": folder,
            "name": os.path.basename(folder.rstrip("/")) or "Root",
            "document_count": count
        })
    
    return folder_list


@router.post("/folders")
async def create_folder(path: str = Query(...)):
    """
    Create a new folder.
    
    Args:
        path: Folder path
        
    Returns:
        Dict[str, str]: Status message
    """
    if not path.startswith("/"):
        path = f"/{path}"
    
    if not path.endswith("/"):
        path = f"{path}/"
    
    return {"status": "Folder created", "path": path}


@router.get("/folders/{path:path}")
async def get_folder_contents(
    path: str,
    skip: int = 0,
    limit: int = 100
):
    """
    Get the contents of a folder.
    
    Args:
        path: Folder path
        skip: Number of documents to skip
        limit: Maximum number of documents to return
        
    Returns:
        Dict[str, Any]: Folder contents
    """
    if not path.startswith("/"):
        path = f"/{path}"
    
    if not path.endswith("/"):
        path = f"{path}/"
    
    docs = await db.list_documents(skip, limit, path)
    
    return {
        "path": path,
        "name": os.path.basename(path.rstrip("/")) or "Root",
        "documents": docs
    }


@router.post("/tags", response_model=Tag)
async def create_tag(tag: Tag):
    """
    Create a new tag.
    
    Args:
        tag: Tag to create
        
    Returns:
        Tag: The created tag
    """
    existing_tag = await db.get_tag_by_name(tag.name)
    if existing_tag:
        raise HTTPException(
            status_code=400,
            detail=f"Tag with name '{tag.name}' already exists"
        )
    
    return await db.create_tag(tag)


@router.get("/tags", response_model=List[Tag])
async def list_tags():
    """
    List all tags.
    
    Returns:
        List[Tag]: List of tags
    """
    return await db.list_tags()


@router.put("/tags/{tag_id}", response_model=Tag)
async def update_tag(
    tag_id: uuid.UUID,
    name: Optional[str] = None,
    color: Optional[str] = None
):
    """
    Update a tag.
    
    Args:
        tag_id: ID of the tag to update
        name: New name for the tag
        color: New color for the tag
        
    Returns:
        Tag: The updated tag
    """
    tag = await db.update_tag(tag_id, name, color)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    return tag


@router.delete("/tags/{tag_id}")
async def delete_tag(tag_id: uuid.UUID):
    """
    Delete a tag.
    
    Args:
        tag_id: ID of the tag to delete
        
    Returns:
        Dict[str, bool]: Success status
    """
    success = await db.delete_tag(tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    return {"success": success}


@router.post("/documents/{document_id}/tags/{tag_id}")
async def add_tag_to_document(document_id: uuid.UUID, tag_id: uuid.UUID):
    """
    Add a tag to a document.
    
    Args:
        document_id: ID of the document
        tag_id: ID of the tag
        
    Returns:
        Document: The updated document
    """
    doc = await db.add_tag_to_document(document_id, tag_id)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Document or tag not found"
        )
    
    return doc


@router.delete("/documents/{document_id}/tags/{tag_id}")
async def remove_tag_from_document(document_id: uuid.UUID, tag_id: uuid.UUID):
    """
    Remove a tag from a document.
    
    Args:
        document_id: ID of the document
        tag_id: ID of the tag
        
    Returns:
        Document: The updated document
    """
    doc = await db.remove_tag_from_document(document_id, tag_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return doc


@router.get("/system/storage", response_model=StorageInfo)
async def get_storage_info():
    """
    Get storage usage information.
    
    Returns:
        StorageInfo: Storage usage information
    """
    info = await db.get_storage_info()
    return StorageInfo(**info)


@router.get("/system/ocr-engines")
async def get_ocr_engines():
    """
    Get a list of available OCR engines.
    
    Returns:
        List[Dict[str, Any]]: List of available OCR engines
    """
    return await get_available_ocr_engines()


@router.get("/system/settings", response_model=SystemSettings)
async def get_system_settings():
    """
    Get system settings.
    
    Returns:
        SystemSettings: System settings
    """
    return await db.get_settings()


@router.put("/system/settings", response_model=SystemSettings)
async def update_system_settings(settings: SystemSettings):
    """
    Update system settings.
    
    Args:
        settings: New system settings
        
    Returns:
        SystemSettings: Updated system settings
    """
    return await db.update_settings(settings)
