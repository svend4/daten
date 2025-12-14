# api/routes/documents.py

from ios_core.tasks.document_tasks import process_document_async

@router.post("/upload/async", status_code=status.HTTP_202_ACCEPTED)
async def upload_document_async(
    file: UploadFile = File(...),
    domain_name: str = Query(...),
    ...
):
    """
    Upload document and process asynchronously
    
    Returns task ID immediately, processing happens in background
    """
    
    # Save file
    file_path = await save_upload_file(file, domain_name)
    
    # Start background task
    task = process_document_async.delay(
        file_path=str(file_path),
        domain_name=domain_name,
        title=title,
        author=author,
        tags=tags
    )
    
    return {
        "task_id": task.id,
        "status": "processing",
        "message": "Document upload accepted, processing in background"
    }


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    Get status of background task
    """
    from celery.result import AsyncResult
    
    task = AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Task is waiting...'
        }
    elif task.state == 'PROGRESS':
        response = {
            'state': task.state,
            'status': task.info.get('status', ''),
            'progress': task.info.get('progress', 0)
        }
    elif task.state == 'SUCCESS':
        response = {
            'state': task.state,
            'result': task.result
        }
    else:  # FAILURE
        response = {
            'state': task.state,
            'error': str(task.info)
        }
    
    return response