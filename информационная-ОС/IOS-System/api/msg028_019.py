# Integrate API with persistence
# api/routes/documents.py

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile,
    domain_name: str,
    ios: IOSSystem = Depends(get_ios_system),
    db: AsyncSession = Depends(get_db)
):
    # Save file
    file_path = await save_upload(file)
    
    # Process with IOS
    doc, classification, entities = await ios.add_document(
        file_path, domain_name
    )
    
    # Save to database
    doc_repo = DocumentRepository(db)
    await doc_repo.save(doc)
    
    return {
        "doc_id": doc.id,
        "classification": classification.to_dict(),
        "entities_count": len(entities)
    }