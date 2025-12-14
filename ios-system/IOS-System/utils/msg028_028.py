# ⚠️ ПРОБЛЕМА: Блокирующие операции
async def upload_document(...):
    # Синхронное чтение файла блокирует event loop
    with open(file_path, 'rb') as f:
        content = f.read()
        
# ✅ РЕШЕНИЕ: Async I/O
async def upload_document(...):
    async with aiofiles.open(file_path, 'rb') as f:
        content = await f.read()