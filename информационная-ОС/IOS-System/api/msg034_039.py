# api/routes/documents.py

from ios_core.security.rbac import require_permission, Permission

@router.post("/upload")
@require_permission(Permission.DOCUMENT_CREATE)
async def upload_document(
    current_user: dict = Depends(get_current_active_user),
    ...
):
    ...

@router.delete("/{document_id}")
@require_permission(Permission.DOCUMENT_DELETE)
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_active_user),
    ...
):
    ...