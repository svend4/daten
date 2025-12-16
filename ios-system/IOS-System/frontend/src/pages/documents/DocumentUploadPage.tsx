/**
 * Document Upload Page - Upload files (PDF, DOCX, TXT)
 */
import { useState } from 'react'
import { Upload, FileText, Loader2, CheckCircle, AlertCircle, X } from 'lucide-react'
import { toast } from 'sonner'
import api from '@services/api'

interface UploadedFile {
  file: File
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress: number
  error?: string
  documentId?: string
}

export default function DocumentUploadPage() {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const droppedFiles = Array.from(e.dataTransfer.files)
    addFiles(droppedFiles)
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files)
      addFiles(selectedFiles)
    }
  }

  const addFiles = (newFiles: File[]) => {
    const uploadFiles: UploadedFile[] = newFiles.map(file => ({
      file,
      status: 'pending',
      progress: 0
    }))
    setFiles(prev => [...prev, ...uploadFiles])
  }

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const uploadFile = async (uploadedFile: UploadedFile, index: number) => {
    try {
      // Update status to uploading
      setFiles(prev => prev.map((f, i) =>
        i === index ? { ...f, status: 'uploading', progress: 0 } : f
      ))

      // Read file content
      const text = await readFileAsText(uploadedFile.file)

      // Simulate progress
      for (let progress = 0; progress <= 90; progress += 30) {
        await new Promise(resolve => setTimeout(resolve, 200))
        setFiles(prev => prev.map((f, i) =>
          i === index ? { ...f, progress } : f
        ))
      }

      // Create document
      const result = await api.createDocument({
        title: uploadedFile.file.name.replace(/\.[^/.]+$/, ''),
        content: text,
        tags: [uploadedFile.file.type.includes('pdf') ? 'pdf' : 'document'],
        category: 'uploaded'
      })

      // Update to success
      setFiles(prev => prev.map((f, i) =>
        i === index
          ? { ...f, status: 'success', progress: 100, documentId: result.id }
          : f
      ))

      toast.success(`${uploadedFile.file.name} загружен успешно`)
    } catch (error: any) {
      setFiles(prev => prev.map((f, i) =>
        i === index
          ? { ...f, status: 'error', error: error.response?.data?.detail || 'Upload failed' }
          : f
      ))
      toast.error(`Ошибка загрузки ${uploadedFile.file.name}`)
    }
  }

  const readFileAsText = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => resolve(e.target?.result as string || '')
      reader.onerror = reject
      reader.readAsText(file)
    })
  }

  const uploadAll = async () => {
    setUploading(true)
    const pendingFiles = files
      .map((f, i) => ({ file: f, index: i }))
      .filter(({ file }) => file.status === 'pending')

    for (const { file, index } of pendingFiles) {
      await uploadFile(file, index)
    }
    setUploading(false)
  }

  const getFileIcon = (type: string) => {
    if (type.includes('pdf')) return '📄'
    if (type.includes('word') || type.includes('document')) return '📝'
    if (type.includes('text')) return '📃'
    return '📁'
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Upload className="w-8 h-8 text-primary-600" />
          Загрузка файлов
        </h1>
        <p className="text-gray-600 mt-1">Загрузите документы в систему (PDF, DOCX, TXT, MD)</p>
      </div>

      {/* Upload Area */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
          dragActive
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 bg-white hover:border-primary-400'
        }`}
      >
        <Upload className={`w-16 h-16 mx-auto mb-4 ${dragActive ? 'text-primary-600' : 'text-gray-400'}`} />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Перетащите файлы сюда
        </h3>
        <p className="text-gray-600 mb-4">или</p>
        <label className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 cursor-pointer transition-colors">
          <FileText className="w-5 h-5" />
          Выбрать файлы
          <input
            type="file"
            multiple
            accept=".pdf,.docx,.txt,.md"
            onChange={handleFileInput}
            className="hidden"
          />
        </label>
        <p className="text-sm text-gray-500 mt-4">
          Поддерживаемые форматы: PDF, DOCX, TXT, MD (макс. 10 MB)
        </p>
      </div>

      {/* Files List */}
      {files.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">
              Файлы ({files.length})
            </h2>
            {files.some(f => f.status === 'pending') && (
              <button
                onClick={uploadAll}
                disabled={uploading}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Загрузка...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    Загрузить все
                  </>
                )}
              </button>
            )}
          </div>

          <div className="divide-y divide-gray-200">
            {files.map((uploadedFile, index) => (
              <div key={index} className="p-4">
                <div className="flex items-start gap-4">
                  <div className="text-3xl">{getFileIcon(uploadedFile.file.type)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="font-medium text-gray-900 truncate">
                        {uploadedFile.file.name}
                      </h3>
                      <div className="flex items-center gap-2">
                        {uploadedFile.status === 'success' && (
                          <CheckCircle className="w-5 h-5 text-green-600" />
                        )}
                        {uploadedFile.status === 'error' && (
                          <AlertCircle className="w-5 h-5 text-red-600" />
                        )}
                        {uploadedFile.status === 'pending' && (
                          <button
                            onClick={() => removeFile(index)}
                            className="p-1 hover:bg-gray-100 rounded"
                          >
                            <X className="w-4 h-4 text-gray-500" />
                          </button>
                        )}
                      </div>
                    </div>
                    <p className="text-sm text-gray-500">
                      {formatFileSize(uploadedFile.file.size)}
                    </p>

                    {/* Progress Bar */}
                    {uploadedFile.status === 'uploading' && (
                      <div className="mt-2">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${uploadedFile.progress}%` }}
                          />
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          {uploadedFile.progress}%
                        </p>
                      </div>
                    )}

                    {/* Error Message */}
                    {uploadedFile.status === 'error' && uploadedFile.error && (
                      <p className="text-sm text-red-600 mt-1">
                        {uploadedFile.error}
                      </p>
                    )}

                    {/* Success Message */}
                    {uploadedFile.status === 'success' && (
                      <p className="text-sm text-green-600 mt-1">
                        ✓ Загружено успешно
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
