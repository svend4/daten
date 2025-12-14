"""
Document management routes
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from pydantic import BaseModel
import aiofiles
import os
from pathlib import Path

from ios_core.system import IOSSystem
from ios_core.config import settings
from ..dependencies import get_ios_system, get_current_active_user

router = APIRouter()


class DocumentResponse(BaseModel):
    document_id: str
    title: str
    classification: dict
    entities_count: int
    relations_count: int
    status: str


class DocumentDetails(BaseModel):
    id: str
    title: str
    document_type: str
    category: str
    domain_name: str
    created_at: str
    tags: List[str]


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    domain_name: str = Query(..., description="Domain to upload to"),
    title: Optional[str] = Query(None, description="Document title"),
    author: Optional[str] = Query(None, description="Document author"),
    tags: List[str] = Query(default=[], description="Document tags"),
    ios: IOSSystem = Depends(get_ios_system),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Upload and process a document
    
    **Supported formats:** PDF, DOCX, TXT, MD
    
    **Processing steps:**
    1. Save file to upload directory
    2. Classify document
    3. Extract entities and relations
    4. Index for search
    5. Save to database
    
    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/documents/upload?domain_name=SGB-IX" \
      -H "Authorization: Bearer $TOKEN" \
      -F "file=@document.pdf" \
      -F "title=My Document"
    ```
    """
    
    # Validate file size
    if file.size and file.size > settings.max_upload_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.max_upload_size / 1024 / 1024}MB"
        )
    
    # Validate file type
    allowed_extensions = ['.pdf', '.docx', '.txt', '.md', '.html']
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save file
    upload_dir = Path(settings.upload_dir) / domain_name
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / file.filename
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    try:
        # Process document
        result = await ios.process_document(
            file_path=str(file_path),
            domain_name=domain_name,
            title=title or file.filename,
            author=author,
            tags=tags
        )
        
        return DocumentResponse(**result)
        
    except Exception as e:
        # Clean up file on error
        if file_path.exists():
            os.remove(file_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentDetails)
async def get_document(
    document_id: str,
    ios: IOSSystem = Depends(get_ios_system),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get document details by ID
    
    **Example:**
    ```bash
    curl "http://localhost:8000/api/documents/abc123" \
      -H "Authorization: Bearer $TOKEN"
    ```
    """
    try:
        document = await ios.get_document(document_id)
        return DocumentDetails(**document)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {str(e)}"
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    ios: IOSSystem = Depends(get_ios_system),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Delete document
    
    **Example:**
    ```bash
    curl -X DELETE "http://localhost:8000/api/documents/abc123" \
      -H "Authorization: Bearer $TOKEN"
    ```
    """
    # TODO: Implement delete in IOSSystem
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Delete not yet implemented"
    )


@router.get("/", response_model=List[DocumentDetails])
async def list_documents(
    domain_name: Optional[str] = Query(None, description="Filter by domain"),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    ios: IOSSystem = Depends(get_ios_system),
    current_user: dict = Depends(get_current_active_user)
):
    """
    List documents with pagination
    
    **Example:**
    ```bash
    curl "http://localhost:8000/api/documents/?domain_name=SGB-IX&limit=20" \
      -H "Authorization: Bearer $TOKEN"
    ```
    """
    # TODO: Implement list in IOSSystem
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="List not yet implemented"
    )