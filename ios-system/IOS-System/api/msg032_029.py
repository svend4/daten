# api/routes/documents.py

from asyncio import Lock

# Global lock for document processing
upload_lock = Lock()

@router.post("/upload")
async def upload_document(...):
    async with upload_lock:
        # Process document (prevents race conditions)
        result = await ios.process_document(...)
    
    return result