# ⚠️ ПРОБЛЕМА: Привязка к файловой системе
class DataStorage:
    def store_document(self, doc):
        with open(file_path, 'wb') as f:
            f.write(doc.content)
            
# ✅ РЕШЕНИЕ: Storage interface
class StorageBackend(ABC):
    @abstractmethod
    def store(self, key: str, data: bytes) -> str:
        pass

class FileSystemStorage(StorageBackend):
    ...

class S3Storage(StorageBackend):
    ...